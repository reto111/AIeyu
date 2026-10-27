# 行内词汇释义增量030与交付008

新增11组词汇/词形比较、52个原印释义对应（8原ready组、3候选），已核PDF397、420、422、423、425、426。行内累计480组（143原ready/337候选）、337个现成对应，144来源页；其中258例组有对应，222个圈定片段只收俄文。新增的是词汇释义对应，不能将52解释成52个平行句；旧285对应也包含整例和短语，均不是逐句金标。

[推荐离线ZIP008](../data/processed/aspect_reference/research_exports/aspect_research_delivery_20261025_008.zip)有253文件，目录[20261025_003](../data/processed/aspect_reference/research_catalog_20261025_003.json)含15包/124包内文件/108份历史与本批证据报告。总例组1933＝1453编号＋480行内；默认412、显式1816，117隔离不返回。编号语言层仍1304双语组/1335对应＋32单语，按ID挂接，不再次增加例组数。旧22目标重合16个ID，不相加。

新增保留заснуть/спать、одеться/быть одет、задуматься/думать的书内释义与比较；汉释只圈原印范围。PDF420词偶旁的汉释只对应左侧原印词形，不替完成体右项补释。斜线词偶、形容词性别尾缀和原中文保留，语义关系是教材说明，不冒称专家认证。中文“思考/思考起来”等重复片段按括号、逗号圈定局部位置后通过唯一范围验收。

[边界与旧记录验收](../data/processed/aspect_reference/reviews/unnumbered_verification_20261024_030.json)、[对应重放](../data/processed/aspect_reference/reviews/unnumbered_parallel_verification_20261024_030.json)、[词汇增量分层](../data/processed/aspect_reference/reviews/lexical_inline_delta_verification_20261025_001.json)确认旧469组/285对应字段不变，新52个对应均属11个词汇组。[角色012](../data/processed/aspect_reference/research_exports/aspect_material_roles_20261024_012/README.md)关联480组/10表，[独立译对复核空包012](../data/processed/aspect_reference/research_exports/aspect_translation_review_20261024_012/README.md)337条/2022空格，实际独立评价0。

[更新后的重复清点](../data/processed/aspect_reference/reviews/example_duplicate_audit_20261025_006.json)：默认412个文本键均不同，显式1816组有1个重复键/2位置（原有Берите!），337个对应文本键不同；不据此推断语义独立或自然样本量。[新缺口队列](../data/processed/aspect_reference/reviews/inline_extraction_queue_20261025_006.json)1333段、480链接、603段仍有区间外俄文字母，114段依角色优先。该数字包括术语、回指和分析，不是剩余例数；本批未把其余段落自动当新例。[复建与位置验收](../data/processed/aspect_reference/reviews/audit_queue_verification_20261025_003.json)检查隔离、源区间和文本偏移。

[统一挂接](../data/processed/aspect_reference/reviews/corpus_language_lookup_verification_20261025_002.json)核全部1816可用引文旧字段保留；目录002/003包版本相同，003追加4项证据。[ZIP验收](../data/processed/aspect_reference/reviews/research_delivery_verification_20261025_008.json)33项禁读原项目/禁网络场景通过，运行前后253文件不变；[独立目录复建](../data/processed/aspect_reference/reviews/research_delivery_reproducibility_20261025_008.json)逐字节一致。新目录003为入口默认，旧007及之前包保留其冻结范围。

解压目录运行`python -X utf8 aspect_corpus_language_lookup.py stats`；候选加`--include-candidates`；`show --id aspect.ch14.s03.02.unnumbered.027`可查词汇组原文与页面。search仍检索整组，含原印标签、汉释及比较，不等于纯俄文词频。行内例未穷尽，独立专家评价和自然语料验证未完成，7疑点不解除。

ZIP SHA256：`4703ce52f01743c3a5fe9c7c364cc27e464ecc3475dcc16ceac669680e8f3231`。
