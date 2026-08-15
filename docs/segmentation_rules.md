# TEM8 Segmentation Rules

> 本文档记录俄语专八 PDF 提取文本的题目切分规则。
> 第一版先从文字版 `2019_full` 试验，输出待审核 JSON，不直接写入正式题库。

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
```

## 8. 验收标准

2019 样板切分通过标准：

- 总题量应为 50 道：综合知识 30 道，阅读理解 20 道。
- 每道题应有 4 个选项。
- 16-65 每题应匹配到答案。
- 阅读题应绑定 passage。
- 不应混入听力、翻译、写作内容。

## 9. 2019 样板结果

脚本：

```text
.venv\Scripts\python.exe scripts\segment_tem8_review_json.py data\processed\tem8_russian_2019_full.txt data\processed\structured\tem8_russian_2019_review.json --year 2019
```

当前结果：

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
```

该文件是中间处理结果，不提交到 Git。
