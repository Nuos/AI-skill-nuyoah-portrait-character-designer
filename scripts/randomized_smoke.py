#!/usr/bin/env python3
"""Seeded, offline multi-character plan/prompt regression. No images or network calls."""
import argparse
import copy
import hashlib
import json
import random
from pathlib import Path
try:
    from .check_turnaround import check, load_plan
    from .build_prompt import render, VIEWS
except ImportError:
    from check_turnaround import check, load_plan
    from build_prompt import render, VIEWS

ROOT = Path(__file__).resolve().parents[1]
STAGES = (
    ("infant", 0.5, "六个月婴儿，保留婴儿自然外观与安全受托姿态"),
    ("child", 8, "8岁儿童的自然外观，不成人化"),
    ("adolescent", 16, "16岁青少年，自然、适龄，无成人化妆"),
    ("adult", 34, "34岁成年人，保留自然细纹与皮肤质感"),
    ("older_adult", 78, "78岁老人，保留真实年龄纹理，不嫩化、不夸张衰弱"),
    ("unspecified", None, "年龄未指定，依已定义角色基准，不自动填成年或年轻化"),
)
ERAS = (
    ("古代启发", "朴素交领长衣与同材质长裤，布带系腰，平底布鞋，无现代标志"),
    ("近现代启发", "米色布衬衫、深色直筒长裤、平底系带鞋，无品牌标志"),
    ("当代", "浅灰圆领长袖上衣、直筒棉裤、平底鞋，无品牌标志"),
    ("未来架空", "哑光浅色长袖连体工作服、简洁拼接缝和低帮鞋，不发光，无装甲"),
    ("神话影视化", "米白长袖束腰长衣、同色长裤、朴素平底鞋，无披风、无手持道具"),
    ("架空年代", "无年代标记的长袖织物上衣与长裤、无品牌平底鞋"),
    ("年代未指定", "用户草案中的素色长袖上衣、长裤与平底鞋，不添加年代标记"),
)
FACES = (
    "偏宽椭圆脸，眉骨平缓、眼窝较浅，颧部中等宽度、下颌角圆缓，短圆下巴；细长眼、自然平眉、宽鼻背、下唇略丰满",
    "长椭圆轮廓，眉骨轻微起伏、眼窝适中，颧部内收、下颌略窄，圆钝下巴；眼距适中、柔弧眉、平直鼻梁、上下唇接近",
    "方圆轮廓，眉骨起伏平缓，颧部与下颌宽度接近、面颊饱满；短眼裂、眉尾略弯、圆鼻尖、嘴唇宽度适中",
    "均衡椭圆轮廓，眉骨与眼窝过渡柔和，颧部稍宽于下颌、短圆下巴；杏形眼、平直眉、鼻翼有自然体量、上唇略薄",
)


def make_plans(seed=20260925, count=24):
    if type(seed) is not int or type(count) is not int or not 1 <= count <= 1000:
        raise ValueError("seed must be an integer and count must be 1..1000")
    rng = random.Random(seed)
    base = load_plan(ROOT / "examples/turnaround-plan.json")
    order = list(range(len(STAGES)))
    rng.shuffle(order)
    plans = []
    for index in range(count):
        p = copy.deepcopy(base)
        stage, years, appearance = STAGES[order[index % len(order)]]
        era, costume = ERAS[rng.randrange(len(ERAS))]
        c = p["character"]
        gender_options = ("男性", "女性", "非二元", "未指定") if stage in ("adult", "older_adult") else ("男性", "女性", "未指定")
        c.update(id="RND-" + format(index + 1, "03d"), asset_version="test-v1", gender=rng.choice(gender_options),
                 age={"years": years, "appearance": appearance, "life_stage": stage},
                 identity_anchor=rng.choice(FACES), expression="目光平静自然，嘴唇轻合，不夸张表演", marks=[])
        c["era"] = {"setting": era, "culture": "原创虚构人物，不由服装或地域推断族裔", "accuracy": "inspired", "source_urls": []}
        c["body"] = {"description": rng.choice(("自然中等体型，肩部与骨盆协调，四肢长度与本年龄相符", "自然偏圆润体型，保留软组织体量，不瘦身、不拉腿")),
                     "height_cm": None, "head_body_ratio": None, "proportion_mode": "natural"}
        c["appearance"] = {"skin": rng.choice(("自然浅暖肤色", "自然中等橄榄调肤色", "自然深棕肤色")) + "，保留适龄纹理，不漂白、不添加伤痕或泥污",
                           "hair": rng.choice(("黑色自然短发，固定发际线与耳侧轮廓", "深棕齐肩发，部分别在耳后，不遮双眼")),
                           "makeup": "自然无妆，不添加彩妆或美容磨皮", "costume": costume,
                           "accessories": "无首饰，无手持道具，鞋履与服装描述一致"}
        if stage == "older_adult":
            c["appearance"]["hair"] = rng.choice(("灰白自然短发，固定发际线与耳侧轮廓", "灰黑相间齐肩发，耳侧自然后拢"))
        if stage == "infant":
            c["identity_anchor"] = "婴儿自然饱满面颊，低起伏眉骨、浅眼窝、短圆下巴，细软眉毛、圆鼻尖；眼鼻唇比例与婴儿阶段相符，不塑造成成人面部"
            c["body"]["description"] = "婴儿自然的头躯干和四肢比例，保留圆润软组织，不采用成人骨架"
            c["appearance"].update(hair="稀疏柔软的深色婴儿头发", costume="适龄不透明长袖长裤连体衣，松软织物，不束腰、不加硬质配件", accessories="无首饰或手持道具，柔软包脚连体衣")
            c["pose"] = {"posture":"supported_reclining", "description":"婴儿在稳定承托垫上自然受托，头颈躯干充分支撑，不强行摆正或转动身体", "support":"宽阔稳定的软垫，保留必要支撑与自然遮挡"}
            c["reference"]["unknown_features"] = ["受托姿态下被支撑遮挡的背部不可确认，背面验收应为PARTIAL"]
        else:
            c["pose"] = {"posture":"standing", "description":"自然中性直立，双脚平行略分，双臂下垂略离躯干，手指自然放松", "support":"无"}
        p["sheet"].update(width_px=2048, height_px=1152, side=rng.choice(("left", "right")))
        for v in p["sheet"]["views"]:
            v.update(character_id=c["id"], asset_version=c["asset_version"])
        p["locks"] = {"character.identity_anchor": c["identity_anchor"], "character.age": copy.deepcopy(c["age"]), "character.gender":c["gender"]}
        p["vocabulary"] = {"include":[], "exclude":[]}
        p["request"]["text"] = "随机回归原创样例；" + c["gender"] + "；" + appearance + "；" + era + "。四视图，自然比例，无妆，无文字。"
        plans.append(p)
    return plans


def invalid_variants(plan):
    tests = []
    for name, path, value in (
        ("profile_45", ("sheet","views",2,"angle_degrees"), 45),
        ("scale_drift", ("sheet","views",2,"scale"), 0.87),
        ("baseline_drift", ("sheet","views",3,"baseline"), 0.8),
        ("identity_drift", ("sheet","views",1,"character_id"), "OTHER"),
        ("implicit_nine_heads", ("character","body","head_body_ratio"), 9),
        ("age_lock_drift", ("character","age","appearance"), "错误变更年龄"),
        ("invalid_vocabulary", ("vocabulary","include"), ["not.a.term"]),
        ("image_without_authorization", ("request","mode"), "image"),
    ):
        p=copy.deepcopy(plan); obj=p
        for key in path[:-1]: obj=obj[key]
        obj[path[-1]]=value
        tests.append((name,p))
    return tests


def run(seed=20260925, count=24, out=None):
    plans = make_plans(seed, count)
    records=[]; rejected=0
    dest=Path(out).resolve() if out else None
    if dest:
        # Refuse an occupied directory rather than deleting or mixing old artifacts.
        if dest.exists() and any(dest.iterdir()):
            raise ValueError("Output directory must be empty")
        dest.mkdir(parents=True, exist_ok=True)
    for p in plans:
        result=check(p)
        if result["status"] != "PASS": raise AssertionError(result)
        before=copy.deepcopy(p); prompts={v:render(p,v) for v in VIEWS}
        if p != before: raise AssertionError("Compiler mutated input")
        for v, text in prompts.items():
            if p["character"]["identity_anchor"] not in text: raise AssertionError("Lost identity anchor")
            if "188" in text or "9 头身" in text: raise AssertionError("Specific preset leaked")
            if v == "portrait" and "脚部裁切" in text: raise AssertionError("Full-body negatives leaked into portrait")
        negatives=[]
        for name,bad in invalid_variants(p):
            r=check(bad)
            if r["status"] != "FAIL": raise AssertionError("Mutation accepted: " + name)
            rejected+=1;negatives.append(name)
        cid=p["character"]["id"]
        records.append({"id":cid,"gender":p["character"]["gender"],"age":p["character"]["age"],"era":p["character"]["era"]["setting"],
                        "side":p["sheet"]["side"],"plan_status":"PASS","prompt_sha256":{v:hashlib.sha256(t.encode()).hexdigest() for v,t in prompts.items()},
                        "rejected_mutations":negatives,"image_review":"UNVERIFIED"})
        if dest:
            folder=dest/cid;folder.mkdir()
            (folder/"plan.json").write_text(json.dumps(p,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            for v,t in prompts.items():(folder/(v+".txt")).write_text(t,encoding="utf-8")
    report={"schema_version":1,"seed":seed,"sampling":"seeded stratified age coverage; other fields pseudorandom, not population statistics",
            "plan_count":len(plans),"prompt_count":len(plans)*len(VIEWS),"rejected_mutations":rejected,"status":"PASS",
            "scope":"offline structured plans and compiled text; not model inference or image validation","cases":records}
    if dest:(dest/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed",type=int,default=20260925)
    parser.add_argument("--count",type=int,default=24)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    try:
        report=run(args.seed,args.count,args.out)
    except (OSError,UnicodeError,ValueError,AssertionError) as exc:
        parser.exit(1,"Random regression failed: "+str(exc)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
