# Adaptive Exam Assistant Plan

> 本文档记录 AIeyu 从“俄语专八练习原型”调整为“个人 AI 自适应备考助手”的产品主线。

## 1. 新核心定位

AIeyu 的核心功能应明确为：

```text
一款面向小语种考试的 AI 自适应备考工具。
系统根据用户在目标考试中的真实作答表现建立能力画像，识别薄弱题型与知识点，并结合结构化题库、RAG 和 AI 生成题，持续提供个性化、不重复的专项训练。
```

第一阶段仍以俄语专八为 MVP，但产品架构应面向多考试、多等级、多用户扩展。

## 2. 当前进度对照

已经完成或基本跑通：

- 俄语专八第一版结构化题库。
- 2019、2021、2023 年专八题目导入与审核。
- 题型：语法、文学、国情、阅读。
- 结构化数据库 schema。
- 随机组卷。
- 默认随机组卷不包含阅读题。
- 页面作答。
- 自动批改。
- 按粗知识点统计薄弱点。
- DeepSeek 同步生成错题讲解。
- 逐题讲解显示在对应错题下方。
- 整体复习建议显示在 AI 对话区。
- AI 追问入口。
- GitHub 私有仓库同步。
- 阿里云 Windows Server 测试部署准备文档。

已经预留但尚未真正实现：

- `users` 表。
- `quiz_sessions`、`user_answers`、`weakness_snapshots` 等学习记录表。
- AI 生成题状态字段：`content_origin`、`generation_status`、`similarity_review_status`。
- RAG 作为辅助知识库的架构原则。

尚未实现但属于新核心的能力：

- 用户画像算法。
- 知识点掌握度长期累计。
- 题型掌握度长期累计。
- 题目曝光记录和不重复抽题。
- 薄弱点专项训练自动组卷。
- AI 生成题入库链路。
- AI 生成题相似度 / 重复度质检。
- RAG 检索接入讲解和出题流程。
- 用户账号或最小用户身份。

## 3. MVP 应调整为的产品闭环

新的 MVP 闭环应为：

```text
考试选择
-> 数据库组卷
-> 用户作答
-> 自动判分
-> AI 错题解析
-> 更新用户画像
-> 展示题型掌握度 / 知识点掌握度
-> 生成弱项专项训练
-> 如题量不足，进入 AI 生成题草稿
-> 相似度和质量检查
-> 人工审核
-> 进入正式训练题库
```

第一版可以先把“用户画像”和“不重复专项训练”做成规则算法，不急着上复杂机器学习。

## 4. 用户画像第一版算法

核心原则：

```text
用户画像不是让大模型“感觉学生哪里弱”，而是用结构化作答数据计算出来。
LLM 只负责解释画像结果、生成复习建议和辅助生成练习题。
```

### 4.1 画像维度

每个用户至少维护：

- 考试体系，例如 `TEM8_RU`
- 等级，例如 `TEM8`
- 题型掌握度，例如语法、文学、国情、阅读
- 知识点掌握度，例如语法、文学、国情、阅读下的细分点
- 最近答题记录
- 重复错误知识点
- 已做题目集合
- 最近训练模式

### 4.2 每次答题记录

每道题提交后至少记录：

```text
user_id
quiz_session_id
question_id
question_type
knowledge_points
selected_answer
correct_answer
is_correct
answered_at
source_year
content_origin
```

后续可扩展：

```text
answer_time_seconds
difficulty
confidence
viewed_explanation
asked_ai_followup
completed_remediation
```

### 4.3 掌握度评分

第一版建议使用可解释的规则模型：

```text
weighted_accuracy = 加权正确数 / 加权作答总数
mastery_score = round(weighted_accuracy * 100)
```

权重规则：

- 最近 20 次相关作答作为主要窗口。
- 最近作答权重大于历史作答。
- 最近 7 天作答权重最高。
- 很久以前的题权重降低。
- 题量少于 5 道时标记为 `insufficient_data`，不做过度判断。
- 最近连续错 2 次以上时，状态强制降一级。

### 4.4 输出状态

每个题型或知识点可输出：

```text
weak
unstable
stable
strong
insufficient_data
```

前端显示时应使用学生能理解的中文：

- 薄弱
- 不稳定
- 基本掌握
- 掌握较好
- 数据不足

分层规则：

```text
attempt_count < 5:
  insufficient_data

mastery_score < 60:
  weak

60 <= mastery_score < 75:
  unstable

75 <= mastery_score < 88:
  stable

mastery_score >= 88:
  strong
```

如果最近连续错 2 次以上，则在上述状态基础上降一级。

### 4.5 弱项优先级

弱项优先级不能只看正确率，还要看题量和最近错误。

第一版推荐：

```text
weakness_priority =
  错误率 * 50
  + 最近错误权重 * 30
  + 连续错误权重 * 20
```

优先推荐：

- 近期错得多。
- 相关题量足够。
- 对目标考试得分影响大。
- 已有足够未做题或可生成变式题。

### 4.6 MVP 最小指标

第一版最小实现以下指标：

```text
type_mastery_score
knowledge_mastery_score
attempt_count
wrong_count
last_wrong_at
recent_wrong_streak
mastery_status
weakness_priority
```

前端先展示：

- 题型掌握度
- 知识点掌握度
- 最薄弱 3 项
- 推荐下一次训练范围
- 已做题过滤状态

## 5. 不重复训练策略

需要记录用户已经做过哪些题，避免专项训练重复。

第一版规则：

- 随机组卷优先抽取用户未做过的题。
- 若未做题不足，再抽取较久以前做过但答错的题。
- 若仍不足，才允许抽取较久以前做对的题。
- 阅读题仍默认不进入随机卷，只作为阅读专项。
- 历年真题如果再次出现，必须继续显示来源标签。

需要新增或明确使用的数据：

```text
question_exposures
user_id
question_id
first_seen_at
last_seen_at
seen_count
last_result
```

如果暂时不新增表，也可以先从 `quiz_items + user_answers` 推导，但长期建议建表提升查询效率。

## 6. 数据表与计算产物建议

为了让用户画像可查询、可缓存、可解释，建议新增三类表。

### 6.1 题目曝光表

```text
question_exposures
- id
- user_id
- question_id
- first_seen_at
- last_seen_at
- seen_count
- correct_count
- wrong_count
- last_is_correct
- last_quiz_session_id
```

用途：

- 避免重复抽题。
- 识别旧错题。
- 支持 spaced repetition。

### 6.2 掌握度快照表

```text
mastery_snapshots
- id
- user_id
- exam_system_id
- level_id
- target_type: question_type / knowledge_point
- target_code
- attempt_count
- wrong_count
- weighted_accuracy
- mastery_score
- mastery_status
- recent_wrong_streak
- weakness_priority
- calculated_at
```

用途：

- 前端快速展示题型掌握度和知识点掌握度。
- 记录每次画像更新时间。
- 后续生成学习曲线。

### 6.3 推荐训练队列表

```text
training_recommendations
- id
- user_id
- exam_system_id
- level_id
- target_type
- target_code
- reason_code
- priority
- recommended_count
- status: active / used / dismissed
- created_at
```

用途：

- 存储“下一次建议练什么”。
- 支持首页直接展示推荐专项。
- 避免每次页面刷新都重新计算。

## 7. 掌握度计算细则

### 7.1 作答窗口

每个题型或知识点单独取最近作答：

```text
window_size = 20
min_attempts = 5
```

如果某个知识点最近作答不足 20 条，就使用全部历史相关作答，但少于 5 条时只输出 `insufficient_data`。

### 7.2 时间权重

推荐第一版采用简单时间权重：

```text
answered_at <= 7 天: weight = 1.0
7 天 < answered_at <= 30 天: weight = 0.7
30 天 < answered_at <= 90 天: weight = 0.4
answered_at > 90 天: weight = 0.2
```

计算：

```text
weighted_accuracy =
  sum(is_correct * weight) / sum(weight)

mastery_score =
  round(weighted_accuracy * 100)
```

### 7.3 连续错误

从最近一次作答往前数，连续错误次数：

```text
recent_wrong_streak = 最近连续 is_correct = false 的数量
```

状态降级规则：

```text
recent_wrong_streak >= 2:
  mastery_status 降一级

recent_wrong_streak >= 3:
  weakness_priority 额外 +10
```

状态等级从高到低：

```text
strong -> stable -> unstable -> weak
```

`insufficient_data` 不参与降级。

### 7.4 弱项优先级细则

```text
error_rate = wrong_count / attempt_count

recent_error_weight:
  最近 7 天有错 = 1
  最近 30 天有错 = 0.7
  最近 90 天有错 = 0.4
  否则 = 0

streak_weight:
  min(recent_wrong_streak, 3) / 3

weakness_priority =
  round(error_rate * 50 + recent_error_weight * 30 + streak_weight * 20)
```

修正规则：

- `attempt_count < 5` 时不标为正式弱项，但可提示“数据不足”。
- 如果题型或知识点在考试中高频，可后续增加 `exam_weight`。
- 如果该知识点可用题量不足，推荐时应提示“需要生成新题或补充题库”。

## 8. 专项训练选题算法

### 8.1 输入

```text
user_id
exam_system
level
target_type: question_type / knowledge_point
target_code
count
exclude_reading_by_default
```

### 8.2 候选题过滤

候选题必须满足：

```text
review_status = approved
source_usage = practice
exam_system / level 匹配
题型或知识点匹配
```

随机综合训练默认排除：

```text
reading_choice
```

阅读只在用户明确选择阅读专项时进入。

### 8.3 排序优先级

选题优先级：

```text
1. 从未做过的题
2. 做过但上次答错，且距离上次出现较久
3. 做过多次但错误率较高
4. 很久以前做对过的题
5. 最近做对过的题，尽量不选
```

可以转成排序分：

```text
selection_score =
  unseen_bonus
  + last_wrong_bonus
  + high_error_rate_bonus
  + old_seen_bonus
  - recent_correct_penalty
  - seen_count_penalty
```

第一版建议：

```text
unseen_bonus = 100 if seen_count = 0 else 0
last_wrong_bonus = 40 if last_is_correct = false else 0
high_error_rate_bonus = user_question_error_rate * 30
old_seen_bonus = days_since_last_seen capped at 30
recent_correct_penalty = 50 if last_is_correct = true and days_since_last_seen < 7 else 0
seen_count_penalty = seen_count * 5
```

### 8.4 题量不足时

如果候选题不足：

```text
1. 放宽到同父级知识点。
2. 放宽到同题型。
3. 加入旧错题。
4. 仍不足时触发 AI 生成题草稿。
```

触发 AI 生成题时，必须标记：

```text
generated_needed = true
generated_reason = insufficient_unseen_questions
```

## 9. API 输出建议

### 9.1 用户画像接口

```text
GET /api/profile
```

返回：

```json
{
  "user_id": 1,
  "exam_system": "TEM8_RU",
  "level": "TEM8",
  "question_type_mastery": [
    {
      "code": "grammar_choice",
      "name": "语法",
      "attempt_count": 12,
      "wrong_count": 5,
      "mastery_score": 58,
      "mastery_status": "weak",
      "weakness_priority": 76
    }
  ],
  "knowledge_mastery": [],
  "top_weaknesses": [],
  "next_training": {
    "mode": "weakness_review",
    "target_type": "question_type",
    "target_code": "grammar_choice",
    "count": 10
  }
}
```

### 9.2 弱项专项组卷接口

```text
POST /api/quiz/weakness
```

输入：

```json
{
  "count": 10,
  "target_type": "auto",
  "target_code": "auto"
}
```

如果 `target_type = auto`，系统从用户画像里选择最高优先级弱项。

返回应包含：

```json
{
  "mode": "weakness_review",
  "target": {
    "type": "question_type",
    "code": "grammar_choice",
    "name": "语法",
    "reason": "近期语法题错误率高"
  },
  "generated_needed": false,
  "questions": []
}
```

## 10. 弱项专项训练

弱项专项训练应基于用户画像生成：

```text
选择用户最薄弱的 1-3 个题型或知识点
-> 从未做过题中抽取
-> 不足时补充旧错题
-> 再不足时触发 AI 生成题候选
```

第一版入口可以是：

```text
开始弱项专项训练
```

输出：

- 本次训练目标
- 题量
- 覆盖知识点
- 是否含 AI 生成题
- 是否全部来自已审核题库

## 11. AI 生成题库链路

AI 生成题不能直接变成正式题库。

推荐链路：

```text
薄弱点识别
-> 提取相似真题结构和知识点
-> LLM 生成新题
-> 自动格式校验
-> 相似度 / 重复度检查
-> 答案和解析自检
-> review_pending
-> 人工审核
-> approved
-> 进入训练题库
```

需要避免重复：

- 不直接复刻历年真题题干。
- 不复用相同选项组合。
- 不生成与已入库题过高相似度的题。
- 每道 AI 生成题保留生成依据和审核状态。

AI 生成题字段建议：

```text
content_origin = ai_generated 或 ai_rewritten
source_usage = practice
generation_status = draft / review_pending / approved / rejected
similarity_review_status = not_checked / passed / flagged / failed
review_status = needs_review / approved
```

当前 schema 已有部分字段，下一步应补齐生成脚本和审核流程。

## 12. RAG 在新闭环中的位置

RAG 不替代题库，也不直接决定答案。

RAG 用于：

- 错题讲解补充依据。
- 文学和国情背景资料检索。
- 语法规则引用。
- AI 生成题时提供材料依据。
- 学生追问时降低幻觉。

第一版可先不接 RAGFlow，先把结构化题库、用户画像和不重复训练跑通。

## 13. 下一阶段开发优先级

建议下一步按以下顺序开发：

1. 最小用户身份：先支持单用户或本地默认用户。
2. 用户作答历史查询：按用户统计题型和知识点表现。
3. 用户画像快照：生成题型掌握度和知识点掌握度。
4. 题目曝光记录：避免重复抽题。
5. 弱项专项训练接口和页面入口。
6. AI 生成题草稿脚本。
7. AI 生成题自动校验和相似度检查。
8. 人工审核表和回写流程。
9. RAGFlow 小规模验证。

## 14. 对当前 MVP 的调整结论

当前项目已经完成“练习 - 批改 - AI 讲解”的半闭环。

现在应从普通刷题系统调整为：

```text
学生画像驱动的自适应训练系统
```

最关键的补齐项不是继续优化讲解，而是：

- 用户画像算法。
- 不重复选题机制。
- 弱项专项训练。
- AI 生成题和质检入库链路。

这些完成后，AIeyu 才真正具备“个人 AI 备考助手”的产品差异。
