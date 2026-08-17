# Grading Workflow Prototype

> 本文档记录俄语专八练习卷的答题、批改、错题统计和入库流程。
> 当前是脚本原型，后续会接入学生端网页。

## 1. 脚本位置

```text
scripts/grade_quiz.py
```

## 2. 生成答案模板

先根据练习卷生成学生答案模板：

```text
.venv\Scripts\python.exe scripts\grade_quiz.py --quiz data\processed\quizzes\tem8_quiz_20260817.json --create-answer-template
```

默认输出：

```text
data\processed\reports\tem8_quiz_20260817_answers_template.json
```

模板结构：

```json
{
  "quiz_path": "...",
  "answers": [
    {
      "quiz_number": 1,
      "question_id": 85,
      "selected_answer": ""
    }
  ]
}
```

学生答案填入 `selected_answer`，例如 `A`、`B`、`C`、`D`。

## 3. 批改但不入库

用于测试或临时查看报告：

```text
.venv\Scripts\python.exe scripts\grade_quiz.py --quiz data\processed\quizzes\tem8_quiz_20260817.json --answers data\processed\reports\tem8_quiz_20260817_sample_answers.json
```

输出报告默认放在：

```text
data\processed\reports\
```

## 4. 批改并入库

正式记录一次答题：

```text
.venv\Scripts\python.exe scripts\grade_quiz.py --quiz data\processed\quizzes\tem8_quiz_20260817.json --answers data\processed\reports\tem8_quiz_20260817_sample_answers.json --persist --title "TEM8 smoke test quiz"
```

入库内容：

- `quiz_sessions`: 一次测试会话
- `quiz_items`: 本次测试中的题目
- `user_answers`: 学生答案和是否正确
- `weakness_snapshots`: 按知识点统计的薄弱点快照

## 5. 当前验证结果

已用正式模式验证一份 10 题练习卷：

- 测试会话：`quiz_session_id = 1`
- 总题数：10
- 答对：7
- 正确率：0.7
- 写入题目记录：10
- 写入答案记录：10
- 写入薄弱点快照：4

测试薄弱点示例：

- `culture`: 2 题，错 1 题，正确率 0.5
- `grammar`: 3 题，错 0 题，正确率 1.0
- `literature`: 1 题，错 1 题，正确率 0.0
- `reading`: 4 题，错 1 题，正确率 0.75

## 6. 后续接入网页端

网页端需要复用这套逻辑：

- 展示题目
- 收集学生选择
- 提交答案
- 自动批改
- 展示正确率
- 展示错题列表
- 展示薄弱知识点
- 进入 AI 中文讲解和巩固练习
