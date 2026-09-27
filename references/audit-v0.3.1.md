# v0.3.1 词表扩展与测试记录

## 一、范围与来源

记录时间：2026-09-25T19:55:30.356696-07:00（America/Los_Angeles）。本次在上轮交付的v0.3.0完整包上增量修改；GitHub main读取结果仍为`99b9a2c90e5b09507c6a61b5c27b9e2740ddb63d`。用户本轮要求补入神话劳作者完整提示词，随后要求提交GitHub并随机测试多组定妆照。

用户原文完整保存于`examples/sources/myth-laborer-user-prompt.txt`。`references/lexicon.md`保留原十七组词条并追加扩展；`references/turnaround-lexicon.json`为编译器直接消费的25条机器词表。范围分布：{"universal": 17, "conditional": 2, "character": 6}。

## 二、优化决策

通用摄影、取景、比例、表情、左右标记与衣服连续性和个体造型分离。中年男性、188厘米、九头身、左脸伤痕、米灰亚麻短袍、尘土和赤足只属于用户预设。神情与标记可用结构化字段锁定；负向词按视图去重，不把特写要求写成全身要求。

准确侧面允许远侧肢体自然遮挡；婴儿支撑保留，不强求背部完整。自然比例词不再全局排斥大头短身或短腿，以免错误压制适龄身体特征。九头身是明确的造型目标，188厘米在无标尺图中不可精确测量；像素目标不等于原生输出能力。

## 三、实际测试

执行环境：Python 3.13.5，Linux。

| 层级 | 结果 | 实际证据与边界 |
|---|---|---|
| 原v0.3.0基线复跑 | PASS | 57项通过，并非照搬旧报告 |
| 当前回归测试 | PASS | 85项通过：原57项＋新增28项；日志`tests/run-v0.3.1.txt` |
| 随机角色输入 | PASS | seed=20260925，24组，6种年龄阶段；有目的地分层覆盖年龄，其它字段伪随机，不代表人口分布 |
| 提示词编译 | PASS | 24×5=120份：每人整表、特写、正面、侧面、背面 |
| 故障注入 | PASS | 24×8=192项全部返回FAIL，覆盖角度、尺度、基线、身份、默认九头身、年龄锁、词条拼错和未授权生图 |
| 示例计划 | PASS | 7份计划×5视图均可编译；不代表生成了图片 |
| GPT资料导出 | PASS | 指令7496字符，小于项目8000字符兼容预算；没有发布在线GPT |
| 实际图像试测 | BLOCKED | fal-ai/nano-banana-pro首个请求返回403 balance_exhausted；无request_id，无图片 |
| 图像质量验收 | UNVERIFIED | 生成图片数0，未评价真实脸部、疤痕或身体比例 |
| GitHub提交 | BLOCKED | create_tree代码写入被平台安全检查拦截；未创建新commit或更新main，不用未完成树对象冒充提交 |

## 四、复现

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_design.py examples/myth-laborer-188.json
python3 scripts/build_prompt.py examples/myth-laborer-188.json --view side
python3 scripts/randomized_smoke.py --seed 20260925 --count 24 --out /tmp/nuyoah-random-new
python3 scripts/export_gpt.py --out /tmp/nuyoah-gpt-new
python3 scripts/build_manifest.py --check
```

随机输出目录必须为空，以免混入旧记录。普通回归和编译完全离线，不需要API密钥；真实图像测试需可用且有余额的图像服务。本次未更换账户、未重复提交失败生图请求，也没有尝试绕过GitHub写入拦截。
