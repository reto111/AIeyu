# TEM8 Knowledge Sources

本目录存放 AI 出题前使用的“出题依据库”文本。

注意：

- 这里不是正式题库。
- 这里的内容用于给 AI 生成题目草稿提供依据。
- AI 生成题必须进入 `needs_review`，人工审核后才能进入学生练习池。
- 官方考试大纲、教材摘录、文学国情资料等应放在这里或由脚本转换后放入这里。

建议文件格式：

```text
---
title: 资料标题
source_type: syllabus / grammar_note / literature_note / culture_note / reading_note / manual_note
question_type: grammar_choice
knowledge_points: grammar.case, grammar.aspect
language: zh
trust_level: 1-5
review_status: draft / reviewed
notes: 资料说明
---

## [knowledge.point] 知识块标题

知识块正文。
```

当前 `grammar_outline_manual.md` 是人工整理草稿，不是官方大纲。后续拿到正式资料后，应单独导入并标注为 `syllabus` 或 `reference_book`。
