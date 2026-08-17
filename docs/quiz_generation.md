# Quiz Generation Prototype

> 本文档记录俄语专八练习卷生成脚本的第一版规则。
> 当前脚本服务于后续学生端组卷逻辑验证，还不是最终网页功能。

## 1. 脚本位置

```text
scripts/generate_quiz.py
```

默认输出目录：

```text
data/processed/quizzes/
```

该目录不提交到 Git。

## 2. 默认组卷规则

正式组卷默认只抽取：

```text
review_status = 'approved'
source_usage = 'practice'
```

这保证学生端不会直接使用未审核题。

当前 2019、2021、2023 的 150 道题已经由用户确认批量审核通过，默认模式可以正式组卷。

## 3. 内部测试模式

为了在审核前验证组卷结构，可以使用内部测试参数：

```text
.venv\Scripts\python.exe scripts\generate_quiz.py --count 5 --type grammar_choice --include-needs-review --seed 42
```

注意：`--include-needs-review` 只能用于内部流程测试，不能作为学生正式练习入口。

## 4. 常用参数

生成 10 题随机练习：

```text
.venv\Scripts\python.exe scripts\generate_quiz.py --count 10
```

限定题型：

```text
.venv\Scripts\python.exe scripts\generate_quiz.py --count 10 --type grammar_choice
```

限定多个题型：

```text
.venv\Scripts\python.exe scripts\generate_quiz.py --count 10 --type grammar_choice --type reading_choice
```

限定年份：

```text
.venv\Scripts\python.exe scripts\generate_quiz.py --count 10 --year 2021
```

固定随机种子，便于复现：

```text
.venv\Scripts\python.exe scripts\generate_quiz.py --count 10 --seed 42
```

## 5. 输出结构

生成的 JSON 每题包含：

- `question_id`: 数据库题目 ID
- `question_type`: 题型
- `stem`: 题干
- `options`: 选项
- `answer_key`: 正确答案
- `source.label`: 来源标签，例如 `2021 年俄语专八真题`
- `source.content_origin`: 内容来源，例如 `past_exam_original`
- `review_status`: 审核状态
- `knowledge_point_codes`: 已绑定知识点代码
- `passage`: 阅读文章，非阅读题为空

历年真题原题进入组卷时，必须保留并展示 `source.label`。

## 6. 后续要接入的能力

后续网页学生端需要在此基础上增加：

- 题目数量选择
- 题型选择
- 年份或综合随机模式
- 答题提交
- 自动批改
- 错题知识点统计
- 中文讲解与追问窗口
