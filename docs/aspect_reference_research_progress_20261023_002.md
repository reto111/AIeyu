# 现代俄语体学：93节候选与论文研究附层

2026-10-23更新。当前为[编校候选23日001](../data/processed/aspect_reference/research_exports/aspect_editorial_candidate_20261023_001/README.md)、[编号锚段23日001](../data/processed/aspect_reference/research_exports/aspect_numbered_examples_20261023_001/README.md)和[学习卡23日001](../data/processed/aspect_reference/research_exports/aspect_study_cards_20261023_001/README.md)。用于理论依据、引文定位和论文研究设计，尚未独立专家审定。

|层次|实际数量|边界|
|---|---|---|
|原印理论|40 ready、60 unresolved|原库不回写候选通过|
|当前候选|40原ready＋53模型候选，7隔离|默认40，显式启用93|
|当前方案23日002|118提案、127编辑|114编辑在允许节，13在隔离节|
|原125疑点|110方案、8保留、5待出处、1理论语境、1墨迹|另8追加项单列，不并入125分母|
|固定外部来源|29项、71证据文件|另有265页未审核的文学原作定位OCR|
|编号锚段|1453＝269原ready＋1067候选＋117隔离|显式可查1336，非全书例句数|
|模型学习卡|100卡350主张，350精确引句|40/119原ready、53/201候选、7/30隔离|
|多轴试标22日002|22目标、39解释引句、110轴值|18俄4汉，有意选例，非金标准|
|复核空包23日001|22目标、两张空表、264空分类格|独立标注完成0，未产生实际一致率|

原印481页PDF与来源库指纹未变：471来源页、135批、40历史页修订、100理论及60非理论单元。481页原始OCR仍unreviewed；练习262编号父题、9题12处方案及181书目段索引继续排除理论检索和学生池。

## 新原作证据

公开取得А.С.Ткаченко《Душа живая》1984年扫描，版权页及尾页均标496页，文件498图；下载实际为ZIP容器，已校CRC并取出唯一DjVu。没有嵌入文字层，复用本地俄文模型识别265页（1–251、276–289）作定位；目标找到后停止余页OCR，不声称全498图已识别或审核。

- 《Мелочи жизни》印刷61/图62写кто эти люди，教材PDF356/印刷336为кто это люди；AS-TI-104候选据原作校эти，解除该项阻断。原作Деятель与教材корреспондент不同，节略也存在，警示随候选保留。同节это его слова仍按合法助词读法保留，Сизов原作未核，不连带改成эти。
- 《В Медынь за медом》印刷287/图288写не изучим пчелу，教材PDF358/印刷338为пчелы；新增AS-NEW-009只改名词字形，不补原作被略去的插入语。该节AS-TI-106鸟鸣署名仍未核，整节继续隔离。

这也说明同作者后续文献不能替代文学原作：2010论文重复это，原作却为эти。[附加论文与历史计数](aspect_reference_literature_evidence_20261023.md)保留过程；其中40/29是作者报告值，不是本项目语料实验。[当前来源](../data/processed/aspect_reference/external_evidence/source_manifest_20261023_001.json)、[265页定位缓存核验](../data/processed/aspect_reference/reviews/lookup_cache_verification_20261023_001.json)及[新词形核图](../data/processed/aspect_reference/reviews/primary_bee_observation_20261023_001.json)可查。

[7项未决](../data/processed/aspect_reference/reviews/remaining_source_queue_20261023_001.md)为5出处、1理论语境、1墨迹，未猜改。原始教材、学生或其他书库未改。

接续检索另存[覆盖记录002](../data/processed/aspect_reference/reviews/negative_source_search_20261023_002.json)：大学资料32页OCR仅作定位，实际核图25页，确认Стрехнин姓名与作品目录，未确认教材两句归属；《Разведку ведет отряд Бороды》电子转录8章指定模式未命中，不代表整个两卷集或作者全部作品均已排查。两项公开作者目录没有目标全文链接；Арутюнова后续著作页面返回交互验证外壳，未执行验证程序，未据此裁定术语。新增解决0，7节继续隔离；这些定位资料不并入固定29来源71文件。

[127处逐编辑证据矩阵](../data/processed/aspect_reference/reviews/edit_evidence_matrix_20261023_001.md)已补齐JSON与TSV：85书内/语言判断、31外部字形/归属、2同作者后刊归属、7外部语境模型改译、2外部论述模型推导。39条附外证提案共43编辑，逐编辑相关外证42处；127行旧值、页绑定及导出字段均重放通过，71证据文件指纹复核。分类不是正确率，也不改变候选文本与范围。

## 工程核验与研究附层

[候选全量审计](../data/processed/aspect_reference/reviews/candidate_verification_20261023_001.json)重建100节、重放127编辑，验证原五表逐行一致、93允许节引用及篡改拒绝、7理论＋60非理论隔离。[索引审计](../data/processed/aspect_reference/reviews/example_index_verification_20261023_001.json)全验1453锚段文本、上下文及原页，含200次范围查询。[增量证明](../data/processed/aspect_reference/reviews/candidate_index_delta_20261023_001.json)只两节正文改变、33锚段状态改变、1锚段候选文字及5上下文改变，原1453锚段与页不变，排序算法未改。

学习卡重绑定当前候选，350主张与原引句、偏移和页绑定全部未改，仅两卡更新过时警示。原29批、重绑定批030与新全量重绑定批031都保留。266个PDF页为引句位置并集。[全量引句核验](../data/processed/aspect_reference/reviews/study_card_verification_20261023_001.json)及[200查询](../data/processed/aspect_reference/reviews/study_card_collection_verification_20261023_001.json)通过。此前350主张配对阅读不等于100节重新完整阅读或语义正确率；[12项41段补证002](../data/processed/aspect_reference/reviews/study_claim_support_overlay_20261023_002.md)已重绑定，2项仍隔离，其余338没有被认证充分，不计算12/350错误率。

22目标多轴试标与复核空包继续固定旧007来源，[兼容报告](../data/processed/aspect_reference/reviews/annotation_source_compatibility_20261023_001.json)证明所选源节的正文、状态和警示在新候选不变。узнаешь保留两组词元/体/时态候选；目标形态时、助动词、构式时、事件时间、发生承诺、结果状态及后果分列。151项重算指纹攻击拒绝不证明语义标签正确。实际独立标注尚未发生，空表和一致率工具见[复核协议](aspect_reference_annotation_review_protocol_20261023.md)。

## 检索结果及限制

[冻结50题复验23日001](../data/processed/aspect_reference/rag/extended_question_acceptance_20261023_001.json)：24自然题词项20/24、passage18/24；8主题重叠范围外仅1/8、3/8空证据，8普通无关均拒绝。旧10隔离预期现7拒绝，3项凭新原作证据合法启用，按当前真实范围10/10符合。旧32开发自然题32/32，原40仅10个预定目标可用且10/32；[旧补充24题](../data/processed/aspect_reference/rag/supplement_revalidation_20261023_001.json)词项17/24、passage20/24，23目标可用。题均同一助手针对已知资料编写；passage曾据旧题开发，不能作独立盲评或生成正确率。

[范围词表候选](aspect_reference_evidence_scope_experiment_20261023.md)首组40题路由39/40、追加16压力题0/16，旧8范围外仍漏2；未默认化，不建议实际门控。这些失败保留，不能说已解决证据充分性。

[范围统计](../data/processed/aspect_reference/reviews/corpus_profile_20261023_001.json)：93允许正文343709个Unicode码点，含空白脚注，非俄语词数或token。414理论PDF页并集＝368仅允许＋12混合＋34仅隔离，不表示整页无误。1453是编号段落锚点，可能含多句、公式或部分对话；完整例句边界及俄汉全量对齐未完成，不能用于自然频率分母。

## 本地入口

```powershell
.venv/Scripts/python.exe -X utf8 scripts/aspect_candidate_rag.py prepare "未完成体为什么能表示行为已经达到结果？" --include-candidates
.venv/Scripts/python.exe -X utf8 scripts/aspect_example_index.py search --contains ловить --include-candidates --limit 5
.venv/Scripts/python.exe -X utf8 scripts/aspect_study_cards.py show --code aspect.ch13.s02.01 --include-candidates
```

36项相关unittest通过。查询不调用生成API，锚段按区分大小写的字面子串查询、保留е/ё。论文引用回原印刷页，模型改译与归纳另标研究者处理。未外发本地PDF、调用收费OCR/生成、部署、提交或推送。独立专家、自然语料实验、正式生成对照仍待实施。
