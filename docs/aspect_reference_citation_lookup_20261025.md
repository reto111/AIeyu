# 体学论文引文的统一查阅入口

当前项目入口[scripts/aspect_corpus_search.py](../scripts/aspect_corpus_search.py)支持`show`：按例证ID查完整组，原转录与编校候选同时返回。已核编号例组044和行内补充018共用同一入口，默认355组、显式候选1647组；117组隔离继续不返回。未知ID返回空，缺少ID拒绝执行。

```powershell
.venv/Scripts/python.exe -X utf8 scripts/aspect_corpus_search.py show --id aspect.ch14.s03.03.unnumbered.002 --include-candidates
.venv/Scripts/python.exe -X utf8 scripts/aspect_corpus_search.py show --id aspect.ch14.s03.03.unnumbered.002 --include-candidates --layer source_text
.venv/Scripts/python.exe -X utf8 scripts/aspect_corpus_search.py show --id aspect.ch10.s02.03.example.047.01 --include-candidates
```

第一例的原转录保留`антену`，候选重放既有编校为`антенну`；第三例为两段、跨两页的编号例组。`selected_text`是本次选定层；`source_transcription`和`editorial_candidate`同时供比较，`editorial_difference`只表示有无文本差异，不是错误数或人工认证。偏移指向归档原转录；页证据保留整组来源，不能据此精确推定谓词字形坐标。

[查阅验收](../data/processed/aspect_reference/reviews/citation_lookup_verification_20261025_001.json)逐条检查显式1647组的两层，共3294条全文/偏移/页证据绑定；117隔离全部拒绝，默认候选隐藏，5个异目录场景和缺ID拒绝通过。这些是数据范围及入口行为检查，不是引文语义充分性或专家正确率。

[工具补充ZIP001](../data/processed/aspect_reference/research_exports/aspect_citation_tool_20261025_001.zip)仅3文件，配合[离线ZIP004](../data/processed/aspect_reference/research_exports/aspect_research_delivery_20261025_004.zip)解压数据，显式指定其目录008即可；不覆盖旧ZIP的脚本或数据。[补充验收](../data/processed/aspect_reference/reviews/citation_addon_verification_20261025_001.json)在异目录执行原转录、候选、默认隐藏和统计4场景，原解压文件及原ZIP保持不变。

论文引用仍须写明张家骅《现代俄语体学（修订本）》、高等教育出版社、2004年第2版、对应印刷页及文本层。PDF页码与印刷页码分开记录，本书正文印刷页通常为PDF页减20，必须回看原页。候选引句应标为编校研究文本；`context`中的作者分析、`ср.`插语、比较符号、汉译或文学署名不能不加说明地当作原作原句。完整例组不等于自然句，教材重引和抽样限制见[边界与重引说明](aspect_reference_projection_and_repetition_20261025.md)。

独立标注仍0；7来源疑点没有解除。没有为本入口调用生成服务、外发资料、改写原库或学生库。

019接续后项目默认目录为009：315行内例组、257对应，默认359/显式1651；[引文验收002](../data/processed/aspect_reference/reviews/citation_lookup_verification_20261025_002.json)检查3302条双层全文绑定。主ZIP004与工具补充001仍固定目录008的311行内组/251对应；显式传旧目录可复现旧范围。新019数据及角色007、译对空包007另存接续，不冒充已进旧ZIP。

021接续后项目目录010：362行内例组、268对应，默认391/显式1698；引文验收003检查3396条双层全文记录。旧目录008及主ZIP004、工具补充001继续固定其原范围。

024接续后项目目录011：401行内例组、270对应，默认393/显式1737；引文验收004检查3474条双层全文记录。主ZIP004仍固定311/251，不以项目后续增量覆盖旧包。

028接续后项目目录012：448行内例组、279对应，默认398/显式1784；引文验收005检查3568条双层全文记录。两次Берите!按不同原段偏移保留，非重复抽取。

029及目录014：469行内例组、285对应，默认404/显式1805；引文验收007检查3610条双层全文记录。离线ZIP005带完整show入口，旧ZIP004和补充工具001保持冻结。
