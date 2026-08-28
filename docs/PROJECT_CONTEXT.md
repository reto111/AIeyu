# AI Russian Tutor Project Context

### Latest checkpoint: TEM4 pending vocabulary LLM review batch 11 (2026-08-28)

- The eleventh pending batch was reviewed directly with the assistant model. Russian headwords were corrected per word, actual `ё` was preserved, and incorrect OCR marks were changed to `е` only where required.
- Cross-page continuations, fixed phrases, and false word heads were rejected, including fragments around `здание`, `здесь`, `знакомый`, `зрение`, `изба`, `известно`, `извинить`, and `издавать`. The preposition `из` and the reconstructable noun `дядя` were retained as proper entries in earlier boundaries.
- Review sheet status after this batch: `approved` = 1031, `rejected` = 136, `needs_review` = 1, `pending` = 2756. The only unresolved manual-review coordinate remains `p154/b2`.
- Formal vocabulary counts after import: `TEM4_RU/TEM4` = 1030 unique words; `TEM8_RU/TEM8` = 3513. The review sheet has 1031 approved rows because one approved row duplicates an existing word and is updated. Import reported `inserted` = 87, `updated` = 944, `invalid_approved` = 0, and `skipped` = 0.
- Review-sheet backup: `data/processed/words/tem4_words_review_simple_before_pending_batch11_20260828_205701.csv`.
- Database backup: `data/processed/backups/russian_ai_tutor_before_tem4_pending_batch11_20260828_205811.sqlite`.
- Approved-meaning audit found zero Cyrillic characters in Chinese meanings.

### Latest checkpoint: TEM4 pending vocabulary LLM review batch 10 (2026-08-28)

- The tenth pending batch was reviewed directly with the assistant model. Headwords were corrected per word, actual `ё` was preserved, and incorrect OCR marks were changed to `е` only where required by Russian spelling.
- A post-apply coordinate audit caught and corrected a real alignment error: `затём` was not an independent row, so its meaning had shifted onto `затылок`, `захватчик`, and `захватывать`. The corrected rows now contain their own meanings, and the nonexistent `p97/b13` decision was removed. This correction was applied before database import.
- Other continuation fragments were rejected around `задавать`, `задерживать`, `закалять`, `заключать`, `закрытый`, `замечание`, `замечать`, `заниматься`, `запах`, `запоминать`, and `захватывать`.
- Review sheet status after this batch: `approved` = 944, `rejected` = 123, `needs_review` = 1, `pending` = 2856. The only unresolved manual-review coordinate remains `p154/b2`; it was intentionally removed per the user's decision.
- Formal vocabulary counts after import: `TEM4_RU/TEM4` = 943 unique words; `TEM8_RU/TEM8` = 3513. The review sheet has 944 approved rows because one approved row duplicates an existing word and is updated. Import reported `inserted` = 89, `updated` = 855, `invalid_approved` = 0, and `skipped` = 0.
- Review-sheet backup: `data/processed/words/tem4_words_review_simple_before_pending_batch10_20260828_204952.csv`.
- Database backup: `data/processed/backups/russian_ai_tutor_before_tem4_pending_batch10_20260828_205201.sqlite`.
- Approved-meaning audit found zero Cyrillic characters in Chinese meanings; the remaining `not_found` report entry is the intentionally removed `p154/b2` coordinate.

### Latest checkpoint: TEM4 pending vocabulary LLM review batch 9 (2026-08-28)

- The ninth pending batch was reviewed directly with the assistant model. Headwords were corrected per word, actual `ё` was preserved, and incorrect OCR marks were changed to `е` only where required by the Russian spelling.
- Cross-page continuations, fixed phrases, and duplicate fragments were rejected, including fragments around `дружить`, `дядя`, `есть`, `доказывать`, `жарить`, `жечь`, `живой`, `журналист`, `заботливый`, `завёртывать`, and `завтра`.
- Review sheet status after this batch: `approved` = 855, `rejected` = 112, `needs_review` = 1, `pending` = 2956. The unresolved manual-review coordinate remains `p143/b6`; `p154/b2` was intentionally removed per the user's decision.
- Formal vocabulary counts after import: `TEM4_RU/TEM4` = 854 unique words; `TEM8_RU/TEM8` = 3513. The review sheet has 855 approved rows because one approved row duplicates an existing word and is updated. Import reported `inserted` = 90, `updated` = 765, `invalid_approved` = 0, and `skipped` = 0.
- Review-sheet backup: `data/processed/words/tem4_words_review_simple_before_pending_batch9_20260828_204330.csv`.
- Database backup: `data/processed/backups/russian_ai_tutor_before_tem4_pending_batch9_20260828_204431.sqlite`.
- Approved-meaning audit found zero Cyrillic characters in Chinese meanings.

### Latest checkpoint: TEM4 pending vocabulary LLM review batch 8 (2026-08-28)

- The eighth pending batch was reviewed directly with the assistant model. Headwords were corrected per word, actual `ё` was preserved, and incorrect OCR marks were changed to `е` only where the word required it.
- Cross-page continuations, fixed-phrase fragments, and duplicate forms were rejected, including fragments around `дети`, `дисциплина`, `дневник`, `доверие`, `доклад`, `доска`, `доставать`, `доходить`, `дочка`, and `дожидаться`.
- One omitted boundary row (`p79/b4`, `доставлять`) was caught by the post-apply pending audit and added before import.
- Review sheet status after this batch: `approved` = 765, `rejected` = 102, `needs_review` = 1, `pending` = 3056. The unresolved manual-review coordinate remains `p143/b6`; `p154/b2` was intentionally removed per the user's decision.
- Formal vocabulary counts after import: `TEM4_RU/TEM4` = 764 unique words; `TEM8_RU/TEM8` = 3513. The review sheet has 765 approved rows because one approved row duplicates an existing word and is updated. Import reported `inserted` = 90, `updated` = 675, `invalid_approved` = 0, and `skipped` = 0.
- Review-sheet backup: `data/processed/words/tem4_words_review_simple_before_pending_batch8_20260828_203645.csv`.
- Database backup: `data/processed/backups/russian_ai_tutor_before_tem4_pending_batch8_20260828_203645.sqlite`.
- Approved-meaning audit found zero Cyrillic characters in Chinese meanings.

### Latest checkpoint: TEM4 pending vocabulary LLM review batch 7 (2026-08-28)

- The seventh pending batch was reviewed directly with the assistant model. Word forms were corrected per word, with real `ё` retained and incorrect OCR marks changed to `е`.
- Cross-page continuations, fixed phrases, and duplicate fragments were rejected, including fragments around `гриб`, `давать`, `даваться`, `двигаться`, `голос`, `гореть`, `дело`, and `дедушка`.
- Review sheet status after this batch: `approved` = 675, `rejected` = 92, `needs_review` = 1, `pending` = 3156. The unresolved manual-review coordinate remains `p143/b6`; `p154/b2` was intentionally removed per the user's decision.
- Formal vocabulary counts after import: `TEM4_RU/TEM4` = 674 unique words; `TEM8_RU/TEM8` = 3513. The review sheet has 675 approved rows because one approved row duplicates an existing word and is updated. Import reported `inserted` = 90, `updated` = 585, `invalid_approved` = 0, and `skipped` = 0.
- Review-sheet backup: `data/processed/words/tem4_words_review_simple_before_pending_batch7_20260828_203029.csv`.
- Database backup: `data/processed/backups/russian_ai_tutor_before_tem4_pending_batch7_20260828_203122.sqlite`.
- Approved-meaning audit again found zero Cyrillic characters in Chinese meanings.

### Latest checkpoint: TEM4 pending vocabulary LLM review batch 6 (2026-08-28)

- The sixth pending batch was reviewed directly with the assistant model. Headwords were corrected per word, with real `ё` retained and incorrect OCR `ё` marks changed to `е`.
- Cross-page continuations and layout fragments were rejected, including fragments around `вытирать`, `выходить`, `гибель`, `глотать`, `голос`, and `гореть`. Duplicate `год` entries were merged into one core entry.
- Review sheet status after this batch: `approved` = 584, `rejected` = 83, `needs_review` = 1, `pending` = 3256. The unresolved manual-review coordinate remains `p143/b6`; `p154/b2` was intentionally removed per the user's decision.
- Formal vocabulary counts after import: `TEM4_RU/TEM4` = 584; `TEM8_RU/TEM8` = 3513. Import reported `inserted` = 91, `updated` = 493, `invalid_approved` = 0, and `skipped` = 0.
- Review-sheet backup: `data/processed/words/tem4_words_review_simple_before_pending_batch6_20260828_202500.csv`.
- Database backup: `data/processed/backups/russian_ai_tutor_before_tem4_pending_batch6_20260828_202552.sqlite`.
- A post-batch audit found zero approved meanings containing Cyrillic characters or retained OCR example text.

### Latest checkpoint: TEM4 pending vocabulary LLM review batch 5 (2026-08-28)

- The fifth pending batch was reviewed directly with the assistant model. Incorrect OCR headwords were corrected per word, and actual `ё` was retained only where it belongs; incorrect `ё` marks were changed to `е`.
- Continuation fragments and layout noise were rejected, including the fixed phrase fragments around `вручать`, `выгонять`, `выдавать`, `вызывать`, `выразительный`, and `вопрос`. Complete entries were rebuilt with Chinese core meanings only.
- Review sheet status after this batch: `approved` = 493, `rejected` = 74, `needs_review` = 1, `pending` = 3356. The unresolved manual-review coordinate remains `p143/b6`; `p154/b2` was intentionally removed per the user's decision.
- Formal vocabulary counts after import: `TEM4_RU/TEM4` = 493; `TEM8_RU/TEM8` = 3513. Import reported `inserted` = 92, `updated` = 401, `invalid_approved` = 0, and `skipped` = 0.
- Review-sheet backup: `data/processed/words/tem4_words_review_simple_before_pending_batch5_20260828_201836.csv`.
- Database backup: `data/processed/backups/russian_ai_tutor_before_tem4_pending_batch5_20260828_201836.sqlite`.
- Three earlier approved meanings with OCR/example contamination were also trimmed to Chinese core meanings: `коренной`, `лишать`, and `танец`.

### Latest checkpoint: TEM4 pending vocabulary LLM review batch 4 (2026-08-28)

- The fourth pending batch was reviewed directly with the assistant model. OCR headwords were corrected only when supported by the source shape and meaning; actual `ё` was retained, while incorrect OCR/stress marks were corrected per word.
- Cross-page continuations and fixed-phrase fragments were rejected. In particular, the continuation blocks for `виноватый`, `власть`, `вопрос`, and `возможный` were not imported as duplicate words; their complete entries were reconstructed or retained at the preceding coordinate.
- Review sheet status after this batch: `approved` = 401, `rejected` = 66, `needs_review` = 1, `pending` = 3456. The unresolved manual-review coordinate remains `p143/b6`; `p154/b2` was intentionally removed per the user's decision.
- Formal vocabulary counts after import: `TEM4_RU/TEM4` = 401; `TEM8_RU/TEM8` = 3513. Import dry-run and formal import both reported `invalid_approved` = 0 and `skipped` = 0.
- Review-sheet backup: `data/processed/words/tem4_words_review_simple_before_pending_batch4_20260828_201244.csv`.
- Database backup: `data/processed/backups/russian_ai_tutor_before_tem4_pending_batch4_20260828_201346.sqlite`.

### Latest checkpoint: TEM4 pending vocabulary LLM review batch 3 (2026-08-28)

- The third pending batch was reviewed directly with the assistant model. OCR headwords were corrected only when the Russian shape and Chinese meaning supported the correction; true `ё` was preserved, while stress/OCR artifacts were changed to `е` per word.
- Layout fragments, page continuations, duplicate entries, and unusable OCR blocks were rejected. A cross-page continuation at `p35/b1` was rejected; the complete `видеться` entry at `p35/b3` was retained.
- Review sheet status after this batch: `approved` = 305, `rejected` = 62, `needs_review` = 1, `pending` = 3556. The single unresolved coordinate remains `p143/b6`; `p154/b2` was intentionally removed per the user's decision.
- Formal vocabulary counts after import: `TEM4_RU/TEM4` = 305; `TEM8_RU/TEM8` = 3513. Import dry-run and formal import both reported `invalid_approved` = 0 and `skipped` = 0.
- Review-sheet backup: `data/processed/words/tem4_words_review_simple_before_pending_batch3_20260828_200430.csv`.
- Database backup: `data/processed/backups/russian_ai_tutor_before_tem4_pending_batch3_20260828_200523.sqlite`.
- Coordinate corrections for `p21/b6` and `p21/b7` were re-applied in this batch so `большевик` means “布尔什维克” and `большинство` means “多数；大多数”.

### Latest checkpoint: TEM4 vocabulary import and exam isolation (2026-08-28)

### Latest checkpoint: TEM4 pending vocabulary LLM review batches 1-2 (2026-08-28)

- The first 200 pending OCR blocks were reviewed directly with the assistant model. Clear headwords and meanings were corrected, while layout fragments and example continuations were rejected.
- Review sheet status after these batches: `approved` = 219, `rejected` = 49, `needs_review` = 1, `pending` = 3655.
- Formal TEM4 vocabulary import now contains 219 rows. The second import added 84 rows and updated 135 existing same-word entries; the import safety gate skipped 0 rows.
- Review-sheet backups: `data/processed/words/tem4_words_review_simple_before_pending_batch1_20260828_195224.csv` and `data/processed/words/tem4_words_review_simple_before_pending_batch2_20260828_195628.csv`.
- Database backups: `data/processed/backups/russian_ai_tutor_before_tem4_pending_batch1_20260828_195256.sqlite` and `data/processed/backups/russian_ai_tutor_before_tem4_pending_batch2_20260828_195641.sqlite`.
- Continue the same rule: do not import remaining pending rows without checking word shape, `е/ё`, source-block alignment, part of speech, and Chinese meaning consistency.

- 43 approved TEM4 vocabulary rows have been imported into the formal vocabulary database. Pending, needs_review, and rejected rows were not imported.
- Import backup: `data/processed/backups/russian_ai_tutor_before_tem4_vocab_import_20260828_183735.sqlite`.
- Formal vocabulary counts: `TEM4_RU/TEM4` = 43; `TEM8_RU/TEM8` = 3513. TEM8 data was unchanged.
- Student word status, review pool, session, and review APIs now filter by `exam_system + level`, keeping TEM4 and TEM8 words, progress, review pools, and check-in records separate.
- The word page displays the active exam level and reloads its vocabulary and review statistics after switching exams.
- Read-only smoke test: TEM4 session returned only TEM4 words; TEM8 session returned only TEM8 words. Python and JavaScript syntax checks passed.

> 本文档用于记录项目共识、已确认标准、待确认问题和后续开发约束。
> 后续设计、编码、数据库建模、提示词编写、版本规划，都应优先参考本文档，避免遗漏、误解或凭空假设。

## 1. 项目定位

项目方向：面向小语种考试的个人 AI 自适应备考助手。

核心定义：

```text
一款面向小语种考试的 AI 自适应备考工具，根据用户在目标考试中的真实作答表现建立能力画像，识别薄弱题型与知识点，并结合题库、RAG 和 AI 生成，持续提供个性化、不重复的专项训练。
```

第一阶段仍以“俄语专八”为基础，验证个人画像、题库组卷、自动判分、AI 错题解析、题型掌握度、弱项专项训练、AI 生成题和质检基础链路。

第一阶段以“俄语专八”为基础，后续需要能够扩展并接入其他俄语考试或等级体系，例如：

- 俄语专业四级
- TORFL / ТРКИ
- A1 / A2 / B1 / B2 / C1 / C2
- 其他自定义考试体系

项目当前主要服务对象：

- 用户本人
- 面向学生群体的备考复习用户
- 后续如效果合适，可扩展为商业化产品

产品气质倾向：

- 更像“私人俄语老师”
- 不只是考试系统
- 需要能解释、追问、补弱、陪练
- 用户做错题后，应能直接和 AI 大模型继续对话，问清楚不懂的地方

## 2. 第一版范围

第一版先聚焦俄语专八。

第一版优先题型：

- 选择题：语法
- 选择题：文学
- 选择题：国情
- 阅读理解题
- 听力理解题，已开始接入音频资产和转写链路

第一版核心闭环：

1. 导入俄语专八真题 PDF
2. 抽取并校对真题结构
3. 标注题型、知识点、答案和来源年份
4. 将审核后的历年真题和 AI 仿真题共同作为练习池
5. 用户选择题型和数量
6. 系统随机或按知识点组卷
7. 用户作答
8. 系统自动批改
9. AI 用中文分析错题集中在哪些知识点
10. AI 给出解决方案、题目讲解和巩固练习
11. 用户可以在对话窗口继续追问

暂不优先纳入第一版的功能：

- 听力题
- 写作题
- 口语题
- 完整商业支付系统
- 多学校/多机构复杂管理
- 大规模公开上线

这些功能需要在后续版本预留扩展空间。

## 3. 内容来源与审核原则

用户可以提供俄语专八 PDF 真题。

PDF 资料可能包括：

- 真题题干
- 选项
- 阅读文章
- 答案
- 解析，若原始材料中存在

需要注意：

- PDF 可能是可复制文字版，也可能是扫描图片版；是否需要 OCR 待确认。
- PDF 解析结果必须支持人工校对，因为俄文、选项编号、阅读题排版和答案对应关系容易解析错误。
- 如果后续商业推广，需要特别注意真题版权与使用范围。
- AI 生成题目在后续商业化阶段需要人工审核后再进入正式题库。
- 历年真题可以用于学生组卷和直接练习，但必须在题目展示、解析和记录中明确标注来源，例如“2019 年俄语专八真题”。
- AI 仿真题可以作为补充题源，需经过人工审核后进入练习池。

AI 生成题目的推荐状态设计：

- `draft`: AI 生成草稿
- `review_pending`: 待人工审核
- `approved`: 已审核可正式使用
- `rejected`: 已拒绝
- `practice_only`: 可临时练习，但不作为正式题库

历年真题题目的推荐标记：

- `content_origin = past_exam_original`: 历年真题原题
- `source_label`: 来源标签，例如“2019 年俄语专八真题”
- `requires_source_label = true`: 前端展示时必须显示来源
- `review_status = approved`: 审核后可进入组卷

## 4. 语言与讲解标准

默认输出语言：

- 中文讲解为主
- 俄语例句和题目内容保留俄语

讲解风格：

- 像私人老师一样解释
- 不只告诉答案，还要解释为什么其他选项不对
- 不要只输出“你选了什么、正确答案是什么”
- 对语法题要指出具体语法点、易错点、解题步骤和选项逐项辨析
- 词义辨析题要说明每个选项的词义、搭配、使用场景，并在必要且可靠时只整理少量同根词或派生词；不确定时说明需要词典或资料核验
- 文学题要介绍作品、作者、时期、流派或文学背景；如果选项包含多个作家，要列出各作家的代表作品
- 国情题要补充历史、地理、政治制度、文化常识、社会背景或中俄名称对应
- 对阅读题要指出原文依据、定位句、干扰项逻辑
- 对学生反复出错的点，要给出复习路径和巩固练习
- 逐题解析要精简，不输出“记忆与复习提示”和“同类巩固练习”；整体 AI 区也不输出“巩固练习安排”，专项训练由系统单独生成

## 5. 数据与架构原则

核心原则：结构化题库为主，RAG 为辅助。

用户画像原则：

- 用户画像必须由结构化作答数据计算，不应让大模型凭感觉判断。
- 用户画像必须按学生账号隔离；新建学生不应继承默认学生或其他学生的历史作答。
- LLM 只负责解释画像结果、生成复习建议和辅助出题。
- 第一版使用规则统计算法，不上复杂机器学习。
- 掌握度以最近 20 次相关作答的加权正确率为基础。
- 时间权重：3 天内 `1.0`，7 天内 `0.7`，10 天内 `0.4`，更早 `0.2`。
- 做题数少于 5 道时标记为“数据不足”。
- 最近连续错 2 次以上时，掌握状态降一级。
- 每个题型和知识点输出 `weak`、`unstable`、`stable`、`strong`、`insufficient_data`。
- 弱项优先级综合错误率、最近错误和连续错误。
- 弱项优先级公式：`错误率 * 50 + 最近错误权重 * 30 + 连续错误权重 * 20`。
- 不重复训练应记录 `question_exposures`，优先抽未做题，其次旧错题，最后才复用近期做对题。
- 弱项专项训练不足题时，先放宽到同父级知识点或同题型，再触发 AI 生成题草稿。

不应把题库主要建成 RAG。

题库、答案、题型、等级、知识点、测试记录、错题统计等应进入结构化数据库，以便：

- 随机组卷
- 按知识点组卷
- 自动批改
- 统计正确率
- 追踪学生学习历史
- 支持个人学习画像和长期备考数据分析

### 5.1 题库质量审计约定

2026-08-23 对俄语专八结构化题库做过一次系统质量审计，主要问题来源如下：

- OCR 将俄文字母、拉丁字母、罗马数字和页脚混淆，例如 `ХУ`/`XV`、`TOM`/`том`。
- 作者缩写或姓名缩写被切题规则误识别为选项编号，例如 `В.Г. Распутин` 被误切成 B 选项。
- PDF 页脚、页码、栏目标题进入选项，例如 `ЛИТЕРАТУРА`、`СТРАНОВЕДЕНИЕ`、年份页脚。
- 原题中的填空位置在抽取后丢失，前端展示时学生不知道选项应放在何处。
- 断行连字符和扫描版排版导致题干不完整。
- 阅读题风险更高，因为一篇文章和多道题绑定；如果阅读题干或选项损坏，应优先下架复核，不应硬猜。

当前处理原则：

- 能从原始 OCR 残片、正确答案、固定俄语搭配和题目常识高置信复原的，允许本地修正。
- 无法可靠复原的历年真题不删除，改为 `review_status = needs_review` 且 `source_usage = source_reference_only`，临时移出学生练习池。
- 学生练习池默认只抽 `review_status = approved` 且 `source_usage = practice` 的题。
- 审计脚本应以学生可见的题干和选项为主，原始 `raw_text` 只做追溯，不直接作为展示错误。
- 人工复核表必须包含所有已下架的历年真题疑难项，避免“规则不再报错但仍需人工看原 PDF”的题漏掉。

相关脚本与输出：

- `scripts/audit_question_bank_quality.py`：扫描题干、选项、阅读文章长度和常见 OCR/切分风险。
- `scripts/apply_question_quality_fixes.py`：应用高置信题库修正，并自动备份数据库。
- `scripts/export_question_quality_review_context.py`：导出带完整题干、选项和人工复核字段的复核表。
- `scripts/import_question_quality_manual_review.py`：导入人工修正后的复核表，导入前会校验题干、选项、答案和残留 OCR 噪声。
- `data/processed/question_quality/question_quality_audit.csv`：完整审计明细。
- `data/processed/question_quality/question_quality_manual_review_context.csv`：最终人工复核工作表。
- `data/processed/question_quality/question_quality_auto_fixes.csv`：自动修正记录。

2026-08-23 用户完成人工复核表后，已通过校验导入 13 道历年真题疑难项。导入后历年真题练习池恢复为 300 道 `approved + practice`，人工复核清单为 0。

### 5.2 OCR 前水印预处理约定

已确认部分 PDF 存在“沙拉俄语”斜向灰色水印，水印会干扰 OCR 和题目切分。2024 年扫描版还存在底部浅色社交平台水印。这类水印多数已经嵌入页面图像，不适合直接从 PDF 文字层删除。

当前采用的稳定方案：

- 原始 PDF 保留不动。
- OCR 前先将 PDF 页面渲染成图片。
- 使用黑白二值化保留黑色正文、抹掉浅灰水印。
- 默认阈值为 `100`，不做自动对比度增强，避免把灰色水印压黑。
- 对底部右侧浅色平台水印，默认擦除页面右下角非正文区域。
- 生成的新文件只作为 OCR/切分输入，不作为原始资料替代。

相关脚本与输出：

- `scripts/preprocess_pdf_for_ocr.py`：生成去水印/二值化 OCR 清洁版 PDF。
- `data/processed/ocr_clean_pdfs/`：批量生成的 OCR 清洁版 PDF。
- 后续若重新 OCR 或重新切题，应优先使用 `ocr_clean_pdfs` 中的文件，而不是直接使用 `data/raw_pdfs`。

RAG 更适合用于：

- 语法讲解
- 文学与国情背景资料问答
- 考试大纲检索
- 教材、讲义、解析资料引用
- 学生在对话窗口追问时提供依据

推荐组合：

- 结构化数据库：历年真题、仿真题、答案、选项、知识点、来源标签、用户记录、测试记录、错题本
- 出题依据库 / RAG：教材、讲义、考试大纲、文学国情资料、解析文档；当前先使用本地 `knowledge_sources` / `knowledge_chunks` 做轻量检索
- 大模型：讲解、错因分析、生成巩固练习、对话答疑

当前学生账号阶段约定：

- 第一版使用本地学生账号分离，用于本人和班级小范围试用。
- 当前账号只是学习记录隔离，不是正式登录认证系统。
- `users` 表保存学生标识，`quiz_sessions`、`user_answers`、`question_exposures`、`weakness_snapshots`、`ai_tutor_threads` 等学习数据按 `user_id` 分离。
- 旧版没有 `user_id` 的历史记录统一归入默认学生，不能归入新建学生。
- 后续公开测试或商业化时，需要升级为真实登录、密码或验证码、会话管理、权限校验和隐私合规。

错题本阶段约定：

- 错题本不单独复制题目内容，而是基于当前学生的 `question_exposures` 和 `user_answers` 动态生成。
- 曾经答错过的题进入错题本。
- 最近一次仍答错或未订正时标记为“待巩固”，最近一次答对时标记为“已订正”。
- 错题本第一版展示题干、题型、来源、最近答案、正确答案、累计做题次数和错误次数。
- 后续可增加按题型/知识点筛选、错题笔记、收藏、AI 复盘和错题重练。

单词打卡阶段约定：

- 单词打卡是独立学习模块，但必须和现有学生账号体系打通。
- 当前词库来源目录为 `data/words`。
- 当前已放入 `data/words/tem8_russian_words.pdf`。
- 该 PDF 共 292 页，抽样检测前 10 页均无可直接提取的文本层，因此按扫描版 PDF 处理。
- 单词库应进入结构化数据库，不应只作为 RAG 文档。
- 单词学习记录必须按 `user_id` 隔离。
- 第一版单词功能目标：建立俄语专八单词库、每日打卡、认识程度记录、简单复习计划。
- 第一版认识程度建议：`不认识`、`模糊`、`认识`、`已掌握`。
- 第一版复习间隔建议：不认识次日复习，模糊 2 天后复习，认识 4 天后复习，已掌握 10 天后复习。
- `data/processed/words/tem8_words_local_correction_candidates.csv` 已由本地模型辅助校对并经用户确认。
- 已生成正式入库表 `data/processed/words/tem8_words_approved_import.csv`。
- 当前 `vocabulary_items` 已按保守策略正式导入 753 条，全部来自用户确认过的修正候选；未逐条人工审核的简化主表不得直接标记为 `approved`。
- 2026-08-22 整体检查发现简化主表仍有明显 OCR 错词，例如把 `абажур` 识成 `абаж`、把 `абрикос` 识成 `абрикбс`。因此正式库采用保守策略：先导入已确认修正候选，主表另行审核后再扩充。
- 2026-08-22 已继续审核简化主表 OCR 错词：主表 3199 条中，2580 条无明显词形风险，603 条生成修正建议，16 条建议删除或拆分，0 条仍悬空待复核。修正草稿为 `data/processed/words/tem8_words_review_simple_corrected_draft.csv`。
- 2026-08-22 已继续用大模型语言能力复核 OCR 修正建议：生成 `data/processed/words/tem8_words_llm_corrected_candidates.csv`，其中 `llm_approved` 579 条、`llm_rejected` 36 条、`llm_needs_review` 3 条。大模型建议仍不得直接等同于正式入库审核，应经用户确认或抽查后再转为 `approved`。
- 2026-08-22 已对剩余 `not_checked` 2581 条做分层审核：`clean_candidate` 2186 条、`needs_llm_review` 322 条、`reject_candidate` 73 条，并生成固定抽查样本 `data/processed/words/tem8_words_not_checked_clean_sample_150.csv`。本轮发现并记录错误：不能只凭词头字符干净就批量通过；`бактёрия`、`банкродство`、`батальбн`、`библог` 等已从 clean 移入复核。
- `ё/e` 标准：不做全量替换；只修正 OCR 把普通 `е` 误识为 `ё` 的项目；真实 `ё` 保留，例如 `актёр`、`свёкла`、`решётка`、`ягнёнок`。
- 详细流程见 `docs/word_checkin_plan.md`。

## 6. 可扩展考试体系设计

从第一版开始，数据结构必须预留多考试体系扩展能力。

基本层级：

```text
ExamSystem
  -> Level
    -> Section / QuestionType
      -> KnowledgePoint
        -> Question
```

示例：

```text
俄语专八
  -> 专八
    -> 语法选择题
      -> 动词体
      -> 格变化
      -> 运动动词

TORFL
  -> B1
    -> Grammar
    -> Reading
```

每道题至少应包含：

- 所属考试体系
- 所属等级
- 题型
- 题干
- 选项
- 正确答案
- 解析
- 知识点标签
- 难度
- 来源
- 年份，若可识别
- 审核状态

## 7. Agent 功能边界

Agent 应负责：

- 理解用户训练目标
- 调用题库生成测试
- 批改结果
- 分析薄弱知识点
- 生成中文讲解
- 生成针对性巩固练习
- 在对话窗口回答学生追问
- 更新用户学习画像

Agent 不应无约束地凭空生成正式题库。

正式题库应优先来自：

- 审核后的历年真题
- 审核后的 AI 仿真题
- 经过校验的数据

历年真题进入学生组卷池时必须保留并展示来源年份。

## 8. 用户场景

当前使用目标：

- 个人自学
- 面向学生群体的备考复习

后续应预留：

- 学生账号或个人用户账号
- 个人学习档案
- 测试分发
- 学生测试记录
- 个人薄弱知识点统计
- 个人学习报告导出
- 内容审核和运营后台

仍需确认：

- 第一版是否需要登录系统
- 学生是否需要独立账号
- 是否需要分享测试链接
- 是否需要个人维度的数据看板

## 9. 建议版本路线

### V0.1 原型版

- 只支持俄语专八
- 支持语法、文学、国情选择题
- 支持阅读理解选择题
- 支持 PDF 导入后的人工整理
- 支持随机组卷
- 支持自动批改
- 支持中文错因分析

### V0.2 私教对话版

- 增加题目讲解对话窗口
- 支持针对单题追问
- 支持针对知识点追问
- 支持根据错题生成巩固练习
- 建立个人错题本

### V0.3 学生账户与学习报告版

- 学生账号或个人用户账号
- 个人测试记录
- 个人薄弱知识点统计
- 错题本和复习计划
- 基础学习报告

### V0.4 多考试扩展版

- 接入俄语专四
- 接入 TORFL / ТРКИ
- 支持不同考试体系的题型和知识点树
- 支持考试体系配置

### V0.5 商业准备版

- AI 生成题人工审核后台
- 内容版权管理
- 支付或订阅能力
- 权限系统
- 数据看板
- 部署上线

## 10. 初步技术方向

技术选型尚未最终确定。

目前建议方向：

- 前端：React / Next.js
- 后端：FastAPI 或 Node.js
- 数据库：开发早期可用 SQLite，后续商业化建议 PostgreSQL
- 向量库：pgvector、Qdrant 或 Chroma
- PDF 解析：根据 PDF 类型决定是否需要 OCR
- AI 能力：用于讲解、错因分析、对话、生成巩固题

开发要求：

- 从一开始建立版本控制
- 保留清晰目录结构
- 重要产品决策写入文档
- 不把临时实验和核心业务逻辑混在一起
- 数据模型要为多考试、多题型、多用户和后续运营审核能力预留空间

## 11. 建议项目目录

初步目录建议：

```text
russian-ai-tutor/
  apps/
    web/
    api/
  packages/
    core/
    ai/
    importer/
  data/
    raw_pdfs/
    processed/
  docs/
    PROJECT_CONTEXT.md
    product_plan.md
    knowledge_taxonomy.md
    database_schema.md
  prompts/
    analysis/
    generation/
    tutoring/
  tests/
```

目录是否采用 monorepo 结构，待正式选型时确认。

## 12. 已确认事项

- 第一阶段面向俄语专八。
- 后续要支持接入其他俄语考试和等级。
- 第一版题型包括选择题中的语法、文学、国情，以及阅读题。
- 用户可以提供 PDF 真题。
- 当前面向学生群体用户的备考复习学习场景，不需要教师端。
- 若效果合适，后续考虑商业推广。
- 输出语言以中文讲解为主。
- 后续推广时，AI 生成题目需要人工审核。
- 产品更像私人俄语老师，而不是单纯考试系统。
- 需要对话窗口，让用户能针对题目和知识点继续问 AI。
- 需要做好版本控制。
- 需要预留后续接入更多功能的空间。
- GitHub 插件已经安装请求确认，可用于后续 GitHub 项目辅助；具体可用能力以后续连接状态为准。
- 历年真题可用于组卷，但如果出现原题，必须标注来源年份和真题来源。

## 13. 待确认问题

以下问题需要用户后续明确：

1. 俄语专八 PDF 是扫描版图片，还是可复制文字版？
2. PDF 真题是否包含标准答案？
3. PDF 真题是否包含官方或现成解析？
4. 第一版希望做网页应用，还是本地可运行原型？
5. 第一版是否需要用户登录？
6. 学生是否需要独立账号？
7. 是否需要测试链接分享能力？
8. 是否已有俄语专八知识点分类表？
9. 是否需要我先建立一版俄语专八知识点树？
10. 真题资料的版权和商业使用边界是否已明确？
11. 首批准备用多少套真题进入题库？
12. 是否希望保留原题出处，如年份、题号、试卷名称？
13. 阅读题是否需要保留原文全文，并支持原文定位讲解？
14. 后续 AI 模型希望使用 OpenAI、国内模型，还是可配置多模型？
15. 是否需要部署到公网供学生访问，还是先在本地/局域网试用？

## 14. 候选外部项目评估

### RAGFlow

仓库地址：https://github.com/infiniflow/ragflow

初步判断：

- 可以用于建立项目的 RAG 知识库。
- 更适合作为“知识库服务”接入本项目，而不是替代本项目的题库、组卷、批改和学生学习画像系统。
- 适合承载教材、讲义、考试大纲、文学国情资料、真题解析等非结构化资料。
- 可用于支持 AI 私教对话窗口中的资料检索、引用依据、讲解溯源和降低幻觉。

适合本项目的用途：

- 上传俄语专八 PDF、讲义、解析文档，建立可检索知识库。
- 为语法、文学、国情、阅读讲解提供参考资料。
- 在学生追问时检索相关段落，再由大模型用中文解释。
- 帮助处理复杂 PDF、扫描件和多格式文档，但实际效果仍需用用户提供的专八 PDF 测试。

不建议用于替代：

- 结构化题库
- 题目选项与答案管理
- 随机组卷逻辑
- 自动批改逻辑
- 错题统计
- 用户学习数据
- 人工审核流程

原因：

- 本项目需要精确记录题目、答案、知识点、来源年份、审核状态和学生答题记录，这些应由结构化数据库负责。
- RAGFlow 是较完整、较重的 RAG 平台，部署依赖较多，适合作为独立服务集成。
- 早期不建议直接 fork 并深度改造 RAGFlow 作为主项目底座，除非后续确认团队能长期维护其复杂架构。

推荐集成方式：

```text
俄语专八 AI 私教应用
  -> 结构化题库数据库：题目、答案、测试、错题、学生画像
  -> RAGFlow：教材、讲义、考纲、解析、文学国情资料检索
  -> 大模型：中文讲解、错因分析、追问答疑、巩固练习生成
```

推荐阶段：

- V0.1 可先保留 RAGFlow 作为候选方案，不强依赖。
- V0.2 私教对话版开始做 RAGFlow 接入验证。
- 在接入前，用用户提供的 1-2 份俄语专八 PDF 测试解析质量、俄文识别、切片效果和引用准确性。

## 15. 项目文档索引

- `docs/PROJECT_CONTEXT.md`: 项目共识、已确认标准、重要注意事项、候选方案评估。
- `docs/product_requirements.md`: 产品需求文档，记录目标用户、功能范围、核心流程、验收标准和版本边界。
- `docs/database_schema.md`: 数据库设计说明，记录建库原则、表结构说明、PDF 导入流程和当前真题批次。
- `docs/segmentation_rules.md`: 题目切分规则，记录专八文本到待审核 JSON 的切分策略。
- `docs/knowledge_taxonomy.md`: 俄语专八第一版知识点树，用于题目打标、错题分析和巩固练习生成。
- `docs/review_workflow.md`: 待审核题目导出、人工校对、知识点标注和审核结论规则。
- `docs/quiz_generation.md`: 专八练习卷生成脚本规则，记录审核状态、来源标签和内部测试模式。
- `docs/grading_workflow.md`: 答题模板、批改、错题统计、薄弱点快照和入库流程。
- `docs/remediation_workflow.md`: 批改后的中文复习建议、薄弱点巩固练习包生成流程。
- `docs/tutoring_prompt_workflow.md`: AI 私教错题讲解提示词和大模型输入上下文构建流程。
- `docs/deepseek_integration.md`: DeepSeek API 本地配置、调用脚本、模型选择和对话入库说明。
- `docs/ai_question_generation_workflow.md`: AI 生成题草稿流程，记录 dry run、DeepSeek 调用、草稿入库和人工审核规则。
- `docs/tutor_followup_workflow.md`: AI 私教讲解后的学生追问流程。
- `docs/student_web_prototype.md`: 学生端本地网页原型，包含组卷、答题、批改和 AI 讲解展示。
- `docs/aliyun_windows_deployment.md`: 阿里云 Windows Server 试用服务器部署流程。
- `docs/adaptive_exam_assistant_plan.md`: 从练习原型调整为个人 AI 自适应备考助手的产品主线和开发优先级。
- `docs/knowledge_base_workflow.md`: 出题依据库和轻量 RAG 流程，记录资料导入、知识块检索和 AI 出题前的依据要求。
- `database/schema.sql`: 初始数据库 SQL 表结构，当前以 SQLite 兼容为主，后续可迁移 PostgreSQL。

## 16. 当前资料批次

用户已准备并更正以下俄语专八真题及答案 PDF：

- 2017
- 2018
- 2019
- 2021
- 2023
- 2024

这些 PDF 已放入 `data/raw_pdfs/`，原始 PDF 不提交到 Git。

注意：

- 用户曾误上传部分专四资料，当前已删除并替换；专四资料不需要保留。
- 旧 2024 文件是专四照片版，当前已替换为新的专八题目。
- OCR 解析的扫描/照片版 PDF 可以暂时放一放，优先处理文字版资料。
- 部分 PDF 需要密码打开，密码不应提交到 Git；本地脚本通过 `PDF_PASSWORD` 环境变量读取。
- 登记脚本默认只登记 `TEM8_RU`，检测为专四或其他考试体系的 PDF 会跳过，避免误入专八题库。
- 数据库仍预留 `TEM4_RU` 和 `TEM8_RU`，但当前批次只保留专八资料。

## 17. 当前题库入库状态

已完成结构化切分并导入本地 SQLite 的专八真题：

- 2017 年：50 题
- 2018 年：50 题
- 2019 年：50 题
- 2021 年：50 题
- 2023 年：50 题
- 2024 年：50 题

当前数据库校验结果：

- 题目总数：300
- 阅读文章：30 篇
- 题型分布：
  - 语法选择题：102
  - 文学选择题：42
  - 国情选择题：36
  - 阅读选择题：120
- 审核状态：已由用户明确确认批量通过，全部回写为 `approved`
- 内容来源：全部为 `past_exam_original`
- 来源展示：全部要求显示 `source_label`，例如 `2019 年俄语专八真题`

这些题目目前是“可进入学生组卷池的历年真题原题”。进入组卷后，前端必须展示来源标签。

2026-08-21 更新：2017、2018 年真题使用“试题 PDF + 答案 PDF”分离流程导入：

- 切题脚本支持 `--answers-input` 单独读取答案文本。
- 入库脚本优先关联 `full` 来源文件，若没有整卷文件则关联同年份 `questions` 来源文件。
- 2017、2018 年各导入 50 题，共 100 题，均保持 `review_status = needs_review`。
- 2017、2018 年答案和四个选项均已补齐；少数 OCR 异常选项已根据渲染后的 PDF 页面人工核对并写入切题覆盖表。
- 审核表：`data/processed/review_sheets/tem8_2017_2018_questions_review.csv`。
- 阅读文章审核表：`data/processed/review_sheets/tem8_2017_2018_passages_review.csv`。
- 未经人工审核前，2017、2018 年题目不得进入正式学生组卷池。

2026-08-22 更新：2024 年真题已导入本地 SQLite：

- 2024 年导入 50 题，均保持 `review_status = needs_review`。
- 题型分布：语法 17、文学 7、国情 6、阅读 20。
- 阅读文章：5 篇，每篇 4 道题。
- 2024 年试卷中 `46-55` 为 `ЗАПОЛНЕНИЕ ПРОПУСКОВ` 填空/完形题，不属于第一版已建题型，本次暂不入库；后续可新增 `cloze_choice` 后再导入。
- 审核表：`data/processed/review_sheets/tem8_2024_questions_review.csv`。
- 阅读文章审核表：`data/processed/review_sheets/tem8_2024_passages_review.csv`。

2026-08-22 更新：阅读题组卷规则改为“按文章抽取”：

- 学生选择阅读题时，系统以 `passage_id` 为单位抽取。
- 抽到一篇文章时，该文章下全部小题都会连续出现。
- 如果用户请求的题量不是 4 的倍数，实际返回题量可能向上补齐到完整文章组，例如请求 5 道阅读题会返回 2 篇文章共 8 道。
- 前端同一篇阅读文章只显示一次，后面连续展示该文章的小题。

2026-08-17 更新：用户明确确认将 150 道题全部标记为 `approved`，并先按粗知识点入库：

- 语法题：`grammar`，51 题
- 文学题：`literature`，21 题
- 国情题：`culture`，18 题
- 阅读题：`reading`，60 题

当前每题已有 1 个粗知识点标签，后续仍应逐步细化到具体考点，例如动词体、运动动词、作家作品、国情地理、阅读推断等。

## 18. 当前知识点树状态

已建立俄语专八第一版知识点树，并写入本地 SQLite 的 `knowledge_points` 表。

当前节点数：35

分类分布：

- 语法与词汇：14
- 俄罗斯文学：7
- 俄罗斯国情：7
- 阅读理解：7

维护入口：

- 文档：`docs/knowledge_taxonomy.md`
- 脚本：`scripts/seed_tem8_knowledge_points.py`

脚本可重复运行；同一 `code` 会更新已有知识点，不会重复插入。后续题目人工审核时，应给每道正式题至少绑定一个知识点。

## 19. 当前人工审核流程状态

已建立待审核题目的导出与回写脚本：

- 导出脚本：`scripts/export_review_sheet.py`
- 回写脚本：`scripts/apply_review_sheet.py`
- 粗知识点预填脚本：`scripts/assign_coarse_knowledge_points.py`
- 审核日志迁移：`scripts/migrate_question_review_logs.py`
- 流程文档：`docs/review_workflow.md`

当前已生成本地审核表：

```text
data/processed/review_sheets/tem8_questions_review.csv
data/processed/review_sheets/tem8_2017_2018_2024_questions_review.csv
data/processed/review_sheets/tem8_2017_2018_2024_passages_review.csv
```

该表曾用于审核 150 道待审核题，保留题干、选项、答案、来源标签，并预留 `knowledge_point_codes`、`review_decision`、`review_notes` 三列供人工填写。

2026-08-17 更新：后续审核表导出改为题目表和阅读文章表分开：

- `tem8_questions_review.csv`: 题目、选项、答案、来源、`passage_id`、审核字段。
- `tem8_passages_review.csv`: 阅读文章全文，每篇文章一行。

这样阅读题不会再因为长文章正文重复出现在每一题行里而难以阅读。

回写策略：

- `approved` 写入题目主状态，且默认必须绑定至少一个知识点。
- `rejected` 写入题目主状态。
- `needs_review` 保持待审核。
- `needs_fix` 记录到审核日志，题目主状态仍保持待审核。

当前回写结果：

- 历年真题 `approved`: 300 题
- 2017、2018、2024 本次新增审核日志：150 条
- 本地回写前数据库备份位于 `data/processed/backups/`

2026-08-22 更新：2017、2018、2024 年待审核题已预填粗知识点：

- 总数：150 题
- `grammar`: 51 题
- `literature`: 21 题
- `culture`: 18 题
- `reading`: 60 题
- 当时题目状态仍为 `needs_review`，人工审核通过前不会进入学生正式练习池。

2026-08-22 更新：用户确认 2017、2018、2024 年 150 道题已审核通过，并已批量回写为 `approved`：

- 新增入正式练习池：150 题
- 当前历年真题正式练习池：300 题
- 回写审核日志 reviewer：`user_confirmed_review`
- 回写前数据库备份：`data/processed/backups/russian_ai_tutor_before_approve_2017_2018_2024_20260822_113058.sqlite`

## 20. 当前组卷原型状态

已建立学生侧练习卷生成脚本：

```text
scripts/generate_quiz.py
```

当前规则：

- 默认只抽 `review_status = approved` 且 `source_usage = practice` 的题。
- 当前 300 道已入库真题均为 `approved`，默认模式可以正式组卷。
- 内部测试仍可临时加 `--include-needs-review` 验证未审核题输出结构，但学生正式入口不应使用该参数。
- 历年真题输出中保留 `source.label`，例如 `2021 年俄语专八真题`。

当前已用正式默认模式生成过：

- 综合练习卷：10 题
- 阅读专项练习卷：5 题

验证来源标签、答案键、知识点标签和阅读文章关联均能输出。

## 21. 当前批改原型状态

已建立学生答题与自动批改脚本：

```text
scripts/grade_quiz.py
```

当前能力：

- 根据练习卷生成答案模板。
- 读取学生答案 JSON。
- 自动判定正确/错误。
- 输出正确率、错题列表、来源标签和知识点。
- 按知识点统计薄弱项。
- 可选择写入 `quiz_sessions`、`quiz_items`、`user_answers`、`weakness_snapshots`。

当前已用 10 题练习卷完成一次入库验证：

- `quiz_session_id = 1`
- 总题数：10
- 答对：7
- 正确率：0.7
- 写入答案记录：10
- 写入薄弱点快照：4

下一步应在批改报告基础上生成中文复习建议和巩固练习包。

## 22. 当前错题复习包状态

已建立批改后复习包生成脚本：

```text
scripts/generate_remediation_pack.py
```

当前能力：

- 读取批改报告。
- 找出有错题的知识点。
- 生成中文总评。
- 给每个薄弱知识点生成规则版中文建议。
- 从已审核题库中抽取同类巩固练习。
- 输出练习题、选项、答案、来源标签和阅读文章关联。

当前已基于 10 题测试报告生成一份复习包：

- 薄弱方向：俄罗斯文学、俄罗斯国情、阅读理解
- 每个薄弱方向：3 道巩固练习

下一步应把规则版建议升级为大模型中文讲解，并建立学生追问对话窗口的数据结构和提示词。

## 23. 当前 AI 私教提示词状态

已建立错题讲解提示词模板：

```text
prompts/tutoring/tem8_wrong_question_tutor.md
```

已建立提示词输入包构建脚本：

```text
scripts/build_tutor_prompt.py
```

当前能力：

- 读取批改报告。
- 读取复习包。
- 整理错题、学生答案、正确答案、选项、阅读原文、来源标签、薄弱知识点和巩固练习。
- 输出 JSON prompt 包，方便后续 API 调用。
- 输出 Markdown 预览，方便人工检查。

当前已完成一次 DeepSeek 真实调用，证明 API Key 和接口可用；但第一次 prompt 过于精简，模型缺少错题选项和阅读原文，阅读题讲解不够具体。后续已将 prompt 构建脚本改为从数据库补全错题选项、阅读文章和来源信息。

2026-08-18 更新：用户已明确同意发送增强版错题数据并写入对话表。增强版 DeepSeek 调用成功，并已保存：

- 输出 JSON：`data/processed/tutor_outputs/tem8_quiz_20260817_sample_report_persisted_tutor_prompt_enriched_deepseek_output.json`
- 输出 Markdown：`data/processed/tutor_outputs/tem8_quiz_20260817_sample_report_persisted_tutor_prompt_enriched_deepseek_output.md`
- 对话线程：`ai_tutor_threads.id = 1`
- 对话消息：system/user/assistant 各 1 条
- 模型：`deepseek-v4-flash`
- token 使用：输入 7974，输出 4715，总计 12689

增强版讲解能看到完整选项和阅读原文，因此阅读题讲解可以定位原文并逐项分析。

## 24. 当前 DeepSeek API 接入状态

用户已确认接入 DeepSeek API。

已建立：

- 本地环境示例：`.env.example`
- 调用脚本：`scripts/call_deepseek_tutor.py`
- 接入文档：`docs/deepseek_integration.md`

当前接口规则：

- `DEEPSEEK_BASE_URL = https://api.deepseek.com`
- 默认模型：`deepseek-v4-flash`
- 可选高质量模型：`deepseek-v4-pro`
- 旧模型名 `deepseek-chat`、`deepseek-reasoner` 不再用于本项目。

API Key 不提交到 Git，只能放在本地 `.env` 或环境变量 `DEEPSEEK_API_KEY` 中。

当前脚本可读取 tutor prompt 包，调用 DeepSeek 生成中文错题讲解，并可选写入 `ai_tutor_threads` 和 `ai_tutor_messages`。

注意：增强版 prompt 会发送完整选项和阅读原文到 DeepSeek。真实调用和写入对话表前，需要用户明确同意发送这份扩展后的测试数据；本轮测试已取得明确同意并完成调用。

## 25. 当前追问对话脚本状态

已建立 AI 私教追问脚本：

```text
scripts/followup_deepseek_tutor.py
```

当前能力：

- 根据 `ai_tutor_threads.id` 读取历史对话。
- 追加学生追问。
- 调用 DeepSeek 继续回答。
- 把学生追问和模型回答写回 `ai_tutor_messages`。
- 输出 JSON 和 Markdown 供本地检查。

注意：追问调用会把该对话线程历史和学生新问题发送到 DeepSeek。如果线程中包含题干、选项、阅读原文或学习表现，正式调用前仍需要确认用户同意发送。

## 26. 当前学生端网页原型状态

已建立本地学生端网页原型：

```text
scripts/serve_student_app.py
apps/student_web/static/
```

当前能力：

- 查看题库状态。
- 新用户可一键开始 30 题入门诊断。
- 入门诊断覆盖语法、文学、国情和阅读四类题型，并尽量均衡抽题。
- 前端显示四类题型掌握度：掌握分、掌握状态和累计作答次数。
- 学生可从能力画像中选择“只练此类”。
- 按题型和年份生成练习。
- 随机组卷默认不包含阅读题。
- 随机组卷已参考题目曝光记录做基础避重。
- 页面作答。
- 自动批改并写入测试记录。
- 批改后更新本地默认学生的题型掌握度、知识点掌握度和弱项训练建议。
- 显示正确率、错题、薄弱知识点和来源标签。
- `/api/grade` 同步完成批改和 DeepSeek 深度错题讲解生成，并写入对话表。
- `/api/profile` 返回当前本地默认学生画像。
- 前端提交后只显示“正在批改中”的等待状态；批改结果和讲解内容等待同一个响应完成后一起出现。
- 逐题讲解显示在对应错题下方；薄弱点排序、复习方案和可追问问题显示在 AI 对话区。
- 学生端不再提供“读取讲解”按钮。
- 预留追问入口，发送前要求确认允许把对话上下文发送到 DeepSeek。

当前验证：

- 首页可访问。
- 题库状态接口返回 300 道 `approved` 题。
- 约 30 题入门诊断接口验证通过；阅读按整篇文章补齐后，当前可返回 31 题左右。
- 组卷接口可生成练习，默认不包含阅读题。
- 批改接口可写入 `quiz_sessions`、`quiz_items`、`user_answers`、`weakness_snapshots`。
- 已新增 `question_exposures`、`mastery_snapshots`、`training_recommendations`，支持画像计算和避重组卷。
- `/api/profile` 可返回题型掌握度、知识点掌握度、前三个薄弱项和下一步训练建议。
- `/api/grade` 返回批改结果时同步返回 DeepSeek 讲解。
- `/api/explain` 保留为内部调试入口，必须收到 `confirm_external_send = true` 才能调用 DeepSeek。
- AI 讲解读取接口只返回 assistant 消息，不把系统提示词和底层 JSON 暴露给学生端。

2026-08-18 更新：用户要求去掉“生成错题讲解”按钮，不再输出“本次表现”。讲解应在批改后自动生成，并按题目显示逐题解析；整体复习内容单独显示在 AI 对话区。

2026-08-18 更新：用户进一步要求去掉“读取讲解”步骤，并让批改与讲解同步出现。当前实现为 `/api/grade` 等待 DeepSeek 返回后再把批改结果和讲解一起返回前端。

当前本地访问地址：

```text
http://127.0.0.1:8765/
```

## 27. 本地 OCR 配置

当前已安装 Tesseract OCR，用于处理扫描版俄语专八 PDF。

配置：

- Tesseract 可执行文件：`C:\Program Files\Tesseract-OCR\tesseract.exe`
- 语言包目录：`C:\Users\Reto\tesseract-tessdata`
- 已配置语言：`rus`、`eng`、`chi_sim`、`osd`

注意：

- 项目目录应使用纯英文路径，例如 `D:\AIeyu`，避免 Tesseract 等工具处理中文路径时出现编码问题。
- 语言包放在纯英文用户目录。
- 后续 OCR 脚本应显式传入 `--tessdata-dir C:\Users\Reto\tesseract-tessdata`。
- 扫描版中文/中俄混排参考书应优先使用 `--lang chi_sim+rus+eng`。

当前知识源扫描 PDF 状态：

- `tem8_countryknowledge_reference_scan.pdf`: 161 页，已完成 OCR，已导入 `knowledge_chunks` 159 个，标记为 `culture_choice` / `culture`。
- `Russian_grammar_reference_scan.pdf`: 641 页，已抽样确认可用，但尚未全量 OCR；建议后续分批处理。

AI 生成题人工反馈：

- 2026-08-20 首次真实生成 2 道国情草稿题，题目 ID 为 151、152。
- 题目 152 被反馈为难度偏低，偏单点词义记忆；后续生成规则应避免此类过低难度题，国情题应更重视背景关系和干扰项辨析。
- 2026-08-20 第二轮生成“红场/克里姆林宫”相关国情草稿题，题目 ID 为 153、154。
- 用户反馈：题目 154 比较符合预期的国情 `difficulty = 4`。该类题应考查“事实节点 + 历史背景 + 易混干扰项辨析”，例如莫斯科成为首都的 1918/1922 时间节点，不应只是单纯名称对应或词义记忆。
- 2026-08-20 暂停听力识别线，回到 AI 题库线。已新增本地 AI 草稿质量审计：检测同批/历史 AI 草稿重复、国情高难题浅层事实题风险，并把风险写入审核日志。
- 当前 AI 草稿质检结果：题目 154 暂作为正向候选；题目 153、155、156、157 已标记为 `similarity_review_status = flagged` 并记录 `needs_fix` 审核日志。AI 草稿仍未进入正式学生练习池。
- 2026-08-20 生成俄罗斯地理与资源方向 AI 草稿题，题目 ID 为 158、159、160，均为 `difficulty = 4`、`needs_review`、`ai_draft`，并通过本地质量审计。该批题以“河流流向/水量/别称”“乌拉尔地理分界/经济区特征”“资源储量/主要产地”做组合辨析，比单点事实题更符合当前难度标准。
- 2026-08-21 生成俄罗斯政治制度与行政划分方向 AI 草稿题，题目 ID 为 161、162、163，均为 `difficulty = 4`、`needs_review`、`ai_draft`，并通过本地质量审计。该批题围绕“联邦会议两院人数与联邦主体数量”“总统任期与连任规定”“联邦主体总数与类型数量”做组合辨析，仍未进入正式学生练习池。

## 28. 当前听力接入状态

用户已建立听力音频目录：

```text
data/listening/raw_audio/tem8/
```

当前材料形态：

- 2017、2018、2023：整套 mp3 音频。
- 2019、2024：分段 mp3 音频，每年 7 段。

确认规则：

- 分段音频不需要合并，第一版每个分段登记为独立听力资产。
- 整套音频先登记为 `full_exam`，后续再按题组自动切段或人工绑定时间范围。
- 小语种 ASR 第一版优先用本地 Whisper / faster-whisper 生成俄语转写草稿。
- 没有听力文字稿也可以开始，但 ASR 结果必须经过人工校对后才能作为正式讲解依据。
- 云端 ASR 只作为备选；发送音频到外部服务前必须取得用户明确授权，并注意听力材料版权边界。
- 2019 年第 1 段已完成本地 ASR 小样本：`base` 能跑通但错误较多，`small` 默认 VAD 会过度过滤，`small --no-vad` 更适合作为人工校对底稿。
- 当前听力转写已支持导出 CSV 校对表，并可在人工校对后回写为 `human_verified`。

已新增听力相关表设计：

- `listening_assets`
- `listening_transcripts`
- `listening_segments`
- `listening_question_links`

听力选择题进入题库主表时使用题型 `listening_choice`。

## 29. 单词库当前状态

2026-08-22 已完成第一批专八单词正式入库。

当前标准：

- 正式词库 `vocabulary_items` 共 3513 条。
- 全部为 `review_status = approved`。
- 本轮最终导入表为 `data/processed/words/tem8_words_final_approved_for_import.csv`。
- 正式导入前备份为 `data/processed/backups/russian_ai_tutor_before_final_vocab_import_20260822_181938.sqlite`。

本轮排除标准：

- `needs_llm_review`、`reject_candidates`、`llm_rejected`、`llm_needs_review` 不进入正式词库。
- 纯俄文字母但疑似 OCR 错词也不能默认放行，例如 `нбвшество`、`парадбкс`、`настрбенный`、`спосдбить`。
- 句子碎片、短语碎片、例句残片不进入单词库，例如 `кает`、`пол-литрамолока`、`ряются`、`Поплатьювстречают`。
- 中文释义必须尽量降为核心释义，不能保留明显 OCR 垃圾符号。

后续继续做单词打卡前，可以先基于当前 3513 条做 MVP；剩余 322 条 `needs_llm_review` 应单独复核后再追加。

2026-08-22 已接入单词打卡 MVP：

- 学生端新增独立“单词”页面。
- 当前学生账号下可以抽取今日单词，优先复习到期词，不够时补充新词。
- 第一版采用自评模式：`认识`、`模糊`、`不认识`。
- 复习间隔：`认识` 不进入复习词库；`模糊` 2 天后复习；`不认识` 每天复习直到学生标记为认识。
- 背词记录写入 `user_word_progress` 和 `word_review_logs`，与学生账号隔离。
- 单词释义展示层会去掉部分 OCR 形态残留；正式词库深度释义校对可后续单独继续。

2026-08-22 单词打卡与账号体验优化：

- 默认 1 号账号改名为“测试专用”，仅用于本地/课堂测试。
- 学生账号入口移动到页面右上角菜单，点击后再选择用户并确认切换。
- 右上角菜单支持输入姓名新增学生名单。
- 单词打卡保留进度条和完成总结；`稍后再看` 已移除。
- 已处理过的单词卡片会显示“已记录”状态，避免在同一轮打卡中重复提交。

2026-08-23 单词打卡体验改版：

- 单词卡片分为两步：第一步只显示俄语词，底部从左到右为 `认识`、`模糊`、`不认识`。
- 点击任意掌握度后停留在当前词的释义页：上方仍显示单词，中间显示词义；如果 `vocabulary_forms` 中存在 `example` 类型记录，则显示例句。
- 释义页底部左侧为 `下一词`，右侧为 `记错了`。
- `记错了` 用于把已选为认识/模糊的词重新改成 `不认识`，并加入每日复习；校正不重复增加 `seen_count`，今日打卡按单词去重统计。

2026-08-23 单词复习与词库质量 checkpoint：

- 页面不再展示“认识/模糊/不认识”的复习规则说明文字，只保留打卡操作与结果。
- 背单词时恢复 `上一词`，完成页也可以回到上一词查看或修正。
- 学生可在单词页右侧查看自己的 `复习词库`，并点击 `立即复习` 只抽取复习词库中的词。
- 词库确定性修正脚本为 `scripts/apply_vocabulary_quality_fixes.py`：运行前自动备份数据库，修正高度确定 OCR/释义错误，并导出剩余可疑项表。
- 已修正示例：`филосбфский` -> `философский`；`откуда-то` 的释义改为 `不知从哪里, 从某处`；`откуда-нибудь` 的释义改为 `从随便什么地方, 不管从哪里`；`будка` 的污染释义改为 `岗亭；小室`。

2026-08-24 词库质量与用户反馈 checkpoint：

- 用户确认：当前正式词库仍存在较多 OCR 词形错误、中文错字、释义缺失和释义过薄问题，不能再只做零散修补。
- 新增全库审计脚本 `scripts/audit_and_improve_vocabulary.py`，检查范围为所有 `review_status='approved'` 的词条。
- 审计维度包括：已知高置信错误、词形疑似 OCR、中文释义 OCR 错字、释义过薄、无中文释义。
- 本轮审计正式词库 3513 条，标出 631 条需要复核/LLM 完善；自动应用 7 条高置信修正，并生成 LLM 审核 payload。
- 已修正用户指出示例：`консерватбрия` -> `консерватория`；`индустриальный` 释义补为 `工业的；产业的`；`разочарование` 释义修为 `失望；扫兴`；`неведомый` 释义补为 `未知的；人所不知的；神秘的`。
- 新增学生端 `单词报错` 功能：学生在单词卡片中提交问题，后端写入 `word_feedback`，保留当时的词形和释义快照。
- 新增学生端 `提建议` 功能：后端写入 `product_feedback`。
- 后续全词库 LLM 完善原则：优先处理审计表和学生报错表；大模型建议不得直接静默覆盖全部词库，应先导出审核表，按高置信/需人工复核分层处理。

2026-08-24 本地 LLM 词库复核 checkpoint：

- 新增 `scripts/apply_local_llm_vocabulary_fixes.py`，用于保存和复用本地大模型高置信词库修正。
- 本轮先应用 137 条高置信修正，随后对剩余审计项继续补 23 条，总计 160 条本地 LLM 修正。
- 修正类型包括：`о/б` OCR 错误、词形污染、词性污染、中文 OCR 错字、动词释义只剩 `未/完`、释义过窄或误译。
- 修正后重新运行 `scripts/audit_and_improve_vocabulary.py`，正式词库 3513 条中，当前高置信审计规则下 `flagged_rows=0`。
- 注意：`flagged_rows=0` 只代表当前规则下没有明显 OCR/释义薄弱项，不等同于权威词典级全量校订。后续继续优先处理学生 `word_feedback` 和新审计规则发现的问题。

2026-08-24 词性标记泄漏修正 checkpoint：

- 用户发现 `пылесос` 释义显示为 `阳吸尘器`，确认问题是词性标记进入 `meaning_zh`，不是用户学习记录问题。
- 新增审计规则 `pos_marker_leaked_into_meaning`：检测 `阳/阴/形/未/完` 等词性或体标记混入中文释义。
- 本轮修正 32 条结构性污染词条，代表例：`пылесос` -> `part_of_speech=阳, meaning_zh=吸尘器`；`волейболист` -> `part_of_speech=阳/阴, meaning_zh=排球运动员`；`смывать` -> `洗掉；冲掉；冲走`。
- 修正后重新审计正式词库 3513 条，新增规则下 `flagged_rows=0`。

2026-08-24 联网词典对照修正 checkpoint：

- 用户指出 `разрядка` 只译为“国际紧张局势的缓和”过窄，且不能再只凭本地猜测补义。
- 已联网核对俄语词典后修正 `разрядка`：`放电；卸除装填；缓和、放松；字母疏排`。
- 后续遇到语义明显不可信或过窄的词条，应优先用俄语词典来源核对，不得把单一语境义作为唯一释义。

2026-08-22 已完成服务器端学生账号隔离：

- 学生端账号入口改为注册/登录/退出，不再展示全体学生名单。
- 注册使用“姓名 + 密码”轻量方案，密码最少 8 位，适合第一版课堂/服务器试用。
- 后端新增 `user_auth` 和 `user_sessions`，密码使用 PBKDF2 哈希存储，浏览器通过 HttpOnly Cookie 保存登录状态。
- `/api/users` 登录后只返回当前学生自己。
- 练习、批改、错题本、单词打卡、AI 追问等学生个人接口都从服务器会话读取当前学生 ID，不再相信前端传来的 `user_id`。
- 未登录访问个人接口返回 401。
- 当前不是商业级手机号/邮箱验证码体系；后续商业化可升级为邮箱/手机号注册、找回密码、管理员后台。

## 30. 后续工作规则

阿里云测试部署规则：

- 当前用户有一台阿里云 ECS Windows Server 2022 试用服务器，配置为 2 vCPU / 4 GiB。
- 推荐通过 GitHub 私有仓库同步代码到服务器。
- `.env`、SQLite 数据库、原始 PDF 和处理产物不得提交到 GitHub。
- 服务器需要单独复制 `.env` 和 `database\russian_ai_tutor.sqlite`。
- 当前学生端服务在服务器上应使用 `--host 0.0.0.0 --port 8765` 启动。
- 正式对外测试前需要开放阿里云安全组和 Windows 防火墙的 TCP `8765` 端口。
- 当前原型没有登录系统，测试链接只应发给可信学生。

随机组卷规则：

- 默认随机组卷不包含阅读题。
- 默认随机范围只包括 `grammar_choice`、`literature_choice`、`culture_choice`。
- 阅读题保留为单独专项，只有用户明确选择阅读时才进入组卷。

后续开发或规划时：

- 如果用户给出新的确定标准，应更新本文档。
- 如果出现与本文档冲突的新需求，应先指出冲突并确认新标准。
- 如果某个功能尚未确认，不应把它当成已确定事实。
- 如果需要做架构决策，应优先兼顾“专八第一版可落地”和“多考试体系可扩展”。
- 如果引入 GitHub 项目作为参考，应先评估许可证、技术栈、维护状态和改造成本。

## 31. 版本控制规则

项目从一开始使用 Git 做版本控制。

后续开发应遵守：

- 每完成一个清晰阶段，应提交一次 Git commit。
- 大功能或有风险的改动应优先创建独立分支。
- 修改代码前后都应检查工作区状态。
- 不应随意删除或覆盖用户已有文件。
- 不应把真题 PDF、解析原件、`.env`、缓存、依赖目录提交到仓库。
- 重要需求、约定、架构变化应同步更新本文档或 `docs/` 下的相关文档。
- 出现错误时优先通过 Git diff、commit history 和小范围回退定位问题。

建议提交粒度：

- `docs: record project context`
- `chore: initialize project structure`
- `feat: add question bank schema`
- `feat: add quiz generation flow`
- `fix: correct pdf parsing edge case`
### 5.3 专四题库接入 checkpoint（2026-08-26）

已按专八相同的“原始资料保留、结构化切分、人工审核后入池”流程接入专四资料：

- 原始 PDF 目录：data/raw_pdfs/tem4/
- 已登记来源 PDF：9 份，覆盖 2017、2018、2019、2021、2022、2023、2024。
- 已生成结构化待审核题目：570 道。
- 题型分布：听力 105、语法 290、国情/礼仪 35、阅读 140。
- 阅读按文章绑定，每年 4 篇文章、每篇 5 道题；组卷时由完整文章单元统一选择。
- 目前不导入完形填空，因为数据库尚未建立独立的 cloze 题型；不得把完形题误归为语法题。
- 2017-2023 优先使用 PDF 文字层；2024 扫描版使用去水印 OCR 临时结果。原始 PDF 不修改。
- 所有专四题目当前为 needs_review，尚未进入学生正式练习池；缺答案、缺选项、题干不完整或填空位置不明确的内容不得自动猜测。
- 待审核表：data/processed/review_sheets/tem4_questions_review.csv、data/processed/review_sheets/tem4_passages_review.csv
- 校验脚本：scripts/validate_tem4_review_json.py
- 导入脚本：scripts/import_tem4_review_json.py
- 数据库导入前备份：data/processed/backups/russian_ai_tutor_before_tem4_import_20260826_200449.sqlite

审核通过后，必须先完成校验，再将明确可用的题目改为 approved + practice。无法从 PDF 可靠确认的题目保留 needs_review + source_reference_only，不进入学生组卷。

### 5.4 专四/专八分页约定（2026-08-26）

- 学生端练习页提供“俄语专八 / 俄语专四”分页。
- 当前考试选择保存于浏览器本地；切换考试会清空当前试卷显示，并重新读取题库、画像和错题本。
- 组卷、批改、画像、错题本均携带 exam_system 和 level，学习数据按考试范围隔离。
- 默认随机组卷继续排除阅读题；阅读题后续按文章完整单元处理。
- 页面只显示当前考试中已审核、可练习的题目；待审核专四题不会被学生端看到。

### 5.5 专四题库处理错误防线

- 不把 OCR 乱码直接当成题干或选项。
- 不把作者姓名缩写、页码、栏目标题误判为选项。
- 不因答案矩阵缺失而推测答案；答案为空必须进入人工审核。
- 阅读题必须同时检查文章、题干、选项和答案的对应关系；任一关键部分损坏就下架复核。
- 每篇阅读文章固定核对题目数量和绑定关系，不能只看单道题。

### 5.6 水印清理与专四题目本地 LLM 复核 checkpoint（2026-08-26）

用户确认原始资料中的“沙拉俄语”斜向水印会影响文章识别、题干切分和选项恢复。本轮处理规则如下：

- 原始 PDF 不修改，继续保存在 data/raw_pdfs/tem4/。
- 已为专四 9 份 PDF 生成 OCR 清洁版，输出在 data/processed/ocr_clean_pdfs/tem4/。
- 清洁版采用页面渲染、黑白阈值处理和底部非正文区域清理，目标是降低浅色水印对 OCR 的干扰；清洁版只作为识别辅助，不替代原始资料。
- 2024 年扫描版已用清洁版重新 OCR，输出为 data/processed/tem4_text_clean/tem4_russian_2024_full.txt，并重新切分为 90 道题。
- 修正了切题防线：不能把完形题中的“Чтение (71)”误认为阅读章节标题；OCR 将题号句号识别为逗号时仍应识别为题号。
- 清洁 OCR 与原结构化结果逐题对比。由于清洁 OCR 并非每一处都优于原文，不允许整篇文章、整套题目或所有选项批量覆盖。
- 本地 LLM 只应用高置信的局部修正：2024 年第 3、26、40 题恢复选项结构；第 66、67、68、69、70、86 题补充经题干和知识事实交叉核对的答案，共 9 道。
- 上述 9 道题仍全部保持 review_status = needs_review；不能可靠恢复的题干、选项、阅读文章和答案继续进入人工审核表，不因模型判断自动放行。
- 本轮数据库修改前备份为 data/processed/backups/russian_ai_tutor_before_tem4_llm_ocr_review_20260826_212321.sqlite。
- 本轮审核记录和复核结果：scripts/apply_tem4_llm_ocr_review.py、data/processed/structured/tem4/tem4_russian_2024_review_llm_checked.json、data/processed/question_quality/tem4/tem4_2024_llm_ocr_audit.csv。
- 专四人工审核表已根据本轮结果刷新：data/processed/review_sheets/tem4_questions_review.csv 和 data/processed/review_sheets/tem4_passages_review.csv。

后续原则：阅读题必须同时核对原文、题干、选项、答案和文章绑定关系。任何一个关键部分无法从原 PDF 或清晰 OCR 可靠确认，都只能保留 needs_review，不能为了提高入库数量而猜测补全。

### 5.7 专四逐题本地 LLM 批量审核 checkpoint（2026-08-26）

已按专八审核规则完成专四 570 道题的第一轮保守审核。审核不是只看题目数量，而是同时检查题干、四个选项、答案、题型、阅读文章绑定和 OCR 噪声。

- 93 道题已标记为 approved + practice，进入正式题库：2017 年 45 道、2018 年 44 道、2024 年 4 道。
- 477 道题继续保持 needs_review + source_reference_only，不会被学生端组卷抽取。
- 待审核原因统计：听力 100 道缺少可核验题干和音频绑定；阅读 132 道需要逐篇核对清洁 OCR 与文章绑定；177 道缺少可靠答案或答案不在完整选项中；43 道语法题填空位置不明确；其余为页脚、OCR 字符或选项结构异常。
- 2017、2018 年中能根据题干、固定搭配和选项高置信确认的少量答案已修正；不确定答案没有猜测补入。
- 2019、2021、2022、2023 的整套 PDF 没有可直接核验的答案表，因此相关题目不能仅靠模型推断后自动放行。
- 阅读题即使选项和题号完整，只要正文存在乱码、拉丁噪声、页脚或文章未逐篇核对，仍不得自动放行。
- 批量审核脚本：scripts/review_tem4_llm_batch.py。
- 全量审核报告：data/processed/question_quality/tem4/tem4_llm_review_report.csv。
- 无法自动补全清单：data/processed/question_quality/tem4/tem4_uncompletable.csv。
- 已刷新人工审核表：data/processed/review_sheets/tem4_questions_review.csv 和 data/processed/review_sheets/tem4_passages_review.csv。
- 数据库写入前备份：data/processed/backups/russian_ai_tutor_before_tem4_batch_review_20260826_225717.sqlite。

后续只有在补齐答案、人工确认清洁 OCR 或完成听力材料绑定后，才能将对应题目从 needs_review 改为 approved + practice。不得因为模型能够推测答案，就跳过来源核验。

### 5.8 直接文字层重建与答案矩阵解析纠正 checkpoint（2026-08-26）

复核发现：除 2024 扫描版外，2017、2018、2019、2021、2022、2023 的 PDF 都有可直接提取的俄文文字层，不应使用 OCR 作为主数据源。此前批量 OCR 造成文字噪声增加；此前答案缺失的主要原因是答案矩阵在文字层中按“连续题号行 + 连续答案行”排版，而解析器只支持题号和答案同一行。

- 2017–2023 已改用 data/processed/tem4_text_direct/ 的直接文字层重建题目、选项、答案和阅读文章。
- 2017、2018 使用独立答案 PDF；2019、2021、2022、2023 使用整套 PDF 末尾的答案章节。
- answer_map 已支持答案矩阵的纵向排版；2019–2023 的答案已经恢复，不再视为资料缺答案。
- 2024 仍使用去水印 OCR 清洁版；原始 PDF 不修改。
- 直接文字层重建脚本：scripts/sync_tem4_direct_text.py；切题脚本：scripts/segment_tem4_review_json.py。
- 重建前备份：data/processed/backups/russian_ai_tutor_before_tem4_direct_text_resync_20260826_231212.sqlite。
- 重建并批量审核后，专四 570 道题中 263 道已 approved + practice，307 道保持 needs_review + source_reference_only。
- 当前 307 道待审核的真实原因：听力 105 道缺少题干/音频绑定；阅读 140 道需要逐篇核对文章；语法填空位置不明确 44 道；另有 18 道存在页脚、拉丁字符、特殊符号或选项数量异常。
- 批量审核报告：data/processed/question_quality/tem4/tem4_llm_review_report.csv；无法自动补全清单：data/processed/question_quality/tem4/tem4_uncompletable.csv。
- 批量审核写入前备份：data/processed/backups/russian_ai_tutor_before_tem4_batch_review_20260826_231228.sqlite。

后续规则：文字层可用时禁止用 OCR 替代文字层；答案章节必须先识别其排版结构再解析；除非能从原 PDF 或清晰文字层核验，否则不允许模型猜答案。

### 5.9 专四干净回退与重新接入 checkpoint（2026-08-27）

为纠正上一轮“所有年份都走 OCR”造成的污染，本轮按专四接入前的干净数据库重新开始。此前 5.3–5.8 的专四数量和审核统计仅作为历史记录，不代表当前数据库状态。

- 当前工作分支：codex/tem4-clean-rebuild。
- 回退基线：data/processed/backups/russian_ai_tutor_before_tem4_import_20260826_200449.sqlite；该基线保留 300 道专八 approved、13 道专八 needs_review 和 3513 个正式词条。
- 回退前当前库另存为 data/processed/backups/russian_ai_tutor_before_clean_tem4_rebuild_20260827.sqlite，后续批量审核前另有自动备份。
- 2017、2018、2019、2021、2022、2023 只使用 data/processed/tem4_text_direct/ 的 PDF 文字层，禁止用 OCR 替代；2017、2018 的答案来自独立答案 PDF，2019、2021、2022、2023 使用 PDF 内答案矩阵，已支持“题号列 + 答案列”的排版。
- 2024 因无可用文字层，只使用 data/processed/tem4_text_clean/tem4_russian_2024_full.txt 的清洁 OCR；2024 题目统一保留 needs_review，必须人工逐题对照原 PDF 后才能开放练习。
- 新结构化文件统一放在 data/processed/structured/tem4_clean_rebuild/；听力题单独导出到 data/processed/tem4_listening_separate/，不写入 questions 表、不参与随机组卷。
- 完形填空继续不导入，因为当前数据库没有独立 cloze 题型；本轮正式题库仅包含语法、国情和阅读。
- 当前专四正式数据库题目：465 道，其中 grammar_choice 290、culture_choice 35、reading_choice 140、listening_choice 0；其中 259 道为 approved + practice，206 道为 needs_review + source_reference_only。
- 2017–2023 的阅读题仍按文章整体绑定并待逐篇核对；2019 第 16、50 题、2023 第 20 题等结构异常项不猜测补全。2024 OCR 题全部待人工审核。
- 导入脚本已支持 `--exclude-question-type listening_choice`；独立听力导出脚本为 scripts/export_tem4_listening_separate.py。
- 当前人工审核表：data/processed/review_sheets/tem4_questions_review.csv、data/processed/review_sheets/tem4_passages_review.csv；质量报告：data/processed/question_quality/tem4/tem4_llm_review_report.csv；无法自动放行清单：data/processed/question_quality/tem4/tem4_uncompletable.csv。

本 checkpoint 的不可变规则：文字层可用年份绝不 OCR；听力绝不混入正式题库；2024 OCR 不因结构完整而自动放行；任何题干、选项、答案、文章绑定无法从原 PDF 可靠核验时，保留 needs_review，不用模型猜测。

### 5.10 专四逐题审核 checkpoint（2026-08-27）

在 5.9 的干净重建基础上，按年份和题号顺序完成了一轮保守逐题审核。审核先检查题干、四个选项、答案、题型和阅读文章绑定，再应用有明确来源依据的局部切分修正；不能从资料可靠确认的内容不猜测。

- 2017–2023 的直接文字层题目中，267 道已标记 approved + practice，可进入学生练习；其中 120 道阅读题继续待逐篇人工核对。
- 2019 第 16、50 题和 2023 第 20 题只有 3 个选项，无法从当前文字层确认缺失选项，已列入人工确认表。
- 2019、2021、2022、2023 第 60 题 D 选项误吸收下一部分完形填空，已按明确章节边界截断并复核通过。
- 2024 的 75 道非听力题全部来自 OCR，统一保留 needs_review；不能因为题目结构看似完整就自动进入练习。
- 当前专四状态：267 approved + practice，198 needs_review + source_reference_only；listening_choice 仍为 0。
- 最终人工确认表已刷新：data/processed/review_sheets/tem4_questions_review.csv（198 道题）；阅读文章表：data/processed/review_sheets/tem4_passages_review.csv（28 篇）。
- 本轮审核报告：data/processed/question_quality/tem4/tem4_llm_review_report.csv；无法确认清单：data/processed/question_quality/tem4/tem4_uncompletable.csv。
- 本轮审核前数据库备份：data/processed/backups/russian_ai_tutor_before_tem4_batch_review_20260827_190117.sqlite。

后续人工审核时：表中 `review_decision` 填 `approve` 才能进入练习，填 `reject` 或留空都保持下架；阅读必须以整篇文章为单位确认，2024 OCR 必须对照原始 PDF。

### 5.11 2024 OCR 与阅读题复核 checkpoint（2026-08-27）

根据用户确认的三道专四缺选项题，以及本轮大模型辅助的高置信文字修正，完成了第二轮专四复核：

- 用户确认的 2019 第 16、50 题和 2023 第 20 题均已补齐为四个选项，绑定 grammar 知识点并进入 approved + practice。
- 2024 OCR 的语法和国情题中，55 道完成高置信题干、选项、答案修正后进入练习；修正保留填空位置，不把正确答案直接写进题干。
- 2024 OCR 阅读正文仍有多处混合字符和词形噪声，20 道阅读题全部保留 needs_review，不能只凭模型猜测放行。
- 2017、2018、2019、2022、2023 阅读题经文章正文、题干、选项和答案检查后，117 道进入练习；2021 第 71、74、88 题因原文字层缺少关键数字或选项内容，3 道保留人工确认。
- 当前专四数据库：442 道 approved + practice，23 道 needs_review + source_reference_only；其中 grammar 290、culture 35、reading approved 117、reading pending 23；listening_choice 仍为 0。
- 阅读正文中的分页标记和“沙拉俄语”水印残留已清除；仅对可明确确认的混淆字符做了局部修正，未整篇猜测改写。
- 2024 高置信修正脚本：scripts/apply_tem4_llm_ocr_review.py；阅读修正脚本：scripts/apply_tem4_reading_llm_review.py。
- 最终人工确认表：data/processed/review_sheets/tem4_questions_review.csv（23 道题）、data/processed/review_sheets/tem4_passages_review.csv（6 篇文章）。
- 本轮关键回退备份：data/processed/backups/russian_ai_tutor_before_tem4_batch_review_20260827_194413.sqlite、data/processed/backups/russian_ai_tutor_before_tem4_reading_review_20260827_194401.sqlite。

不可变规则继续有效：文字层可用年份不 OCR；听力不入正式题库；2024 OCR 阅读必须人工对照原 PDF；任何无法可靠确认的内容保持下架。

### 5.12 专四人工补全结果与 2024 OCR 阅读暂缓 checkpoint（2026-08-27）

根据用户最新确认，2021 年第 74 题无法可靠补全，已从练习范围下架；数据库保留该原始记录并标记为 `rejected + source_reference_only`，便于审计和回退。2024 年 OCR 阅读题噪声较多，本阶段不纳入正式题库，20 道题统一保持 `needs_review + source_reference_only`，不得随机组卷。

- 当前专四正式练习池：442 道 `approved + practice`。
- 当前专四待审核表：22 道，包括 2021 年第 71、88 题及 2024 年阅读题 81–100。
- 最新审核表中 2021 年第 71 题 A 选项仍缺年份、88 题题干仍缺年份，且 `review_decision` 为空；本轮不猜测放行，继续等待人工确认。
- 本轮数据库回退备份：`data/processed/backups/russian_ai_tutor_before_tem4_hold_20260827_20260827_200259.sqlite`。

本 checkpoint 的处理规则：用户明确删除或判定无法补全的题目从练习池下架但默认保留记录；2024 OCR 阅读不因答案看似完整而入库；只有题干、选项、答案和阅读文章均可可靠核验时，才允许标记 `approved + practice`。

### 5.13 专四 2021 阅读第 71、88 题补全入库 checkpoint（2026-08-27）

根据绑定文章原文完成核验并入库：

- 第 71 题 A 选项补为 `Он начал играть на скрипке в 14 лет.`；同时修正数据库中 B 选项被错误切分的残留文本为 `Он научился играть на инструментах.`；答案 C。
- 第 88 题题干补为 `Какая команда стала чемпионом мира по черлидингу в 2011 году?`；答案 C。
- 两题均已标记 `approved + practice`，专四正式练习题从 442 道增至 444 道。
- 2024 OCR 阅读题 81–100 仍为 20 道 `needs_review + source_reference_only`，继续不进入练习池。
- 本轮数据库回退备份：`data/processed/backups/russian_ai_tutor_before_tem4_71_88_approve_20260827_202031.sqlite`；审核表回退备份：`data/processed/review_sheets/tem4_questions_review_before_71_88_approve_20260827_202031.csv`。

### 5.14 学生端专四测试界面优化 checkpoint（2026-08-27）

- 学生端增加当前考试概览，动态显示可练题量、年份数量和题型数量；切换专四、专八时沿用同一套组件。
- 试卷生成后显示已作答进度，选择任意选项会实时更新进度条；长试卷提交栏保持可见。
- 阅读文章继续按文章整组返回，页面在文章标题处显示“整篇文章”，并保留完整正文排版。
- 题干、选项、来源和阅读正文统一进行 HTML 转义，避免题库文本中的特殊字符破坏页面结构。
- 本地验证地址：`http://127.0.0.1:8789/`；专四状态接口返回 444 道正式题，页面资源和 JavaScript 校验通过。

### 5.15 专四词汇 OCR 接入 checkpoint（2026-08-28）

本轮开始接入专四背单词词库。用户提供的文件实际路径为 `data/words/tem4_russian_words.pdf`；用户消息中的下划线是 Markdown 转义，不代表真实目录名。

- OCR 使用与专八相同的 `pypdfium2 + Tesseract` 流程，专四 PDF 共 354 页，逐页原文输出到 `data/processed/words/tem4_ocr_text/`。
- 已将 `scripts/ocr_word_pdf.py`、`scripts/extract_word_candidates.py` 改为支持 `--prefix` 和来源文件参数，专八默认参数保持不变。
- 已将 `scripts/migrate_vocabulary.py`、`scripts/import_reviewed_words.py` 改为支持考试系统和等级参数；专四使用 `TEM4_RU/TEM4`，来源 `word_sources.id=2`，不得写入专八记录。
- OCR 候选共 3999 条；按专八清洗规则保留 3925 条，剔除 74 条封面、标题、格变化标记、重复候选或明显非词条。OCR 风险审核发现 369 条，包含 296 条建议修正、35 条疑似词组/句子、38 条需人工确认。
- 审核文件：`data/processed/words/tem4_words_review_simple.csv`；人工复核子表：`data/processed/words/tem4_words_review_only.csv`；剔除记录：`data/processed/words/tem4_words_removed_nonwords.csv`。
- 专四词源已登记为 `ocr_done + in_review`，但尚未把任何未审核词条写入正式 `vocabulary_items`；正式入库只能使用用户审核后标为 `approved` 的行。
- 数据库回退备份：`data/processed/backups/russian_ai_tutor_before_tem4_words_source_20260828_175512.sqlite`、`data/processed/backups/russian_ai_tutor_before_tem4_words_source_refresh_20260828_175701.sqlite`。
- 本机 OCR 依赖为 `pypdfium2` 和 `Pillow`；Tesseract 语言包使用 `rus+chi_sim`。继续遵守既有规则：不全局替换 `ё/е`，不凭猜测补齐无法识别词条，正式词库只收审核通过项。

### 5.16 专四词汇高风险 OCR 本地模型复核 checkpoint（2026-08-28）

对专四审核表中 73 条高风险记录进行逐页、逐块复核：结合俄文词形、词性、中文释义和原始 OCR 块进行保守修正。

- 41 条可可靠还原并标为 `approved`，例如 `Щв`→`в`、`кнгск`→`киоск`、`эконбомия`→`экономия`、`капля B M6pe`→`капля в море`。
- 28 条确认是例句、固定短语、格变化标记、页码或版式噪声，标为 `rejected`，不进入背词库。
- 3 条仅凭当前 OCR 无法安全还原，继续标为 `needs_review`；用户确认第 154 页第 2 块无法确认，已直接移除并保留删除审计记录。
- 预览导入结果为 41 条新增、0 条更新、0 条跳过；尚未执行正式数据库导入，专四正式词条仍为 0。
- 复核脚本：`scripts/apply_tem4_word_llm_review.py`；复核报告：`data/processed/words/tem4_words_llm_review_report.json`；人工复核子表已同步为 3 条：`data/processed/words/tem4_words_review_only.csv`；删除记录：`data/processed/words/tem4_words_removed_by_llm.csv`。
- 正式导入增加内容闸门：词头含替换字符或非俄文字母、中文释义为空、释义开头混入孤立词性标记时，即使状态误为 `approved` 也会拦截；`ё/е` 仍只允许逐词核对，禁止全局替换。

### 5.17 专四剩余 OCR 人工确认更新 checkpoint（2026-08-28）

- 用户确认第 134 页第 1 块为 `лишать`，并要求保留完成体 `лишить`；已作为“未完成体 `лишать` / 完成体 `лишить`”写入词条释义。
- 用户确认第 332 页第 2 块为 `центральный`；已修正为形容词并补全中心、中央、核心及相关搭配释义。
- 第 143 页第 6 块仍无法判断，继续保留 `needs_review`，不猜测入库。
- 当前专四审核表 3924 条：43 条 `approved`、28 条 `rejected`、1 条 `needs_review`、3852 条 `pending`；正式数据库尚未导入。
- 审核表回退备份：`data/processed/backups/tem4_words_review_simple_before_llm_review_20260828_181452.csv`。
