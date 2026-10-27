# 现代俄语体学：当前研究入口

当前为[候选006](../data/processed/aspect_reference/research_exports/aspect_editorial_candidate_20261022_006/README.md)、[编号锚段索引004](../data/processed/aspect_reference/research_exports/aspect_numbered_examples_20261022_004/README.md)和[学习卡附层001](../data/processed/aspect_reference/research_exports/aspect_study_cards_20261022_001/README.md)。用于论文理论依据、引文定位和研究设计，尚未独立专家审定或正式论文验收。

|层次|实际范围|边界|
|---|---|---|
|原印理论|40 ready、60 unresolved|原印库不回写候选通过|
|候选006|40原ready＋51模型候选，9隔离|默认40，显式启用91|
|编校方案010|114提案、123编辑|110编辑在允许候选，13在隔离节|
|原125疑点说明|108方案、8保留、7待来源、1理论语境、1墨迹|一条可含多个问题，另6追加项单列|
|外部资料|27来源、59证据文件|扫描、转录、语法合法性及模型推断分开|
|编号锚段|1453＝269原ready＋1028候选＋156隔离|显式允许1297，非全书例句数|
|模型学习卡|100节、350主张、29批|40/119原ready、51/195候选、9/36隔离|
|模型语义试标|22个目标＝18俄语＋4汉语|有意选例，用于发展规范，非金标准|

原印仍为471来源页记录、135批、40历史页修订、100理论及60非理论单元；481页原始OCR仍unreviewed。练习262编号父题、9题12处方案和181书目段落索引保留，继续排除理论检索和学生池。

## 来源与编校

006只比005新增AS-NEW-007：PDF52/印刷32原印“是双肘支撑着膝盖”改为模型候选“是双肘支在膝盖上”。原句、同段俄文及前句中文一致以膝为支点。[原页核验](../data/processed/aspect_reference/reviews/study_observation_visual_20261022_001.json)已保存，原印保留。[增量检查](../data/processed/aspect_reference/reviews/candidate_index_delta_20261022_002.json)证明只一节正文改变，1453锚段正文及原页不变，仅两条邻近上下文改变，检索算法未改。

[候选全量审计006](../data/processed/aspect_reference/reviews/candidate_verification_20261022_006.json)验证100节重建、123编辑、原五表一致、91允许节引用与篡改拒绝及9理论＋60非理论隔离。[索引全量审计004](../data/processed/aspect_reference/reviews/example_index_verification_20261022_004.json)验证1453锚段的文本、页和上下文，含200次单位范围查询。20项unittest相关测试通过。

[9项未决](../data/processed/aspect_reference/reviews/remaining_source_queue_20261022_002.md)继续保留隔离。это仅由学术语法支持一般合法性，不称已找到Сизов原作；Катаев的Леня男称有原刊扫描支持，并保护同节另一女性Лена。Мамин饮酒译文据电子原作语境修正，中间引文纸本未核。详见[来源008](../data/processed/aspect_reference/external_evidence/source_manifest_20261022_008.json)和[59文件核验](../data/processed/aspect_reference/external_evidence/verification_20261022_002.json)。

## 学习卡与标注附层

100节均经同一助手完整源节阅读后归纳。每条模型主张与原书连续引句分列，350引句在原印和固定候选005中均精确唯一匹配，并保存原单位偏移、PDF页、印刷页和页图指纹。[全量检查](../data/processed/aspect_reference/reviews/study_card_verification_20261022_001.json)及[200次查询范围验收](../data/processed/aspect_reference/reviews/study_card_collection_verification_20261022_001.json)通过。266个PDF页仅为引句所在页并集，不是全页语义正确率。卡片固定005，未静默改版；[兼容报告](../data/processed/aspect_reference/reviews/study_card_compatibility_20261022_001.json)确认350引句在006仍原样，来源状态不变。

[22条试标](../data/processed/aspect_reference/reviews/semantic_annotation_pilot_20261022_001.md)分开记录形式体、时/式、事件时间、结果、情态、重复及时间量度对象，并保留узнаешь无ё/重音书写的判读歧义。只给每锚段一个定位目标试标，不称完成1453条语义审核或俄汉对齐。学习卡、试标和提示题未接RAG、未入学生池，均非独立专家结果。后续自然语料问题与抽样边界见[论文研究问题](aspect_reference_corpus_hypotheses_20261022.md)。

## 检索结果与已知限制

默认lexical保留，passage可选。[最新冻结50题复验004](../data/processed/aspect_reference/rag/extended_question_acceptance_20261022_004.json)：24自然题默认20/24、段落18/24；8主题重叠范围外题仅1/8、3/8空证据；8普通无关题均8/8。旧10隔离预期现9项仍拒绝，另1项因原刊证据成为候选，按当前状态10/10符合。[旧补充24再验003](../data/processed/aspect_reference/rag/supplement_revalidation_20261022_003.json)为默认17/24、段落20/24，23目标可用。段落模式曾据旧题开发；所有题均同一助手按已知资料编写，不能当独立盲评，也不是生成答案正确率。

1453是编号段落锚点，可能含多句、公式或部分对话。无编号、行内、表格和练习答案未统计；不能当自然语料句数或频率。当前91节允许正文337298个Unicode码点（Python len，含空白脚注），非俄语词数或token。[范围统计003](../data/processed/aspect_reference/reviews/corpus_profile_20261022_003.json)仍为414理论页并集：362仅允许、11混合、41仅隔离，不是页正确率。

## 本地使用

```powershell
.venv/Scripts/python.exe -X utf8 scripts/aspect_candidate_rag.py prepare "未完成体为什么能表示行为已经达到结果？" --include-candidates
.venv/Scripts/python.exe -X utf8 scripts/aspect_example_index.py search --contains ловить --include-candidates --limit 5
.venv/Scripts/python.exe -X utf8 scripts/aspect_study_cards.py show --code aspect.ch11.s01.03 --include-candidates
```

查询不调用生成API；锚段为区分大小写的字面子串搜索，保留е/ё。引用论文须回原印刷页；候选译改和模型笔记不得冒称原书逐字正文。未改原PDF、学生或其他书库，未外发本地PDF、付费OCR/生成、部署、提交或推送。
