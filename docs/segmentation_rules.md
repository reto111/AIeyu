# TEM8 Segmentation Rules

> 本文档记录俄语专八 PDF 提取文本的题目切分规则。
> 第一版先从文字版 `2019_full` 试验，输出待审核 JSON。历年真题可以用于组卷，但必须显示来源年份。

## 1. 当前策略

第一阶段只切分第一版需要的客观题：

- 综合知识：16-45
- 阅读理解：46-65

暂时跳过：

- 口语表述
- 听力理解
- 翻译
- 写作

## 2. 题型映射

综合知识题号暂按以下规则映射：

- 16-32: `grammar_choice`
- 33-39: `literature_choice`
- 40-45: `culture_choice`
- 46-65: `reading_choice`

该映射需要人工校对，尤其 33-45 中可能存在文学、艺术、国情交叉内容。

## 3. 题目边界

文字版题目通常使用独立题号行：

```text
16
题干
A. ...
B. ...
C. ...
D. ...
```

阅读题中也可能出现题号和题干同一行：

```text
50 Как автор формулирует понятие мечты?
```

脚本同时支持这两种形式。

## 4. 选项识别

选项支持拉丁字母和俄文字母混排：

```text
A. / А.
B. / В.
C. / С.
D. / Д.
```

脚本会标准化为：

```text
A
B
C
D
```

## 5. 阅读题处理

阅读理解以 `文章1`、`文章2` 等作为 passage 边界。

每道阅读题输出时会携带：

- passage title
- passage body
- question stem
- options
- answer

后续入库时，passage 应进入 `passages` 表，小题进入 `questions` 表并关联 `passage_id`。

## 6. 答案匹配

2019 文本末尾包含 `答案` 区。

答案区采用题号块加答案块排版：

```text
16
17
18
B
A
C
```

脚本会按顺序配对为：

```text
16 -> B
17 -> A
18 -> C
```

## 7. 输出格式

脚本输出待审核 JSON：

```text
data/processed/structured/tem8_russian_2019_review.json
```

所有题目默认：

```text
review_status = needs_review
source_usage = practice
content_origin = past_exam_original
requires_source_label = true
source_label = "<年份> 年俄语专八真题"
eligible_for_quiz_after_approval = true
```

这些切分结果需要人工审核；审核后可以用于学生组卷，但必须展示来源标签。

## 8. 验收标准

2019 样板切分通过标准：

- 总题量应为 50 道：综合知识 30 道，阅读理解 20 道。
- 每道题应有 4 个选项。
- 16-65 每题应匹配到答案。
- 阅读题应绑定 passage。
- 不应混入听力、翻译、写作内容。

## 9. 当前文字版切分结果

脚本：

```text
.venv\Scripts\python.exe scripts\segment_tem8_review_json.py data\processed\tem8_russian_2019_full.txt data\processed\structured\tem8_russian_2019_review.json --year 2019
.venv\Scripts\python.exe scripts\segment_tem8_review_json.py data\processed\tem8_russian_2021_full.txt data\processed\structured\tem8_russian_2021_review.json --year 2021
.venv\Scripts\python.exe scripts\segment_tem8_review_json.py data\processed\tem8_russian_2023_full.txt data\processed\structured\tem8_russian_2023_review.json --year 2023
```

2019、2021、2023 当前结果均为：

```text
total_questions: 50
grammar_choice: 17
literature_choice: 7
culture_choice: 6
reading_choice: 20
missing_options: 0
missing_answers: 0
reading_passages: 5
questions_per_passage: 4
```

待审核 JSON：

```text
data/processed/structured/tem8_russian_2019_review.json
data/processed/structured/tem8_russian_2021_review.json
data/processed/structured/tem8_russian_2023_review.json
```

这些文件是中间处理结果，不提交到 Git；人工审核后才能导入可组卷题库。

验证脚本：

```text
.venv\Scripts\python.exe scripts\validate_review_json.py data\processed\structured\tem8_russian_2019_review.json data\processed\structured\tem8_russian_2021_review.json data\processed\structured\tem8_russian_2023_review.json
```

## 10. 已修正的切分问题

- 俄语句首 `В ...` 可能被误识别成 `B` 选项；规则已改为选项字母后必须紧跟 `.` 或 `)`。
- 阅读文章正文中的数字，例如 `48 странах мира`，可能被误识别成题号；规则已改为每篇文章按预期起始题号切分：46、50、54、58、62。

## 11. OCR / 新版排版待处理

2024 OCR 版暂不能使用当前文字版规则自动切分。

已观察到的差异：

- 章节标题使用俄文：`ГРАММАТИКА, ЛЕКСИКА И СТИЛИСТИКА`、`ЧТЕНИЕ`。
- 题号格式为 `16.`、`17.`，不是独立数字行。
- 选项可能同一行并排出现，例如 `А) ... В) ...`。
- OCR 会把 `D)` 识别成 `2)`、`О)`、`р)` 等，需要单独标准化。
- 2024 文本后半部分似乎包含带 `Задание` 的材料或答案/解析页，需要先区分试卷正文和后附内容。

因此后续应增加 `ocr_layout` 切分模式，而不是把 2024 强行套用 2019/2021/2023 的文字版规则。

当前决策：

- OCR 解析的扫描/照片版资料可以暂时放一放。
- 优先处理 2019、2021、2023 文字版真题。
- 历年真题可用于组卷，但题目展示和解析中必须标注来源年份。
