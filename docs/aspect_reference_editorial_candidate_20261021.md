# 现代俄语体学：编校研究候选使用说明

2026-10-21。本库服务于俄语体范畴研究的理论依据、可溯源例证检索和后续RAG实验。当前可检查成果包括原印转录、逐项复核记录及独立的编校候选包；正式论文研究版尚未冻结。

## 使用入口

推荐当前候选包：[aspect_editorial_candidate_20261021_002](../data/processed/aspect_reference/research_exports/aspect_editorial_candidate_20261021_002/README.md)。001为本轮较早快照，保留历史，不混用其统计。

原印数据库仍是 `data/processed/aspect_reference/aspect_reference.sqlite`，135批、40条历史页修订、471条转录记录。原有五张表在候选包中逐行保留，新增表 `aspect_candidate_sections` 存放编校文字和溯源元数据。没有修改学生库或其他书库。

|范围|数量|使用状态|
|---|---:|---|
|原印理论节|100|40 ready、60 unresolved，原印状态未改|
|候选包保留的原ready理论节|40|默认可检索，正文逐字不变|
|模型编校理论候选节|33|显式启用后可检索，必须标“编校候选层表述”|
|候选包继续隔离的理论节|27|任何检索模式均不返回|
|练习、答案、书目和前置材料|60单元|按用途排除出理论检索|

33节候选中包括1节复核后保留原文的单元；候选资格不意味着每节都改过字，也不意味着独立专家审定。

## 实际完成的内容工作

- 60节125条原有理论隔离说明均有逐项模型判断：[最新003版](../data/processed/aspect_reference/reviews/theory_issue_review_20261021_003.md)。83条形成具体编校方案；30条仍需原著来源、4条理论或语境未决、7条保留原文、1条墨迹不可辨。一条说明可能包含多个问题，不能把125当独立错误数。
- 另有2条明确追加的候选。共85条提案、91处精确修改，分布于45节；59处位于可显式检索的候选节，32处仍随未决节隔离。原偏移、精确旧值和新值见[机器可重放方案](../data/processed/aspect_reference/reviews/editorial_plan_20261021_002.json)。
- 28组262编号父题已逐项对读题干与原书答案，a/b/c子项写在父题说明中：[逐项报告](../data/processed/aspect_reference/reviews/exercise_semantic_review_20261021_002.md)。233项在预期读法下可成立、8项需语境、9项有具体差异、12项涉及题干或目标标注。不是262道独立单空选择题，也不是233题已获唯一答案认证。
- 9个具体差异父题形成[12处修订预览](../data/processed/aspect_reference/reviews/exercise_editorial_plan_20261021_001.md)。题干和原答保持归档，全部不进入学生练习池。
- 7条外部来源记录区分原著、同一作者后续论文及仅索引线索：[来源清单](../data/processed/aspect_reference/external_evidence/source_manifest_20261021_002.json)。其中Ремарк、Полевой的后续论文支持来自同一作者，文学原作仍未独立定位；不能合称“全部经原著证实”。
- [原书著录索引](../data/processed/aspect_reference/reviews/bibliographic_source_index_20261021_001.md)保存158个参考文献段、23个例句出处段的原文、偏移、年份查询词与页绑定。181段不等于181部已核著作，原印专名和疑似错误均保留。

复核撤回了将“对别关系”改成“对比关系”、把罕见词Беспромедлительно判为误拼，以及把一般持续结果动词не написал否定行为本身认作理论冲突等推断。旧说明与旧报告保留，新决定通过追加版本记录。

## 本地运行

在项目根目录运行，明确指定002包，避免读到较早快照：

```powershell
.venv/Scripts/python.exe scripts/aspect_candidate_rag.py verify --db data/processed/aspect_reference/research_exports/aspect_editorial_candidate_20261021_002/aspect_reference.sqlite

.venv/Scripts/python.exe scripts/aspect_candidate_rag.py prepare "未完成体过去时怎样表达概括事实意义？" --db data/processed/aspect_reference/research_exports/aspect_editorial_candidate_20261021_002/aspect_reference.sqlite --include-candidates --output tmp/aspect_research_packet.json
```

省略 `--include-candidates` 时只返回40节原ready。加 `--code aspect.ch05.s04.02` 可明确取一节候选；仍隔离的来源会返回无证据。代码按整节预算截取，超预算的节会列入 `omitted_sections`，不会用断章片段补算命中。包内 `aspect_candidate_rag.py` 也可直接运行，只依赖Python标准库，无需原PDF或网络。

输出包含原PDF指纹、节键、印刷页、原页哈希、编校文本哈希及修改对应疑点。`prompt_package` 是待使用的证据包，本轮没有调用生成API。连续逐字引用校验只验证引文确实出自所给资料。

## 检索与验证边界

[002候选验收](../data/processed/aspect_reference/reviews/candidate_verification_20261021_002.json)核实9个包内文件指纹、五张原表、91处修改重放、73节可用来源、73次伪造引用拒绝、73次篡改证据包拒绝及27节理论/60单元非理论隔离。SQLite完整性ok，外键问题0。11项相关unittest通过。

冻结的开发范围为32道自然问题、4道明确指定隔离来源的问题和4道无关问题。原40节入口有10个目标在启用范围内，命中9个；另22个目标原本隔离，因此全32题为9/32。显式候选73节入口为30/32；两种入口的隔离4/4和无关4/4均符合预期。见[按可用范围解释的结果](../data/processed/aspect_reference/rag/coverage_aware_acceptance_20261021_001.json)。32题中含旧开发8题，新入口在旧8题为6/8；旧原始空白分词入口的0/8仍作为历史失败保留。检索机制和检索范围同时变化，不能从这些数字单独推导某一个因素的增益。

两个漏题的预定来源排名为14和7，详见[漏检诊断](../data/processed/aspect_reference/rag/miss_analysis_20261021_001.json)。由同一助手按已知目录编写的问题，不能作为独立专家盲评、泛化召回率或生成答案正确率。

## 论文引用与后续研究

书目著录：张家骅. 现代俄语体学[M]. 2版. 北京：高等教育出版社，2004. 原件ISBN 7-04-014221-X。

正文印刷页通常为PDF页减20；前置页另有编号，使用保存的 `printed_pages`。引用编校文字时同时说明“编校候选层”、原书位置和所用候选包版本；需要逐字引原书时回到原印层及原图。未查文学原作的引例应披露转引关系。

该库用于理论参照和例证定位。书中例句经过作者选择，研究自然使用频率、搭配分布及体选择比例时，另需明确的自然语料抽样、去重与统计方案。

下一阶段仍需核查30条原著来源和4条理论或语境问题，保留PDF39墨迹占位，改进两道开发检索漏题，并开展独立语义评价及单独的生成验收。不得把模型自检、二轮核图或零工程告警表述为正确率100%。
