# v0.3.1 验证与提交记录

## 内容位置

- 项目源码与词表：仓库根目录下原有 `SKILL.md`、`references/`、`scripts/`、`tests/`、`examples/`、`evals/` 等；源码与已交付v0.3.1包的46个文件逐字节一致。
- `randomized/`：上一轮24组人物计划、120份完整提示词及report.json。
- `baseline-tests.txt`、`distribution-tests.txt`：上一轮基线与解压包测试日志。
- `original-delivery/`：上一轮交付说明与审计副本；历史失败状态保留。
- `submission-20260926/`：本次85项回归复测、24组随机测试、192项故障拒绝、144份历史与复现文件逐字节比较，以及远端写入结果。
- 仓库路径 `exports/gpt/v0.3.1/`：位于仓库根目录exports下的4份GPT派生资料；仅导出，不是在线应用发布。

## 状态

本记录编制时，GitHub源码写入被平台安全检查拦截；main仍为99b9a2c90e5b09507c6a61b5c27b9e2740ddb63d。没有新远端提交、没有创建或合并拉取请求。本目录保存在离线待提交补丁内，不宣称已入库。

全部程序与结构化测试通过不等于真实图片通过。本次没有再次调用付费图像服务；历史图像试测仍是余额不足、零张图片、图像审查UNVERIFIED。

本目录和exports为交付证据，不属于根manifest.json的技能源码清单；源码清单仍校验45个文件，排除manifest自身。
