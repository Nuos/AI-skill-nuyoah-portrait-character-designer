# v0.3.0 改造与审计记录

## 一、范围与基线

日期：2026-09-25。目标仓库：Nuos/AI-skill-nuyoah-portrait-character-designer。
基线提交：`99b9a2c90e5b09507c6a61b5c27b9e2740ddb63d`，基线树：`d17aa3d2d2b9c7e993494b113729fab28e0639bc`。

保留 Agent Skill → references → scripts → tests/evals/examples → agents → manifest 的原架构；不改仓库名或技能调用名，不删除历史文件。主任务升级为任意性别、年龄和时代的人像特写／正面全身／标准侧面全身／背面全身定妆表。

## 二、实际执行结果

本地执行环境：Python 3.13.5，Linux；运行代码仅依赖标准库。本记录是本地验证，不是 GitHub Actions、宿主生图或模型评测的通过证明。

| 项目 | 实际结果 | 证据及限制 |
|---|---|---|
| 全部程序回归 | PASS，57项 | `python3 -m unittest discover -s tests -v`；原11项＋新增46项 |
| 原模块保留 | PASS，9份文件逐字节一致 | MIT、gitignore、原案例、词表、面部规则、v1合同和原测试的SHA256与基线核对 |
| 性别／年龄／时代组合 | PASS，210组结构合同 | 一个程序测试内5×6×7组合；不是210次模型或图像生成 |
| 六份四视图计划 | PASS | 当代木匠、儿童、老人、未来、神话、婴儿；image_review均UNVERIFIED |
| 提示词编译 | PASS，30份 | 每份计划编译合成图及四个独立视图，完整复用身份基准 |
| GPT导出 | PASS | 四份导出文件，指令6674字符；源与输出哈希核对，未上传在线应用 |
| 语义评测材料 | UNVERIFIED，24条 | `evals/turnaround-cases.json`新增材料；未宣称运行语言模型 |
| 新版本图片效果 | UNVERIFIED | 本次没有生成、编辑或上传人物图片 |
| 宿主安装／在线GPT行为 | UNVERIFIED | 未在用户宿主安装或发布，配置导出不等于应用已生效 |

## 三、增量检查与修正

先保留原v1回归，再对v2检查字段类型、非法输入、重复键、非有限数、模式授权、身份编号、资产版本、视角顺序、角度、裁切、同尺度和基线、锁定路径、允许编辑范围、全龄自然比例及支撑条件。

末轮修正：测试辅助方法改用assert_invalid，避免覆盖unittest自身fail；受托人物背面提示不再同时强求遮挡部位完全可见；左右侧统一为未镜像画面下左侧可见时鼻尖朝画面左、右侧可见时朝画面右。身高与头身比不默认填值，数字只是设定，不是图片测量结果。

婴儿计划结构可以通过，但被支撑遮挡的背部需要图像审查时标PARTIAL；不能以计划PASS宣称完整背部已经出现。历史verified只验证来源字段存在，史实是否正确仍须阅读来源。任意性别和年龄的支持是输入与规则适配，不是用布尔声明代替图像安全检查。

## 四、复现与维护

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_design.py examples/turnaround-plan.json
python3 scripts/build_prompt.py examples/turnaround-plan.json --view side
python3 scripts/export_gpt.py --out /tmp/portrait-gpt-export
python3 scripts/build_manifest.py --check
```

清单由源文件重建，排除manifest自身及缓存；不得沿用旧发布包的哈希或伪造新commit编号。更改后重新测试、生成清单并检查。图像和宿主未验证项必须通过后续真实执行另行更新，不由本次代码测试代填通过。
