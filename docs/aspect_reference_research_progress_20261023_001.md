# 现代俄语体学：研究知识库当前入口

更新于2026-10-23（北京时间）。当前为[候选007](../data/processed/aspect_reference/research_exports/aspect_editorial_candidate_20261022_007/README.md)、[编号索引005](../data/processed/aspect_reference/research_exports/aspect_numbered_examples_20261022_005/README.md)、[学习卡002](../data/processed/aspect_reference/research_exports/aspect_study_cards_20261022_002/README.md)与[多轴试标002](../data/processed/aspect_reference/research_exports/aspect_annotation_pilot_20261022_002/README.md)。用于理论依据、原页定位、研究设计和后续论文标注规范；尚未独立专家审定。

|层次|实际数量|使用边界|
|---|---|---|
|原印理论|40 ready、60 unresolved|保留原始状态，不回写候选通过|
|候选007|40原ready＋52模型候选，8隔离|默认40，显式启用92|
|编校方案011|116提案、125编辑|112编辑在允许节，13在隔离节|
|原125疑点|109形成方案、8保留、6待来源、1理论语境、1墨迹|另7条追加记录单列；一条可含多个问题|
|外部证据|28来源、61文件|电子转录、原刊扫描和模型判断分层|
|编号锚段|1453＝269原ready＋1034候选＋150隔离|显式可查1303，不是全书例句数|
|模型学习卡|100卡350主张，350引句|40/119原ready、52/198候选、8/33隔离|
|多轴试标|22目标＝18俄语＋4汉语|39解释引句、110轴值；非金标准|

原印仍为481页扫描PDF、471来源页记录、135批、40历史页修订；100理论及60非理论单元。481页原始OCR均保留unreviewed，不用后续审核覆盖原始层。练习262编号父题、9题12处方案及181书目段索引继续排除理论检索与学生池。

## 本轮来源处理

В. Рыбин电子原作《Земля зовет》（收于《Здравствуй, Галактика!》）支持PDF59/印刷39漏印л的候选恢复；同文明确是宇宙飞船，也支持将“军舰也是新式的”改为“飞船也仍然是新的”。原页已核图，原印保留。电子版出版年份元数据不一致，未据此认定纸本版次。书中节略末词仍保留节略，不擅补整句。[新增来源](../data/processed/aspect_reference/external_evidence/source_manifest_20261022_009.json)、[原页记录](../data/processed/aspect_reference/reviews/primary_continuation_visual_20261022_001.json)、[增量证明](../data/processed/aspect_reference/reviews/candidate_index_delta_20261022_003.json)可查。

[8项未决](../data/processed/aspect_reference/reviews/remaining_source_queue_20261022_003.md)包括6条原作出处、1条理论术语切换、1条墨迹。作者2007年论文新增核图的приход/приезд段没有直接裁定радовал处术语切换；1980文集公开目录要求会员下载，未取得全文。不按语法通顺、姓名近似或负检索推断正确原文。[本轮未成功查源记录](../data/processed/aspect_reference/reviews/negative_source_search_20261022_002.json)保留。

[候选审计007](../data/processed/aspect_reference/reviews/candidate_verification_20261022_007.json)验证100节重建、125编辑、原五表一致、92允许节引句/篡改拒绝及8理论＋60非理论隔离。[索引审计005](../data/processed/aspect_reference/reviews/example_index_verification_20261022_005.json)全验1453锚段的来源、原页、上下文及200次单位范围查询。原始PDF和来源库指纹不变。

## 学习卡与多轴标注

学习卡002重绑定候选007，保留原29批来源链，新增一个完整重绑定批030。350引句在原印及候选中均精确唯一存在，原单位偏移和页绑定全验；266个PDF页为引句位置并集。仅修改一条模型归纳，去掉容易误解为“未完成体不能表达有限重复”的对比表述；原书不因此新增编校项。[卡片修订链](../data/processed/aspect_reference/reviews/study_card_amendments_20261022_001.json)、[源句全验](../data/processed/aspect_reference/reviews/study_card_verification_20261022_002.json)及[200次查询](../data/processed/aspect_reference/reviews/study_card_collection_verification_20261022_002.json)可查。原学习卡001保留固定005来源。

多轴试标002重用既有22个有意选定教材目标，另存联合词形候选、作者选定读法、目标形态时、语法时、助动词、构式时态、事件时间及五个语义轴。узнаешь保留两组词元/体/时态分析；заказывать本身无形态时，另绑定будете；汉语了₁/了₂共5个标记逐字定位。[机械审计](../data/processed/aspect_reference/reviews/semantic_annotation_multiaxis_verification_20261022_001.json)核验22目标、39解释引句、1助动词、7量度短语及5汉语标记。命令/许可不自动变成事件已发生，结果状态取消不自动否定后果相关性。

这些标签仍是同一助手依据教材的模型判读。引句存在不证明解释正确，22目标不代表自然语料、随机样本、独立一致率或金标准；TSV只导出作者选定读法，analysis_count=2不能作无歧义词形标签。学习卡、试标和提示题未接RAG或学生池。

## 检索评价与范围

[冻结50题复验005](../data/processed/aspect_reference/rag/extended_question_acceptance_20261022_005.json)：24自然题默认词项20/24、passage18/24；8主题重叠范围外仅1/8、3/8空证据，8普通无关均8/8。原10隔离预期现8拒绝，2项因出处证据成为候选；按当前真实范围10/10符合。旧预期不改写，检索算法未改。旧32自然开发题为32/32，不能当留出；[旧24补充题复验004](../data/processed/aspect_reference/rag/supplement_revalidation_20261022_004.json)默认17/24、passage20/24，23目标可用。题目均同一助手针对已知资料编写，passage曾据旧题开发；均非独立盲评或生成准确率。

[范围统计004](../data/processed/aspect_reference/reviews/corpus_profile_20261022_004.json)：92节允许正文338211个Unicode码点（含空白、引句、脚注），非俄语词数或token。414理论PDF页并集为363仅允许、11混合、40仅隔离，不表示整页无误。1453是编号段落锚点，可能含多句、公式或部分对话；完整例句边界、无编号例句及俄汉全量对齐未完成，不能用作自然频率分母。

## 本地使用

```powershell
.venv/Scripts/python.exe -X utf8 scripts/aspect_candidate_rag.py prepare "未完成体为什么能表示行为已经达到结果？" --include-candidates
.venv/Scripts/python.exe -X utf8 scripts/aspect_example_index.py search --contains ловить --include-candidates --limit 5
.venv/Scripts/python.exe -X utf8 scripts/aspect_study_cards.py show --code aspect.ch01.s04.06 --include-candidates
```

查询不调用生成API；锚段为区分大小写的字面子串搜索，保留е/ё。论文引用须回原印刷页，候选译改与模型笔记另标研究者处理。30项相关unittest通过。未改学生或其他书库，未上传本地PDF、付费OCR/生成、部署、提交或推送。

另完成[范围词表候选对照](aspect_reference_evidence_scope_experiment_20261023.md)：首组40题路由39/40，追加16压力题0/16，保留全部失败，候选不建议用于实际门控、未默认化、未做生成。30项相关工程测试通过，不据此宣称语义或泛化正确。

续做350条主张/引句配对阅读（非100节完整重读），发现部分单引句只覆盖核心定义或列举引出语。另存[12项41段补充证据](../data/processed/aspect_reference/reviews/study_claim_support_overlay_20261023_001.md)，区分每段所支持的子项，并[全验偏移、页和状态](../data/processed/aspect_reference/reviews/study_claim_support_verification_20261023_001.json)。其中2项来源仍隔离，入口继续拒绝；350主张和旧卡片指纹未改。12为定向样例，不是全部问题数或12/350错误率；其他338未被认证充分，新增引句也不替代独立蕴涵判断。

附加[2010论文与历史计数说明](aspect_reference_literature_evidence_20261023.md)：同作者重复это字形仍非文学原作核验，8项隔离不变；其40/29计数另存为文献报告值，不算本项目实测。
