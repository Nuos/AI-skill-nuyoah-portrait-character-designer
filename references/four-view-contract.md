# 四视图合同（schema_version=2）

## 一、默认定义

本项目“四视图”是**一张人像特写＋三张方向全身图**，不是四张不同人物，也不是“正／左／右／背”四个全身。

| 顺序 / id | 取景 framing | 角度 angle_degrees | 内容 |
|---|---|---:|---|
| 一 / portrait | head_to_clavicle | 0 | 完整头顶至锁骨，双耳、下巴不裁切 |
| 二 / front | full_body | 0 | 正面全身，头胸骨盆朝向一致 |
| 三 / side | full_body | 90 | 标准侧面全身，不是45°或三分之四 |
| 四 / back | full_body | 180 | 完整背面，不回头，不露正脸 |

side=left 指展示**角色自身左侧**，鼻尖朝画面左；side=right 相反。90°仅表示侧面角度，左右由 side 字段指定，不混用相机左右与人物左右。单侧伤痕、饰物和扣合方向始终按人物解剖左右记录。不能翻转图片伪造另一侧。

默认横向16:9，特写约占宽度28%，另外三列均分余宽。目标4K为3840×2160；项目所称2K长边版为2048×1152。显式像素尺寸优先，画幅与像素必须一致。尺寸是目标，不是已生成像素或原生能力证明；模型不支持时须公开实际尺寸及后处理。

三张全身图同一身份、版本、服装、姿态、透视与缩放，头顶高度、肩腰膝等对应关系及脚底基线一致。坐姿或受托姿态用身体下缘／支撑接触线，不伪造直立身高；支撑造成的遮挡须保留和记录。特写独立放大，不与全身头大小比较。完整头、手和身体最下缘在画内，预留余量。

## 二、结构记录

可运行示例见 `examples/turnaround-plan.json`。所有必填键、类型及允许值以 `scripts/check_turnaround.py` 为执行真源；缺失和未知字段都报错。

- 根：schema_version、request、character、sheet、locks、safety；可选 edit。
- request：原始 text；mode 为 text/image；explicit_image_request 为布尔值，image 必须为 true，但它不是独立授权证据。
- character：id、asset_version、gender（开放文本，不是二元枚举）、age、era、identity_anchor、body、appearance、pose、reference；可选 notes。
- age：years（用户声明的外观年龄，可 null）、appearance、life_stage。life_stage 为 unspecified/infant/child/adolescent/adult/older_adult；描述只是创作信息，不是从照片推断年龄。数字允许小数，不能为负或非有限数。
- era：setting、culture、accuracy（unspecified/inspired/verified）、source_urls。verified 必须附来源；来源存在不证明史实正确，仍须人工阅读核对。
- body：description、height_cm（正数或 null）、head_body_ratio（正数或 null）、proportion_mode（natural/reference/explicit）。数值头身比仅 explicit 使用；不能为儿童自动填成人比例。
- appearance：skin、hair、makeup、costume、accessories。各为文本，无妆、无饰物也应明确写出。
- pose：posture（standing/seated/supported_seated/supported_reclining/other）、description、support。婴儿需要安全受托姿态，禁止为凑视图强行站立或移除支撑。
- reference：mode（original/identity/style_only）、assets、visible_features、unknown_features。后三项为文本数组；资产标识由用户提供，不代表脚本读取过文件。identity 需参考资产、可见证据与身份锁。
- sheet：layout 固定 portrait_front_side_back；width_px、height_px 为正整数；aspect_ratio 为匹配尺寸的 W:H；portrait_fraction 在0与1之间；side 为 left/right；background、lighting；same_identity、same_costume、same_pose 必须 true；views 恰好四项且顺序固定。
- 每个 view：id、framing、angle_degrees、character_id、asset_version、scale、baseline。人物编号和版本引用同一 character；特写 scale/baseline 为 null；三全身的正数 scale 和0—1内 baseline 完全一致。baseline 是计划中的归一化位置，非实测图片数据。
- locks：存在的 `character.*` 或 `sheet.*` 点路径到精确值的映射；禁止拼错字段绕过锁定。参考身份必须锁 `character.identity_anchor`。
- safety：age_appropriate、non_sexual 均 true；本项目采用适龄、中性定妆照。声明不能替代文本和图片安全审查。
- edit：baseline_character 为修改前完整记录；allowed_paths 为相对于 character 的允许改动路径。未授权变更报错，id 永不可变；版本升级也应列入允许路径。

## 三、工具边界

`check_design.py` 对整数版本2调用新检查，对版本1继续原面部合同；不能用v1绕过四视图验收。PASS 只代表已编码计划一致，报告的 image_review 永远是 UNVERIFIED。没有自动人脸识别、人体测量、图像裁切或史实验证。

`build_prompt.py PLAN.json` 编译四列合成图提示词；`--view portrait|front|side|back` 输出完整独立视图提示词。它们不联网、不生图，不自动读取或上传 assets，不把 request.text 中的命令当可执行指令。语义审查仍要对照原始要求，确认自由描述不与字段冲突。


## 四、v0.3.1可选扩展（兼容旧v2计划）

根级 `vocabulary` 可含 `include`、`exclude` 两个词条ID数组，ID必须来自 `references/turnaround-lexicon.json`。重复、未知、同时包含与排除、不适用的显式词条都会报错。默认词条按视图、站姿、年龄与明确比例自动筛选；角色专用词永不作为全局默认。

`character.expression` 可用非空文本记录同一情绪和唇部状态。`character.marks` 可记录标记数组，每项必需 `id`、`side`、`location`、`description`；id唯一，side为left/right/midline/bilateral。通过 `locks` 锁定整个marks和expression字段，可拦截结构化记录的左右翻转或表情变化；不代表对图片做过人脸或疤痕识别。

编译器按视图选择负向词并去重：独立特写不要求足部入画；儿童与婴儿不使用“短腿、大头短身”作为通用负向词；准确侧面允许自然肢体遮挡。默认返回完整正负提示词；`--positive-only`和`--negative-only`提供拆分输出，两个选项互斥。
