# 南鸢·人像角色设定师

说出你想要的人物气质、五官或妆容，得到一句角色方向和一份完整中文提示词。普通“设计一个角色”先输出文字；明确说“生成图片”后，才调用当前工具的图片能力。

## 下载

- [下载 v0.2.1 完整 ZIP](https://github.com/nuyoah-ai-works/nuyoah-portrait-character-designer/releases/download/v0.2.1/nuyoah-portrait-character-designer-v0.2.1.zip)
- [查看版本与更新](https://github.com/nuyoah-ai-works/nuyoah-portrait-character-designer/releases)
- [阅读真实案例与完整提示词](examples/real-cases.md)

请下载整个文件夹，保留 `references/` 等配套文件。只复制 `SKILL.md` 会缺少它引用的设计规则。

## 在 Codex 里安装

将下面这段话发给有本地文件能力的 Codex：

```text
使用 $skill-installer，从 https://github.com/nuyoah-ai-works/nuyoah-portrait-character-designer 安装仓库根目录的 Skill，安装名称设为 nuyoah-portrait-character-designer。如果已有同名版本，先告诉我，不要直接覆盖。
```

安装完成后，在下一轮输入下方示例。若没有被识别，先检查安装结果与文件位置，再重启 Codex。

也可以手动安装：下载并解压 ZIP，把里面的 `nuyoah-portrait-character-designer` 整个文件夹放入个人目录 `~/.agents/skills/`。最终应能找到 `~/.agents/skills/nuyoah-portrait-character-designer/SKILL.md`，不要多套一层文件夹。已有同名版本时先保留自己的修改。位置与发现机制见 [OpenAI 官方说明](https://learn.chatgpt.com/docs/build-skills)。

这是一份独立 Agent Skill，不是已经上架插件目录的插件。其他支持 Agent Skill 的工具请使用各自的安装入口；本版的实用案例来自 Codex，不承诺所有宿主表现一致。

## 第一次使用

```text
使用 $nuyoah-portrait-character-designer，设计一个明媚妆容的女性角色，中国唐风妆容。
```

正常会得到一句角色方向，以及一个可以单独复制的完整中文 Prompt。你不需要自己填表或先学习骨相术语。

确定方向后，可以继续：

```text
按刚才的完整提示词生成一张图片。
```

生成图片需要当前宿主具备图片能力，额度或费用按所用平台计算。没有图片工具时，也可以把完整提示词复制到自己使用的生图工具中。

## 继续修改

- “我想要设计一个日系昭和感的成年女性角色形象。”
- “同一套桃粉妆，设计五个不同脸的成年角色。”
- “保留人物五官和肤色，只把眼线改得柔和一点。”
- “这张图只拆妆容，别把参考人物的脸带过去。”
- “只给提示词。”

局部修改默认返回完整新稿；多个角色分别给出完整提示词。固定脸换妆时保留原有结构；固定妆换脸时保留妆的主色、质地、线条方向和相对落点。

## 设计方法与边界

原创人物会写出眉骨/眼窝、颧部、下颌/下巴之间的具体关系，并将骨架、面颊软组织、妆容与光影分开。柔和骨相同样是有效设计；不把某种气质、国籍或肤色绑定成唯一脸型。详细候选见 [词表](references/lexicon.md)。

本 Skill 重点是人物结构和妆容。完整写真企划、泛用海报反推、视频跨镜头连续性需要其它能力，本 Skill 不要求你安装那些近邻工具。

参考图只描述可见信息，不能从强侧光或遮挡推断未知骨相。不同脸的文字设计、保留人物的指令，都不等于实际生图一定保持身份或每次达到预期审美。

## 版本与验证

v0.2.1 为首次公开发行整理：增加 MIT 许可、下载与安装说明、四份真实生图提示词。角色设计规则延续 v0.2.0，未宣称此次打包提升了图像效果。

已有 11 项程序回归覆盖模式、锁定、结构差异、同妆合同与 GPT 导出。`evals/cases.json` 的 21 项自然语言材料用于人工/模型复核，并非 21 项都经过自动模型执行。运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

作者曾进行普通原创、柔和骨相锁定、已知/未知骨相下的改唇色、五角色同妆文字测试。早期详细人物要求曾误触发生图，补充模式边界后相同原请求复测返回文字；局部编辑的极简代码块格式也出现过偏差。

2026-09-11 的真实图像例子包括唐风、窗边人像与两版校园人像：有可用方向，也有被作者否定的脸型和笑容。唐风图发髻顶缘有裁切；窗边图部分反光偏强；校园调整版仍额外生成了肩包。图像效果请看具体案例，不将程序通过写成所有图片稳定。

`scripts/check_design.py` 检查内部结构记录，不判断图片；`scripts/export_gpt.py` 从同一规则导出 GPT 资料，不登录、不上传、不自动公开 GPT。适配说明见 [应用适配](references/acceptance-and-gpt.md)。

## 许可与来源

Skill 的代码和文档使用 [MIT License](LICENSE)，保留版权及许可声明即可按许可使用。来源和未验证事项见 [sources.md](references/sources.md)。第三方参考图片不包含在发行包中。

本公开仓库是发行版本；作者从自己的统一维护源生成更新，避免多份规则各自变化。
