# 行内031：纯汉语例证分区与主交付010

新增26个原印纯汉语例组（21原ready、5候选），核PDF397、422–426，未补俄文，未改变任何旧俄汉对应。行内累计506组（164原ready/342候选）、144来源页；明确分为258组有337个对应、222个圈定片段仅俄文、26个片段仅汉语。单语是圈定片段的性质，不据此断言原书附近从无其他语言材料。

[范围验收031](../data/processed/aspect_reference/reviews/unnumbered_verification_20261024_031.json)保留旧480组全部字段，[对应验收031](../data/processed/aspect_reference/reviews/unnumbered_parallel_verification_20261024_031.json)保留旧337对应。[单语分区验收](../data/processed/aspect_reference/reviews/inline_monolingual_verification_20261025_001.json)拒绝汉语冒充俄文、俄文冒充汉语、遗漏、重复和有对应组混入单语等6类错误。旧构建器与旧包保留，新v2仅用于含纯汉语的版本。

新组包括“他穿了件皮夹克”情境、快乐/高兴、关门/门关着、劝说/说服，以及活动持续和动词重叠示例。书内原句、引号和斜线保留，比较组不硬拆成句数，不按教材分析直接填语义金标。

[新缺口队列007](../data/processed/aspect_reference/reviews/inline_extraction_queue_20261025_007.json)保留原俄文字母队列全部原字段；另提示616段中带引号、斜线、冒号或示例词的纯汉语未圈区间，其中101段依角色优先。603段仍有区间外俄文、114段俄文角色优先，两套段数可能重合，不相加当剩余例数，也不证明提示处一定有例证。[队列验收](../data/processed/aspect_reference/reviews/inline_han_gap_queue_verification_20261025_001.json)验证全部新增范围原文偏移、与506组不重叠、117隔离段不进优先，并复现旧队列在PDF397没有区间外俄文却仍遗漏汉语示例的情况。所有自动新增数为0，行内仍未穷尽。

[新重复清点007](../data/processed/aspect_reference/reviews/example_duplicate_audit_20261025_007.json)默认433组文本键不同；显式1842组仍有原先Берите!的1个重复键/2位置，未合并。[队列与包含关系复建](../data/processed/aspect_reference/reviews/audit_queue_verification_20261025_004.json)验证版本及偏移。[挂接验收003](../data/processed/aspect_reference/reviews/corpus_language_lookup_verification_20261025_003.json)核1842条可用引文旧字段保留、候选默认隐藏及117隔离不返回。

[推荐主ZIP010](../data/processed/aspect_reference/research_exports/aspect_research_delivery_20261025_010.zip)272文件，目录006含16包/131包内文件/119份历史与本批证据。总1959来源组＝1453编号＋506行内，默认433/显式1842，117隔离。编号1336可用组语言范围已核、1335条编号专家评阅8010空格；行内337条评阅2022空格，独立专家评价仍0。新译对空包013只解释单语分区，未给纯汉语制造空译对。

[36项隔离验收](../data/processed/aspect_reference/reviews/research_delivery_verification_20261025_010.json)及[独立目录逐字节复建](../data/processed/aspect_reference/reviews/research_delivery_reproducibility_20261025_010.json)通过，运行前后272文件不变。主入口默认目录006；旧主009与25日论文方法底稿固定其1933/480的历史快照，不能回填为本版实验结果。本批新增纯汉语不增加俄汉对应分母；自然语料、翻译准确率及专家一致率仍未测定，7来源疑点不解除。

ZIP SHA256：`af898071da74eb80370d92ed515a65a29a67a271244359920255eea6baf7492d`。
