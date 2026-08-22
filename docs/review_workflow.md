# Question Review Workflow

> 本文档记录俄语专八题库的人工审核流程。
> 当前产品面向学生端，但内容入库仍需要人工审核，避免题干、答案、来源和知识点出错。

## 1. 当前审核对象

当前待审核对象包括：

- 2017、2018、2024 年俄语专八真题切分结果。
- 后续 AI 生成题草稿。

数据库状态：

- 题目：150 道
- 选项：600 个
- 阅读文章：15 篇
- 审核状态：全部 `needs_review`
- 内容来源：全部 `past_exam_original`
- 来源标签：全部必须展示，例如 `2019 年俄语专八真题`
- 2019、2021、2023 年 150 道真题已经审核为 `approved`，不再属于当前待审核批次。

AI 生成题草稿状态：

- `review_status = needs_review`
- `content_origin = ai_generated`
- `generation_status = ai_draft`
- `source_label = AI 生成题草稿`
- 人工审核前不会进入学生练习池。

## 2. 导出审核表

运行：

```text
.venv\Scripts\python.exe scripts\export_review_sheet.py
```

默认输出：

```text
data\processed\review_sheets\tem8_questions_review.csv
data\processed\review_sheets\tem8_passages_review.csv
```

该目录不提交到 Git，避免提交真题内容。

导出结构：

- `tem8_questions_review.csv`: 题目、选项、答案、来源、`passage_id`、知识点、中文解析、AI 生成依据和审核结论。
- `tem8_passages_review.csv`: 阅读文章全文，每篇文章一行，通过 `passage_id` 与题目表对应。

注意：题目表不再重复放入阅读文章全文，避免阅读题在表格中显得被长文章打散。

只导出某一年：

```text
.venv\Scripts\python.exe scripts\export_review_sheet.py --year 2019
```

导出当前待审核批次：

```text
.venv\Scripts\python.exe scripts\export_review_sheet.py --year 2017 --year 2018 --year 2024 --output data\processed\review_sheets\tem8_2017_2018_2024_questions_review.csv --passages-output data\processed\review_sheets\tem8_2017_2018_2024_passages_review.csv
```

## 2.1 预填粗知识点

历年真题可先按题型预填粗知识点，减少人工审核表重复填写：

```text
.venv\Scripts\python.exe scripts\assign_coarse_knowledge_points.py --year 2017 --year 2018 --year 2024
```

对应关系：

- `grammar_choice` -> `grammar`
- `literature_choice` -> `literature`
- `culture_choice` -> `culture`
- `reading_choice` -> `reading`

该脚本只写入 `question_knowledge_points`，不会把题目改为 `approved`。

## 3. 审核表关键列

系统字段：

- `question_id`: 数据库题目 ID
- `source_year`: 来源年份
- `source_question_number`: 原题号
- `source_label`: 前端必须展示的来源标签
- `question_type`: 题型
- `stem`: 题干
- `option_a` 到 `option_d`: 选项
- `correct_answer`: 正确答案
- `explanation_zh`: 中文解析；AI 生成题必须重点检查解析是否支撑答案
- `passage_id`: 阅读文章 ID，非阅读题为空
- `passage_title`: 阅读文章标题，非阅读题为空
- `generation_status`: AI 生成或人工导入状态
- `similarity_review_status`: 相似度检查状态
- `generation_references`: AI 生成题使用的知识块来源
- `source_basis_zh`: AI 生成题自述的依据摘要

人工填写字段：

- `knowledge_point_codes`: 知识点代码，多个用英文逗号分隔，例如 `grammar.aspect,grammar.lexical_choice`
- `review_decision`: 建议填写 `approved`、`needs_review`、`needs_fix` 或 `rejected`
- `review_notes`: 记录题干问题、答案疑问、OCR/切分错误或讲解备注

## 4. 审核标准

每道题至少检查：

- 题干是否完整，俄文字符是否正确。
- 四个选项是否完整，顺序是否正确。
- 正确答案是否与答案 PDF 或原始材料一致。
- 阅读题是否关联正确文章。
- 来源年份和原题号是否正确。
- 历年真题来源标签是否保留。
- 至少绑定一个知识点。

如果是 AI 生成题，还需要额外检查：

- 是否照抄真题、参考书题干或选项。
- 是否只是把已有题换了选项顺序。
- 是否有唯一正确答案。
- 中文解析是否能支撑答案。
- 题目是否符合专八难度和题型风格。

审核结论建议：

- `approved`: 可以进入学生练习池。
- `needs_fix`: 需要修正题干、选项、答案、文章或标签。
- `rejected`: 暂不使用。

## 5. 回写审核结果

填完审核表后，先干跑检查：

```text
.venv\Scripts\python.exe scripts\apply_review_sheet.py --dry-run
```

确认无误后正式回写：

```text
.venv\Scripts\python.exe scripts\apply_review_sheet.py
```

回写规则：

- `approved`: 题目状态写为 `approved`，可进入练习池。
- `rejected`: 题目状态写为 `rejected`，不进入练习池。
- `needs_review`: 题目状态保持 `needs_review`。
- `needs_fix`: 题目状态保持 `needs_review`，同时在审核日志中记录需要修改的原因。

如果 `review_decision = approved`，默认必须填写至少一个 `knowledge_point_codes`。如确有特殊情况，可加：

```text
--allow-approved-without-knowledge
```

每次回写都会向 `question_review_logs` 写入一条审核日志，保留审核结论、备注和当次知识点代码。

## 6. 正式组卷规则

正式组卷只应抽取：

```text
review_status = 'approved'
source_usage = 'practice'
```

如果题目是历年真题原题，前端必须展示：

```text
source_label
```


