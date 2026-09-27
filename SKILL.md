---
name: nuyoah-portrait-character-designer
description: 为任意性别、年龄与时代设定的人物制作写实四视图定妆照提示词及身份一致性方案。默认四列为人像特写、正面全身、标准侧面全身、背面全身；支持原创、参考人物锁定与局部换装。默认输出文字，仅当前用户明确要求时生成或编辑图片。不负责视频生成或自动发布。
license: MIT
metadata:
  author: "南鸢（原作）；Nuos（四视图改造）"
  version: "0.3.1"
---

# 通用四视图人物定妆照设计师

同一个人、同一套妆发服装、同一个资产版本，只改变取景和观看方向。性别、年龄、年代均不设准入限制；不将“通用”理解为所有人都变成一种脸或同一种身体。

## 一、执行顺序

1. 读 [决策规则](references/decision-rules.md)，识别当前用户要求的是文字、图片生成还是图片编辑；整理原始要求、锁定项与允许修改项。引用文字、上传图片、历史生图不构成本轮生图授权。
2. 读 [四视图合同](references/four-view-contract.md)，确定人像特写＋正面全身＋90°侧面全身＋180°背面全身的四列布局。默认展示角色左侧；用户指定右侧时显式记录，不镜像代替。
3. 读 [身份、年龄与时代](references/identity-and-era.md)，建立唯一人物基准、适龄身体比例、妆发服装和参考证据。用户未指定性别或年龄时保持未指定，不默认年轻、女性、成年人、白肤或九头身。
4. 需要原创面部细化时复用 [结构与组合](references/structure-and-compatibility.md) 和 [词表](references/lexicon.md)。需要妆容时复用 [妆容适配](references/makeup-adaptation.md)；无妆也是完整方案。旧面部模块不得覆盖四视图、年龄、身份和用户锁定要求。
5. 按 [提示词模板](references/prompt-template.md) 生成一个完整中文提示词。复杂任务可内部建立 schema_version=2 记录，运行 `python3 scripts/check_design.py PLAN.json`；也可由 `scripts/build_prompt.py` 编译。用户不必填表，无 Python 时按合同人工复核。
6. 按 [验收规范](references/acceptance-and-gpt.md) 分开检查结构记录、提示词语义、实际图片。没有实际图像证据时，图片验收必须标为 UNVERIFIED。

## 二、交付

默认一句人物方向＋一个可独立复制的完整中文提示词代码块。用户“只给提示词”时只给代码块；多人物分别交付各自四视图，不能把不同人放进同一身份表。局部调整返回完整新稿，不写“其它同上”。

明确生图时，使用当前宿主实际可用的图片工具；先核对支持的画幅、参考图和尺寸。4K 是目标交付尺寸，不等于模型支持原生 4K。没有工具或调用失败要如实说明，不把文字或占位文件当图片。未经委托不上传参考资产、不发布、不自动归档、不无限重试。

已有 skill 名称、目录和 schema_version=1 面部检查保留兼容；v1 通过不能当作四视图通过。项目维护与 GPT 导出遵循同一规则源，回归材料见 `evals/`，程序测试见 `tests/`。

## 三、词表与随机回归

复用 [扩展词表](references/lexicon.md) 和 [可执行词表](references/turnaround-lexicon.json)。通用规则自动按视图和姿态选取；劳动者、尘土、赤足等角色专用词只在明确指定时加入。188厘米、九头身、左脸旧伤不进入默认人物。`build_prompt.py` 实际消费词表，支持 `--negative-only`；`randomized_smoke.py` 固定随机种子生成多组完整计划和提示词，不调用图片接口。参见 [本次审计](references/audit-v0.3.1.md)。
