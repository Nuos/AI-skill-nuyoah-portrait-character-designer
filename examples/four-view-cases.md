# 四视图使用示例

以下为**结构化创作样例**，不是实际生图报告；未附真人参考图片，不宣称模型已实现其效果。生成提示词后仍须按原始需求进行语义与图像审查。

| 样例文件 | 角色与时代 | 验证重点 |
|---|---|---|
| turnaround-plan.json | 70岁男性退休木匠，当代 | 自然体型、皱纹、无默认身高头身比 |
| turnaround-child.json | 8岁女孩，当代 | 适龄比例、无妆、不成人化 |
| turnaround-future.json | 34岁非二元研究员，架空未来 | 性别开放文本、真实身体、单侧腕带不镜像 |
| turnaround-elder.json | 82岁女性医师，1930年代启发 | 不嫩化；时代启发不冒充历史复原 |
| turnaround-myth.json | 西西弗斯成年男性国王，神话电影 | 190厘米与九头身仅因明确要求生效；无披风 |
| turnaround-infant.json | 六个月婴儿，性别未指定 | 安全受托、不强迫站立；遮挡背面须标PARTIAL |

## 一、生成完整提示词

```bash
python3 scripts/build_prompt.py examples/turnaround-myth.json
python3 scripts/build_prompt.py examples/turnaround-child.json --view front
```

输出是文本，不调用图片工具。四张独立提示词均重复完整人物基准，不靠“同上”维持身份。婴儿样例说明严格方向与真实支撑可能冲突，程序PASS只证明计划记录完整，不代表背面在图片里完整可见。

## 二、保持同一人，只换服装

先复制当前 character 为 edit.baseline_character。修改 appearance.costume；将允许项设为 `["appearance.costume", "asset_version"]`，批准后升级asset_version，并同步sheet.views中的版本。脸、年龄、体型、肤色、头发若同时改变，必须报错，不能把“国王装束”解释为另换演员。

真实参考图使用 reference.mode=identity、用户实际提供的 assets 标识、可见特征与 unknown_features，同时锁定 character.identity_anchor。仅上传图不自动生图；示例里的文字设定不能冒充对实际图片的观察。

## 三、任意性别、年龄与时代

```text
使用 $nuyoah-portrait-character-designer，给我的角色做四视图定妆照提示词。
性别和精确年龄未指定；不要替我设成年女性。
人物造型参照我已批准的角色描述，时代为架空，不做历史复原宣称。
输出：人像特写＋正面全身＋标准右侧全身＋背面全身。
```

未指定字段保留未指定；一旦获得明确人物基准，四视图必须沿用它。不能用“通用”掩盖身份基准尚未形成，也不能从未知信息宣称已达到生产级一致性。
