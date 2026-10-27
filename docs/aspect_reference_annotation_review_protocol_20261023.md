# 22目标源文复核：待填写协议

[空白复核包](../data/processed/aspect_reference/research_exports/aspect_review_packet_20261023_001/README.md)含22个既有教材目标、两张空CSV和6字段代码表。模型词形/语义标签已遮蔽，原书及编校语境保留；作者解释可能出现在窗口内，因此是对模型标签遮蔽的源文知情复核，不是对作者观点盲评。目标有意选取，非自然随机样本。当前没有已完成的独立标注。

1. 两位复核者各复制A、B空表，按review_id查看source_contexts.jsonl，先独立填写，不相互看标签。
2. 五语义轴为话语地位、发生承诺、词汇目标达成、参照时结果状态及后果相关性；另记语境充分性。代码值与中文定义在codebook.json。空白代表未填写，unknown代表明确未决，not_applicable代表不适用，三者不合并。
3. 若需源节全文，context_sufficiency填need_full_unit并查原页；不可用章标题或模型旧标签补空。discourse_status的other必须说明；工具不强加模型的跨轴组合规则，允许复核者提出模型分类不适用。
4. 保留两份原始独立表，另存分歧裁决，不以裁决回写原表制造一致率。记录实际人员、日期、资料可见范围、查阅完整源节的项目和裁决理由；两个不同ID本身不能证明独立。
5. 完成后运行包内标准Python工具，Windows按项目习惯显式启用UTF-8：

```powershell
python -X utf8 aspect_annotation_agreement.py --packet . --left A_completed.csv --right B_completed.csv --left-reviewer reviewer_A --right-reviewer reviewer_B --output agreement.json
```

每字段单独报告双方填写数、空白、不确定数量、共同填写分母、原始一致率与名义Cohen κ，以及分歧ID。κ＝(pₒ−pₑ)/(1−pₑ)，pₑ由共同填写项目上双方的类别边际频率估计，公式及非加权定义参见[scikit-learn官方文档](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html)。本工具仅以标准库实现，未安装该库。

空表的共同填写数为0，不能算100%一致；单一常数边际时κ未定义，也不填成1。unknown计作一个明确类别，空白排除在该字段配对分母之外。不要把不同分母的字段混成一个总分。高一致率不证明正确，22条结果也不能外推为自然语料频率或正式研究准确率。

[空表实跑](../data/processed/aspect_reference/reviews/annotation_blank_comparison_20261023_001.json)正确返回no_paired_annotations；[包核验](../data/processed/aspect_reference/reviews/annotation_review_packet_verification_20261023_001.json)确认264分类格全部为空、模型字段不外泄、6文件重建一致、5类异常输入拒绝及异目录离线入口可运行。名义κ单元测试含官方示例0.6875、缺标、unknown与退化边际；这些合成计算测试不是实际人的标注结果。

该包固定候选22日007和锚段22日005；[兼容核验](../data/processed/aspect_reference/reviews/annotation_source_compatibility_20261023_001.json)证明22目标在23日新93节候选中正文、状态及警示不变。未静默改写旧包，也未将任何标签接入RAG或学生池。

## 2026-10-23接续：当前重绑定版

当前使用[试标23日001](../data/processed/aspect_reference/research_exports/aspect_annotation_pilot_20261023_001/README.md)及[空包23日002](../data/processed/aspect_reference/research_exports/aspect_review_packet_20261023_002/README.md)，绑定候选23日002和索引23日002。原22标签、39依据、词形及目标不变；2条所在源节的字形/警示元数据更新。旧22日002与旧空包001固定旧来源保留，不能按当前全兼容引用。264格仍空，独立标注0；重绑定不算新的语义审核。

## 2026-10-23完整例句补充版

当前空包改为[23日003](../data/processed/aspect_reference/research_exports/aspect_review_packet_20261023_003/README.md)，来源候选/索引/试标与002相同，另绑定22例边界层002。增加complete_source_example/complete_candidate_example与跨页证据，模型语义及依据选择未公开；作者解释仍可见。两份CSV和代码表与002逐字相同，264格空，独立复核0。见[整例对应与验证说明](aspect_reference_parallel_illustrations_20261023.md)。
