# Question Review Workflow

> 本文档记录俄语专八题库的人工审核流程。
> 当前产品面向学生端，但内容入库仍需要人工审核，避免题干、答案、来源和知识点出错。

## 1. 当前审核对象

当前待审核对象是 2019、2021、2023 年俄语专八文字版真题切分结果。

数据库状态：

- 题目：150 道
- 选项：600 个
- 阅读文章：15 篇
- 审核状态：全部 `needs_review`
- 内容来源：全部 `past_exam_original`
- 来源标签：全部必须展示，例如 `2019 年俄语专八真题`

## 2. 导出审核表

运行：

```text
.venv\Scripts\python.exe scripts\export_review_sheet.py
```

默认输出：

```text
data\processed\review_sheets\tem8_questions_review.csv
```

该目录不提交到 Git，避免提交真题内容。

只导出某一年：

```text
.venv\Scripts\python.exe scripts\export_review_sheet.py --year 2019
```

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
- `passage_body`: 阅读文章全文，非阅读题为空

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


