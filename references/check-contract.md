# 内部设计记录与检查合同

此格式用于复杂阵容和回归验证，不要求用户填写，也不默认展示。脚本只检查记录的内部一致性；自然语言与图像是否对应、请求是否真的授权，仍由执行者核对。

```json
{
  "schema_version": 1,
  "request": {"text": "同一套桃粉妆，设计五个不同脸的成年角色", "mode": "text", "explicit_image_request": false},
  "roster_goal": "distinct",
  "same_makeup": true,
  "locks": {},
  "characters": [
    {
      "id": "A",
      "axes": {
        "face.ratio": "short", "face.midface": "short",
        "jaw.width": "medium", "jaw.chin": "round",
        "eyes.length": "short", "eyes.opening": "large", "eyes.spacing": "medium", "eyes.lid": "double", "eyes.tilt": "level",
        "nose.height": "low", "nose.width": "medium", "nose.tip": "round",
        "lips.width": "medium", "lips.ratio": "lower_fuller",
        "brows.arc": "soft", "brows.distance": "medium"
      },
      "locks": {},
      "makeup": {"palette": "桃粉", "finish": "薄透底妆、缎光唇", "direction": "平直细眼线", "placement": "双颊中央柔边"}
    }
  ]
}
```

完整示例数据中只有一个角色，所以尚不满足 distinct 的数量要求。单人设定用 single；同脸修改用 identity 并给 reference_axes；相似/亲缘目标用 related。distinct 至少两人，每一对六组中至少四组不同，其中 face/eyes/nose 至少两组。程序不把缺失轴算差异，distinct/identity 必须包含完整离散轴；single/related 可以部分记录未知信息。

axes 只接受脚本 AXES 表中的键和值；自由文本词与近义词先归一化，不能使用未定义轴、数组或重复 JSON 键躲过冲突检查。低/中/高等是创作比较，不是人体测量标准；同一阵容使用一致参照。详细自由文本可以保留在角色 prompt、observations 等字段，不参与得分。

骨相补强由执行者核对实际 Prompt：原创是否写出眉骨/眼窝、颧部、下颌/下巴的具体关系；骨架、软组织、妆面与光影是否混淆；固定脸的已知项和未知项是否保留；参考深度是否有可见依据。当前16个离散轴不覆盖眉骨起伏、眼窝深浅、颧位或面中投影，不新增第七个骨相组，不以脚本 PASS 代替这些语义检查。中庭长度对应 face.midface，不能用它编码面中凸凹；眉骨不是 brows.arc。

全局 locks 与单人 locks 均为轴值映射；两者冲突不能输出。identity 的 reference_axes 是固定身份基线，任何改变都报告失败。妆容、肤色等额外锁定由自然语言检查，不冒充本脚本已覆盖。
same_makeup 为 true 时，四个妆容合同字段必须完全一致；不同脸的具体铺色范围可在 prompt 中适配，不能改变合同。此比较不证明语义等价或图片妆容相同。

request.mode 是 text 或 image；image 必须附 explicit_image_request=true，且保留本轮完整请求便于人工核对。这个布尔值是执行者的判断，不是授权证据本身；脚本不通过“出图”关键词替执行者理解否定、引用或上下文。不联网、不生图。

执行：
`python3 scripts/check_design.py /absolute/path/plan.json`

stdout 输出 JSON 检查报告；PASS 只代表已编码合同，FAIL 列出可定位错误并以退出码1结束。输入格式错误也安全返回 FAIL，不打印堆栈或读取其它路径。阈值不足时先按结构规则修复；锁定空间不足则如实说明具体限制，不改阈值伪装通过。
