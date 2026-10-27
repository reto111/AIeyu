# 语法研究包：独立校验与页级引文（2026-10-22）

本轮继续完成本地校验、逐条引文审核和独立交付，没有新增DeepSeek请求。先前20次生成的原始响应、失败和评分均保持原样，不能把新提示词的本地重放当成新的生成结果。

当前独立包为[guarded_research_20261022_002](../data/processed/grammar_reference/research_exports/guarded_research_20261022_002/README.md)，共116个受指纹保护的文件。001保留为不含页定位入口的历史包。002包含原368节编校版、默认检索、可选candidate_v1、独立校验层、引句页定位及原20次实验资料；不含密钥、.env、学生库、原PDF或生成API执行器。

## 实际运行

在安装了依赖的Python环境中进入包目录，运行：

```powershell
python -I grammar_research.py verify
python -I grammar_research.py prepare "不定式是否有人称和体的区别？" --retriever candidate_v1 --output ../packet.json
python -I grammar_research.py check "不定式是否有人称和体的区别？" --packet ../packet.json --response ../response.json
python -I grammar_research.py locate --code morphology.075 --quote "|四格|同一格|同一格|同一格|" --output ../quote_pages.json
```

输出存到包外，已有文件不覆盖。引句以连字符开头时采用`--quote="-кть、-гть（-кти/-гти）"`形式，避免参数解析器把引句当选项。首次002验证曾因测试命令未使用等号形式而退出；修正测试调用后通过，包内容未改。无需配置DeepSeek密钥，命令不会调用生成。

参考依赖位于包内`edition/source_code/requirements-research.txt`。项目环境已实测；未在另一台未装依赖的电脑上安装验证，不能称为零依赖程序。

## 独立性和来源绑定

[002实际验证报告](../data/processed/grammar_reference/reviews/guarded_kit_verification_20261022_002.json)通过隔离Python运行，并通过审计钩子禁止项目源码、PDF、学生库读取及网络操作。116个文件全部通过指纹检查；候选检索、合法引用检查、提示词篡改拒绝、整附表排除、范围拒绝、重复引句定位及编校派生标记均实测通过。运行前后包指纹不变，没有缓存写入；真实密钥值扫描未发现密钥进入包。

新增校验层为[scripts/grammar_editorial_guard.py](../scripts/grammar_editorial_guard.py)。旧校验只验证来源正文和引用，替换提示词但保留正文仍会通过；本轮先复现该情况，再验证新层拒绝。新层将调用者提供的原问题、检索选项、范围规则、提示词、全部来源及元数据重新生成并逐字段比较，同时拒绝异常JSON结构、无引用主张和错误来源ID。默认旧入口和封存版未改，新层可单独使用。

`prepared`仅表示已找到候选来源；`allow`仅表示没有命中有限范围拦截规则。两者都不是资料充分性、语义正确性或专家批准。`unsupported_request`和`no_evidence`不提供生成提示词。

## 范围与旧结果重放

[范围验收](../data/processed/grammar_reference/rag/guard_acceptance_20261022_001.json)包含在实现、运行前冻结的24题（12条范围外和12条近邻语法题），全部符合预期；60条旧检索题的目标命中没有被新规则误拦。默认命中仍为开发集28/36、新表述9/17；candidate_v1仍为35/36、17/17。没有改写已有候选分数。

8条旧主题重叠范围外题中，7条不再准备提示词。剩余“把所有形容词长期转成名词的程序需要多少内存？”仍被放行；有限规则尚不能识别所有请求目标。没有据这条失败继续改规则并覆盖报告。24/24不是通用分类正确率，也不是独立盲评。

旧10份RAG响应本地重放：9份实质回答中6份通过，原3份引用失败继续失败；统计题P10会在请求准备阶段被范围规则挡住。未做任何追加生成、修复或重试。

## 引文支持逐条复核

[27条主张审核](../data/processed/grammar_reference/reviews/pilot_claim_review_20261022_001.json)保留原始主张、每处引句、前后120字符上下文、来源指纹、逐字性及阅读说明。14条现有引句能覆盖所述细节，12条需要更多上下文，1条没有引用。这是同一助手据来源逐条审阅，不是独立专家盲评；需补上下文不等于事实错误，也不重写原来的预设要点覆盖分数。

已另做[事后分层](../data/processed/grammar_reference/reviews/pilot_stratified_summary_20261022_001.json)：8道一般语法题要点有RAG21/21、对照12/21；1道本书特定题3/3与1/3；1道无统计依据题两组2/2。分层用于避免把“本书特定信息需要资料”的优势误归为一般语法能力提升，未宣称预注册或统计显著。

## 引句页级追踪

[scripts/grammar_quote_locator.py](../scripts/grammar_quote_locator.py)从已核页转录按字符保存页来源，重放编校编辑后再匹配逐字引句。新增字符继承被替换片段的来源页；插入点跨页时保留两页，不擅选一页。删除造成的新相邻文字即使没有新增字符，也不会被误判为原转录连续引句。

[全量页定位报告](../data/processed/grammar_reference/reviews/quote_locations_20261022_001.json)：368节、565855个去排版符号字符通过映射，2623个字符由替换或插入产生。字符数量不是编辑条数或错误数。39处实验引句37处可逐字定位，2处原格式/重音失败仍未匹配；3处涉及编校派生文字。唯一多位置引句“|四格|同一格|同一格|同一格|”在PDF165页两处、166页一处，完整保留3个位置。

定位结果区分`literal_transcription_span`和`editorial_derived_span`。字段`literal_in_original_at_this_span`中的original专指本库归档的原页转录，不是直接核验PDF字形、更不是规范正确性证明。原页转录中的图示说明、格式转写仍是转录表示。字符偏移也不是PDF图像坐标；编校文字页号是来源锚定，不能冒称原PDF逐字印有修订后的文字。

7项页定位测试覆盖原转录保留、编校插入、重复表行、重音/格式不匹配、删除造成的拼接、跨页来源锚定及隔离附表拒绝。校验层另10项测试、原实验5项保护测试均通过。本轮未新增需要用户裁定的书中疑点。

## 论文交接与下一步

[论文方法与结果底稿](grammar_reference_thesis_methods_20261022.md)已整理数据范围、原文与编校区别、配对设计、评分指标、分层结果、用量、失败案例及局限性，可以直接据此起草方法和实验章节。它不是已完成的正式论文，也未包含独立专家评价。

当前数据库工程、指定20次试验、本地独立运行和页级引文追踪均有可检查结果。尚需独立俄语专业评分、按研究设计扩大样本，以及候选检索在新提示词下的生成评价；新增外部生成仍需另定数量范围。实时Codex余额不可读取，不能把本次保存断点解释为余额已耗尽。
