# AIeyu Word Check-in Plan

> 本文档记录单词数据库与单词打卡功能的建设流程。
> 当前词库来源：`data/words/tem8_russian_words.pdf`。

## 1. 当前判断

- `data/words` 目录已有 `tem8_russian_words.pdf`。
- PDF 共 292 页。
- 抽样检测前 10 页均无可直接提取的文本层。
- 因此第一版按扫描版 PDF 处理：先 OCR，再清洗和人工校对，最后入结构化数据库。
- 已完成全量 OCR：292 页均生成逐页文本。
- OCR 合并文本：`data/processed/words/ocr_text/tem8_russian_words_ocr_combined.txt`。
- OCR manifest：`data/processed/words/ocr_text/tem8_russian_words_ocr_manifest.json`。
- 已生成候选词校对表：`data/processed/words/tem8_words_review.csv`。
- 当前候选词条数：4184 条，其中 3658 条自动解析，526 条需要重点人工复核。
- 已创建单词模块数据库表。
- 当前正式单词表 `vocabulary_items` 已按保守策略导入 753 条，全部来自用户确认过的修正候选；不直接导入未人工审核的简化主表。
- 已生成低风险简化校对表：`data/processed/words/tem8_words_review_simple.csv`。
- 简化校对表当前保留 3199 条，不含拉丁字母/数字词形；`ё/e` 只做低风险纠错，真实 `ё` 保留。
- 需人工处理表：`data/processed/words/tem8_words_needs_manual.csv`，当前 985 条，其中 402 条为 `ё/e` 不确定项。
- 本地 AI 修正候选表：`data/processed/words/tem8_words_local_correction_candidates.csv`，共 897 条，用户已审核通过。
- 正式入库 CSV：`data/processed/words/tem8_words_approved_import.csv`，默认由已审核修正候选生成，当前 753 条。简化主表 3199 条需单独人工审核后，才能使用 `--include-simple` 合并入库。

## 2. 功能定位

单词打卡是 AIeyu 的独立学习模块，但要和现有学生账号体系打通。

第一版目标：

1. 建立俄语专八单词数据库。
2. 支持按学生账号记录每日背词。
3. 支持认识 / 模糊 / 不认识 / 已掌握等学习状态。
4. 支持按遗忘曲线或简单规则安排复习。
5. 后续可接入 AI 例句、词根词缀、词义辨析和真题关联。

第一版不做：

- 复杂社交排行。
- 商业化会员体系。
- 完整移动端 App。
- 大规模词典版权数据接入。

## 3. 数据原则

单词库必须进入结构化数据库，不应只做成 RAG。

原因：

- 单词需要去重、排序、分级、打卡、复习计划和掌握度统计。
- 学生的背词记录必须按 `user_id` 隔离。
- 后续要支持按考试等级、词性、主题、词频和掌握状态筛选。

RAG 只作为辅助：

- 查询词根词缀解释。
- 查询教材或讲义中的例句。
- 支持 AI 对话追问。
- 给 AI 生成词义辨析和记忆提示提供依据。

## 4. 推荐数据库表

第一版新增 5 类表。

### word_sources

记录词库来源文件。

字段建议：

- `id`
- `exam_system_id`
- `level_id`
- `title`
- `file_path`
- `file_hash`
- `source_type`
- `ocr_status`
- `review_status`
- `created_at`
- `updated_at`

### vocabulary_items

保存单词主表。

字段建议：

- `id`
- `exam_system_id`
- `level_id`
- `word`
- `lemma`
- `accent`
- `part_of_speech`
- `meaning_zh`
- `meaning_en`
- `difficulty`
- `frequency_rank`
- `source_id`
- `source_page`
- `source_line`
- `review_status`
- `created_at`
- `updated_at`

### vocabulary_forms

保存变体、同根词、派生词和常见搭配。

字段建议：

- `id`
- `vocabulary_item_id`
- `form_text`
- `form_type`
- `meaning_zh`
- `notes`

`form_type` 示例：

- `inflected_form`
- `same_root`
- `derived_word`
- `collocation`
- `synonym`
- `antonym`

### user_word_progress

保存每个学生对每个词的掌握状态。

字段建议：

- `id`
- `user_id`
- `vocabulary_item_id`
- `status`
- `seen_count`
- `correct_count`
- `wrong_count`
- `last_seen_at`
- `next_review_at`
- `ease_factor`
- `created_at`
- `updated_at`

`status` 建议：

- `new`
- `learning`
- `fuzzy`
- `known`
- `mastered`

### word_review_logs

保存每一次背词作答记录。

字段建议：

- `id`
- `user_id`
- `vocabulary_item_id`
- `review_mode`
- `prompt_type`
- `user_response`
- `result`
- `reviewed_at`

`review_mode` 示例：

- `daily_checkin`
- `weak_review`
- `random_review`

`prompt_type` 示例：

- `ru_to_zh`
- `zh_to_ru`
- `choice`
- `spelling`

当前已在 `database/schema.sql` 和本地 SQLite 中创建上述表。

当前迁移脚本：

```text
scripts/migrate_vocabulary.py
```

人工审核后导入脚本：

```text
scripts/build_approved_word_import_sheet.py
scripts/import_reviewed_words.py
```

## 5. 建库流程

### Step 1. 文件登记

把 `data/words/tem8_russian_words.pdf` 登记到 `word_sources`。

需要记录：

- 文件路径
- 文件 hash
- 页数
- 是否需要 OCR
- 来源标题
- 对应考试：俄语专八

### Step 2. OCR

因为当前 PDF 没有文本层，需要 OCR。

推荐先走本地 OCR：

- 俄语识别语言：`rus`
- 如含中文释义，再加 `chi_sim`
- 输出每页原始 OCR 文本

输出目录建议：

```text
data/processed/words/ocr_text/
```

每页一个文件：

```text
tem8_russian_words_page_001.txt
tem8_russian_words_page_002.txt
...
```

当前已完成该步骤，执行脚本：

```text
scripts/ocr_word_pdf.py
```

### Step 3. 粗切分

从 OCR 文本中提取候选词条。

输出 CSV：

```text
data/processed/words/tem8_words_candidates.csv
```

字段建议：

```text
source_file, source_page, raw_line, word, lemma, part_of_speech, meaning_zh, notes, parse_status
```

第一版允许 `lemma`、`part_of_speech` 暂时为空，但 `word` 和 `meaning_zh` 必须尽量完整。

当前已完成该步骤，执行脚本：

```text
scripts/extract_word_candidates.py
```

当前额外生成了校对用 CSV：

```text
data/processed/words/tem8_words_review.csv
```

当前建议优先使用低风险简化版：

```text
data/processed/words/tem8_words_review_simple.csv
```

简化版处理原则：

- 不强行猜测中低置信 OCR 词形。
- `ё/e` 不做全量替换，只纠正明显由重音 OCR 导致的误识别，例如 `Амёрика` 输出为 `Америка`。
- 真实 `ё` 保留，例如 `актёр`、`берёзка`、`дирижёр`。
- 释义只保留中文关键词，去掉后续例句、词组和长解释。
- 无法可靠识别的词条进入 `tem8_words_needs_manual.csv`。

### Step 4. 人工校对

当前已完成：本地 AI 修正候选表已由用户确认。整体检查发现简化主表仍有少量明显 OCR 错词，因此正式库先采用更保守的导入策略，只导入用户确认过的 753 条修正候选。

生成校对表：

```text
data/processed/words/tem8_words_review.csv
```

校对重点：

- 俄文字符是否识别错。
- 重音符号是否保留或规范。
- 中文释义是否串行。
- 一行多个词是否拆开。
- 同一个词是否重复。
- 词性是否正确。
- 专八相关性是否明确。

人工审核字段：

```text
review_status, review_notes
```

审核状态：

- `approved`
- `needs_fix`
- `rejected`

### Step 5. 去重与规范化

入库前做规范化：

- 去掉前后空格。
- 统一俄文字母大小写。
- 统一 `ё` 和 `е` 的策略：第一版建议保留原词，同时在 notes 中记录变体。
- 相同 `lemma + part_of_speech` 合并。
- 释义相近但词性不同的词保留独立记录。

### Step 6. 入库

只导入 `review_status = approved` 的词。

入库目标：

- `word_sources`
- `vocabulary_items`
- 可选：`vocabulary_forms`

导入后生成统计：

- 总词数
- 已审核词数
- 重复词数
- 需要修复词数
- 被拒绝词数

### Step 7. 前端打卡 MVP

新增“单词”页面。

第一版页面包含：

- 今日单词数量设置。
- 开始打卡。
- 显示俄语词，学生选择认识程度。
- 展示中文释义。
- 记录当前学生学习状态。
- 显示今日完成数、待复习数、掌握词数。

第一版按钮建议：

- 不认识
- 模糊
- 认识
- 已掌握

### Step 8. 复习规则

先用简单规则，不上复杂算法。

建议：

- `不认识`：明天复习。
- `模糊`：2 天后复习。
- `认识`：4 天后复习。
- `已掌握`：10 天后复习。

连续多次正确后提高间隔；答错后降回更短间隔。

### Step 9. AI 增强

在词库稳定后再接 AI。

AI 可做：

- 生成例句。
- 解释词根词缀。
- 整理同根词。
- 做词义辨析。
- 根据错词生成小测。

AI 生成内容进入正式展示前，建议保留人工审核状态。

## 6. 下一步执行顺序

建议下一轮开发按这个顺序：

1. 新增单词数据库表。
2. 写 PDF/OCR 检测脚本。
3. 对 `tem8_russian_words.pdf` 做 OCR。
4. 生成 `tem8_words_candidates.csv`。
5. 人工校对 CSV。
6. 导入已审核单词。
7. 新增学生端“单词”页面。
8. 接入每日打卡与复习记录。
