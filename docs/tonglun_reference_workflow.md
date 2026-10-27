# 《新时代俄语通论》双册研究语料与RAG

<!-- tonglun-current-start -->
## 2026-10-27《新时代俄语通论》双册知识库（持续）

- 最新[89处候选与227快照](tonglun_reference_current89_20261027.md)、[论文方法及结果底稿](tonglun_reference_thesis_preparation_20261027_001.md)。801原页、730正文页/302单元；175 ready（上65/下110）、127隔离、139原待核保持；整体内容审核尚未完成。
- [候选27日002](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261027_002.json)：139补证、79提案/60待证、89处建议，72局部组件为重叠维度；应用0、独立复核0。“将来时时”及свету等混合case保留仍有效。新增бобр→河狸学名桥接、雪莲花→雪花莲双语预览旁证、энергией→энергии电子原作及专著证据；укроп仍因规范名/俗名关系待证，017年代仍待证。
- [89处字符出处](../data/processed/tonglun_reference/editorial_candidates/editorial_coordinates_20261027_002/README.md)保持原87处ID、原范围、页绑定及责任：3括注、12转录、74未全面分类，不计为89处教材勘误。[数据卡27日002](../data/processed/tonglun_reference/research_exports/dataset_card_20261027_002/README.md)含302单元元数据，无隔离正文；其227未测是创建时状态，后续已测见论文底稿。
- [当前139项统一评阅包002](../data/processed/tonglun_reference/research_reviews/issues139_current_20261027_002/README.md)：139case、127审计预览、278空槽，未盲化，独立评分0；原139待核原文及哈希保持。
- [五单元规范化](tonglun_reference_normalized_five_units_20261026.md)5455码位/235记法/92教学组；047限纯文本，词内斜体、精确字形、调核与理论未认证。另两编校单元原3136码位/5页完整纯文本复读，227固定175＋47编校未批准＋5规范化未批准、61编辑、395096码位，不自动应用当前89建议。
- [227研究快照](../data/processed/tonglun_reference/research_exports/editorial227_preview_20261027_001/README.md)保留旧225全部记录，默认175、编校开关222、规范化开关180、两项227。原139待核/127隔离不因研究快照纳入而解除。
- [冻结227检索](../data/processed/tonglun_reference/rag/editorial227_evaluation_20261027_001.json)：原四组150/16/127及5开发题沿用225封存，只重算222/227；942名次记录中322新算/620沿用。220→222、225→227旧150名次逐条不变，新两开发题目标均第1；227旧150 top1/3/5为97/121/126。225时066从4跌出前5、069从1降2的退步仍保留。普通无关8/8空、重叠范围外3/8空，未纳入目标泄漏0；非独立正确率。
- [225本地证据包](tonglun_reference_traceable225_local_20261027.md)仍用自身冻结数据，支持检索/重放/逐字引句页定位。225来源、57派生、413跨页及620旧命中表通过；无关主张配有效引句仍可通过，语义支持未解决。两版本各8次移目录隔离命令无网络/DB，Python审计钩子不是操作系统沙箱。
- [需求规则第二版压力检验](tonglun_reference_requirement_challenges_20261027.md)：原40题已用于开发，另新20题仍漏6/误2；同一助手压力题，不推断总体准确率，不默认接学生流程。新增收费OCR/生成0，未读学生库、未改其他书库/PDF，未部署、提交、推送。
- 语调342编辑上下文、603记号及540星号对，32曲线另计，不称自然例句或完整调核；附录32页895首轮记录、5待核及正式导入0保持。[书目原页与RIS/BibTeX](tonglun_reference_bibliographic_evidence_20261026.md)保留。
- [最新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261027_102131.json)固定1530文件，[封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_029.json)；采样2026-10-27T02:21:30.426Z为5小时96.0%、周41.0%，不是财务余额。继续未决组件、整单元和独立专家/语义/生成评价。


- 新外层已另实跑：[52级封存/1706唯一指纹](../data/processed/tonglun_reference/reviews/recursive_chain_verification_20261027_002.json)与[115份Markdown/2361本地链接](../data/processed/tonglun_reference/reviews/current_documents_links_with_origins_20261026_003.json)均通过；链接计数对应该次检查范围。本行是随后追加的验证入口，不改任何封存文件。
<!-- tonglun-current-end -->

## 以下为历史批次原记录（保留当时表述）

本任务用途已由用户确认：与既有语法书相同，准备可溯源检索/RAG研究。不是自动生成练习题，也不是俄语例句语言学标注任务。

## 2026-10-25 13:06补证断点（当前）

- 13:06接续：确认新5小时窗口，最新采样2026-10-25T05:06:08.798Z，5小时已用70.0%、周57.0%。旧96%为昨夜事件，不当作当前额度；比例不是货币余额。
- 原始801页归档；正文730整页、302编号单元，175个ready（上65/下110）、127个隔离。[原正文断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)的四审核表仍一致，139条原待核状态未解除。
- [当前补证说明](tonglun_reference_evidence_progress_20261025_009.md)与[候选009](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261025_009.json)累计73条，58项建议65处编辑、14项待证、1项局部误报撤回，11项仅部分组件；另66条未在此补证系列处理。[重放](../data/processed/tonglun_reference/reviews/editorial_evidence_verification_20261025_007.json)及[来源核验](../data/processed/tonglun_reference/reviews/new_evidence_integrity_20261025_005.json)通过，应用0，默认检索未改变。
- 新增2234页公开外来词词典下载，实际核图首页及3词条；旧3188页正字法词典17词条核图和23页机构书目仍保留。公开网页索引节选与完整PDF核图分别标注；模型翻译建议不冒称专家勘误。未上传教材PDF或整段正文，新增收费OCR/生成调用0。
- 附录32页首轮候选：787术语行、108条书目，正式导入0、5项待核；[附录说明](tonglun_reference_appendix_progress_20261024.md)及[新增建议](../data/processed/tonglun_reference/editorial_candidates/appendix_evidence_proposals_20261024_001.json)保留1985/2005年份差异。默认检索不收附录。
- [问句基线](tonglun_reference_question_baseline_20261025.md)沿用150开发题，指定目标top5候选125/150、手给关键词150/150；普通无关8/8空返回、重叠范围外3/8。127隔离目标未返回，但仅89题整体空返回；均非生成正确率，19相关测试通过。候选未按这组失败调参，未默认化。
- [166题评阅材料](../data/processed/tonglun_reference/research_reviews/question166_20261025_001/question_index.md)316组、172完整来源、632空评分槽；[抽样说明](tonglun_reference_question_sampling_20261025.md)列25未目标化ready。实际独立评分0。[175原转录快照](../data/processed/tonglun_reference/research_exports/source175_original_20261025_001/README.md)在项目外隔离Python校验及两种篡改拒绝通过，不含隔离正文或候选。
- [最新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_130609.json)及latest_evidence固定123项文件指纹，接续昨夜[追加封存004](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_004.json)；旧正文/附录/检索包均保留。未改学生库、其他书库或原PDF，未部署、提交、推送。
- 继续待核证据、原作出处与音标排版复核。正式编校研究版、独立问题评价、来源充分性及生成对照未完成；[139条旧接续队列](../data/processed/tonglun_reference/reviews/next_review_queue_20261025_001.json)为39条补证时的历史，不据当前建议解除139条待核。

## 2026-10-25 12:44补证断点（历史）

- 12:44接续：确认新5小时窗口，最新采样2026-10-25T04:44:54.054Z，5小时已用37.0%、周52.0%。旧96%为昨夜事件，不当作当前额度；比例不是货币余额。
- 原始801页归档；正文730整页、302编号单元，175个ready（上65/下110）、127个隔离。[原正文断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)的四审核表仍一致，139条原待核状态未解除。
- [当前补证说明](tonglun_reference_evidence_progress_20261025_007.md)与[候选007](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261025_007.json)累计69条，57项建议64处编辑、11项待证、1项局部误报撤回，9项仅部分组件；另70条未在此补证系列处理。[重放](../data/processed/tonglun_reference/reviews/editorial_evidence_verification_20261025_005.json)及[来源核验](../data/processed/tonglun_reference/reviews/new_evidence_integrity_20261025_003.json)通过，应用0，默认检索未改变。
- 新增2234页公开外来词词典下载，实际核图首页及3词条；旧3188页正字法词典17词条核图和23页机构书目仍保留。公开网页索引节选与完整PDF核图分别标注；模型翻译建议不冒称专家勘误。未上传教材PDF或整段正文，新增收费OCR/生成调用0。
- 附录32页首轮候选：787术语行、108条书目，正式导入0、5项待核；[附录说明](tonglun_reference_appendix_progress_20261024.md)及[新增建议](../data/processed/tonglun_reference/editorial_candidates/appendix_evidence_proposals_20261024_001.json)保留1985/2005年份差异。默认检索不收附录。
- [问句基线](tonglun_reference_question_baseline_20261025.md)沿用150开发题，指定目标top5候选125/150、手给关键词150/150；普通无关8/8空返回、重叠范围外3/8。127隔离目标未返回，但仅89题整体空返回；均非生成正确率，19相关测试通过。候选未按这组失败调参，未默认化。
- [166题评阅材料](../data/processed/tonglun_reference/research_reviews/question166_20261025_001/question_index.md)316组、172完整来源、632空评分槽；[抽样说明](tonglun_reference_question_sampling_20261025.md)列25未目标化ready。实际独立评分0。[175原转录快照](../data/processed/tonglun_reference/research_exports/source175_original_20261025_001/README.md)在项目外隔离Python校验及两种篡改拒绝通过，不含隔离正文或候选。
- [最新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_124455.json)及latest_evidence固定106项文件指纹，接续昨夜[追加封存004](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_004.json)；旧正文/附录/检索包均保留。未改学生库、其他书库或原PDF，未部署、提交、推送。
- 继续待核证据、原作出处与音标排版复核。正式编校研究版、独立问题评价、来源充分性及生成对照未完成；[139条旧接续队列](../data/processed/tonglun_reference/reviews/next_review_queue_20261025_001.json)为39条补证时的历史，不据当前建议解除139条待核。

## 2026-10-25 12:39补证断点（历史）

- 12:39接续：确认新5小时窗口，最新采样2026-10-25T04:39:54.199Z，5小时已用30.0%、周51.0%。旧96%为昨夜事件，不当作当前额度；比例不是货币余额。
- 原始801页归档；正文730整页、302编号单元，175个ready（上65/下110）、127个隔离。[原正文断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)的四审核表仍一致，139条原待核状态未解除。
- [当前补证说明](tonglun_reference_evidence_progress_20261025_006.md)与[候选006](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261025_006.json)累计66条，54项建议61处编辑、11项待证、1项局部误报撤回，8项仅部分组件；另73条未在此补证系列处理。[重放](../data/processed/tonglun_reference/reviews/editorial_evidence_verification_20261025_004.json)及[来源核验](../data/processed/tonglun_reference/reviews/new_evidence_integrity_20261025_002.json)通过，应用0，默认检索未改变。
- 新增2234页公开外来词词典下载，实际核图首页及3词条；旧3188页正字法词典17词条核图和23页机构书目仍保留。公开网页索引节选与完整PDF核图分别标注；模型翻译建议不冒称专家勘误。未上传教材PDF或整段正文，新增收费OCR/生成调用0。
- 附录32页首轮候选：787术语行、108条书目，正式导入0、5项待核；[附录说明](tonglun_reference_appendix_progress_20261024.md)及[新增建议](../data/processed/tonglun_reference/editorial_candidates/appendix_evidence_proposals_20261024_001.json)保留1985/2005年份差异。默认检索不收附录。
- [问句基线](tonglun_reference_question_baseline_20261025.md)沿用150开发题，指定目标top5候选125/150、手给关键词150/150；普通无关8/8空返回、重叠范围外3/8。127隔离目标未返回，但仅89题整体空返回；均非生成正确率，19相关测试通过。候选未按这组失败调参，未默认化。
- [166题评阅材料](../data/processed/tonglun_reference/research_reviews/question166_20261025_001/question_index.md)316组、172完整来源、632空评分槽；[抽样说明](tonglun_reference_question_sampling_20261025.md)列25未目标化ready。实际独立评分0。[175原转录快照](../data/processed/tonglun_reference/research_exports/source175_original_20261025_001/README.md)在项目外隔离Python校验及两种篡改拒绝通过，不含隔离正文或候选。
- [最新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_123956.json)及latest_evidence固定99项文件指纹，接续昨夜[追加封存004](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_004.json)；旧正文/附录/检索包均保留。未改学生库、其他书库或原PDF，未部署、提交、推送。
- 继续待核证据、原作出处与音标排版复核。正式编校研究版、独立问题评价、来源充分性及生成对照未完成；[139条旧接续队列](../data/processed/tonglun_reference/reviews/next_review_queue_20261025_001.json)为39条补证时的历史，不据当前建议解除139条待核。

## 2026-10-25 12:35补证断点（历史）

- 12:35接续：确认新5小时窗口，最新采样2026-10-25T04:35:35.339Z，5小时已用22.0%、周50.0%。旧96%为昨夜事件，不当作当前额度；比例不是货币余额。
- 原始801页归档；正文730整页、302编号单元，175个ready（上65/下110）、127个隔离。[原正文断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)的四审核表仍一致，139条原待核状态未解除。
- [当前补证说明](tonglun_reference_evidence_progress_20261025_005.md)与[候选005](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261025_005.json)累计55条，49项建议55处编辑、5项待证、1项局部误报撤回，5项仅部分组件；另84条未在此补证系列处理。[重放](../data/processed/tonglun_reference/reviews/editorial_evidence_verification_20261025_003.json)及[来源核验](../data/processed/tonglun_reference/reviews/new_evidence_integrity_20261025_001.json)通过，应用0，默认检索未改变。
- 新增2234页公开外来词词典下载，实际核图首页及3词条；旧3188页正字法词典17词条核图和23页机构书目仍保留。公开网页索引节选与完整PDF核图分别标注；模型翻译建议不冒称专家勘误。未上传教材PDF或整段正文，新增收费OCR/生成调用0。
- 附录32页首轮候选：787术语行、108条书目，正式导入0、5项待核；[附录说明](tonglun_reference_appendix_progress_20261024.md)及[新增建议](../data/processed/tonglun_reference/editorial_candidates/appendix_evidence_proposals_20261024_001.json)保留1985/2005年份差异。默认检索不收附录。
- [问句基线](tonglun_reference_question_baseline_20261025.md)沿用150开发题，指定目标top5候选125/150、手给关键词150/150；普通无关8/8空返回、重叠范围外3/8。127隔离目标未返回，但仅89题整体空返回；均非生成正确率，19相关测试通过。候选未按这组失败调参，未默认化。
- [166题评阅材料](../data/processed/tonglun_reference/research_reviews/question166_20261025_001/question_index.md)316组、172完整来源、632空评分槽；[抽样说明](tonglun_reference_question_sampling_20261025.md)列25未目标化ready。实际独立评分0。[175原转录快照](../data/processed/tonglun_reference/research_exports/source175_original_20261025_001/README.md)在项目外隔离Python校验及两种篡改拒绝通过，不含隔离正文或候选。
- [最新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_123536.json)及latest_evidence固定93项文件指纹，接续昨夜[追加封存004](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_004.json)；旧正文/附录/检索包均保留。未改学生库、其他书库或原PDF，未部署、提交、推送。
- 继续待核证据、原作出处与音标排版复核。正式编校研究版、独立问题评价、来源充分性及生成对照未完成；[139条旧接续队列](../data/processed/tonglun_reference/reviews/next_review_queue_20261025_001.json)为39条补证时的历史，不据当前建议解除139条待核。

## 2026-10-25 00:35补证断点（历史）

- 00:35接续断点：继续至额度接近用尽；最新平台采样2026-10-24T16:35:38.027Z，5小时已用93%、周45%。比例不是货币余额，未声称账户余额为零。
- 两册801页原始层归档；正文730整页、302编号单元首轮边界齐，175个ready（上65/下110）、127个隔离。[正文断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)的四张审核表仍逐表一致，139条原待核记录未解除。
- 附录32页首轮候选齐：26页787行术语、6页108条书目；[术语014](../data/processed/tonglun_reference/appendix_candidates/terminology_20261024_014.json)仅修正5处自身颚/腭转录，书目003保持两册差异。正式导入0、默认检索不收附录，附录5项仍待裁定。
- [本轮补证说明](tonglun_reference_evidence_progress_20261025_003.md)：[当前正文候选](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261025_003.json)覆盖39条，35项建议38处编辑，3项待证、1项局部误报撤回，3项仅局部组件；[验收](../data/processed/tonglun_reference/reviews/editorial_evidence_verification_20261025_001.json)通过精确旧值与预览重放。应用0，另100条尚未在本补证批处理。
- [附录新增候选](../data/processed/tonglun_reference/editorial_candidates/appendix_evidence_proposals_20261024_001.json)补真值词形和Ковтунова首字母2项建议，原有词典互换/平行系列3行建议保留；1985/2005年份差异未裁定。TLA-V1-001与正文TL-V1-005为同词形不同位置，不重复算独立错误。
- 复用并校验公开3188页正字法词典；实际核图首页及17词头行。新增公开词头/熟语、书目检索和一份23页公开机构书目下载，未上传教材PDF或整段教材正文。无收费OCR/生成API调用，未改其他书库、学生库或原PDF，未部署、提交、推送。
- [本地检索入口](tonglun_reference_local_research_quickstart_20261024.md)示例实测3来源；175单元页级定位453工程引句通过。新[问句候选基线](tonglun_reference_question_baseline_20261025.md)沿用150开发题，指定目标top5为125/150，手给关键词150/150；普通无关8/8空返回、主题重叠范围外3/8空返回。127隔离目标未返回但仅89题整体空返回，均非生成正确率。19项相关测试通过，候选不默认化。
- [166题未评分材料](../data/processed/tonglun_reference/research_reviews/question166_20261025_001/question_index.md)保留316组实际返回、172完整来源、632空评分槽；方法逐题A/B遮蔽，非独立题集或已完成盲评。[核验](../data/processed/tonglun_reference/reviews/question_review_packet_verification_20261025_001.json)通过映射、来源指纹、空格和链接；实际独立评分0，真实包来源绑定与3类伪造拒绝通过。
- [附录阅读与895行空表](tonglun_reference_appendix_progress_20261024.md)、[正文127单元/139条二审材料](tonglun_reference_review_packet_20261024.md)及[复核口径](tonglun_reference_review_protocol_20261024.md)已备；实际独立复核与专家评分均0。
- [最新补证断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_003548.json)及latest_evidence指针固定本轮68项指纹；正文和附录原断点分别保留，原[追加封存003](../data/processed/tonglun_reference/reviews/delivery_addendum_20261024_003.json)27项仍全部通过。
- [覆盖核查](tonglun_reference_question_sampling_20261025.md)：150题目标覆盖150/175原ready，绪论3、词汇5、词法17共25单元未作目标；开发题非随机独立样本。[来源175快照](../data/processed/tonglun_reference/research_exports/source175_original_20261025_001/README.md)保留完整转录与127隔离身份，项目外隔离Python校验及两种篡改拒绝通过；无隔离正文或学生数据。
- [本轮封存001](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_001.json)87项/28源码快照及[追加002](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_002.json)固定新来源快照与抽样材料；旧包不变，整体研究未完成。
- 下一步继续其余100条补证及39条候选复核；139条原待核状态未变。问句开发基线已完成，独立问题评价、引文充分性、正式编校研究版与生成对照未完成。旧批次撤回、页修订和范围勘误详见[工作流历史](tonglun_reference_workflow.md)，不能据模型建议冒称原书勘误或正确率100%。

## 2026-10-25 00:30补证断点（历史）

- 00:30补证断点：继续用户“工作到余额用尽”；最新平台采样2026-10-24T16:29:44.291Z，5小时已用86%、周44%。这是新窗口比例，不是货币余额，未声称耗尽。
- 两册801页原始层归档；正文730整页、302编号单元首轮边界齐，175个ready（上65/下110）、127个隔离。[正文断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)的四张审核表仍逐表一致，139条原待核记录未解除。
- 附录32页首轮候选齐：26页787行术语、6页108条书目；[术语014](../data/processed/tonglun_reference/appendix_candidates/terminology_20261024_014.json)仅修正5处自身颚/腭转录，书目003保持两册差异。正式导入0、默认检索不收附录，附录5项仍待裁定。
- [本轮补证说明](tonglun_reference_evidence_progress_20261025_003.md)：[当前正文候选](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261025_003.json)覆盖39条，35项建议38处编辑，3项待证、1项局部误报撤回，3项仅局部组件；[验收](../data/processed/tonglun_reference/reviews/editorial_evidence_verification_20261025_001.json)通过精确旧值与预览重放。应用0，另100条尚未在本补证批处理。
- [附录新增候选](../data/processed/tonglun_reference/editorial_candidates/appendix_evidence_proposals_20261024_001.json)补真值词形和Ковтунова首字母2项建议，原有词典互换/平行系列3行建议保留；1985/2005年份差异未裁定。TLA-V1-001与正文TL-V1-005为同词形不同位置，不重复算独立错误。
- 复用并校验公开3188页正字法词典；实际核图首页及17词头行。新增公开词头/熟语、书目检索和一份23页公开机构书目下载，未上传教材PDF或整段教材正文。无收费OCR/生成API调用，未改其他书库、学生库或原PDF，未部署、提交、推送。
- [本地检索入口](tonglun_reference_local_research_quickstart_20261024.md)示例实测3来源；175单元页级定位453工程引句通过。新[问句候选基线](tonglun_reference_question_baseline_20261025.md)沿用150开发题，指定目标top5为125/150，手给关键词150/150；普通无关8/8空返回、主题重叠范围外3/8空返回。127隔离目标未返回但仅89题整体空返回，均非生成正确率。19项相关测试通过，候选不默认化。
- [166题未评分材料](../data/processed/tonglun_reference/research_reviews/question166_20261025_001/question_index.md)保留316组实际返回、172完整来源、632空评分槽；方法逐题A/B遮蔽，非独立题集或已完成盲评。[核验](../data/processed/tonglun_reference/reviews/question_review_packet_verification_20261025_001.json)通过映射、来源指纹、空格和链接；实际独立评分0，真实包来源绑定与3类伪造拒绝通过。
- [附录阅读与895行空表](tonglun_reference_appendix_progress_20261024.md)、[正文127单元/139条二审材料](tonglun_reference_review_packet_20261024.md)及[复核口径](tonglun_reference_review_protocol_20261024.md)已备；实际独立复核与专家评分均0。
- [最新补证断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_003010.json)及latest_evidence指针固定本轮55项指纹；正文和附录原断点分别保留，原[追加封存003](../data/processed/tonglun_reference/reviews/delivery_addendum_20261024_003.json)27项仍全部通过。
- 下一步继续其余100条补证及39条候选复核；139条原待核状态未变。问句开发基线已完成，独立问题评价、引文充分性、正式编校研究版与生成对照未完成。旧批次撤回、页修订和范围勘误详见[工作流历史](tonglun_reference_workflow.md)，不能据模型建议冒称原书勘误或正确率100%。

## 2026-10-25 00:13补证断点（历史）

- 00:13补证断点：继续用户“工作到余额用尽”；最新平台采样2026-10-24T16:12:29.144Z，5小时已用57%、周40%。这是新窗口比例，不是货币余额，未声称耗尽。
- 两册801页原始层归档；正文730整页、302编号单元首轮边界齐，175个ready（上65/下110）、127个隔离。[正文断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)的四张审核表仍逐表一致，139条原待核记录未解除。
- 附录32页首轮候选齐：26页787行术语、6页108条书目；[术语014](../data/processed/tonglun_reference/appendix_candidates/terminology_20261024_014.json)仅修正5处自身颚/腭转录，书目003保持两册差异。正式导入0、默认检索不收附录，附录5项仍待裁定。
- [本轮补证说明](tonglun_reference_evidence_progress_20261025_003.md)：[当前正文候选](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261025_003.json)覆盖39条，35项建议38处编辑，3项待证、1项局部误报撤回，3项仅局部组件；[验收](../data/processed/tonglun_reference/reviews/editorial_evidence_verification_20261025_001.json)通过精确旧值与预览重放。应用0，另100条尚未在本补证批处理。
- [附录新增候选](../data/processed/tonglun_reference/editorial_candidates/appendix_evidence_proposals_20261024_001.json)补真值词形和Ковтунова首字母2项建议，原有词典互换/平行系列3行建议保留；1985/2005年份差异未裁定。TLA-V1-001与正文TL-V1-005为同词形不同位置，不重复算独立错误。
- 复用并校验公开3188页正字法词典；实际核图首页及17词头行。新增公开词头/熟语、书目检索和一份23页公开机构书目下载，未上传教材PDF或整段教材正文。无收费OCR/生成API调用，未改其他书库、学生库或原PDF，未部署、提交、推送。
- [本地检索入口](tonglun_reference_local_research_quickstart_20261024.md)的示例已实测3来源；页级定位175单元260600字符、278跨页边界453工程引句通过，127隔离全部拒绝，15项相关测试通过。150/150是指定关键词开发检查，均非自然问题或生成准确率。
- [附录阅读与895行空表](tonglun_reference_appendix_progress_20261024.md)、[正文127单元/139条二审材料](tonglun_reference_review_packet_20261024.md)及[复核口径](tonglun_reference_review_protocol_20261024.md)已备；实际独立复核与专家评分均0。
- [最新补证断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_001304.json)及latest_evidence指针固定本轮39项指纹；正文和附录原断点分别保留，原[追加封存003](../data/processed/tonglun_reference/reviews/delivery_addendum_20261024_003.json)27项仍全部通过。
- 下一步继续编号/表头/例句书内对照与139条待核补证；候选编校未回写，正式研究版、自然问题评价、引文充分性与生成对照仍未完成。旧批次撤回、页修订和范围勘误详见[工作流历史](tonglun_reference_workflow.md)，不能据模型建议冒称原书勘误或正确率100%。

## 2026-10-25 00:02补证断点（历史）

- 00:02补证断点：继续用户“工作到余额用尽”；最新平台采样2026-10-24T16:01:29.714Z，5小时已用39%、周37%。这是新窗口比例，不是货币余额，未声称耗尽。
- 两册801页原始层归档；正文730整页、302编号单元首轮边界齐，175个ready（上65/下110）、127个隔离。[正文断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)的四张审核表仍逐表一致，139条原待核记录未解除。
- 附录32页首轮候选齐：26页787行术语、6页108条书目；[术语014](../data/processed/tonglun_reference/appendix_candidates/terminology_20261024_014.json)仅修正5处自身颚/腭转录，书目003保持两册差异。正式导入0、默认检索不收附录，附录5项仍待裁定。
- [本轮补证说明](tonglun_reference_evidence_progress_20261025.md)：[正文候选002](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261024_002.json)覆盖13条，12项建议13处编辑，1项保留；[验收](../data/processed/tonglun_reference/reviews/editorial_evidence_verification_20261024_001.json)通过精确旧值、来源与预览重放。实际应用0，另126条尚未在本补证批处理。
- [附录新增候选](../data/processed/tonglun_reference/editorial_candidates/appendix_evidence_proposals_20261024_001.json)补真值词形和Ковтунова首字母2项建议，原有词典互换/平行系列3行建议保留；1985/2005年份差异未裁定。TLA-V1-001与正文TL-V1-005为同词形不同位置，不重复算独立错误。
- 复用并校验公开3188页正字法词典；实际核图首页及17词头行。新增公开词头/熟语、书目检索和一份23页公开机构书目下载，未上传教材PDF或整段教材正文。无收费OCR/生成API调用，未改其他书库、学生库或原PDF，未部署、提交、推送。
- [本地检索入口](tonglun_reference_local_research_quickstart_20261024.md)的示例已实测3来源；页级定位175单元260600字符、278跨页边界453工程引句通过，127隔离全部拒绝，15项相关测试通过。150/150是指定关键词开发检查，均非自然问题或生成准确率。
- [附录阅读与895行空表](tonglun_reference_appendix_progress_20261024.md)、[正文127单元/139条二审材料](tonglun_reference_review_packet_20261024.md)及[复核口径](tonglun_reference_review_protocol_20261024.md)已备；实际独立复核与专家评分均0。
- [最新补证断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_000247.json)及latest_evidence指针固定本轮35项指纹；正文和附录原断点分别保留，原[追加封存003](../data/processed/tonglun_reference/reviews/delivery_addendum_20261024_003.json)27项仍全部通过。
- 下一步继续编号/表头/例句书内对照与139条待核补证；候选编校未回写，正式研究版、自然问题评价、引文充分性与生成对照仍未完成。旧批次撤回、页修订和范围勘误详见[工作流历史](tonglun_reference_workflow.md)，不能据模型建议冒称原书勘误或正确率100%。

## 2026-10-24 18:02附录断点（历史）

- 18:02附录中途断点：继续用户“工作到余额用尽”的安排，最近平台采样2026-10-24T10:02:11.489Z已用92%、周29%；采样是否在10分钟内：True，不是货币余额。用途仍为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不表示全书正文审核完成。
- 累计273个已应用批次（上142、下131）、181条历史页修订；730整页、0局部页，768页队列38页未核。上册PDF18–27、30–206、208–334、336–385整页；下册PDF15–166、169–382整页。上册207、335及下册168分编扉页不计正文完成。
- 175个完整单元可检索（上65、下110），127个隔离，0个目录单元尚未入审核库。较21日20:30新增176整页、18个可检索单元、43个隔离单元，局部页另计。
- [139条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261024_130615.json)保留原文与原页。调型规则、语段切分、交际结构表及构词音标/词内斜体的转写限制已明确标记；转写待二审不是原书错误裁定。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261024_002.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次及全部单元重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261024_002.json)覆盖302单元，代码、标题、起页无差异。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261024_002.json)：150/150目标命中、127/127隔离目标未返回。为开发性指定词检查，不是自然问题召回率或生成准确率；21日004失败131/132与005改供明确词后的132/132报告保留，检索器未为本轮调参。
- 正文一致性备份仍为[13:06断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)，四张审核表逐表保持不变；[附录接续断点](../data/processed/tonglun_reference/appendix_checkpoint_20261024_180249.json)及latest_appendix指针固定候选、页级定位与校验。下一步为正文139条二审、附录5项证据裁定及独立评价。
- 116审核说明中‘语音学编最后两单元’为范围误述：实际是第十章第四节第2、3单元，后续还有第4单元和第十一章；116正文与目录代码不变。
- 上册108仅把107标题的全角连接号统一为冻结目录的ASCII连接号，正文、边界与待核说明不变。TL-V1-032的“噪音重复”断言已由071撤回068，仍保留嗓/噪字形待核。上册100、下册104为21日撤回未应用草稿；24日上册134→135（疑点页码和移行）、137→138（蝲蛄字形）、143→145（лям-а字形）亦在应用前撤回替代，禁止重放旧草稿；这些为自身转写修正，不是原书勘误。
- [全部历史修订链](../data/processed/tonglun_reference/reviews/revision_chain_verification_20261024_002.json)复现181条旧JSON、哈希、前后批次与当前链路；本轮追加片段与108标题修订分别精确验证，8项工程unittest通过。
- [302单元正文首轮边界验收](../data/processed/tonglun_reference/reviews/body_completion_20261024_001.json)通过；730整页全部闭合，附录32页及6张分编扉页另计。上册17、29、207、335与下册14、168均非编号正文单元。
- [论文准备记录](tonglun_reference_thesis_preparation_20261024.md)明确教材知识库与自然语料库的区别；[302行独立复核空表](../data/processed/tonglun_reference/reviews/independent_review_blank_20261024_001.json)固定来源指纹，评分字段均空，实际独立复核0。
- [阅读导出与页队列验收](../data/processed/tonglun_reference/reviews/export_verification_20261024_001.json)仍为175个ready来源快照和768页状态；附录32页已完成首轮候选，26页787行术语、6页108条书目（1条跨页），正式附录导入0，不进入默认检索。
- 本轮为同一助手原页视觉初核，ready仅表示完整边界且无已登记阻断项；不表示逐字或语义正确率100%，未做独立专家盲评或生成验收。全书转录、二轮核对、疑点证据裁定和研究版封存尚未完成。
- 未改原PDF、学生库或其他书库，未外发、调用外部OCR/收费生成API、部署、提交或推送。
- [术语候选014](../data/processed/tonglun_reference/appendix_candidates/terminology_20261024_014.json)接续13版追加链并仅修正5处自身颚/腭转录；[书目候选003](../data/processed/tonglun_reference/appendix_candidates/bibliography_20261024_003.json)保留3版追加链。[附录5项书内证据](../data/processed/tonglun_reference/reviews/appendix_intrabook_evidence_20261024_001.json)形成2组3行未应用编校建议，独立二审0。
- [附录接续说明](tonglun_reference_appendix_progress_20261024.md)提供895条阅读稿、来源JSONL和空评分表；[本轮验收](../data/processed/tonglun_reference/reviews/appendix_research_verification_20261024_001.json)通过895条来源绑定和27556处字符偏移，不是语义正确率。
- [页级引句定位](../data/processed/tonglun_reference/reviews/quote_locations_20261024_001.json)通过175个ready单元、260600字符、278跨页边界与453工程引句；127隔离单元全部拒绝，15项相关测试通过。新本地入口scripts/tonglun_quote_locator.py不改变默认RAG。
- [正文二审材料](tonglun_reference_review_packet_20261024.md)固定127个隔离单元、139条原疑点及原页片段；[材料验收](../data/processed/tonglun_reference/reviews/body_second_review_packet_verification_20261024_001.json)通过重建与空裁定检查，实际独立二审0、编校应用0。
- [独立复核口径](tonglun_reference_review_protocol_20261024.md)分开定义转录忠实度、术语对应与版式关系，未实际评分；[追加交付002](../data/processed/tonglun_reference/reviews/delivery_addendum_20261024_002.json)固定81文件、556链接及原24项封存验证。

## 2026-10-24 17:59附录断点（历史）

- 17:59附录中途断点：继续用户“工作到余额用尽”的安排，最近平台采样2026-10-24T09:58:36.144Z已用89%、周29%；采样是否在10分钟内：True，不是货币余额。用途仍为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不表示全书正文审核完成。
- 累计273个已应用批次（上142、下131）、181条历史页修订；730整页、0局部页，768页队列38页未核。上册PDF18–27、30–206、208–334、336–385整页；下册PDF15–166、169–382整页。上册207、335及下册168分编扉页不计正文完成。
- 175个完整单元可检索（上65、下110），127个隔离，0个目录单元尚未入审核库。较21日20:30新增176整页、18个可检索单元、43个隔离单元，局部页另计。
- [139条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261024_130615.json)保留原文与原页。调型规则、语段切分、交际结构表及构词音标/词内斜体的转写限制已明确标记；转写待二审不是原书错误裁定。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261024_002.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次及全部单元重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261024_002.json)覆盖302单元，代码、标题、起页无差异。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261024_002.json)：150/150目标命中、127/127隔离目标未返回。为开发性指定词检查，不是自然问题召回率或生成准确率；21日004失败131/132与005改供明确词后的132/132报告保留，检索器未为本轮调参。
- 正文一致性备份仍为[13:06断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)，四张审核表逐表保持不变；[附录接续断点](../data/processed/tonglun_reference/appendix_checkpoint_20261024_175915.json)及latest_appendix指针固定候选、页级定位与校验。下一步为正文139条二审、附录5项证据裁定及独立评价。
- 116审核说明中‘语音学编最后两单元’为范围误述：实际是第十章第四节第2、3单元，后续还有第4单元和第十一章；116正文与目录代码不变。
- 上册108仅把107标题的全角连接号统一为冻结目录的ASCII连接号，正文、边界与待核说明不变。TL-V1-032的“噪音重复”断言已由071撤回068，仍保留嗓/噪字形待核。上册100、下册104为21日撤回未应用草稿；24日上册134→135（疑点页码和移行）、137→138（蝲蛄字形）、143→145（лям-а字形）亦在应用前撤回替代，禁止重放旧草稿；这些为自身转写修正，不是原书勘误。
- [全部历史修订链](../data/processed/tonglun_reference/reviews/revision_chain_verification_20261024_002.json)复现181条旧JSON、哈希、前后批次与当前链路；本轮追加片段与108标题修订分别精确验证，8项工程unittest通过。
- [302单元正文首轮边界验收](../data/processed/tonglun_reference/reviews/body_completion_20261024_001.json)通过；730整页全部闭合，附录32页及6张分编扉页另计。上册17、29、207、335与下册14、168均非编号正文单元。
- [论文准备记录](tonglun_reference_thesis_preparation_20261024.md)明确教材知识库与自然语料库的区别；[302行独立复核空表](../data/processed/tonglun_reference/reviews/independent_review_blank_20261024_001.json)固定来源指纹，评分字段均空，实际独立复核0。
- [阅读导出与页队列验收](../data/processed/tonglun_reference/reviews/export_verification_20261024_001.json)仍为175个ready来源快照和768页状态；附录32页已完成首轮候选，26页787行术语、6页108条书目（1条跨页），正式附录导入0，不进入默认检索。
- 本轮为同一助手原页视觉初核，ready仅表示完整边界且无已登记阻断项；不表示逐字或语义正确率100%，未做独立专家盲评或生成验收。全书转录、二轮核对、疑点证据裁定和研究版封存尚未完成。
- 未改原PDF、学生库或其他书库，未外发、调用外部OCR/收费生成API、部署、提交或推送。
- [术语候选014](../data/processed/tonglun_reference/appendix_candidates/terminology_20261024_014.json)接续13版追加链并仅修正5处自身颚/腭转录；[书目候选003](../data/processed/tonglun_reference/appendix_candidates/bibliography_20261024_003.json)保留3版追加链。[附录5项书内证据](../data/processed/tonglun_reference/reviews/appendix_intrabook_evidence_20261024_001.json)形成2组3行未应用编校建议，独立二审0。
- [附录接续说明](tonglun_reference_appendix_progress_20261024.md)提供895条阅读稿、来源JSONL和空评分表；[本轮验收](../data/processed/tonglun_reference/reviews/appendix_research_verification_20261024_001.json)通过895条来源绑定和27556处字符偏移，不是语义正确率。
- [页级引句定位](../data/processed/tonglun_reference/reviews/quote_locations_20261024_001.json)通过175个ready单元、260600字符、278跨页边界与453工程引句；127隔离单元全部拒绝，15项相关测试通过。新本地入口scripts/tonglun_quote_locator.py不改变默认RAG。
- [正文二审材料](tonglun_reference_review_packet_20261024.md)固定127个隔离单元、139条原疑点及原页片段；[材料验收](../data/processed/tonglun_reference/reviews/body_second_review_packet_verification_20261024_001.json)通过重建与空裁定检查，实际独立二审0、编校应用0。

## 2026-10-24 17:51附录断点（历史）

- 17:51附录中途断点：继续用户“工作到余额用尽”的安排，最近平台采样2026-10-24T09:48:28.797Z已用82%、周28%；采样是否在10分钟内：True，不是货币余额。用途仍为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不表示全书正文审核完成。
- 累计273个已应用批次（上142、下131）、181条历史页修订；730整页、0局部页，768页队列38页未核。上册PDF18–27、30–206、208–334、336–385整页；下册PDF15–166、169–382整页。上册207、335及下册168分编扉页不计正文完成。
- 175个完整单元可检索（上65、下110），127个隔离，0个目录单元尚未入审核库。较21日20:30新增176整页、18个可检索单元、43个隔离单元，局部页另计。
- [139条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261024_130615.json)保留原文与原页。调型规则、语段切分、交际结构表及构词音标/词内斜体的转写限制已明确标记；转写待二审不是原书错误裁定。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261024_002.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次及全部单元重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261024_002.json)覆盖302单元，代码、标题、起页无差异。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261024_002.json)：150/150目标命中、127/127隔离目标未返回。为开发性指定词检查，不是自然问题召回率或生成准确率；21日004失败131/132与005改供明确词后的132/132报告保留，检索器未为本轮调参。
- 正文一致性备份仍为[13:06断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)，四张审核表逐表保持不变；[附录接续断点](../data/processed/tonglun_reference/appendix_checkpoint_20261024_175101.json)及latest_appendix指针固定候选、页级定位与校验。下一步为正文139条二审、附录5项证据裁定及独立评价。
- 116审核说明中‘语音学编最后两单元’为范围误述：实际是第十章第四节第2、3单元，后续还有第4单元和第十一章；116正文与目录代码不变。
- 上册108仅把107标题的全角连接号统一为冻结目录的ASCII连接号，正文、边界与待核说明不变。TL-V1-032的“噪音重复”断言已由071撤回068，仍保留嗓/噪字形待核。上册100、下册104为21日撤回未应用草稿；24日上册134→135（疑点页码和移行）、137→138（蝲蛄字形）、143→145（лям-а字形）亦在应用前撤回替代，禁止重放旧草稿；这些为自身转写修正，不是原书勘误。
- [全部历史修订链](../data/processed/tonglun_reference/reviews/revision_chain_verification_20261024_002.json)复现181条旧JSON、哈希、前后批次与当前链路；本轮追加片段与108标题修订分别精确验证，8项工程unittest通过。
- [302单元正文首轮边界验收](../data/processed/tonglun_reference/reviews/body_completion_20261024_001.json)通过；730整页全部闭合，附录32页及6张分编扉页另计。上册17、29、207、335与下册14、168均非编号正文单元。
- [论文准备记录](tonglun_reference_thesis_preparation_20261024.md)明确教材知识库与自然语料库的区别；[302行独立复核空表](../data/processed/tonglun_reference/reviews/independent_review_blank_20261024_001.json)固定来源指纹，评分字段均空，实际独立复核0。
- [阅读导出与页队列验收](../data/processed/tonglun_reference/reviews/export_verification_20261024_001.json)仍为175个ready来源快照和768页状态；附录32页已完成首轮候选，26页787行术语、6页108条书目（1条跨页），正式附录导入0，不进入默认检索。
- 本轮为同一助手原页视觉初核，ready仅表示完整边界且无已登记阻断项；不表示逐字或语义正确率100%，未做独立专家盲评或生成验收。全书转录、二轮核对、疑点证据裁定和研究版封存尚未完成。
- 未改原PDF、学生库或其他书库，未外发、调用外部OCR/收费生成API、部署、提交或推送。
- [术语候选014](../data/processed/tonglun_reference/appendix_candidates/terminology_20261024_014.json)接续13版追加链并仅修正5处自身颚/腭转录；[书目候选003](../data/processed/tonglun_reference/appendix_candidates/bibliography_20261024_003.json)保留3版追加链。[附录5项书内证据](../data/processed/tonglun_reference/reviews/appendix_intrabook_evidence_20261024_001.json)形成2组3行未应用编校建议，独立二审0。
- [附录接续说明](tonglun_reference_appendix_progress_20261024.md)提供895条阅读稿、来源JSONL和空评分表；[本轮验收](../data/processed/tonglun_reference/reviews/appendix_research_verification_20261024_001.json)通过895条来源绑定和27556处字符偏移，不是语义正确率。
- [页级引句定位](../data/processed/tonglun_reference/reviews/quote_locations_20261024_001.json)通过175个ready单元、260600字符、278跨页边界与453工程引句；127隔离单元全部拒绝，15项相关测试通过。新本地入口scripts/tonglun_quote_locator.py不改变默认RAG。

## 2026-10-24 17:27附录断点（历史）

- 17:27附录中途断点：继续用户“工作到余额用尽”的安排，新5小时窗口采样2026-10-24T09:26:50.879Z已用58%、周24%；不是货币余额。用途仍为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不表示全书正文审核完成。
- 累计273个已应用批次（上142、下131）、181条历史页修订；730整页、0局部页，768页队列38页未核。上册PDF18–27、30–206、208–334、336–385整页；下册PDF15–166、169–382整页。上册207、335及下册168分编扉页不计正文完成。
- 175个完整单元可检索（上65、下110），127个隔离，0个目录单元尚未入审核库。较21日20:30新增176整页、18个可检索单元、43个隔离单元，局部页另计。
- [139条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261024_130615.json)保留原文与原页。调型规则、语段切分、交际结构表及构词音标/词内斜体的转写限制已明确标记；转写待二审不是原书错误裁定。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261024_002.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次及全部单元重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261024_002.json)覆盖302单元，代码、标题、起页无差异。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261024_002.json)：150/150目标命中、127/127隔离目标未返回。为开发性指定词检查，不是自然问题召回率或生成准确率；21日004失败131/132与005改供明确词后的132/132报告保留，检索器未为本轮调参。
- 正文一致性备份仍为[13:06断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)，四张审核表逐表保持不变；[附录接续断点](../data/processed/tonglun_reference/appendix_checkpoint_20261024_172720.json)及latest_appendix指针固定本轮候选与校验文件。下一步对照正文和原页复核附录5项疑点，再推进正文139条二审。
- 116审核说明中‘语音学编最后两单元’为范围误述：实际是第十章第四节第2、3单元，后续还有第4单元和第十一章；116正文与目录代码不变。
- 上册108仅把107标题的全角连接号统一为冻结目录的ASCII连接号，正文、边界与待核说明不变。TL-V1-032的“噪音重复”断言已由071撤回068，仍保留嗓/噪字形待核。上册100、下册104为21日撤回未应用草稿；24日上册134→135（疑点页码和移行）、137→138（蝲蛄字形）、143→145（лям-а字形）亦在应用前撤回替代，禁止重放旧草稿；这些为自身转写修正，不是原书勘误。
- [全部历史修订链](../data/processed/tonglun_reference/reviews/revision_chain_verification_20261024_002.json)复现181条旧JSON、哈希、前后批次与当前链路；本轮追加片段与108标题修订分别精确验证，8项工程unittest通过。
- [302单元正文首轮边界验收](../data/processed/tonglun_reference/reviews/body_completion_20261024_001.json)通过；730整页全部闭合，附录32页及6张分编扉页另计。上册17、29、207、335与下册14、168均非编号正文单元。
- [论文准备记录](tonglun_reference_thesis_preparation_20261024.md)明确教材知识库与自然语料库的区别；[302行独立复核空表](../data/processed/tonglun_reference/reviews/independent_review_blank_20261024_001.json)固定来源指纹，评分字段均空，实际独立复核0。
- [阅读导出与页队列验收](../data/processed/tonglun_reference/reviews/export_verification_20261024_001.json)仍为175个ready来源快照和768页状态；附录32页已完成首轮候选，26页787行术语、6页108条书目（1条跨页），正式附录导入0，不进入默认检索。
- 本轮为同一助手原页视觉初核，ready仅表示完整边界且无已登记阻断项；不表示逐字或语义正确率100%，未做独立专家盲评或生成验收。全书转录、二轮核对、疑点证据裁定和研究版封存尚未完成。
- 未改原PDF、学生库或其他书库，未外发、调用外部OCR/收费生成API、部署、提交或推送。
- [术语候选013](../data/processed/tonglun_reference/appendix_candidates/terminology_20261024_013.json)的13版追加链、[书目候选003](../data/processed/tonglun_reference/appendix_candidates/bibliography_20261024_003.json)的3版追加链及全部来源绑定均通过；[术语3项疑点](../data/processed/tonglun_reference/reviews/appendix_issue_register_20261024_001.json)、[书目2项疑点](../data/processed/tonglun_reference/reviews/bibliography_issue_register_20261024_001.json)保留原文，独立二审0。

## 2026-10-24 13:06续审断点（历史）

- 13:06收尾断点：继续用户“工作到余额用尽”的安排。额度采样2026-10-24T05:05:19.844Z：5小时已用91%、周14%；为平台额度采样，不是货币余额。用途为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不表示全书正文审核完成。
- 累计273个已应用批次（上142、下131）、181条历史页修订；730整页、0局部页，768页队列38页未核。上册PDF18–27、30–206、208–334、336–385整页；下册PDF15–166、169–382整页。上册207、335及下册168分编扉页不计正文完成。
- 175个完整单元可检索（上65、下110），127个隔离，0个目录单元尚未入审核库。较21日20:30新增176整页、18个可检索单元、43个隔离单元，局部页另计。
- [139条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261024_130615.json)保留原文与原页。调型规则、语段切分、交际结构表及构词音标/词内斜体的转写限制已明确标记；转写待二审不是原书错误裁定。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261024_002.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次及全部单元重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261024_002.json)覆盖302单元，代码、标题、起页无差异。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261024_002.json)：150/150目标命中、127/127隔离目标未返回。为开发性指定词检查，不是自然问题召回率或生成准确率；21日004失败131/132与005改供明确词后的132/132报告保留，检索器未为本轮调参。
- 一致性备份、指纹与范围见[收尾断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)及latest指针。下一上册：145个编号正文单元首轮已齐至PDF385；附录386–387有候选，继续388–401术语、402–404书目；候选尚未正式导入。80个隔离单元待证据二审。 下一下册：157个编号正文单元首轮已齐至PDF382；附录383–384有候选，继续385–392术语、393–395书目；候选尚未正式导入。47个隔离单元待证据二审。
- 116审核说明中‘语音学编最后两单元’为范围误述：实际是第十章第四节第2、3单元，后续还有第4单元和第十一章；116正文与目录代码不变。
- 上册108仅把107标题的全角连接号统一为冻结目录的ASCII连接号，正文、边界与待核说明不变。TL-V1-032的“噪音重复”断言已由071撤回068，仍保留嗓/噪字形待核。上册100、下册104为21日撤回未应用草稿；24日上册134→135（疑点页码和移行）、137→138（蝲蛄字形）、143→145（лям-а字形）亦在应用前撤回替代，禁止重放旧草稿；这些为自身转写修正，不是原书勘误。
- [全部历史修订链](../data/processed/tonglun_reference/reviews/revision_chain_verification_20261024_002.json)复现181条旧JSON、哈希、前后批次与当前链路；本轮追加片段与108标题修订分别精确验证，8项工程unittest通过。
- [302单元正文首轮边界验收](../data/processed/tonglun_reference/reviews/body_completion_20261024_001.json)通过；730整页全部闭合，附录32页及6张分编扉页另计。上册17、29、207、335与下册14、168均非编号正文单元。
- [论文准备记录](tonglun_reference_thesis_preparation_20261024.md)明确教材知识库与自然语料库的区别；[302行独立复核空表](../data/processed/tonglun_reference/reviews/independent_review_blank_20261024_001.json)固定来源指纹，评分字段均空，实际独立复核0。
- [阅读导出与页队列验收](../data/processed/tonglun_reference/reviews/export_verification_20261024_001.json)复现175个ready来源快照和768页状态；[32页附录队列002](../data/processed/tonglun_reference/reviews/appendix_queue_20261024_002.json)已固定来源，4页100行术语仅为首轮候选（含2行原英语），001的38行保留；正式附录导入0，不进入默认检索。
- 本轮为同一助手原页视觉初核，ready仅表示完整边界且无已登记阻断项；不表示逐字或语义正确率100%，未做独立专家盲评或生成验收。全书转录、二轮核对、疑点证据裁定和研究版封存尚未完成。
- 未改原PDF、学生库或其他书库，未外发、调用外部OCR/收费生成API、部署、提交或推送。

## 2026-10-24 13:03续审断点（历史）

- 13:03中途断点：继续用户“工作到余额用尽”的安排。额度采样2026-10-24T05:03:23.853Z：5小时已用88%、周14%；为平台额度采样，不是货币余额。用途为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不表示全书正文审核完成。
- 累计273个已应用批次（上142、下131）、181条历史页修订；730整页、0局部页，768页队列38页未核。上册PDF18–27、30–206、208–334、336–385整页；下册PDF15–166、169–382整页。上册207、335及下册168分编扉页不计正文完成。
- 175个完整单元可检索（上65、下110），127个隔离，0个目录单元尚未入审核库。较21日20:30新增176整页、18个可检索单元、43个隔离单元，局部页另计。
- [139条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261024_130358.json)保留原文与原页。调型规则、语段切分、交际结构表及构词音标/词内斜体的转写限制已明确标记；转写待二审不是原书错误裁定。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261024_002.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次及全部单元重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261024_002.json)覆盖302单元，代码、标题、起页无差异。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261024_002.json)：150/150目标命中、127/127隔离目标未返回。为开发性指定词检查，不是自然问题召回率或生成准确率；21日004失败131/132与005改供明确词后的132/132报告保留，检索器未为本轮调参。
- 一致性备份、指纹与范围见[中途断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130358.json)及latest指针。下一上册：145个正文单元首轮已齐至PDF385；附录386–401、402–404未正式导入；386仅有术语候选，继续387并按疑点登记二审。 下一下册：157个正文单元首轮已齐至PDF382；附录383–392、393–395未正式导入；383仅有术语候选，继续384并按疑点登记二审。
- 116审核说明中‘语音学编最后两单元’为范围误述：实际是第十章第四节第2、3单元，后续还有第4单元和第十一章；116正文与目录代码不变。
- 上册108仅把107标题的全角连接号统一为冻结目录的ASCII连接号，正文、边界与待核说明不变。TL-V1-032的“噪音重复”断言已由071撤回068，仍保留嗓/噪字形待核。上册100、下册104为21日撤回未应用草稿；24日上册134→135（疑点页码和移行）、137→138（蝲蛄字形）、143→145（лям-а字形）亦在应用前撤回替代，禁止重放旧草稿；这些为自身转写修正，不是原书勘误。
- [全部历史修订链](../data/processed/tonglun_reference/reviews/revision_chain_verification_20261024_002.json)复现181条旧JSON、哈希、前后批次与当前链路；本轮追加片段与108标题修订分别精确验证，8项工程unittest通过。
- [302单元正文首轮边界验收](../data/processed/tonglun_reference/reviews/body_completion_20261024_001.json)通过；730整页全部闭合，附录32页及6张分编扉页另计。上册17、29、207、335与下册14、168均非编号正文单元。
- [论文准备记录](tonglun_reference_thesis_preparation_20261024.md)明确教材知识库与自然语料库的区别；[302行独立复核空表](../data/processed/tonglun_reference/reviews/independent_review_blank_20261024_001.json)固定来源指纹，评分字段均空，实际独立复核0。
- [阅读导出与页队列验收](../data/processed/tonglun_reference/reviews/export_verification_20261024_001.json)复现175个ready来源快照和768页状态；[32页附录队列](../data/processed/tonglun_reference/reviews/appendix_queue_20261024_001.json)已固定来源，2页38行术语仅为首轮候选，正式附录导入0，不进入默认检索。
- 本轮为同一助手原页视觉初核，ready仅表示完整边界且无已登记阻断项；不表示逐字或语义正确率100%，未做独立专家盲评或生成验收。全书转录、二轮核对、疑点证据裁定和研究版封存尚未完成。
- 未改原PDF、学生库或其他书库，未外发、调用外部OCR/收费生成API、部署、提交或推送。

## 2026-10-24 12:42续审断点（历史）

- 12:42中途断点：继续用户“工作到余额用尽”的安排。额度采样2026-10-24T04:41:32.837Z：5小时已用63%、周10%；为平台额度采样，不是货币余额。用途为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不表示全书正文审核完成。
- 累计267个已应用批次（上142、下125）、178条历史页修订；716整页、0局部页，768页队列52页未核。上册PDF18–27、30–206、208–334、336–385整页；下册PDF15–166、169–368整页。上册207、335及下册168分编扉页不计正文完成。
- 173个完整单元可检索（上65、下108），123个隔离，6个目录单元尚未入审核库。较21日20:30新增162整页、16个可检索单元、39个隔离单元，局部页另计。
- [135条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261024_124221.json)保留原文与原页。调型规则、语段切分、交际结构表及构词音标/词内斜体的转写限制已明确标记；转写待二审不是原书错误裁定。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261024_001.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次及全部单元重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261024_001.json)覆盖296单元，代码、标题、起页无差异。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261024_001.json)：148/148目标命中、123/123隔离目标未返回。为开发性指定词检查，不是自然问题召回率或生成准确率；21日004失败131/132与005改供明确词后的132/132报告保留，检索器未为本轮调参。
- 一致性备份、指纹与范围见[中途断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_124221.json)及latest指针。下一上册：正文145个目录单元已全部视觉初核至PDF385；386–401术语表、402–404参考文献尚未审核；现有80个隔离单元继续二审，不称全册完成。 下一下册：PDF369第十四章第三节第4单元带接续从属句的主从复合句；369已看图未转录，370起未看。
- 116审核说明中‘语音学编最后两单元’为范围误述：实际是第十章第四节第2、3单元，后续还有第4单元和第十一章；116正文与目录代码不变。
- 上册108仅把107标题的全角连接号统一为冻结目录的ASCII连接号，正文、边界与待核说明不变。TL-V1-032的“噪音重复”断言已由071撤回068，仍保留嗓/噪字形待核。上册100、下册104为21日撤回未应用草稿；24日上册134→135（疑点页码和移行）、137→138（蝲蛄字形）、143→145（лям-а字形）亦在应用前撤回替代，禁止重放旧草稿；这些为自身转写修正，不是原书勘误。
- [全部历史修订链](../data/processed/tonglun_reference/reviews/revision_chain_verification_20261024_001.json)复现178条旧JSON、哈希、前后批次与当前链路；本轮追加片段与108标题修订分别精确验证，8项工程unittest通过。
- 本轮为同一助手原页视觉初核，ready仅表示完整边界且无已登记阻断项；不表示逐字或语义正确率100%，未做独立专家盲评或生成验收。全书转录、二轮核对、疑点证据裁定和研究版封存尚未完成。
- 未改原PDF、学生库或其他书库，未外发、调用外部OCR/收费生成API、部署、提交或推送。

## 2026-10-24 11:31续审断点（历史）

- 11:31中途断点：继续用户“工作到余额用尽”的安排。额度采样2026-10-24T03:31:09.623Z：5小时已用1%、周0%；为平台额度采样，不是货币余额。用途为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不表示全书正文审核完成。
- 累计251个已应用批次（上130、下121）、168条历史页修订；668整页、1局部页，768页队列99页未核。上册PDF18–27、30–206、208–334、336–350整页；下册PDF15–166、169–355整页，PDF356局部。上册207、335及下册168分编扉页不计正文完成。
- 169个完整单元可检索（上61、下108），115个隔离，18个目录单元尚未入审核库。较21日20:30新增114整页、12个可检索单元、31个隔离单元，局部页另计。
- [125条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261024_113155.json)保留原文与原页。本轮调型规则、语段切分、交际结构表的斜体/上标/着重点转写明确标记；转写待二审不是原书错误裁定。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261023_002.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次及全部单元重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261023_002.json)覆盖284单元，代码、标题、起页无差异。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261023_002.json)：144/144目标命中、115/115隔离目标未返回。为开发性指定词检查，不是自然问题召回率或生成准确率；21日004失败131/132与005改供明确词后的132/132报告保留，检索器未为本轮调参。
- 一致性备份、指纹与范围见[中途断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_113155.json)及latest指针。下一上册：PDF351第四编第二章下一单元；尚未看图。PDF335构词学扉页已看，另计。 下一下册：PDF356余部第十四章第三节第3单元带疏状从属句的主从复合句；356已看图未转录，357起未看。
- 116审核说明中‘语音学编最后两单元’为范围误述：实际是第十章第四节第2、3单元，后续还有第4单元和第十一章；116正文与目录代码不变。
- 上册108仅把107标题的全角连接号统一为冻结目录的ASCII连接号，正文、边界与待核说明不变。TL-V1-032的“噪音重复”断言已由071撤回068，仍保留嗓/噪字形待核。上册100、下册104均为21日撤回未应用草稿，禁止重放。
- [全部历史修订链](../data/processed/tonglun_reference/reviews/revision_chain_verification_20261023_002.json)复现168条旧JSON、哈希、前后批次与当前链路；本轮追加片段与108标题修订分别精确验证，8项工程unittest通过。
- 本轮为同一助手原页视觉初核，ready仅表示完整边界且无已登记阻断项；不表示逐字或语义正确率100%，未做独立专家盲评或生成验收。全书转录、二轮核对、疑点证据裁定和研究版封存尚未完成。
- 未改原PDF、学生库或其他书库，未外发、调用外部OCR/收费生成API、部署、提交或推送。

## 2026-10-23 21:43续审断点（历史）

- 21:43中途断点：继续用户“工作到余额用尽”的安排。可读取的历史采样2026-10-23T13:42:24.119Z为5小时24%、周32%；采样已过期，实时余额未知，不据此声称用尽或窗口重置。用途为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不表示全书正文审核完成。
- 累计234个已应用批次（上120、下114）、157条历史页修订；613整页、1局部页，768页队列154页未核。上册PDF18–27、30–206、208–318整页，PDF319局部；下册PDF15–166、169–331整页。上册207、下册168分编扉页不计正文完成。
- 162个完整单元可检索（上60、下102），103个隔离，37个目录单元尚未入审核库。较21日20:30新增59整页、5个可检索单元、19个隔离单元，局部页另计。
- [113条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261023_214311.json)保留原文与原页。本轮调型规则、语段切分、交际结构表的斜体/上标/着重点转写明确标记；转写待二审不是原书错误裁定。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261023_001.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次及全部单元重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261023_001.json)覆盖265单元，代码、标题、起页无差异。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261023_001.json)：137/137目标命中、103/103隔离目标未返回。为开发性指定词检查，不是自然问题召回率或生成准确率；21日004失败131/132与005改供明确词后的132/132报告保留，检索器未为本轮调参。
- 一致性备份、指纹与范围见[中途断点](../data/processed/tonglun_reference/continuation_checkpoint_20261023_214311.json)及latest指针。下一上册：PDF319余部第十一章第二节第1单元俄语元音方面的中国口音；319已看图未转录，320起未看。 下一下册：PDF332第十四章第一节第1单元复合句的概念；332已看图未转录。
- 116审核说明中‘语音学编最后两单元’为范围误述：实际是第十章第四节第2、3单元，后续还有第4单元和第十一章；116正文与目录代码不变。
- 上册108仅把107标题的全角连接号统一为冻结目录的ASCII连接号，正文、边界与待核说明不变。TL-V1-032的“噪音重复”断言已由071撤回068，仍保留嗓/噪字形待核。上册100、下册104均为21日撤回未应用草稿，禁止重放。
- [全部历史修订链](../data/processed/tonglun_reference/reviews/revision_chain_verification_20261023_001.json)复现157条旧JSON、哈希、前后批次与当前链路；本轮追加片段与108标题修订分别精确验证，8项工程unittest通过。
- 本轮为同一助手原页视觉初核，ready仅表示完整边界且无已登记阻断项；不表示逐字或语义正确率100%，未做独立专家盲评或生成验收。全书转录、二轮核对、疑点证据裁定和研究版封存尚未完成。
- 未改原PDF、学生库或其他书库，未外发、调用外部OCR/收费生成API、部署、提交或推送。

## 2026-10-22 11:20续审断点（历史）

- 11:20中途断点：继续用户“工作到余额将近”的安排。最新采样2026-10-22T03:16:58.178Z：5小时已用45%、周63%；本窗口已重置，不沿用21日停止线。用途为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不表示全书正文审核完成。
- 累计225个已应用批次（上113、下112）、150条历史页修订；586整页、2局部页，768页队列180页未核。上册PDF18–27、30–206、208–304整页，PDF305局部；下册PDF15–166、169–318整页，PDF319局部。上册207、下册168分编扉页不计正文完成。
- 160个完整单元可检索（上58、下102），93个隔离，49个目录单元尚未入审核库。较21日20:30新增32整页、3个可检索单元、9个隔离单元，局部页另计。
- [103条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261022_112030.json)保留原文与原页。本轮调型规则、语段切分、交际结构表的斜体/上标/着重点转写明确标记；转写待二审不是原书错误裁定。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261022_001.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次及全部单元重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261022_001.json)覆盖253单元，代码、标题、起页无差异。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261022_001.json)：135/135目标命中、93/93隔离目标未返回。为开发性指定词检查，不是自然问题召回率或生成准确率；21日004失败131/132与005改供明确词后的132/132报告保留，检索器未为本轮调参。
- 一致性备份、指纹与范围见[中途断点](../data/processed/tonglun_reference/continuation_checkpoint_20261022_112030.json)及latest指针。下一上册：PDF305余部第十章第四节第1单元调型的辨义功能；305–308已看图未转录。 下一下册：PDF319余部第十三章第3单元命题意义和情态意义；319–323已看图未转录。
- 上册108仅把107标题的全角连接号统一为冻结目录的ASCII连接号，正文、边界与待核说明不变。TL-V1-032的“噪音重复”断言已由071撤回068，仍保留嗓/噪字形待核。上册100、下册104均为21日撤回未应用草稿，禁止重放。
- 本次为中途检查点，继续转录；最终历史修订链重放、工程回归和交接验收将在收尾完成，旧验收不代替新增范围。
- 本轮为同一助手原页视觉初核，ready仅表示完整边界且无已登记阻断项；不表示逐字或语义正确率100%，未做独立专家盲评或生成验收。全书转录、二轮核对、疑点证据裁定和研究版封存尚未完成。
- 未改原PDF、学生库或其他书库，未外发、调用外部OCR/收费生成API、部署、提交或推送。

## 2026-10-21 20:30续审断点（历史）

- 20:30收尾断点：继续用户“工作到余额将近”的安排。本轮窗口已重置，最新采样2026-10-21T12:30:08.836Z为5小时已用87%、周56%；以本轮新采样为准，不沿用上一窗口停止点。用途仍为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不代表全书正文审核完成。
- 当前累计211批（上105、下106），138条历史页修订；554整页、1局部页，768页队列213页未核。上册PDF18–27、30–206、208–292整页；下册PDF15–166、169–298整页，PDF299局部。上册207、下册168分编扉页已看图未入正文审核层，不计完成。
- 157个完整单元可检索（上58、下99），84个隔离，61目录单元尚未入审核库。较上一收尾新增74整页、16个可检索单元、18个隔离单元；局部页另计。
- [94条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261021_203038.json)保留在隔离层。本轮新增弱化元音、软化辅音组合、外来词与父称音标，以及下册署名待核等疑点；部分是转写不确定性，不可全部称为原书错误。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261021_004.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次和全部单元内存重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261021_004.json)覆盖241单元，无代码、标题或起页差异。工程检查不代表逐字或语义正确率。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261021_005.json)：132/132返回目标，84/84隔离目标未返回；为人工指定词开发性检查，不是自然提问召回率或生成准确率。旧失败及修正报告保留。
- 双册SQLite backup一致性备份与指纹见[收尾断点](../data/processed/tonglun_reference/continuation_checkpoint_20261021_203038.json)及latest指针。下一上册：PDF293第十章第三节第1单元调型-1使用规则；293已看图但未转录，294起尚未核图。 下一下册：PDF299余部第十二章第2单元句子实际切分的表达手段；299余部和300已看图未转录，301起继续核图。
- [全部历史修订链](../data/processed/tonglun_reference/reviews/revision_chain_verification_20261021_002.json)复现138条旧JSON、前后批次、哈希及当前链路。8项unittest工程测试通过；本轮局部页追加逐条核旧片段不变；094另据原图修正两页自身转写中的字母与重音，旧分类表注与字形撤回证据沿用原记录，不能冒称全部历史修订逐字不变。
- TL-V1-032不再断言原印重复“噪音”：071撤回068的过度确定读法，正文明确标出嗓/噪字形待核，仍隔离。音标与连读弧Unicode候选、图表层级转写和斜体/句调标记的表示方法见各批review_note；不宣称逐字原排版等同或全书二审通过。
- [上一断点保留核验](../data/processed/tonglun_reference/reviews/evening_delta_verification_20261021_001.json)：原141个ready单元与480页审核记录逐行不变。上册100、下册104为预览后撤回未应用草稿，替代批次和禁止重放理由另有记录；批号不等于已应用数量。
- 本晚关键词004初测131/132，误用不在目标段中的“语调手段”未得证据；005改供目标段明确短语后132/132，未调检索器，旧失败[004报告](../data/processed/tonglun_reference/rag/keyword_smoke_20261021_004.json)保留。不能把修订指定词检查称为自然问句改进。
- 新增正文均为同一助手原页视觉初核；语调斜体、下划线、曲线与着重点的文字表示带显式说明并隔离待二审，原页仍是排版证据。没有独立专家语义盲评或生成回答验收。
- 全书转录、二轮逐字复核、疑点外部证据裁定、自然问题/生成验收及研究版封存尚未完成。未改原PDF、学生库或语法研究包，未外发、调用外部OCR/收费生成API、部署、提交或推送。

## 2026-10-21 19:43续审断点（历史）

- 19:43中途断点：继续用户“工作到余额将近”的安排。本轮窗口已重置，最新采样2026-10-21T11:43:38.956Z为5小时已用43%、周49%；以本轮新采样为准，不沿用上一窗口停止点。用途仍为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不代表全书正文审核完成。
- 当前累计195批（上98、下97），128条历史页修订；514整页、1局部页，768页队列253页未核。上册PDF18–27、30–206、208–275整页；下册PDF15–166、169–275整页，PDF276局部。上册207、下册168分编扉页已看图未入正文审核层，不计完成。
- 149个完整单元可检索（上57、下92），73个隔离，80目录单元尚未入审核库。较上一收尾新增34整页、8个可检索单元、7个隔离单元；局部页另计。
- [83条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261021_194354.json)保留在隔离层。本轮新增弱化元音、软化辅音组合、外来词与父称音标，以及下册署名待核等疑点；部分是转写不确定性，不可全部称为原书错误。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261021_003.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次和全部单元内存重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261021_003.json)覆盖222单元，无代码、标题或起页差异。工程检查不代表逐字或语义正确率。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261021_003.json)：124/124返回目标，73/73隔离目标未返回；为人工指定词开发性检查，不是自然提问召回率或生成准确率。旧失败及修正报告保留。
- 双册SQLite backup一致性备份与指纹见[中途断点](../data/processed/tonglun_reference/continuation_checkpoint_20261021_194354.json)及latest指针。下一上册：PDF276第九章第1单元表音法；276已看图，未转录。 下一下册：PDF276第九章第3单元独立同位语；276后段未入库，277起继续核图。
- 本次为中途备份，继续转录；历史修订链全范围复现和最终交接验收将在收尾再跑，上一窗口116条修订链验收不代替当前范围。
- 全书转录、二轮逐字复核、疑点外部证据裁定、自然问题/生成验收及研究版封存尚未完成。未改原PDF、学生库或语法研究包，未外发、调用外部OCR/收费生成API、部署、提交或推送。

## 2026-10-21 13:13续审断点（历史）

- 13:13收尾断点：继续用户“工作到余额将近”的安排。本轮窗口已重置，最新采样2026-10-21T05:12:17.882Z为5小时已用85%、周41%；以本轮新采样为准，不沿用上一窗口停止点。用途仍为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不代表全书正文审核完成。
- 当前累计179批（上89、下90），116条历史页修订；480整页、0局部页，768页队列288页未核。上册PDF18–27、30–206、208–257整页；下册PDF15–166、169–259整页。上册207、下册168分编扉页已看图未入正文审核层，不计完成。
- 141个完整单元可检索（上55、下86），66个隔离，95目录单元尚未入审核库。较上一收尾新增59整页、19个可检索单元、12个隔离单元；局部页另计。
- [76条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261021_131303.json)保留在隔离层。本轮新增音标连弧、长音与元音附标、语音位置表对应，以及接厉、职业词俄中对应等疑点；部分是转写不确定性，不可全部称为原书错误。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261021_002.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次和全部单元内存重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261021_002.json)覆盖207单元，无代码、标题或起页差异。工程检查不代表逐字或语义正确率。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261021_002.json)：116/116返回目标，66/66隔离目标未返回；为人工指定词开发性检查，不是自然提问召回率或生成准确率。旧失败及修正报告保留。
- 双册SQLite backup一致性备份与指纹见[收尾断点](../data/processed/tonglun_reference/continuation_checkpoint_20261021_131303.json)及latest指针。下一上册：PDF258第八章第一节第1单元读音法的概念和意义；258已看图但未转录，不能计完成。 下一下册：PDF260第七章第6单元称名句；260已看图但未转录，不能计完成。
- [全部历史修订链](../data/processed/tonglun_reference/reviews/revision_chain_verification_20261021_001.json)复现116条旧JSON、前后批次、哈希及当前链路。8项unittest工程测试通过；本轮局部页追加逐条核旧片段不变；旧分类表注与字形撤回证据沿用原记录，不能冒称全部历史修订逐字不变。
- TL-V1-032不再断言原印重复“噪音”：071撤回068的过度确定读法，正文明确标出嗓/噪字形待核，仍隔离。音标与连读弧Unicode候选、图表层级转写和斜体/句调标记的表示方法见各批review_note；不宣称逐字原排版等同或全书二审通过。
- 全书转录、二轮逐字复核、疑点外部证据裁定、自然问题/生成验收及研究版封存尚未完成。未改原PDF、学生库或语法研究包，未外发、调用外部OCR/收费生成API、部署、提交或推送。

## 2026-10-21 12:48续审断点（历史）

- 12:48中途断点：继续用户“工作到余额将近”的安排。本轮窗口已重置，最新采样2026-10-21T04:47:33.363Z为5小时已用37%、周34%；以本轮新采样为准，不沿用上一窗口停止点。用途仍为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不代表全书正文审核完成。
- 当前累计162批（上79、下83），103条历史页修订；446整页、1局部页，768页队列321页未核。上册PDF18–27、30–206、208–241整页，PDF242局部；下册PDF15–166、169–241整页。上册207、下册168分编扉页已看图未入正文审核层，不计完成。
- 129个完整单元可检索（上48、下81），61个隔离，112目录单元尚未入审核库。较上一收尾新增25整页、7个可检索单元、7个隔离单元；局部页另计。
- [71条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261021_124800.json)保留在隔离层。本轮新增音标连弧、长音与元音附标、语音位置表对应，以及接厉、职业词俄中对应等疑点；部分是转写不确定性，不可全部称为原书错误。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261021_001.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次和全部单元内存重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261021_001.json)覆盖190单元，无代码、标题或起页差异。工程检查不代表逐字或语义正确率。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261021_001.json)：104/104返回目标，61/61隔离目标未返回；为人工指定词开发性检查，不是自然提问召回率或生成准确率。旧失败及修正报告保留。
- 双册SQLite backup一致性备份与指纹见[中途断点](../data/processed/tonglun_reference/continuation_checkpoint_20261021_124800.json)及latest指针。下一上册：PDF242第六章第3单元强音位和弱音位；同页前段已入库，后段仅看图尚未转录。 下一下册：PDF242第六章第7单元状语；已看图尚未转录，不能计完成。
- 本次为中途备份，继续转录；历史修订链全范围复现和最终交接验收将在收尾再跑，上一窗口95条修订链验收不代替当前范围。
- 全书转录、二轮逐字复核、疑点外部证据裁定、自然问题/生成验收及研究版封存尚未完成。未改原PDF、学生库或语法研究包，未外发、调用外部OCR/收费生成API、部署、提交或推送。

## 2026-10-20 22:11续审断点（历史）

- 22:11收尾断点：继续用户“工作到余额将近”的安排。本轮窗口已重置，最新采样2026-10-20T14:10:35.287Z为5小时已用84%、周27%；不沿用19:11的84%停止点。用途仍为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不代表全书正文审核完成。
- 当前累计148批（上71、下77），95条历史页修订；421整页、0局部页，768页队列347页未核。上册PDF18–27、30–206、208–228整页；下册PDF15–166、169–229整页。上册207、下册168分编扉页已看图未入正文审核层，不计完成。
- 122个完整单元可检索（上45、下77），54个隔离，126目录单元尚未入审核库。较19:11新增55整页、19个可检索单元、7个隔离单元；局部页另计。
- [64条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261020_221149.json)保留在隔离层。新增包括音标组合与弧线转写待核、ц分类表横向排位、否定句/否定词用词、俄中颜色词对应；前两类含转写或排版不确定性，不可把全部记录称为已证实的原书错误。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261020_003.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次和全部单元内存重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261020_004.json)覆盖176单元，无代码、标题或起页差异。工程检查不代表逐字或语义正确率。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261020_004.json)：97/97返回目标，54/54隔离目标未返回；为人工指定词开发性检查，不是自然提问召回率或生成准确率。旧失败及修正报告保留。
- 双册SQLite backup一致性备份与指纹见[收尾断点](../data/processed/tonglun_reference/continuation_checkpoint_20261020_221149.json)及latest指针。下一上册：PDF229第四章第一节第4单元塞通音和颤音；229–230虽已看图，尚未逐页转录，不能计作完成。 下一下册：PDF230第六章句子的次要成分第1单元；已看图但未转录，不能计作完成。
- [全部历史修订链](../data/processed/tonglun_reference/reviews/revision_chain_verification_20261020_002.json)复现95条旧JSON、前后批次、哈希及当前链路。8项unittest工程测试通过；分类表补充证据与空疑点默认字段分别说明，不能冒称全部修订逐字不变。
- TL-V1-032不再断言原印重复“噪音”：071撤回068的过度确定读法，正文明确标出嗓/噪字形待核，仍隔离。音标与连读弧Unicode候选、图表层级转写和斜体/句调标记的表示方法见各批review_note；不宣称逐字原排版等同或全书二审通过。
- 全书转录、二轮逐字复核、疑点外部证据裁定、自然问题/生成验收及研究版封存尚未完成。未改原PDF、学生库或语法研究包，未外发、调用外部OCR/收费生成API、部署、提交或推送。

## 2026-10-20 21:52续审断点（历史）

- 21:52中途断点：继续用户“工作到余额将近”的安排。本轮窗口已重置，最新采样2026-10-20T13:51:19.189Z为5小时已用51%、周22%；不沿用19:11的84%停止点。用途仍为可溯源检索/RAG研究。
- 双册801页均已提取，799页本地OCR、2页直接提取，原始层仍全部unreviewed；18页目录核图得到407层级条目、6编、45章、302编号单元，不代表全书正文审核完成。
- 当前累计141批（上67、下74），90条历史页修订；407整页、1局部页，768页队列360页未核。上册PDF18–27、30–206、208–225整页；下册PDF15–166、169–218整页，PDF219局部。上册207、下册168分编扉页已看图未入正文审核层，不计完成。
- 119个完整单元可检索（上43、下76），52个隔离，131目录单元尚未入审核库。较19:11新增41整页、16个可检索单元、5个隔离单元；局部页另计。
- [62条待核记录](../data/processed/tonglun_reference/reviews/issue_register_20261020_215235.json)保留在隔离层。新增包括音标组合与弧线转写待核、ц分类表横向排位、否定句/否定词用词、俄中颜色词对应；前两类含转写或排版不确定性，不可把全部记录称为已证实的原书错误。
- [本范围全量审计](../data/processed/tonglun_reference/continuation_verification_20261020_002.json)通过801条来源/文本/图像指纹、SQLite/JSONL、不可变批次和全部单元内存重建。[目录对齐](../data/processed/tonglun_reference/reviews/catalog_alignment_20261020_003.json)覆盖171单元，无代码、标题或起页差异。工程检查不代表逐字或语义正确率。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261020_003.json)：94/94返回目标，52/52隔离目标未返回；为人工指定词开发性检查，不是自然提问召回率或生成准确率。旧失败及修正报告保留。
- 双册SQLite backup一致性备份与指纹见[中途断点](../data/processed/tonglun_reference/continuation_checkpoint_20261020_215235.json)及latest指针。下一上册：PDF226第四章音素发音描述，未看图未转录。 下一下册：PDF219第2单元谓语及其表达手段；须校验旧页哈希并完整保留前单元片段。
- 本次为中途备份，继续转录；历史修订链全范围复现和最终交接验收将在收尾再跑，19:11的76条修订链验收不代替当前范围。
- 全书转录、二轮逐字复核、疑点外部证据裁定、自然问题/生成验收及研究版封存尚未完成。未改原PDF、学生库或语法研究包，未外发、调用外部OCR/收费生成API、部署、提交或推送。

## 2026-10-20 19:11续审断点（历史）

- 19:11收尾断点：按用户“工作到余额将近”续审。最新采样2026-10-20T11:10:58.713Z为5小时已用84%、周13%。用途为可溯源检索/RAG研究；审批中断和等待空档不计净工时。
- 全801页提取完整，799页本地Tesseract、2页数字化附页直接提取；原始层仍全部unreviewed。18页目录已核图，407层级条目、6编、45章、302编号单元；不代表正文全量审核。
- 累计118批（上53、下65）、76条历史页修订（上36、下40）。上册PDF18–27、30–206共187整页；下册PDF15–166、169–195共179整页。合计366整页、0局部页，768页审核队列402页未核。上册207、下册168分编扉页已看图但未入正文审核层，不计完成页。
- 当前103 ready（上34、下69）、47 unresolved（上22、下25）、0 incomplete；152目录单元尚未入审核库。较昨日20:01增加51整页、6可检索单元、9隔离单元；本轮21个新批次、15条页修订。
- 当前57条正式待核疑点涉及47个隔离单元，原文保留；清单[57条疑点登记](../data/processed/tonglun_reference/reviews/issue_register_20261020_191123.json)。本轮新增原印拼写、词典编者署名、术语与例句译文不一致等9条；仅核原图，未完成外部证据裁定。
- [全量审计](../data/processed/tonglun_reference/continuation_verification_20261020_001.json)通过801条来源/文本/图像指纹、SQLite/JSONL一致性、118批不可变证据、366页审核记录及全部单元重建。8项unittest工程测试通过；pytest未安装，未安装新依赖。
- [目录对照](../data/processed/tonglun_reference/reviews/catalog_alignment_20261020_002.json)：150个已转录单元代码、层级标题和起页全部一致。首次检查发现052新单元代码前缀及标题录入错误，053以5页可追溯修订纠正；原批次保留，正文及疑点不变。
- [历史修订链](../data/processed/tonglun_reference/reviews/revision_chain_verification_20261020_001.json)复现全部76条。新增10次局部页追加中9次旧片段完全一致，1次只补unresolved空数组；另5次为目录元数据更正。不能称15次均为正文追加或逐字不变。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261020_002.json)78项均返回目标，47隔离目标均未返回；新增6项覆盖本轮全部新增ready单元。首次77/78报告保留，1项测试词补齐标题“表示的”后另跑，未改检索器。跨册手写引句、伪造/错卷拒绝、无关题及整单元预算验证通过；不是自然问题召回率或生成准确率。
- [5页定向二次核图](../data/processed/tonglun_reference/reviews/targeted_visual_recheck_20261020_001.json)覆盖上册202–203、下册193–195中的6个指定点，含2处跨页接合；未新增修正。这里只核所列词句与接合，不代表整5页逐字二轮审核或全量语义验收。
- 双册SQLite backup一致性备份、指纹及完整范围见[收尾断点](../data/processed/tonglun_reference/continuation_checkpoint_20261020_191123.json)和latest指针，旧断点保留。下一上册PDF208语音学第一章；下册PDF196第三章“句子概述”。下册196已看图但未逐页转录，不计完成。
- 全书转录、第二轮复核、疑点定向裁定、自然提问/生成验收及研究版封存尚未完成。未改原PDF、学生库或原语法研究包，未调用外部OCR/收费生成API、提交、推送、上传或部署。流程与历史见[双册工作流](tonglun_reference_workflow.md)。

## 2026-10-19 20:01续审断点（历史）

- 20:01收尾断点：按用户“工作到余额将近”续审。最新采样2026-10-19T12:00:58.700Z为5小时已用87%、周56%；停止新增正文后完成审计、备份和交接。工具审批超时或中断空档不计净工时。用途仍为可溯源检索/RAG研究。
- 全801页提取完整，799页本地Tesseract、2页数字化附页直接提取；原始层全部保留unreviewed。18页目录已核图，407层级条目、6编、45章、302编号单元；不等于全书正文审核完成。
- 累计97批（上42、下55）、61条历史页修订（上27、下34）。上册PDF18–27、30–177共158整页；下册PDF15–166、169–173共157整页，PDF174局部。合计315整页正文、1局部页，768页队列452页未核；PDF168分编扉页已看图但未入正文审核层，不计整页完成。
- 当前97 ready（上32、下65）、38 unresolved（上17、下21）、0 incomplete；167目录单元尚未入审核库。本次接续比16:02断点增加54整页、17可检索单元和9隔离单元；24个新批次、14条追加页修订。
- 当前48条正式待核疑点涉及38单元，原文保留隔离；清单[48条疑点登记](../data/processed/tonglun_reference/reviews/issue_register_20261019_200155.json)。新增术语译名、原印拼写、前置词配格、例句与译文或说明不一致；不是专家错误裁定。TL-V2-017及本轮光年под误读均已放大纠正或撤回，不计当前48条。
- 8项工程测试通过；[本轮全量审计](../data/processed/tonglun_reference/continuation_verification_20261019_003.json)通过801条来源/文本/图像指纹、SQLite/JSONL一致性、97批不可变证据、316页审核记录及全部单元内存重建。135个已转录单元代码、层级标题和起页与冻结目录一致，见reviews/catalog_alignment_20261019_002.json。
- [历史修订链复现](../data/processed/tonglun_reference/reviews/revision_chain_verification_20261019_003.json)逐条核验全部61条旧JSON、前后批次、哈希和当前页链路；本轮14次局部页追加均完整保留旧片段。不把历史工程检查当作语义正确率。
- [指定关键词检查](../data/processed/tonglun_reference/rag/keyword_smoke_20261019_003.json)：72项均返回目标，当前38隔离目标全部未返回；其中新增17项覆盖本轮全部新增ready单元。跨册手写引句、错卷/伪造拒绝、无关题及整单元预算验证通过。这些不是自然问题召回率、独立留出题或生成准确率。
- 双册SQLite backup一致性备份、指纹及完整范围见[收尾断点](../data/processed/tonglun_reference/continuation_checkpoint_20261019_200155.json)和latest指针；16:02及更早历史保留。下一上册PDF178“俄汉熟语概念对比”（178–182虽已看图但尚未逐页转录，不计完成）；下册PDF174“句法联系的表达手段”，须匹配旧页哈希并保留已有片段后追加。
- 全书清洗、第二轮复核、疑点定向裁定、自然提问/生成验收及研究版封存未完成。未改原PDF、学生库或原语法研究包，未调用外部OCR/收费生成API、提交、推送、上传或部署。流程与历史见[双册工作流](tonglun_reference_workflow.md)。

## 2026-10-19 16:02续审断点（历史）

- 按用户“按照安排，工作到余额将近”续审；停止线采样2026-10-19T08:00:15.217Z为5小时已用85%、周42%。停止新增正文后只完成导出、审计、备份和文档。工具权限审查中断不计净工时。
- 累计73批（上册33、下册40）、47条历史页修订（上23、下24）。上册PDF18–27、30–151共132整页；下册PDF15–143共129整页，PDF144局部。合计261整页正文、1局部页，768页队列506页未核；18页目录另计。
- 当前80 ready（上24、下56）、29 unresolved（上14、下15）、0 incomplete；302目录单元中193个尚未入审核库。推进了词汇系统关系、词层起源及下册副词、代词、动词体/式/时/人称、形动词，不代表这些章节所有单元均可检索。
- 当前38条正式待核疑点见`reviews/issue_register_20261019_160209.json`，涉及29单元，原文保留隔离。另有已撤回TL-V2-017：PDF130放大确认Начальник，初次缩图误读Начальнику；下册034批纠正转录并撤回误报，032历史保留。上册027批草稿修改命令失败后误执行导入，028批已用旧页哈希修正-йj-转录并登记两项原印疑点，未改写027历史。
- 上册026批调整两处脚注位置，保持原文字词并防止脚注打断跨页句。图表转写明确标注线性化，不宣称逐符号外交式转录。历史借词出处、作者署名、军衔等未全面进行书外考据；疑点候选不是专家裁定。
- 8项双册工程测试通过。`continuation_verification_20261019_002.json`核对801条来源/文本/图像指纹、SQLite/JSONL一致性、73批不可变证据、262页审核记录和所有单元内存重建；当前2条跨册手写引句及伪造/错卷/无关题/整单元预算门槛通过。演示在`rag/continuation_verification_20261019_002/`。
- 新增独立目录对照`reviews/catalog_alignment_20261019_001.json`：109个已转录单元的卷别代码、完整层级标题和起页均与冻结目录一致；未审核193单元的正文边界仍未核。
- `rag/keyword_smoke_20261019_002.json`：55项显式关键词均返回目标，当前29隔离目标全部未返回，未调整检索器。001运行的55正例通过，但因读取旧隔离导出只覆盖15旧负例；002改为直接读取当前SQLite，001保留历史。这些是开发者按已读内容制定的检查，不能作为自然问题召回率、盲评或生成准确率。
- 双册SQLite backup一致性备份、完整页范围和指纹见`continuation_checkpoint_20261019_160209.json`及latest指针，备份文件后缀同为`20261019_160209.sqlite`。12:22中途审计`continuation_verification_20261019_001.json`的67 ready、175整页为历史，不再作为当前状态。
- 下一上册PDF152，第二节“积极词和消极词”第1单元；下册PDF144，第八节“副动词”第1单元。下册该页已含形动词构成片段，必须核验最新旧页哈希后追加。全书清洗、第二轮复核、疑点定向裁定、自然提问与生成实验、研究版封存仍未完成。

## 2026-10-18 17:57续审断点（历史）

- 本轮从上册PDF43、下册PDF29继续，新增18个已应用批次；累计28批、15条旧页修订，原有片段均按哈希保留后追加。原PDF、原始OCR及学生库不改写。
- 上册PDF18–27、30–79共60页整页，PDF80局部；下册PDF15–68共54页整页，PDF69局部。合计114页整页正文、2页局部；768页队列另有652页未核。18页目录独立计数。
- 当前42个ready（上16、下26）、7个unresolved、0 incomplete；302目录单元中253个尚未入审核库。绪论、词汇学引论、词汇意义层面和类型、多义词结构、名词、形容词及数词部分已推进，不意味着相应章节所有内容均可检索。
- 9条正式疑点涉及7个单元：上册TL-V1-001至004，下册TL-V2-001至005；全量登记在`reviews/issue_register_20261018_175736.json`，原文在审核库隔离层。包含植物词译名、原型/例句编号、дуло释义、重音格标、词尾表、词素截音和性数表头等疑点，未作专家错误裁定。音位竖线、重音、跨页表及图连接边均按原图保存。
- 8项双册工程测试通过。报告`continuation_verification_20261018_002.json`核对801条来源/图像/文本指纹、28批不可变证据、116页审核记录和全部单元状态；新真实跨册手写引用示例位于`rag/continuation_verification_20261018_002/`，错卷、伪造引文、无关题及整节预算检查通过。
- `rag/keyword_smoke_20261018_002.json`包含25条指定关键词检查，25个目标返回；7个隔离目标均未返回。问题与关键词由已读材料制定，未调检索器，不是独立留出题、自动自然问题检索或生成实验。
- 接近额度停止线后停止新增页，断点采样2026-10-18T09:56:31.728Z为5小时已用85%、周已用28%。两册SQLite backup一致性备份及指纹见`continuation_checkpoint_20261018_175736.json`；`latest_continuation_checkpoint.json`指向本次。先前断点保留历史，不将中断空档计为净工时。
- 下一步：上册PDF80“2. 同音词产生的原因”，下册PDF69“7. 分数数词”，均是已有局部页，必须校验旧页哈希并保留原片段后追加。全书清洗、第二轮复核、疑点定向裁定、自然提问验收及研究版封存仍未完成。

## 2026-10-18 12:08续审断点（历史）

- 用户授权连续工作至余额将近。停止线采样为2026-10-18T04:07:44.748Z，5小时已用86%、周已用13%；达到约85%–90%后停止新增核图，完成备份与断点保存。
- 18页目录逐行核图完成：407条层级记录，6编、45章、49个节标题、302个编号知识单元（上册145、下册157）。目录转写TSV及原图/文本指纹在两册`reviews/toc_*20261018.*`；`toc_catalog.json`含层级和候选起页。目录审核不等于全部正文标题或首尾已核。
- 上册术语表起点已由初始粗定位的印刷380页纠正为目录明确列出的370页，即PDF386；派生页角色已更新，旧`source_catalog_initial_20261018.json`保留。下册术语表仍为印刷370页/PDF383。
- 审核库累计10批，3条旧页修订均为保留已有片段并补齐未审部分。上册8个ready，下册7个ready、1个unresolved；合计15个可检索完整单元、1个隔离完整单元、0 incomplete，286个目录单元尚未入审核库。
- 整页正文：上册PDF18–27、30–42，共23页；下册PDF15–28，共14页。局部片段：上册PDF43第二节前、下册PDF29第二节前。总计37页整页正文、2页局部；768页队列另有729页未核。18页目录另计，不能加算为正文转写。
- 上册完成绪论三单元、词汇学引论三单元、词汇语义第一节两单元。下册完成词法学引论六单元及名词概述两单元，其中“语法手段”保留原书疑点TL-V2-001：PDF19原印во́лос标复数第一格，原图放大确认而不猜改；整个单元隔离，其他七单元ready。
- 8项双册测试通过；801条原始提取、图像/文本/原PDF指纹与JSONL一致性通过。10批证据不可变、39页审核哈希、全部单元跨页拼接和审核状态在内存重建一致。真实引用示例通过；零错误报告不能证明全文准确率。
- 新报告`continuation_verification_20261018_001.json`；新示例在`rag/continuation_verification_20261018_001/`。原始示例包保留历史，页审核哈希已变化的旧包不能继续当当前有效证据。曾发现演示脚本按卷号覆盖同册多命中，引用校验已拦截；现改按具体单元代码引用，未修改检索排名。
- 两册SQLite一致性备份和指纹、当前额度采样、完整页清单及接续入口在`continuation_checkpoint_20261018_120821.json`和`latest_continuation_checkpoint.json`。
- 下一步上册从PDF43“第二节 词汇意义的层面 / 1. 概念意义”继续，下册从PDF29“第二节 名词的性 / 1. 概述”继续。两页都是已有部分页，要校验当前旧值并追加，不能重放旧批次覆盖。

## 2026-10-18建库初始记录（历史）

- 张家骅主编，商务印书馆，2006年版。上册405个PDF页、下册396个PDF页，共801页。各册仅最后数字化附页有文字层，其他799页用本地Tesseract识别。原PDF不改写。
- 801页已逐页提取，失败0、缺页0。每页保存文本、原图、PDF指纹、文本和图像SHA-256。所有原始提取记录仍为`unreviewed`，已核文本另存审核层，不覆盖OCR。
- 上册首个单元为“第二编 词汇学 / 第一章 引论 / 1. 词汇学的对象和任务”，PDF30–32，印刷14–16；下册首个单元为“第五编 词法学 / 第一章 引论 / 1. 词法学的对象”，PDF15–16，印刷2–3。共2个`ready`完整知识单元。
- 正文视觉核验实际覆盖：上册30–31整页、32页下一小节前的部分；下册15整页、16页下一小节前的部分。共3页整页正文、2页局部。缩略图检查封面、目录和书末只用于结构定位，不计作正文逐字审核。
- 原图转写恢复OCR漏行、乱码和错字；中文标点、俄文周围空格、字体加粗及排版断词作可读化处理。不是保留每个排版符号的外交式转录。原图和OCR原值可复核；不自动补重音或ё，不把书中称名、语体等表述规范化。
- 上册30页的音位竖线、软音标记、生产词干`са|д’|-`、`Ребенка`原印е已另外放大核图；下册保留`тетя`原印，不补成`тётя`。这些是字形核验，不是外部词典或语言学专家复核。
- 上册PDF28、下册PDF167的提取文本为空，已看原图确认为空白页，保留源记录并单独分类；不是OCR执行失败。
- 排除两张已核空白页后，双册正文、术语表及参考文献合计768个PDF页进入页面队列：3页整页正文已核，2页部分已核，763页未核。正文范围含编章扉页，不等同于768个知识节。尚未逐页核完目录、正文和全部印刷页码；未统计全书知识单元总数。
- 当前8项双册工程测试、8项既有语法审核模块回归通过。全量原始提取层的数据完整性检查与真实样例证据包验证另存本地报告。它们不证明逐字准确率、任意问题召回率或生成回答正确率。

目前完成的是原始语料层、审核入口及小范围可溯源检索样本。**全书审核研究版尚未完成，不能将801页称为已清洗可引用知识库，也不能沿用既有语法书232节研究版的验收结果。**

## 文件与数据隔离

工作目录：`data/processed/tonglun_reference/`，已被Git忽略。

| 文件 | 用途 |
| --- | --- |
| `volume1/source.json`、`volume2/source.json` | 两册来源和逐页文字层清单 |
| `volumeN/raw/pNNNN.json` | 原始提取、方法、指纹及未审核状态 |
| `volumeN/renders/pNNNN.png` | 原图渲染 |
| `volumeN/reviews/batch001.json` | 不可变审核批次；跨页片段与边界 |
| `volumeN/reviewed.sqlite` | 各册独立审核库 |
| `tonglun_corpus.sqlite` | 双册原始提取库，卷别+PDF页号联合主键 |
| `raw_pages.jsonl`、`volumeN/raw_pages.md` | 原始语料导出，含明确未审核标记 |
| `reviewed_units.jsonl`、`reviewed_units.md` | 只导出当前ready完整单元 |
| `source_catalog.json` | 书前、正文、术语、文献、数字化附页的结构范围 |
| `review_queue.json` | 未审/部分/整页正文状态及待核候选印刷页 |
| `checkpoint.json` | 提取与审核分别计数 |
| `rag/` | 本地证据包、引用检查及验收样例 |

不打开或写入`database/russian_ai_tutor.sqlite`，不修改原语法库及其封存研究包。语料、PDF、数据库和原文转写不提交Git；代码、工作流可记录。已有工作区其他改动保留，未执行Git提交、推送或部署。

## 处理规则

1. 文字层逐页检查，扫描页OCR。按页缓存，复跑校验来源和文本指纹；更换来源或DPI不得静默复用。部分成功后重跑只处理缺页。
2. OCR内容只作定位材料。按原图恢复中俄文、音标、上下标、表格和重音；不能凭语言通顺或模型自检认定正确。实在不能辨认的字形保留待核。
3. 编、章、节、小节写入稳定代码，包含卷别和学科前缀。上册与下册重号不能合并。片段需保留标题、原印页和PDF页及明确首尾；跨页断词只按原图接合。
4. 沿用`grammar_reference.import_batch`的预览、事务、一致性备份、批次不可变和旧值哈希保护。追加修正用新批次和`expected_review_sha256`，不得修改已应用批次重放。
5. 只有连续、首尾齐全且无未决说明的完整单元进入正式检索。原书疑点与OCR错误分开记录；未决单元整体隔离，不删掉疑点段落后只放行其余正文。
6. 原始库末尾数字化附页保留作来源档案，但从书籍文本检索排除。其他书前及文献材料仍明确标记页角色，不自动当作规则正文。
7. 候选印刷页使用上册`PDF页-16`、下册`PDF页-13`，仅供寻找原图。除已核片段外，不能宣称全书逐页映射已验证。
8. 检索目前为显式关键词，各词均须命中，忽略重音但保留ё。没有俄语词形还原、向量检索或自然提问召回验收。原语法书主题词规则不直接移作本书质量证明。
9. RAG证据包完整装入知识单元；预算不足时排除整个单元，不能截去限制或例外。来源同时固定卷别、原PDF、正文和逐页审核哈希。
10. 引用验证会重新核验来源和当前隔离状态，拒绝错卷、伪造引句和已变化证据；`citations_checked`仅表示机械可追溯，不代表解释可由引句推出。

## 可复现命令

```powershell
.venv/Scripts/python.exe -X utf8 scripts/tonglun_reference.py inventory
.venv/Scripts/python.exe -X utf8 scripts/tonglun_reference.py extract --workers 8
.venv/Scripts/python.exe -X utf8 scripts/tonglun_reference.py status
.venv/Scripts/python.exe -X utf8 scripts/tonglun_reference.py build
.venv/Scripts/python.exe -X utf8 scripts/tonglun_reference.py export
.venv/Scripts/python.exe -X utf8 scripts/audit_tonglun_reference.py

# 预览后应用；分别选择对应卷别
.venv/Scripts/python.exe -X utf8 scripts/tonglun_reference.py import data/processed/tonglun_reference/volume2/reviews/batch001.json --volume 2
.venv/Scripts/python.exe -X utf8 scripts/tonglun_reference.py import data/processed/tonglun_reference/volume2/reviews/batch001.json --volume 2 --apply

# 默认只查审核通过的完整单元
.venv/Scripts/python.exe -X utf8 scripts/tonglun_reference.py search '词法学的对象'
# 调阅未审OCR仅供定位，不能作为已审核引文
.venv/Scripts/python.exe -X utf8 scripts/tonglun_reference.py search '同义词' --include-unreviewed --limit 2

.venv/Scripts/python.exe -X utf8 scripts/tonglun_rag.py prepare --question '本书如何区分词汇学和词法学？' --query '研究对象' --output data/processed/tonglun_reference/rag/cross_volume_demo.json
.venv/Scripts/python.exe -X utf8 scripts/tonglun_rag.py validate --packet data/processed/tonglun_reference/rag/cross_volume_demo.json --response data/processed/tonglun_reference/rag/cross_volume_response.json
.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_tonglun_reference.py -v
```

## 接续与研究版验收

当前接续位置以上方2026-10-24 13:06断点及latest指针为准。早期绪论和下册PDF16的起点已经推进；目录已核，302单元的全部正文边界和第二轮审核仍需继续，不将OCR目录自动当作审核证据。

后续研究版需完成约定范围的原图清洗、整页复核、跨页接合、疑点隔离清单和定向纠正；冻结新检索题及负例后再评估，开发/回归与留出题分开记。再导出SQLite、JSONL、代码/固定依赖、来源指纹和质量证据，执行离线复现。

生成回答对照实验尚未开始，也没有新增收费模型调用额度。研究版封存、生成回答实验和导师/专家验收是不同阶段。本次未调用外部OCR、生成模型或上传资料。

## 2026-10-25 13:20 研究材料补录

- 13:20接续：最新采样2026-10-25T05:20:32.593Z，5小时已用90.0%、周60.0%。比例不是货币余额，未声称研究全部完成。
- 原始801页归档；正文730整页、302编号单元，175个ready（上65/下110）、127个隔离。[原正文断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)的四审核表仍一致，139条原待核状态未解除。
- [当前补证说明](tonglun_reference_evidence_progress_20261025_009.md)与[候选009](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261025_009.json)累计73条，58项建议65处编辑、14项待证、1项局部误报撤回，11项仅部分组件；另66条未在此补证系列处理。[重放](../data/processed/tonglun_reference/reviews/editorial_evidence_verification_20261025_007.json)及[来源核验](../data/processed/tonglun_reference/reviews/new_evidence_integrity_20261025_005.json)通过，应用0，默认检索未改变。
- 新增2234页公开外来词词典下载，实际核图首页及3词条；旧3188页正字法词典17词条核图和23页机构书目仍保留。公开网页索引节选与完整PDF核图分别标注；模型翻译建议不冒称专家勘误。未上传教材PDF或整段正文，新增收费OCR/生成调用0。
- 附录32页首轮候选：787术语行、108条书目，正式导入0、5项待核；[附录说明](tonglun_reference_appendix_progress_20261024.md)及[新增建议](../data/processed/tonglun_reference/editorial_candidates/appendix_evidence_proposals_20261024_001.json)保留1985/2005年份差异。默认检索不收附录。
- [问句基线](tonglun_reference_question_baseline_20261025.md)沿用150开发题，指定目标top5候选125/150、手给关键词150/150；普通无关8/8空返回、重叠范围外3/8。127隔离目标未返回，但仅89题整体空返回；均非生成正确率，19相关测试通过。候选未按这组失败调参，未默认化。
- [166题评阅材料](../data/processed/tonglun_reference/research_reviews/question166_20261025_001/question_index.md)316组、172完整来源、632空评分槽；[抽样说明](tonglun_reference_question_sampling_20261025.md)列25未目标化ready。实际独立评分0。[175原转录快照](../data/processed/tonglun_reference/research_exports/source175_original_20261025_001/README.md)在项目外隔离Python校验及两种篡改拒绝通过，不含隔离正文或候选。
- [最新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_132034.json)固定209项文件；[追加封存005](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_005.json)接续旧封存，历史指纹与新增链接通过。未改学生库、其他书库或原PDF，未部署、提交、推送。
- [本轮研究交付](tonglun_reference_research_checkpoint_20261025_001.md)汇总[论文底稿](tonglun_reference_thesis_methods_20261025.md)、字符清点及139条编校评阅包；127隔离来源、65处精确旧值、425张相关页图重放通过，278槽全空，实际独立评分0。
- 当前[待核队列002](../data/processed/tonglun_reference/reviews/next_review_queue_20261025_002.json)为73条补证、66条未覆盖，139条均未解除；旧001保留为历史。植物补录晚于冻结评阅包，联读且不改写原包。正式编校研究版、独立评价和生成对照未完成。


## 2026-10-25 13:26 额度边缘断点

- 13:26额度边缘断点：采样2026-10-25T05:26:13.601Z，5小时已用96.0%、周61.0%。比例不是财务余额，研究未整体完成。
- 原始801页归档；正文730整页、302编号单元，175个ready（上65/下110）、127个隔离。[原正文断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)的四审核表仍一致，139条原待核状态未解除。
- [当前补证说明](tonglun_reference_evidence_progress_20261025_009.md)与[候选009](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261025_009.json)累计73条，58项建议65处编辑、14项待证、1项局部误报撤回，11项仅部分组件；另66条未在此补证系列处理。[重放](../data/processed/tonglun_reference/reviews/editorial_evidence_verification_20261025_007.json)及[来源核验](../data/processed/tonglun_reference/reviews/new_evidence_integrity_20261025_005.json)通过，应用0，默认检索未改变。
- 新增2234页公开外来词词典下载，实际核图首页及3词条；旧3188页正字法词典17词条核图和23页机构书目仍保留。公开网页索引节选与完整PDF核图分别标注；模型翻译建议不冒称专家勘误。未上传教材PDF或整段正文，新增收费OCR/生成调用0。
- 附录32页首轮候选：787术语行、108条书目，正式导入0、5项待核；[附录说明](tonglun_reference_appendix_progress_20261024.md)及[新增建议](../data/processed/tonglun_reference/editorial_candidates/appendix_evidence_proposals_20261024_001.json)保留1985/2005年份差异。默认检索不收附录。
- [问句基线](tonglun_reference_question_baseline_20261025.md)沿用150开发题，指定目标top5候选125/150、手给关键词150/150；普通无关8/8空返回、重叠范围外3/8。127隔离目标未返回，但仅89题整体空返回；均非生成正确率，19相关测试通过。候选未按这组失败调参，未默认化。
- [166题评阅材料](../data/processed/tonglun_reference/research_reviews/question166_20261025_001/question_index.md)316组、172完整来源、632空评分槽；[抽样说明](tonglun_reference_question_sampling_20261025.md)列25未目标化ready。实际独立评分0。[175原转录快照](../data/processed/tonglun_reference/research_exports/source175_original_20261025_001/README.md)在项目外隔离Python校验及两种篡改拒绝通过，不含隔离正文或候选。
- [最新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_132614.json)固定218项文件；[追加封存006](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_006.json)接续005及原8包链，原351个不同文件校验通过。本次四审核表再次与原正文断点一致，未改学生库、其他书库或原PDF，未部署、提交、推送。
- [本轮研究交付](tonglun_reference_research_checkpoint_20261025_001.md)汇总[论文底稿](tonglun_reference_thesis_methods_20261025.md)、字符清点及139条编校评阅包；127隔离来源、65处精确旧值、425张相关页图重放通过，278槽全空，实际独立评分0。
- 当前[待核队列002](../data/processed/tonglun_reference/reviews/next_review_queue_20261025_002.json)为73条补证、66条未覆盖，139条均未解除；旧001保留为历史。植物补录晚于冻结评阅包，联读且不改写原包。正式编校研究版、独立评价和生成对照未完成。

- [66条分类型接续清单](../data/processed/tonglun_reference/reviews/remaining_issue_workplan_20261025_001.json)：46语音/语调、7构词版式、3信息结构版式、9词源/词义/原作、1混合；只描述主要任务，不作为错误数量。73条已补证也仍待逐组件裁定。


## 2026-10-25 13:27 入口核验补录

- 13:27额度边缘断点：采样2026-10-25T05:27:22.918Z，5小时已用98.0%、周62.0%。比例不是财务余额，研究未整体完成。
- 原始801页归档；正文730整页、302编号单元，175个ready（上65/下110）、127个隔离。[原正文断点](../data/processed/tonglun_reference/continuation_checkpoint_20261024_130615.json)的四审核表仍一致，139条原待核状态未解除。
- [当前补证说明](tonglun_reference_evidence_progress_20261025_009.md)与[候选009](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261025_009.json)累计73条，58项建议65处编辑、14项待证、1项局部误报撤回，11项仅部分组件；另66条未在此补证系列处理。[重放](../data/processed/tonglun_reference/reviews/editorial_evidence_verification_20261025_007.json)及[来源核验](../data/processed/tonglun_reference/reviews/new_evidence_integrity_20261025_005.json)通过，应用0，默认检索未改变。
- 新增2234页公开外来词词典下载，实际核图首页及3词条；旧3188页正字法词典17词条核图和23页机构书目仍保留。公开网页索引节选与完整PDF核图分别标注；模型翻译建议不冒称专家勘误。未上传教材PDF或整段正文，新增收费OCR/生成调用0。
- 附录32页首轮候选：787术语行、108条书目，正式导入0、5项待核；[附录说明](tonglun_reference_appendix_progress_20261024.md)及[新增建议](../data/processed/tonglun_reference/editorial_candidates/appendix_evidence_proposals_20261024_001.json)保留1985/2005年份差异。默认检索不收附录。
- [问句基线](tonglun_reference_question_baseline_20261025.md)沿用150开发题，指定目标top5候选125/150、手给关键词150/150；普通无关8/8空返回、重叠范围外3/8。127隔离目标未返回，但仅89题整体空返回；均非生成正确率，19相关测试通过。候选未按这组失败调参，未默认化。
- [166题评阅材料](../data/processed/tonglun_reference/research_reviews/question166_20261025_001/question_index.md)316组、172完整来源、632空评分槽；[抽样说明](tonglun_reference_question_sampling_20261025.md)列25未目标化ready。实际独立评分0。[175原转录快照](../data/processed/tonglun_reference/research_exports/source175_original_20261025_001/README.md)在项目外隔离Python校验及两种篡改拒绝通过，不含隔离正文或候选。
- [最新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_132723.json)固定221项文件；[追加封存007](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_007.json)保留360个不同文件及9包链校验记录和34个当前入口链接检查。原四审核表不变；未改学生库、其他书库或原PDF，未部署、提交、推送。
- [本轮研究交付](tonglun_reference_research_checkpoint_20261025_001.md)汇总[论文底稿](tonglun_reference_thesis_methods_20261025.md)、字符清点及139条编校评阅包；127隔离来源、65处精确旧值、425张相关页图重放通过，278槽全空，实际独立评分0。
- 当前[待核队列002](../data/processed/tonglun_reference/reviews/next_review_queue_20261025_002.json)为73条补证、66条未覆盖，139条均未解除；旧001保留为历史。植物补录晚于冻结评阅包，联读且不改写原包。正式编校研究版、独立评价和生成对照未完成。

- [66条分类型接续清单](../data/processed/tonglun_reference/reviews/remaining_issue_workplan_20261025_001.json)：46语音/语调、7构词版式、3信息结构版式、9词源/词义/原作、1混合；只描述主要任务，不作为错误数量。73条已补证也仍待逐组件裁定。


## 2026-10-25 17:15 补证及元数据接续

- 17:15接续：最新采样2026-10-25T09:15:13.193Z，5小时已用31.0%、周5.0%。已确认新窗口，旧98%为上一窗口历史，不当作当前额度；比例不是财务余额。
- 原始801页归档；正文730整页、302编号单元，175个ready（上65/下110）、127个隔离。原正文断点四审核表仍一致，139条原待核状态未解除。
- [补证011](tonglun_reference_evidence_progress_20261025_011.md)及[当前候选](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261025_011.json)累计78条：62项建议70处编辑、15项待证、1项局部误报撤回，13项只核部分组件；应用0。[队列003](../data/processed/tonglun_reference/reviews/next_review_queue_20261025_003.json)另61条未进入补证系列，139条仍待核。
- 本批核5份公开PDF及1章原作HTML：12张有效裁图逐像素重渲染通过。Тынянов为1937扫描，其余电子本/转载本底本未核，3张不完整初裁不作完整引句图证。新增两项组件另档；当前TL-W25事实ID共27项，留存层级另列。收费OCR/生成调用0。
- 附录仍32页首轮候选、787术语行、108书目项；正式导入0，5项待核，不入默认检索。
- 既有[150开发题基线](tonglun_reference_question_baseline_20261025.md)不变：关键词目标top5为150/150，自然问句125/150；普通无关8/8空，重叠范围外3/8，127隔离目标未返回但89题整体空。19相关测试为既有结果，未据失败调参；非生成正确率。
- [139条编校评阅包001](../data/processed/tonglun_reference/research_reviews/issues139_20261025_001/README.md)固定候选009、278空槽，新增5条联读本批增量；[166题检索评阅材料](../data/processed/tonglun_reference/research_reviews/question166_20261025_001/README.md)632空槽，独立评分均0。[175原ready快照](../data/processed/tonglun_reference/research_exports/source175_original_20261025_001/README.md)未混候选。旧[论文底稿](tonglun_reference_thesis_methods_20261025.md)和[字符清点](tonglun_reference_unicode_inventory_20261025.md)保留原版。
- [最新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_171515.json)固定290项文件，[追加封存008](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_008.json)接续旧链。旧断点limits沿用39条说明的元数据问题已追加说明，新断点从当前候选重建，不改历史文件。
- 继续音标、调核、版式与未覆盖组件复核；正式编校研究版、独立评价、引文充分性和生成对照未完成。未改学生库、其他书库或原PDF，未部署、提交、推送。


## 2026-10-25 17:36 补证及元数据接续

- 17:36接续：最新采样2026-10-25T09:35:59.605Z，5小时已用52.0%、周8.0%。已确认新窗口，旧98%为上一窗口历史，不当作当前额度；比例不是财务余额。
- 原始801页归档；正文730整页、302编号单元，175个ready（上65/下110）、127个隔离。原正文断点四审核表仍一致，139条原待核状态未解除。
- [补证012](tonglun_reference_evidence_progress_20261025_012.md)及[当前候选](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261025_012.json)累计82条：65项建议73处编辑、16项待证、1项局部误报撤回，17项只核部分组件；应用0。[队列004](../data/processed/tonglun_reference/reviews/next_review_queue_20261025_004.json)另57条未进入补证系列，139条仍待核。
- 本批核5份公开PDF及1章原作HTML：12张有效裁图逐像素重渲染通过。Тынянов为1937扫描，其余电子本/转载本底本未核，3张不完整初裁不作完整引句图证。新增两项组件另档；当前TL-W25事实ID共27项，留存层级另列。收费OCR/生成调用0。
- 附录仍32页首轮候选、787术语行、108书目项；正式导入0，5项待核，不入默认检索。
- 既有[150开发题基线](tonglun_reference_question_baseline_20261025.md)不变：关键词目标top5为150/150，自然问句125/150；普通无关8/8空，重叠范围外3/8，127隔离目标未返回但89题整体空。19相关测试为既有结果，未据失败调参；非生成正确率。
- [139条编校评阅包001](../data/processed/tonglun_reference/research_reviews/issues139_20261025_001/README.md)固定候选009、278空槽，新增9条联读本批增量；[166题检索评阅材料](../data/processed/tonglun_reference/research_reviews/question166_20261025_001/README.md)632空槽，独立评分均0。[175原ready快照](../data/processed/tonglun_reference/research_exports/source175_original_20261025_001/README.md)未混候选。旧[论文底稿](tonglun_reference_thesis_methods_20261025.md)和[字符清点](tonglun_reference_unicode_inventory_20261025.md)保留原版。
- [最新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_173601.json)固定343项文件，[追加封存009](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_009.json)接续旧链。旧断点limits沿用39条说明的元数据问题已追加说明，新断点从当前候选重建，不改历史文件。
- 继续音标、调核、版式与未覆盖组件复核；正式编校研究版、独立评价、引文充分性和生成对照未完成。未改学生库、其他书库或原PDF，未部署、提交、推送。

- [语调原页候选层](tonglun_reference_prosody_pilot_20261025.md)：4单元31记录/30例组、42语段；28看图候选元音锚、1理论推定，另2语段待核。9图重渲染及5类构造修改拒绝通过，3处改助手括注不称原书错误。隔离状态与默认检索不变。


## 2026-10-25 17:53 补证及元数据接续

- 17:53接续：最新采样2026-10-25T09:53:02.044Z，5小时已用82.0%、周13.0%。已确认新窗口，旧98%为上一窗口历史，不当作当前额度；比例不是财务余额。
- 原始801页归档；正文730整页、302编号单元，175个ready（上65/下110）、127个隔离。原正文断点四审核表仍一致，139条原待核状态未解除。
- [补证013](tonglun_reference_evidence_progress_20261025_013.md)及[当前候选](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261025_013.json)累计83条：65项建议73处编辑、17项待证、1项局部误报撤回，18项只核部分组件；应用0。[队列005](../data/processed/tonglun_reference/reviews/next_review_queue_20261025_005.json)另56条未进入补证系列，139条仍待核。
- 本批核5份公开PDF及1章原作HTML：12张有效裁图逐像素重渲染通过。Тынянов为1937扫描，其余电子本/转载本底本未核，3张不完整初裁不作完整引句图证。新增两项组件另档；当前TL-W25事实ID共27项，留存层级另列。收费OCR/生成调用0。
- 附录仍32页首轮候选、787术语行、108书目项；正式导入0，5项待核，不入默认检索。
- 既有[150开发题基线](tonglun_reference_question_baseline_20261025.md)不变：关键词目标top5为150/150，自然问句125/150；普通无关8/8空，重叠范围外3/8，127隔离目标未返回但89题整体空。19相关测试为既有结果，未据失败调参；非生成正确率。
- [139条编校评阅包001](../data/processed/tonglun_reference/research_reviews/issues139_20261025_001/README.md)固定候选009、278空槽，新增10条联读本批增量；[166题检索评阅材料](../data/processed/tonglun_reference/research_reviews/question166_20261025_001/README.md)632空槽，独立评分均0。[175原ready快照](../data/processed/tonglun_reference/research_exports/source175_original_20261025_001/README.md)未混候选。旧[论文底稿](tonglun_reference_thesis_methods_20261025.md)和[字符清点](tonglun_reference_unicode_inventory_20261025.md)保留原版。
- [最新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_175304.json)固定422项文件，[追加封存010](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_010.json)接续旧链。旧断点limits沿用39条说明的元数据问题已追加说明，新断点从当前候选重建，不改历史文件。
- 继续音标、调核、版式与未覆盖组件复核；正式编校研究版、独立评价、引文充分性和生成对照未完成。未改学生库、其他书库或原PDF，未部署、提交、推送。

- [语调原页候选层](tonglun_reference_prosody_pilot_20261025.md)：4单元31记录/30例组、42语段；28看图候选元音锚、1理论推定，另2语段待核。9图重渲染及5类构造修改拒绝通过，3处改助手括注不称原书错误。隔离状态与默认检索不变。

- [曲线图例候选层](tonglun_reference_contour_atlas_20261025.md)：5页29幅、7调型；2处错裁已重裁，29个文字定位与图像重渲染、4类构造修改拒绝通过。曲线数值、完整调核字形与喉塞符号范围未标，原单元继续隔离。


- 17:59新增[219单元实验包](tonglun_reference_editorial219_preview_20261025.md)：175原ready＋44未批准候选、54处派生编辑，83仅元数据；原库仍127隔离/139待核。6类构造修改拒绝及独立进程-I实跑通过。原150题top5为125/150→126/150，新44旧标题题42/44；固定公式未调参、非独立评测、生成0。
- 本次[断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_175912.json)固定442文件，[追加封存011](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_011.json)接续；最新用量采样2026-10-25T09:59:10.951Z，5小时89.0%。

## 2026-10-25《新时代俄语通论》双册知识库（持续）

- 18:04断点：最新采样2026-10-25T10:04:50.815Z，5小时已用96.0%、周15.0%；比例不等于财务余额。按用户持续安排推进，整体未完成。
- 原801页归档；正文730页、302单元，175 ready（上65/下110）、127隔离，139原待核不解除；原正文四审核表与基准一致。附录仍32页首轮、787术语行、108书目项、5待核，正式导入0。
- [补证013](tonglun_reference_evidence_progress_20261025_013.md)覆盖83条：65项建议、73处编辑、17待证、1局部误报撤回、18只核部分组件；应用0。[队列005](../data/processed/tonglun_reference/reviews/next_review_queue_20261025_005.json)另56条未进入该系列。фунт新增官方网页与原页联读线索，但直接借入/远源未形成唯一改文，另档不增加候选计数。
- [语调候选层](tonglun_reference_prosody_pilot_20261025.md)：4单元31记录/30例组、42语段，28看图候选元音锚、1理论推定、2语段待核；完整斜体范围未标。3项修正是助手转录括注，非原书错误。
- [曲线图例](tonglun_reference_contour_atlas_20261025.md)：5页29图/7调型；2错裁已修，29文字/图像绑定及4类构造修改拒绝通过，非声学测量，完整音标/调核字形仍待核。
- [219实验快照](tonglun_reference_editorial219_preview_20261025.md)：175原ready＋44未批准助手候选，54处派生编辑；83仅排除元数据，原库仍127隔离。保留原转录、原注和改文日志；6类构造修改拒绝、标准库-I进程实跑通过，未默认化。
- 固定旧150题：top1 101→98、top3 121→121、top5 125→126；普通无关8/8空、重叠范围外3/8空。新44目标旧标题题42/44，但只有43种不同问句；仍排除83目标均不返回。[6题排序解释](tonglun_reference_editorial219_rank_analysis_20261025.md)及完整结果保留，未调参、非独立评测、生成0。旧175组150题前5代码/分数和16负例均逐项重现历史结果。
- [编校增量评阅包](../data/processed/tonglun_reference/research_reviews/issues_incremental_20261025_001/README.md)10新增补证/20空槽；旧139条包仍固定009/278空槽、166题检索包632空槽，独立评分均0。原175来源包及旧论文底稿保持原版，219结果另档。
- [当前断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_180452.json)固定460文件，[追加封存012](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_012.json)接续历史链。5份新公开PDF/1章HTML的12有效裁图已核；27个TL-W25事实ID留存分层不变。官方фунт线索不冒称已核历史词源专著。
- 继续56条未进入补证系列及局部未核组件；完整音标版式、独立专家审核、引文充分性和生成对照未完成。19相关产品测试是既有结果，本批未改生产行为而未重复跑。收费OCR/生成0，未外发教材、未改学生库/其他书库/原PDF、未部署、提交或推送。

- 22:18接续：[本批说明](tonglun_reference_prosody_extension_20261025.md)。表情实体3图＋旧29图共32图；连贯话语9组、42跨度、41调型标记、43斜体元音锚候选。7有效裁图重渲染、8类构造修改拒绝通过。跨页及原文未印调型/斜线均保留，原录音未核。 当前候选014覆盖85条、73处建议编辑、19待证、20局部核实；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_221848.json)固定508文件，[追加封存013](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_013.json)；当前额度采样2026-10-25T14:18:46.502Z，5小时15.0%、周18.0%。新窗口已刷新，旧97%为历史。

- 22:23接续：[本批说明](tonglun_reference_intonation_literal_index_20261025.md)。新增语调全章字面索引19单元/30页/164段、603调型标记/540对转录星号，37多选与4双峰分别保留。7类构造修改拒绝、显式隔离读取及字符映射通过；新增逐符看图0，不据索引增加补证覆盖。 当前候选014覆盖85条、73处建议编辑、19待证、20局部核实；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_222332.json)固定523文件，[追加封存014](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_014.json)；当前额度采样2026-10-25T14:23:31.317Z，5小时18.0%、周19.0%。新窗口已刷新，旧97%为历史。

- 22:32接续：[本批说明](tonglun_reference_quote_correspondence_20261025.md)。新增3条原句/词源联读。原页明确印查尔斯基，提出恢复转录漏基，非原书勘误；Семёнов电子原作有同样не то что，保留俄文不补только，中文解释仍待核。2公开PDF图＋1教材图重渲染及归档HTML句文通过。 当前候选015覆盖88条、74处建议编辑、21待证、22局部核实；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_223233.json)固定549文件，[追加封存015](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_015.json)；当前额度采样2026-10-25T14:32:32.609Z，5小时30.0%、周20.0%。新窗口已刷新，旧97%为历史。

- 22:38接续：[本批说明](tonglun_reference_editorial_coordinates_20261025.md)。新增74编辑字符追踪，区分原归档转录与候选派生；4处明确助手层，其余70责任层未全量分类，不计原书错误。新增220未批准实验快照：175＋45、55编辑、82元数据排除；旧219不变。仅附45候选映射，6类归属拒绝与2类子集混入拒绝通过，未套用旧检索成绩。 当前候选015覆盖88条、74处建议编辑、21待证、22局部核实；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_223828.json)固定580文件，[追加封存016](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_016.json)；当前额度采样2026-10-25T14:38:27.555Z，5小时37.0%、周21.0%。新窗口已刷新，旧97%为历史。

- 22:51接续：[本批说明](tonglun_reference_phonetic_layout_audit_20261025.md)。辅音表37候选按物理排位保留，ц不迁位、х/х’清浊合并格不强配。ИК5精选6条/12元音候选，建议恢复щено́к转录漏重音，未印调型不补，星号对不作调核计数。两层各4类构造修改拒绝通过。 当前候选017覆盖90条、75处建议编辑、22待证、24局部核实；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_225139.json)固定619文件，[追加封存017](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_017.json)；当前额度采样2026-10-25T14:51:38.491Z，5小时54.0%、周24.0%。新窗口已刷新，旧97%为历史。

- 23:04接续：[本批说明](tonglun_reference_dataset_card_appendix_20261025.md)。新增研究数据卡区分175/219/220、字符/标记/修订位置与自然语料频次。附录895条原首轮/5字段提案并列，研究开关默认排除，32页指纹及4类拒绝通过；原5待核/正式导入0。增量评阅002补7条/14空槽，三批材料并集90case，评分0。 当前候选017覆盖90条、75处建议编辑、22待证、24局部核实；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_230432.json)固定650文件，[追加封存018](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_018.json)；当前额度采样2026-10-25T15:04:31.469Z，5小时68.0%、周26.0%。新窗口已刷新，旧97%为历史。

- 23:15接续：[本批说明](tonglun_reference_requirements_guard_20261025.md)。新增独立可选证据需求检查，不改排序。旧16负例原5份提示词被抑制，检索来源仍保留；旧150仅需求判断0拦截，新20预期决策20/20，非独立/生成正确率。5类篡改拒绝与CLI通过，生成0、学生库读取0。 当前候选017覆盖90条、75处建议编辑、22待证、24局部核实；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_231507.json)固定662文件，[追加封存019](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_019.json)；当前额度采样2026-10-25T15:15:07.171Z，5小时88.0%、周29.0%。新窗口已刷新，旧97%为历史。

## 2026-10-25《新时代俄语通论》双册知识库（持续）

- 23:20断点：本窗口22:07已刷新，最新采样2026-10-25T15:20:14.373Z，5小时已用93.0%、周30.0%；旧97%是上一窗口历史，比例不是财务余额。整体任务未完成。
- 原801页归档；正文730页、302单元，175 ready（上65/下110）、127隔离、139原待核不解除。原四审核表与基准一致，最新证明为候选017重放报告014；本轮编校提案回写0。
- [候选017](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261025_017.json)覆盖90条，67项建议75处编辑、22待证、1局部误报撤回，24局部核实为重叠标记；另49条未进入补证系列。原页恢复查尔斯基漏基、щено́к漏重音分别为转录修复，不计原书勘误。[版式复核](tonglun_reference_phonetic_layout_audit_20261025.md)。
- [数据卡与口径](tonglun_reference_dataset_card_appendix_20261025.md)：175/219/220快照原始正文字符分别260817/382420/386504，非词数或token。[220快照](../data/processed/tonglun_reference/research_exports/editorial220_preview_20261025_002/README.md)固定015＝175原ready＋45未批准候选/55编辑，82仅排除元数据；原库仍127隔离。未套用旧219检索成绩。
- [字符追踪](tonglun_reference_editorial_coordinates_20261025.md)固定015的76预览单元/74编辑，区分原转录与派生，拒绝候选冒称原转录、原转录自动认证原印；后续第75处重音提案另有原页证据。4处明确助手层，其余70在该旧台账尚未全量分类，不据编辑数计原书错误。
- [语调扩展](tonglun_reference_prosody_extension_20261025.md)：旧29＋表情实体3＝32曲线；连贯话语9组/42跨度/41调型/43元音锚候选。ИК5另精选6条/12元音；37辅音符号按原表物理排位保存，ц不迁位、х共享格不强配清行；完整字形与原音频未认证。
- [语调字面索引](tonglun_reference_intonation_literal_index_20261025.md)：19单元、30页、164段、603调型标记（37多选/4双峰）、540对转录星号；不是603例句或540已核调核。研究读取隔离材料须显式开关，不改默认。
- [附录895预览](../data/processed/tonglun_reference/research_exports/appendix895_preview_20261025_001/README.md)原首轮/提案并列，仅预览既有5字段改动；32页/787术语行/108书目项、原5待核、正式导入0，Николаева1985/2005不统一。旧评阅包009＋增量001/002材料并集90case，所有独立评分0，原139问题不增加。
- [可选需求检查](tonglun_reference_requirements_guard_20261025.md)不改排序/默认入口：旧16负例原5份提示词被抑制，检索来源仍保留；旧150只重放需求判断0拦截，新20开发题需求决策20/20，非独立或问答正确率。5类篡改拒绝、CLI通过；未拦截不等于充分。
- 旧175自然问句top5 125/150；219固定旧150题top1 101→98、top5 125→126，新44旧标题目标42/44且仅43种问句。220无新增检索/生成成绩，19相关旧产品测试不冒称本轮重跑。独立专家评价、整例边界、完整音标与引文充分性仍待完成。
- [当前断点](../data/processed/tonglun_reference/evidence_checkpoint_20261025_232015.json)固定668文件，[追加封存020](../data/processed/tonglun_reference/reviews/delivery_addendum_20261025_020.json)接续；此前22级封存链818项指纹及46份Markdown/1584个本地链接通过。新增收费OCR/生成0，未上传教材PDF或整段正文，未读学生库，未改学生/其他书库及原PDF，未部署、提交或推送。

- 2026-10-26 12:44接续：[本批说明](tonglun_reference_segmental_layout_20261026.md)。新增6条选段补证、3处助手转录修复。保存11裁片、4音位表、5四节点图，保留合并区域/原空白和各表II/III编号环境差异；Unicode完全等价与全节例词仍待核。两份布局验证各拒绝6类变化，不是专家正确率。 当前补证96条、78处建议编辑、25待证、30局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_124405.json)固定704文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_001.json)；额度采样2026-10-26T04:44:04.877Z，5小时20.0%、周34.0%，不是财务余额。

- 2026-10-26 12:52接续：[本批说明](tonglun_reference_intonation_extents_20261026_001.md)。调型1、2全部18用法组核59个印刷例示边界（28/31），2例跨页、1主语缺损保留；95调型标签与92对转录星号各绑定一次，非调核数。7类边界篡改拒绝；独立标准库读取入口默认0/研究开启1个跨页实测通过，修复GBK组合重音输出。 当前补证98条、78处建议编辑、27待证、32局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_125208.json)固定733文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_002.json)；额度采样2026-10-26T04:52:07.272Z，5小时33.0%、周37.0%，不是财务余额。

- 2026-10-26 12:58接续：[本批说明](tonglun_reference_intonation_extents_20261026_002.md)。整例累计4单元/45组/163上下文，旧59记录逐字段保留，新增104。287调型标签/280星号各绑定一次；4作者括号释义另标角色，3跨页、1主语缺损保留。新增298断行拼接1处助手转录修复建议。7类篡改拒绝，4组标准库CLI通过；非语料频次或调核正确率。 当前补证100条、79处建议编辑、28待证、34局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_125841.json)固定764文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_003.json)；额度采样2026-10-26T04:58:41.096Z，5小时43.0%、周38.0%，不是财务余额。

- 2026-10-26 13:17接续：[本批说明](tonglun_reference_intonation_extents_20261026_003.md)。第三节使用规则全部7单元/65编号组及3附加组核258个上下文，旧163记录保留，新增95；420方括号标签/445星号各绑定，6跨页。新增21中文译注/2比较说明/3等义变体另标角色；圆括号(1)和无标签Замечательно保留。17有效裁片、6类篡改拒绝、6种CLI情形通过，不认证全部调核。 当前补证102条、79处建议编辑、30待证、36局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_131736.json)固定802文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_004.json)；额度采样2026-10-26T05:17:35.353Z，5小时60.0%、周41.0%，不是财务余额。

- 2026-10-26 13:23接续：[本批说明](tonglun_reference_editorial_coordinates_20261026.md)。最新90审计单元/79编辑字符台账完成；旧74项ID/原值/候选值/原范围/页绑定保留。明确9助手层（3括注、6转录修复），70责任未全量分类，不按编辑数计原书错误。79候选归属拒绝与79原值定位重放，6类负检验及2种CLI通过。新增12case评阅增量/24空槽，旧90case不改，独立评分0。 当前补证102条、79处建议编辑、30待证、36局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_132333.json)固定826文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_005.json)；额度采样2026-10-26T05:23:33.101Z，5小时68.0%、周42.0%，不是财务余额。

- 2026-10-26 13:31接续：[本批说明](tonglun_reference_intonation_contrasts_20261026.md)。新增3单元40辨义上下文/77对比侧/27原印比较标题，90标签/95星号各绑定，6裁片及6类负检验通过。与使用规则003合计298上下文、510/603标签、540/540归档星号各一次；不等于调核或全部字形认证。新增3case/6评阅空槽，旧102case保持；当前79编辑坐标固定005含90审计单元，006另3无编辑单元不冒称同范围。 当前补证105条、79处建议编辑、33待证、39局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_133155.json)固定861文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_006.json)；额度采样2026-10-26T05:31:54.951Z，5小时79.0%、周44.0%，不是财务余额。

- 2026-10-26 13:39接续：[本批说明](tonglun_reference_thesis_preparation_20261026.md)。形成论文方法与结果工作底稿及当前研究数据卡。302单元元数据不含正文；原175/127/139、补证105/79/34、字符图005与当前006范围差异均实核，26项来源指纹通过。区分结构覆盖、检索命中、引文充分性及独立评价；219的top1退步与top5微增并列，220无新成绩。 当前补证105条、79处建议编辑、33待证、39局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_133907.json)固定875文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_007.json)；额度采样2026-10-26T05:39:06.563Z，5小时89.0%、周45.0%，不是财务余额。

## 2026-10-26《新时代俄语通论》双册知识库（持续）

- 13:42断点：额度采样2026-10-26T05:42:15.527Z，5小时已用93.0%、周46.0%，不是财务余额；本轮持续推进，整体任务仍未完成。
- 原801页归档，正文730页/302单元；175 ready（上65/下110）、127隔离、139原待核不解除。[本次重放006](../data/processed/tonglun_reference/reviews/editorial_evidence_verification_20261026_006.json)证明原四审核表与基准一致，本轮编校提案回写0。
- [当前候选006](../data/processed/tonglun_reference/editorial_candidates/evidence_preview_20261026_006.json)补证105条，71项含79处建议编辑、33待证、1局部误报撤回；39局部核实为重叠标记，另34条未补证。本日新增15条覆盖、4处助手转录修复，不计教材原书勘误。
- [字符出处](tonglun_reference_editorial_coordinates_20261026.md)固定005的90审计单元，79编辑与当前006一致；006新增3个无编辑单元不在该坐标图。明确9助手层（3括注/6转录修复），70责任层未全量分类；79错误原转录归属拒绝、79原值定位通过，原印不自动认证。
- [使用规则整例003](tonglun_reference_intonation_extents_20261026_003.md)258上下文＋[辨义上下文](tonglun_reference_intonation_contrasts_20261026.md)40，合10隔离单元/298编辑分组上下文。510/603方括号标签和540/540星号各绑定一次；余93标签另列，完整斜体/调核与音频未认证，不按上下文或标记数推算自然语料频次。
- [音段/音位表](tonglun_reference_segmental_layout_20261026.md)保留合并区域、原空白和各表II/III环境差异；特殊字形不强换Unicode。旧32曲线、37辅音、精选IK5与连贯话语材料保留，不与新整例数量相加。
- [论文方法与结果底稿](tonglun_reference_thesis_preparation_20261026.md)及[本日数据卡](../data/processed/tonglun_reference/research_exports/dataset_card_20261026_001/README.md)已成形；302单元元数据不含正文。175/219/220字符260817/382420/386504为Python len，非词或token。219旧150题top1 101→98、top5 125→126；220固定旧015、175＋45未批准候选/55编辑，无新增检索或生成成绩。
- 旧009及4份增量评阅材料并集105补证case；本日两包15case/30空槽，实际独立评分0。附录32页/787术语/108书目、895首轮预览、原5待核和5字段提案保留，正式导入0，Николаева1985/2005不统一。
- [可选需求检查](tonglun_reference_requirements_guard_20261025.md)保留排序/默认；旧16负例5份提示词被抑制，旧150只需求判断0拦截，新20开发题决策20/20，非独立或问答正确率，未拦截不等于充分。新增收费OCR/生成0，未上传教材，未读学生库，未改学生/其他书库或PDF，未部署、提交或推送。
- [当前断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_134216.json)固定884文件，[追加封存008](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_008.json)接续；此前30级封存链1039项指纹、62份Markdown/2082本地链接通过，最终外层追加检查另实跑。[续接清单](../data/processed/tonglun_reference/reviews/resume_priorities_20261026_001.json)列34未补证/39局部组件；正式书目、独立问题/专家评价与引文充分性仍待完成。

- 2026-10-26 13:44最终续接：余93标签定位7单元/24块，新增核图0。[断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_134456.json)与[封存009](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_009.json)；原175/139及105补证/79编辑不变，整体未完成。

- 2026-10-26 15:56接续：[本批说明](tonglun_reference_intonation_remaining_extents_20261026.md)。语调余93标签已分为86个例示关联标签和7个图例标签；新增44上下文，合计342上下文，603标签均绑定范围，非全章正确性或调核认证。5项防误用及4项独立CLI检查通过。 当前补证105条、79处建议编辑、33待证、39局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_155601.json)固定907文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_010.json)；额度采样2026-10-26T07:56:01.238Z，5小时21.0%、周3.0%，不是财务余额。

- 2026-10-26 16:02接续：[本批说明](tonglun_reference_phonetic_attachments_20261026.md)。6条新音标补证、18条附标观察、24表格符号位置；17裁图像素及5项防误用检查通过，12个独立评阅空槽。原105条case保持，新增编辑0。 当前补证111条、79处建议编辑、39待证、45局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_160238.json)固定948文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_011.json)；额度采样2026-10-26T08:02:37.554Z，5小时29.0%、周4.0%，不是财务余额。

- 2026-10-26 16:09接续：[本批说明](tonglun_reference_pronunciation_layout_20261026.md)。7条新补证、18条观察、弱化表12物理格；16裁图像素及4项防误用检查通过。父称多с为助手转录，新增1处修订建议；14个评阅空槽。 当前补证118条、80处建议编辑、45待证、52局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_160902.json)固定988文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_012.json)；额度采样2026-10-26T08:09:02.114Z，5小时37.0%、周6.0%，不是财务余额。

- 2026-10-26 16:23接续：[本批说明](tonglun_reference_accent_examples_20261026.md)。9条新补证、19条观察、24个原编号段落；15裁图及5项防误用检查通过，错误示例不作推荐读音。新增向→问及跨页词间漏空格2处建议；18个评阅空槽。 当前补证127条、82处建议编辑、52待证、61局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_162308.json)固定1027文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_013.json)；额度采样2026-10-26T08:23:08.163Z，5小时52.0%、周8.0%，不是财务余额。

- 2026-10-26 16:37接续：[本批说明](tonglun_reference_morpheme_layout_20261026.md)。7条新补证、20条观察、13裁图、3层嵌套；4项防误用检查通过。零位、非词星号、截音/重合条件保留，无新增编辑；14个评阅空槽。 当前补证134条、82处建议编辑、59待证、68局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_163707.json)固定1064文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_014.json)；额度采样2026-10-26T08:37:06.452Z，5小时61.0%、周10.0%，不是财务余额。

- 2026-10-26 16:57接续：[本批说明](tonglun_reference_syntax_layout_20261026.md)。最后5条句法问题补证：15观察、11裁图、8表格例句，累计139条补证/83处建议；单斜线说明修复一处，10个评阅空槽。原139待核及127隔离未解除。 当前补证139条、83处建议编辑、63待证、73局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_165725.json)固定1097文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_015.json)；额度采样2026-10-26T08:57:23.080Z，5小时76.0%、周12.0%，不是财务余额。

- 2026-10-26 17:06接续：[本批说明](tonglun_reference_thesis_preparation_20261026_002.md)。坐标002覆盖127审计单元/83建议，旧79项原范围保留；13助手层、70责任待分类。数据卡002逐条保留139原待核，未补证0不等于未解决0；49case/98空槽实际评分0。旧175/219/220研究快照及成绩保持。 当前补证139条、83处建议编辑、63待证、73局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_170638.json)固定1122文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_016.json)；额度采样2026-10-26T09:06:36.578Z，5小时81.0%、周13.0%，不是财务余额。

- 2026-10-26 17:20接续：[本批说明](tonglun_reference_research_handoff_20261026.md)。双册原页书目及8裁图、RIS/BibTeX草稿完成；统一139case/127审计预览/278空槽，8项结构防误用通过，实际评分0。旧150题逐题配对及300命中表名次重放，无新检索/生成；坐标003仅修正002说明标签，数据相同。 当前补证139条、83处建议编辑、63待证、73局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_172054.json)固定1175文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_017.json)；额度采样2026-10-26T09:20:51.721Z，5小时93.0%、周15.0%，不是财务余额。

- 2026-10-26 17:26接续：[本批说明](tonglun_reference_checkpoint_validation_20261026.md)。原样入口摘录保留源目录基准，另存003重定位链接版本；原字节和003目标均验证。带原目录元数据的84份Markdown/2180本地目标通过；整体内容审核仍未完成。 当前补证139条、83处建议编辑、63待证、73局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_172622.json)固定1197文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_019.json)；额度采样2026-10-26T09:26:20.939Z，5小时97.0%、周15.0%，不是财务余额。

- 2026-10-26 23:30接续：[本批说明](tonglun_reference_syntax_component_reviews_20261026.md)。3条剩余句法问题补5组件：署名建议В. Панова，地名按原印克里木修复归档多米；谚语свету及将来时时保留。累计85处建议；136旧case不改，139原待核均保留。 当前补证139条、85处建议编辑、63待证、73局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_233051.json)固定1229文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_020.json)；额度采样2026-10-26T15:30:50.250Z，5小时20.0%、周18.0%，不是财务余额。

- 2026-10-26 23:45接续：[本批说明](tonglun_reference_normalized_readings_20261026.md)。3短单元2537码位完整规范化复读，93记法/27教学组/11参考→错误对；新223快照保留原220条记录、扩展层分别开关。冻结四层检索：旧150 top1为101/98/100/97，top5为125/126/125/126；新3开发题在178/223名次4/1/1，非独立正确率。 当前补证139条、85处建议编辑、63待证、73局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261026_234527.json)固定1265文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_021.json)；额度采样2026-10-26T15:45:26.718Z，5小时38.0%、周21.0%，不是财务余额。

- 2026-10-27 00:00接续：[本批说明](tonglun_reference_normalized_five_units_20261026.md)。再完整复读068/047，累计5单元5455码位/235记法/92教学组；第三链〈k〉修复归档，累计86建议。ель按整词定位，拒绝落在сельдь内部。新225保留223全部记录，047仅纯文本解释，未套用223检索成绩。 当前补证139条、86处建议编辑、62待证、73局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261027_000052.json)固定1301文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_022.json)；额度采样2026-10-26T16:00:51.294Z，5小时60.0%、周25.0%，不是财务余额。

- 2026-10-27 09:11接续：[本批说明](tonglun_reference_research_handoff_20261027.md)。бобр通过学名桥接提出河狸译名；累计87建议、72局部组件。新字符出处保留旧83项身份与责任，新数据卡和139项统一空评阅材料同步，278槽仍空。 当前补证139条、87处建议编辑、62待证、72局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261027_091140.json)固定1349文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_023.json)；额度采样2026-10-27T01:11:39.065Z，5小时12.0%、周27.0%，不是财务余额。

- 2026-10-27 09:16接续：[本批说明](tonglun_reference_normalized225_evaluation_20261027.md)。225冻结四层评价完成；旧150名次逐条保持223实验，但新开发题066从4跌出前5、069从1降2；不调权重抹去退步。普通负例8/8空、主题重叠3/8空，范围外问题仍在。 当前补证139条、87处建议编辑、62待证、72局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261027_091620.json)固定1362文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_024.json)；额度采样2026-10-27T01:16:19.047Z，5小时21.0%、周29.0%，不是财务余额。

- 2026-10-27 09:25接续：[本批说明](tonglun_reference_traceable225_local_20261027.md)。225本地独立证据包可检索/重放/页定位，默认175、扩展显式开启。225来源、57派生、413跨页、620冻结命中与13误用拒绝通过；8移目录隔离命令无网络/DB。20规则开发题符合预期，不证明需求判别准确率；无关主张仍可过逐字引文检查。 当前补证139条、87处建议编辑、62待证、72局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261027_092546.json)固定1386文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_025.json)；额度采样2026-10-27T01:25:44.106Z，5小时36.0%、周31.0%，不是财务余额。

- 2026-10-27 09:32接续：[本批说明](tonglun_reference_requirement_challenges_20261027.md)。需求第一版新措辞20题漏8/误4；第二版单独修规则，开发40题符合预期，另新20压力题仍漏6/误2，不默认化。两版数据/排序保持，第二版8移目录隔离命令通过，无新增生成。 当前补证139条、87处建议编辑、62待证、72局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261027_093235.json)固定1414文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_026.json)；额度采样2026-10-27T01:32:34.554Z，5小时46.0%、周33.0%，不是财务余额。

- 2026-10-27 10:01接续：[本批说明](tonglun_reference_current89_20261027.md)。新增雪花莲和энергии两处提案，укроп仍因俗名歧义待证；累计89建议、79提案/60待证。出处、数据卡及139项空评阅包同步。新227保留旧225全记录，追加两单元4编辑、合61快照编辑，尚未评测。 当前补证139条、89处建议编辑、60待证、72局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261027_100145.json)固定1483文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_027.json)；额度采样2026-10-27T02:01:44.593Z，5小时79.0%、周38.0%，不是财务余额。

- 2026-10-27 10:10接续：[本批说明](tonglun_reference_thesis_preparation_20261027_001.md)。227已测：220→222、225→227旧150名次逐条不变，新两开发题目标均第1；范围外重叠仅3/8空，非独立正确率。论文方法底稿及3份CSV明确942名次记录中322新算/620沿用，专家与生成0。 当前补证139条、89处建议编辑、60待证、72局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261027_101042.json)固定1506文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_028.json)；额度采样2026-10-27T02:10:41.074Z，5小时87.0%、周39.0%，不是财务余额。

- 2026-10-27 10:21接续：[本批说明](tonglun_reference_checkpoint_validation_20261027.md)。当前89建议、227研究快照及论文方法底稿接续；两个书库顶部入口纠正陈旧当前值、历史保留。保存两个人工夹具本地示例及入口JSON原文。此前51级封存1681指纹、113MD/2316链接通过，新外层另实跑。 当前补证139条、89处建议编辑、60待证、72局部核实（重叠）；原139待核/127隔离、默认175不变。
- [新断点](../data/processed/tonglun_reference/evidence_checkpoint_20261027_102131.json)固定1530文件，[追加封存](../data/processed/tonglun_reference/reviews/delivery_addendum_20261026_029.json)；额度采样2026-10-27T02:21:30.426Z，5小时96.0%、周41.0%，不是财务余额。
