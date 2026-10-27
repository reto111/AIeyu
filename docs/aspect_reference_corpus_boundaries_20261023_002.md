# 教材例句边界与角色分类：当前238条

当前包为[aspect_corpus_extents_20261023_007](../data/processed/aspect_reference/research_exports/aspect_corpus_extents_20261023_007/README.md)。238条例句范围＝237条原索引例句＋1条异常编号补定位；另1条原索引段落经核图确认为作者分析，单列排除。因此，1453条原索引已分类238条，尚余1215条；不能用“1453减238条例句”忽略补定位和排除的不同来源。

|项目|实际范围|
|---|---|
|累计例句范围|238条、65张来源页，15例需要扩入后续段落|
|来源状态|原ready40、模型候选195、隔离3；均为例句记录数，不是理论节数|
|查询范围|默认40；显式候选235；隔离3及作者分析排除段均不返回|
|已分类全部编号锚段的单元|15个；第十一章9单元、第十四章4单元、ch07.s02、ch13.s02.01|
|俄汉对应与语义标注|仍仅原22目标的18整例对应和22语义试标；新增216例未自动扩样|

第十四章原索引60条中59条是例句范围、1条是作者分析。原“aspect.ch14.s01.example.018.02”以“(18)的прочитал在这里表达的……”起段，回指前例，不是第二个例(18)，在excluded_anchors.jsonl保留原文、页和理由。例(18)本身同段包含行内(19)中文译文，作为整例保存，未声称句数或全部行内编号已清点。

PDF403的两条汉语对话(14)/(15)各有回答另起段，已补入；后面的“穿在了肋条上/着了凉”分析不纳入。此前只筛“俄文首段无汉字”的标记不会发现这两条中文对话，所以结构标记仅供定位，不能当错误率或完整性证明。其他表格、行内例、无编号例仍未全量切分。

[全量重建验证004](../data/processed/aspect_reference/reviews/corpus_extent_verification_20261023_004.json)核238条JSONL/TSV、1条排除记录及476次按ID/来源范围查询；旧186条记录不变，6类排除失配被拒绝。对1453条做“编号后紧接的/中/与/和”的机械筛查，只找到上述1候选；不证明其他段落都是真实例句。36项相关回归通过，工程验证不等于边界或翻译准确率。

异常编号(В43)的原印/候选和[100节编号差异](../data/processed/aspect_reference/reviews/numbered_marker_delta_20261023_001.json)保持不变。历史[186条说明](aspect_reference_corpus_boundaries_20261023.md)和各版40/57/73/104/136/186包保留。全部审核来自同一助手，独立专家复核0；原PDF、原转录、候选正文、默认RAG及学生数据均未改。

在包目录离线运行：

```powershell
python -X utf8 aspect_corpus_extents.py verify
python -X utf8 aspect_corpus_extents.py list --include-candidates
python -X utf8 aspect_corpus_extents.py show --id aspect.ch14.s02.02.example.014.01 --include-candidates
```

下一步优先补原ready范围尚余229条的边界，使默认例句研究集覆盖更完整；这些依然是教材选例，不是独立自然语料。
