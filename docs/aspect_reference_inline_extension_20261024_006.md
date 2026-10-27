# 行内例证接续006：83例组与82俄汉对应

当前[例证006](../data/processed/aspect_reference/research_exports/aspect_unnumbered_examples_20261024_006/README.md)累计83组：28原ready、55模型候选，默认28/显式83，38个来源页。原004的57组逐条保持；005新增16、006新增10组，本批核PDF387–392、399–400、404、406–407、409–413共16张原图，例文实际涉及其中12页。

新增内容包括带斜线可选形式的谓词短语、作者的俄文释义改写、带数学关系记号的对照和原书标为不正确的构式。保留原星号；作者在后文否定但未印星号的例子不另添星号。原段有行内(10)–(17)等号码时保留上下文，不把它们冒充新增行首编号锚点；原1453编号锚点分类和044完整边界不变。

[对应006](../data/processed/aspect_reference/research_exports/aspect_unnumbered_parallel_20261024_006/pairs.tsv)累计82组，覆盖62个例组；另21个圈定片段仅收俄文。后者可能在作者论述中另有对应汉语，不表示原书没有汉译；本层不跨分析段落拼接译对、不补主语或翻译。四个短语构成的比较列表可能对应四组译对，例组与译对不得混为分母，也不解释为自然句频率。

[材料角色002](../data/processed/aspect_reference/research_exports/aspect_material_roles_20261024_002/README.md)更新1333段到83例及10表的链接，原角色、正文、来源状态和页证据保持。旧角色包001固定57例链接保留，不静默覆盖。[译对复核空包002](../data/processed/aspect_reference/research_exports/aspect_translation_review_20261024_002/README.md)有82项、492个空分类格，统一评价候选文本；独立评阅仍0，旧57项/342格包保留。

[研究目录003](../data/processed/aspect_reference/research_catalog_20261024_003.json)固定13包112个包内文件和21份证据报告。项目例证查询默认改用此目录：默认297例组（编号269、行内28），显式1419（编号1336、行内83），117隔离不返回；归档1536条不能当作自然句总数。旧目录002及主ZIP002仍固定57行内组、57译对；旧论文附件001与42项事实清单固定其原版本，不将新数回写为旧实验结果。

```powershell
.venv/Scripts/python.exe -X utf8 scripts/aspect_corpus_search.py search --term пришел --match cyrillic_form --include-candidates
.venv/Scripts/python.exe -X utf8 scripts/aspect_unnumbered_examples.py show --collection data/processed/aspect_reference/research_exports/aspect_unnumbered_examples_20261024_006 --id aspect.ch14.s02.02.unnumbered.001 --include-candidates
```

验收包括新增26条原始范围及候选重放、82对应/164语言片段与TSV一致、历史记录保持、1333材料段及117隔离过滤、492空格和无共同标注输出，以及[查询003](../data/processed/aspect_reference/reviews/corpus_literal_search_verification_20261024_003.json)的4308处匹配位置、5异目录场景、4异常输入拒绝。新材料没有增加自然语料、专家判分或生成服务调用，7来源疑点继续隔离。
