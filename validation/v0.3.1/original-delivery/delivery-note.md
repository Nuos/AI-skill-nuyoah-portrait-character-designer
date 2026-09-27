# 通用四视图人物定妆照 v0.3.1 交付说明

## 交付状态

项目词表扩展、提示词编译、离线随机测试与ZIP解压复测已完成。
GitHub代码写入被平台安全检查拦截，没有新commit或main更新。
远端main最后复查仍为99b9a2c90e5b09507c6a61b5c27b9e2740ddb63d。
真实生图首个fal请求返回403 balance_exhausted，没有图片；后续请求未执行，没有重试或换账户。
不得把程序PASS、120份文本提示词或孤立Git树对象写成图片合格或远端提交完成。

## 内容

- nuyoah-portrait-character-designer/：完整46文件项目，可安装的技能根目录。
- validation/randomized/：24组固定种子的随机角色、120份完整提示词及report.json。
- validation/distribution-tests.txt：从源ZIP重新解压后执行的85项回归与清单校验日志。
- validation/baseline-tests.txt：原v0.3.0的57项复跑日志。
- gpt-export/：4份离线导出材料，未发布在线GPT。
- audit-v0.3.1.md：实际测试和受阻情况记录。

## 验证边界

25条新结构化词条：17通用、2条件、6特定角色。188cm、九头身、左脸旧伤、破亚麻短袍、汗尘和赤足不是全局默认。
85项回归通过；24组计划和120份提示词通过结构/编译检查；192项故障注入均被拒绝。
随机生成采用seed=20260925、年龄分层，其余特征伪随机，不代表人口统计抽样。
随机人物文件是文本资产，不是已经生成的照片。实际图片数量为0，图像质量UNVERIFIED。

## 复现

在nuyoah-portrait-character-designer/目录内：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_manifest.py --check
python3 scripts/check_design.py examples/myth-laborer-188.json
python3 scripts/build_prompt.py examples/myth-laborer-188.json --view side
python3 scripts/randomized_smoke.py --seed 20260925 --count 24 --out /tmp/nuyoah-random-fresh
```

随机测试输出目录必须为空。普通程序测试完全离线，不需要图片服务账户。
