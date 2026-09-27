#!/usr/bin/env python3
"""Compile scoped vocabulary and a validated plan; never call a media service."""
import argparse
import sys
from pathlib import Path
try:
    from .check_turnaround import check, load_plan, selected_terms
except ImportError:
    from check_turnaround import check, load_plan, selected_terms

VIEWS = ("sheet", "portrait", "front", "side", "back")


def validate(plan, view):
    if view not in VIEWS:
        raise ValueError("Unknown view: " + str(view))
    report = check(plan)
    if report["status"] != "PASS":
        raise ValueError("Invalid plan: " + "; ".join(report["errors"]))


def negative_prompt(plan, view="sheet"):
    """View-scoped, deduplicated negatives, without rewriting the source plan."""
    validate(plan, view)
    return "，".join(dict.fromkeys(word for term in selected_terms(plan, view)
                                  for word in term["negative"]))


def render(plan, view="sheet", include_negative=True):
    validate(plan, view)
    c, s = plan["character"], plan["sheet"]
    age, body, look, pose = (c[k] for k in ("age", "body", "appearance", "pose"))
    side = "左侧" if s["side"] == "left" else "右侧"
    nose = "画面左方" if s["side"] == "left" else "画面右方"
    labels = {
        "portrait": "正面人像特写，0°，完整头顶至锁骨，眼平机位，不裁切头发、可见耳部或下巴",
        "front": "正面全身，0°，头部、胸腔、骨盆共同正对镜头，完整头顶至身体最下缘",
        "side": "标准侧面全身，90°，展示角色自身" + side + "，鼻尖朝" + nose + "；头部、胸腔、骨盆同向，不是三分之四视角，不用镜像伪造",
        "back": "背面全身，180°，完全背对镜头，不回头，保留后脑、服装背部及身体最下缘",
    }
    if pose["posture"].startswith("supported_"):
        labels["back"] = "背面参考方向，180°；保留必要支撑及自然遮挡，仅记录可安全展示的后脑与服装背部；无法完整展示时标记验收状态 PARTIAL，不移除支撑、不强行转动身体"
    parts = ["真人写实人物定妆参考照。"]
    if view == "sheet":
        parts += ["【画面布局】\n横向四列参考表，画幅 " + s["aspect_ratio"] + "，目标交付尺寸 " +
                  str(s["width_px"]) + "×" + str(s["height_px"]) + " 像素；只呈现同一个人的四个参考视图。",
                  "从左到右严格排列：\n" + "\n".join(str(i+1) + "、" + labels[k] + "。" for i, k in enumerate(labels)),
                  "人像特写占整张画面宽度约 " + format(s["portrait_fraction"]*100, ".6g") +
                  "% ，三张全身均分余宽，轮廓互不重叠。"]
    else:
        parts.append("【独立视图】\n只生成一张独立参考照：" + labels[view] + "。不要拼图或增加其它视图。")
    parts.append("【人物身份与面部】\n" + c["identity_anchor"] + "\n性别设定：" + c["gender"] + "。年龄外观：" + age["appearance"] + "。")
    if age["years"] is not None:
        parts.append("此角色设定的外观年龄为 " + str(age["years"]) + " 岁；保持该阶段，不自动年轻化、成人化或老化。")
    if c.get("expression"):
        parts.append("神情状态：" + c["expression"] + "。所有可见面部状态一致，背面不回头展示表情。")
    sides = {"left":"自身左侧", "right":"自身右侧", "midline":"身体中线", "bilateral":"身体两侧"}
    for mark in c.get("marks", []):
        parts.append("稳定标记：角色" + sides[mark["side"]] + "的" + mark["location"] + "，" + mark["description"] +
                     "。位置、形状和长度固定；只在该部位实际可见时出现，不迁移、不镜像。")
    parts.append("时代与世界设定：" + c["era"]["setting"] + "。文化与职业语境：" + c["era"]["culture"] + "。")
    if c["era"]["accuracy"] == "inspired":
        parts.append("采用时代启发的影视化设计，不宣称严格历史复原。")
    parts.append("【体型与比例】\n" + body["description"] + "。")
    if body["height_cm"] is not None:
        parts.append("角色设定身高 " + str(body["height_cm"]) + " 厘米，保持整体骨架，不靠厚底鞋、低机位或单独拉长小腿伪造身高。")
    if body["head_body_ratio"] is not None:
        parts.append("用户明确指定约 " + str(body["head_body_ratio"]) + " 头身，头部和颈部自然衔接，肩、胸、背、腰、骨盆及四肢协调。")
    else:
        parts.append("采用与年龄、体型和参考证据相符的自然头身比例，不套用统一成人或模特比例。")
    for key, title in (("skin","肤色与皮肤质感"),("hair","头发"),("makeup","妆容"),("costume","服装"),("accessories","配饰与辅助器具")):
        parts.append("【" + title + "】\n" + look[key])
    if view != "portrait":
        parts.append("【姿态】\n" + pose["description"] + "。支撑方式：" + pose["support"] + "。")
    else:
        parts.append("【姿态】\n沿用此角色的头颈、神情及衣领状态；本图只取头顶至锁骨，不要求手脚入画。必要支撑保持不变：" + pose["support"] + "。")
    parts.append("【摄影与照明】\n背景：" + s["background"] + "。光线：" + s["lighting"] + "。")
    if view == "sheet":
        baseline = "脚底基线" if pose["posture"] == "standing" else "身体下缘与支撑接触基线"
        parts.append("三张全身共享缩放比例、同一姿态和" + baseline + "，特写单独放大；是同一状态绕身体垂直轴的观察记录，而非四个独立表演。")
    ref = c["reference"]
    if ref["mode"] == "identity":
        parts.append("【参考身份】\n以实际随任务提供的参考资产为身份依据：" + "；".join(ref["assets"]) +
                     "。不得另选模特或套用审美模板换脸。可见证据：" + "；".join(ref["visible_features"]) + "。")
    elif ref["mode"] == "style_only":
        parts.append("【参考范围】\n参考资产只取造型：" + "；".join(ref["assets"]) + "；不复制参考人物身份。")
    if ref["unknown_features"]:
        parts.append("尚未确认：" + "；".join(ref["unknown_features"]) + "。只能保守补全，不把补全当参考事实，不新增显著标记，不移除必要支撑。")
    if c.get("notes"):
        parts.append("【补充造型约束】\n" + c["notes"])
    parts.append("【一致性与取景约束】\n" + "\n".join(t["text"] for t in selected_terms(plan, view)))
    parts.append("保持适龄、中性的定妆姿态与衣着，不增加无关人物。像素是目标参数，不宣称实际输出已达到原生分辨率。")
    if include_negative:
        parts.append("【负向提示词】\n" + negative_prompt(plan, view))
    return "\n\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--view", choices=VIEWS, default="sheet")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--negative-only", action="store_true")
    group.add_argument("--positive-only", action="store_true")
    args = parser.parse_args()
    try:
        plan = load_plan(args.plan)
        text = negative_prompt(plan, args.view) + "\n" if args.negative_only else render(plan, args.view, not args.positive_only)
        print(text, end="")
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        print("Prompt build failed: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
