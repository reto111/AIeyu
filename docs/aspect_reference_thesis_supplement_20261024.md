# 论文附件与教材例证查询

[论文附件ZIP001](../data/processed/aspect_reference/research_exports/aspect_thesis_supplement_20261024_001.zip)共36文件、382085字节，SHA-256：`3f0b72255ec43161918ff4301c8630a2bd16c2b638a79f10bcf94f343f56a340`。它汇集方法与结果底稿、42项统计记录及8个固定JSON来源、57译对待独立复核空包、八题完整重放包及证据充分性诊断。没有原PDF、原库、学生数据或外部服务配置。

[离线验收](../data/processed/aspect_reference/reviews/thesis_bundle_verification_20261024_001.json)在项目外禁联网、禁读原项目的临时目录通过：35份内容文件指纹、42项统计的原字段绑定，以及57译对空表均可独立检查；342格全空，输出无共同标注、一致率和κ为空。修改附件文件会被拒绝。附件中的两个文档副本将未包含的原项目链接明确标为“需原项目”，原文档保持不变，副本转换与指纹在附件清单记录。

该轻量附件与[主研究ZIP002](aspect_reference_research_delivery_20261024_002.md)分别交付，前者用于论文证据与独立评价准备，后者提供现成理论/例证查询包。统计来源manifest的其他文件指纹仅保留作历史信息，轻量附件不包含那些manifest列出的全部源包，不能声称能够从PDF完整重建。

## 统一例证查询

项目新增`scripts/aspect_corpus_search.py`，读取目录002固定的完整编号044及行内补充004，逐文件核指纹并要求同一候选版本。两类记录归档共1510条，其中默认原ready297（编号269、行内28）；显式候选1393（编号1336、行内57）；117隔离记录不返回。这些是教材例组记录，跨章重复未去重，也不是俄语句数、词数或频率样本。

```powershell
.venv/Scripts/python.exe -X utf8 scripts/aspect_corpus_search.py stats
.venv/Scripts/python.exe -X utf8 scripts/aspect_corpus_search.py search --term письмо --term написал --include-candidates
.venv/Scripts/python.exe -X utf8 scripts/aspect_corpus_search.py search --term писал --match cyrillic_form --include-candidates
.venv/Scripts/python.exe -X utf8 scripts/aspect_corpus_search.py search --term антенну --kind inline_supplement_group --layer source_text --include-candidates
```

多个`--term`按同一例组内AND匹配，可能出现在不同句子或不同对话话轮，不能解释为同一句共现。默认是大小写不敏感的字面子串；`cyrillic_form`只接受单个俄文字母词形，以西里尔字母边界查找，因而`писал`不会混中`написал`，但也不自动查`писала`、`писали`或还原词元。它不是完整分词器，不处理连字符复合词、重音或`е/ё`归一。

`--layer source_text`查归档转录，默认`candidate_text`查既有编校；例如教材天线词的转录`антену`与候选`антенну`结果不同。输出位置是所选例文本层内字符偏移，页证据覆盖整例组，不冒称匹配字词的PDF字形坐标。分页保留总匹配例组数，不能把第一页条数当总体。

[查询验收002](../data/processed/aspect_reference/reviews/corpus_literal_search_verification_20261024_002.json)完成来源范围、117隔离、原文/候选区别、字面AND、转义模式、4256处文本层匹配位置及5个异目录CLI场景；缺包、越界路径、混候选版本和正文篡改均拒绝。新增查询脚本晚于两个ZIP封存，当前在项目中运行，不静默改写历史包。

## 断点可恢复性

[链路验收001](../data/processed/aspect_reference/reviews/continuation_chain_verification_20261024_001.json)以015为当时链头，解析39节点、611条历史指纹记录和471份最新文件指纹，全部匹配。较旧同路径的134条版本记录由较新固定记录解释，不要求历史版本字节等于当前版本。该结果只覆盖所列研究文件和指纹链，不认证语言学真值或整个项目状态。
