# 通用四视图人物定妆照设计师

**v0.3.1 · 任意性别、年龄与时代设定 · 写实摄影 · 身份一致性优先**

在原“南鸢·人像角色设定师”的 Agent Skill 架构上改造。保留面部结构、妆容、参考锁定、检查脚本、回归及 GPT 导出；主任务扩展为完整人物的四视图定妆照。仓库名称与技能调用名不变，避免已有安装失效。

## 一、四视图是什么

从左到右固定为：**正面人像特写 → 正面全身0° → 标准侧面全身90° → 背面全身180°**。特写是头顶至锁骨，其余是完整全身。不是四张不同人物，也不是四个方向的全身图。

默认展示角色左侧（鼻尖朝画面左），可明确指定右侧。三张全身同一身份、服装、姿态、尺度、头顶高度与基线。默认16:9、特写约28%宽度；4K目标3840×2160，2K长边版2048×1152。目标尺寸不代表已经原生生成，须记录实际像素。

## 二、通用能力

性别使用开放文本，支持不指定；不默认女性或强行中性化。年龄覆盖婴幼儿、儿童、青少年、成人、老人及未定年龄，保持适龄体型；不统一套成人身高、瘦身或九头身。古代、近现代、当代、未来、神话与架空均可设定，区分影视化设计与有来源的历史复原。

参考人物锁定骨相、五官、肤色、身体及稳定标记，只变取景。换装时保留同一人物并以字段级变更合同检查；不同状态分别保存资产版本。需要支撑或坐姿的人物不被强制站立。自然无妆是有效方案。

## 三、使用

```text
使用 $nuyoah-portrait-character-designer，为一个70岁的退休木匠设计四视图人物定妆照。当代，自然体型，保留皱纹，浅灰摄影棚背景。只给完整中文提示词。
```

```text
使用 $nuyoah-portrait-character-designer，以我提供的人物图为唯一身份基准，保持五官、年龄、肤色和身体比例，只将服装换成科林斯国王的影视化装束。四视图从左到右为人像特写、正面全身、左侧全身、背面全身。
```

普通设计默认输出文字。明确说“按该提示词生成图片”才调用当前宿主的图片能力；本仓库不是独立生图引擎，不包含模型权重、图片API适配器或 ComfyUI 工作流。没有图片工具时仍可完整编写提示词。

## 四、安装与目录

把整个项目目录安装为 `nuyoah-portrait-character-designer`，必须保留配套 `references/` 和 `scripts/`。在支持 `$skill-installer` 的宿主中，可指定本仓库地址与根目录；已有同名版本先备份，不能误装回上游v0.2.1。具体发现路径按当前宿主文档确认，见 [来源](references/sources.md)。

```text
SKILL.md                         技能入口，调用名兼容
agents/                          通用与OpenAI界面适配
references/                      原面部模块＋四视图、年龄、时代、身份、验收规则
scripts/check_design.py           统一入口：兼容v1，分发v2
scripts/check_turnaround.py       四视图计划校验（不检查图片）
scripts/build_prompt.py           合成图／独立视图完整中文提示词
scripts/export_gpt.py             从同一规则源导出GPT资料
scripts/build_manifest.py         清单哈希构建／校验
examples/                        历史案例＋新四视图结构化示例与说明
evals/                           原案例＋四视图语义评测材料
tests/                           原回归＋新增程序回归
manifest.json                    当前版本文件完整性清单
CHANGELOG.md                     迁移与变化说明
```

## 五、运行与验证

Python 3.10或更高版本，脚本仅使用标准库，无需图片API密钥。

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_design.py examples/turnaround-plan.json
python3 scripts/build_prompt.py examples/turnaround-plan.json
python3 scripts/build_prompt.py examples/turnaround-plan.json --view side
python3 scripts/export_gpt.py --out /tmp/portrait-gpt-export
python3 scripts/build_manifest.py --check
```

普通用户不必填写JSON；它是复杂任务与工程接入的可选内部合同。完整规范见 [四视图合同](references/four-view-contract.md)、[身份年龄时代](references/identity-and-era.md)、[示例](examples/four-view-cases.md)。原schema_version=1检查继续可用，但不能证明新四视图合格。

最新验证结果见 [v0.3.1审计记录](references/audit-v0.3.1.md)，旧版记录保留。**程序PASS不等于图片PASS**：无真实图片时图像验收保持UNVERIFIED；新增自然语言评测材料不冒称已做模型执行。原 [真实案例](examples/real-cases.md) 仅为v0.2.1历史记录。

## 六、许可

遵循 [MIT License](LICENSE)，保留原作者南鸢及其版权声明；本次由 Nuos 维护的派生版单独记录来源。仓库地址不变，不替原作者发布上游版本，也不自动发布GPT或上传参考人物资料。


## 七、v0.3.1：可执行词表与随机测试

新增25条摄影、全身、神情、材质和一致性词条，[文字词表](references/lexicon.md)与[机器词表](references/turnaround-lexicon.json)相互对应。词条分通用／条件／角色专用，编译器实际消费它们，按视图生成并去重负向词。

用户提供的188厘米中年神话劳作者已保存为[完整优化例](examples/myth-laborer-188-optimized.md)和[可运行计划](examples/myth-laborer-188.json)。这是一个个体预设，不会把儿童、女性、老人或未指定年龄的人物改成九头身男演员。

```bash
python3 scripts/build_prompt.py examples/myth-laborer-188.json
python3 scripts/build_prompt.py examples/myth-laborer-188.json --view portrait --negative-only
python3 scripts/randomized_smoke.py --seed 20260925 --count 24 --out /tmp/nuyoah-random-new
```

本地85项测试通过，24组随机人物生成120份提示词、192个故障变体全部被拦截。详见[随机记录](evals/randomized-v0.3.1.json)与[测试日志](tests/run-v0.3.1.txt)。这是离线程序测试，不是120张图片。真实生图试测因fal账户余额不足返回403，未生成图片，见[图像试测记录](evals/image-test-v0.3.1.json)。远端提交尝试被平台安全检查拦截，本包保留完整文件；不把未提交状态标成GitHub已更新。
