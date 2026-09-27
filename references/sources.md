# 来源、维护与证据边界

## 一、项目来源

本项目是 Nuos 对南鸢 `nuyoah-ai-works/nuyoah-portrait-character-designer` v0.2.1 的通用四视图改造。原始仓库来源与 MIT 作者声明保留；LICENSE 不变。

- 原始项目：https://github.com/nuyoah-ai-works/nuyoah-portrait-character-designer
- 当前维护项目：https://github.com/Nuos/AI-skill-nuyoah-portrait-character-designer
- 本次改造基线 commit：`99b9a2c90e5b09507c6a61b5c27b9e2740ddb63d`
- 基线 tree：`d17aa3d2d2b9c7e993494b113729fab28e0639bc`

保留原面部结构、妆容、词表、v1检查合同、原自然语言案例、真实案例和原程序回归；新增四视图合同、身份年龄时代适配、v2检查、提示词编译与相应回归。原真实案例仍是旧功能历史样例，不是v0.3.0新生成结果。

## 二、外部技术依据

2026-09-25核对的官方入口：
- OpenAI Skills 文档：https://learn.chatgpt.com/docs/build-skills
- OpenAI Skills API 概览：https://developers.openai.com/api/docs/guides/tools-skills

它们用于确认 SKILL.md 与配套资源的组织方式，不为本项目的脸部或四视图效果背书。宿主的模型、图片接口、安装与能力限制需要按当前文档核对；仓库没有绑定某个图片模型或虚构其原生分辨率。

## 三、未验证事项

几何、身份锚点、28%特写宽度、修复轮数等是项目设计约定，不是医学标准、精确人体测量或模型效果保证。图像质量、人脸一致性、严格历史复原与宿主端行为必须分别取得实际证据。年龄与性别由用户声明或保持未指定，不从参考照片推断敏感身份。

参考图片与素材版权由各自权利人持有；本次不下载、不新增或上传真实人物照片，也没有付费生图调用。代码内 assets 只是引用标识。
