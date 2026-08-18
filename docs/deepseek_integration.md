# DeepSeek API Integration

> 本文档记录 DeepSeek API 在 AIeyu 项目中的第一版接入方式。
> API Key 只放在本地环境变量或 `.env`，不提交到 Git。

## 1. 官方接口依据

DeepSeek API 当前兼容 OpenAI Chat Completions 风格：

- Base URL: `https://api.deepseek.com`
- Endpoint: `/chat/completions`
- 推荐模型：`deepseek-v4-flash`、`deepseek-v4-pro`

旧模型名 `deepseek-chat` 和 `deepseek-reasoner` 已在 2026-07-24 弃用，不应在本项目中继续使用。

## 2. 本地配置

复制：

```text
.env.example -> .env
```

然后填写：

```text
DEEPSEEK_API_KEY=你的 DeepSeek API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_THINKING=disabled
DEEPSEEK_REASONING_EFFORT=high
```

也可以只在当前 PowerShell 设置：

```text
$env:DEEPSEEK_API_KEY="你的 DeepSeek API Key"
```

注意：`.env` 已被 `.gitignore` 忽略，不会提交。

## 3. 调用脚本

```text
scripts\call_deepseek_tutor.py
```

调用：

```text
.venv\Scripts\python.exe scripts\call_deepseek_tutor.py --prompt data\processed\tutor_prompts\tem8_quiz_20260817_sample_report_persisted_tutor_prompt.json
```

默认输出：

```text
data\processed\tutor_outputs\
```

输出包括：

- JSON：包含 DeepSeek 原始响应和 assistant 文本
- Markdown：方便人工阅读的讲解结果

## 4. 写入对话表

如果希望把讲解保存到数据库：

```text
.venv\Scripts\python.exe scripts\call_deepseek_tutor.py --prompt data\processed\tutor_prompts\tem8_quiz_20260817_sample_report_persisted_tutor_prompt.json --persist
```

会写入：

- `ai_tutor_threads`
- `ai_tutor_messages`

注意：如果 prompt 包包含完整题干、选项和阅读原文，调用 DeepSeek 前需要明确确认允许把这些内容发送到外部模型服务。

学生端网页的正式入口是批改接口：

```text
POST /api/grade
```

该接口会先写入批改记录，再同步调用 DeepSeek，最后一次性返回批改结果、逐题讲解和整体复习建议。

内部调试仍保留单独讲解入口：

```text
POST /api/explain
```

该接口会从数据库读取指定 `quiz_session_id` 的错题、选项、学生答案、正确答案、来源标签和薄弱点，套用 `prompts\tutoring\tem8_wrong_question_tutor.md`，调用 DeepSeek 生成深度中文讲解，并写入 `ai_tutor_threads` / `ai_tutor_messages`。

当前提示词要求 DeepSeek 只返回 JSON：

```json
{
  "question_explanations": [
    {
      "quiz_number": 1,
      "question_id": 123,
      "explanation_zh": "..."
    }
  ],
  "study_advice_zh": "..."
}
```

前端显示规则：

- `question_explanations`: 放入对应错题下方。
- `study_advice_zh`: 放入 AI 对话区，包含薄弱点排序、复习方案、巩固练习和可追问问题。
- 不再输出“本次表现”。

接口必须收到：

```json
{
  "quiz_session_id": 1,
  "confirm_external_send": true
}
```

如果没有 `confirm_external_send = true`，`/api/explain` 必须拒绝调用 DeepSeek。学生端原型按用户确认规则在 `/api/grade` 中自动同步调用 DeepSeek；商业化前应补充隐私政策和服务条款确认。

## 5. 学生追问

初始讲解写入对话表后，可以基于同一个线程继续追问：

```text
.venv\Scripts\python.exe scripts\followup_deepseek_tutor.py --thread-id 1 --message "第2题为什么不能选A？请再用更简单的话解释。"
```

追问会读取该线程历史，并把新问题与模型回答继续写入 `ai_tutor_messages`。

## 6. 模型选择建议

第一阶段建议：

- 默认：`deepseek-v4-flash`
- 更高质量讲解：`deepseek-v4-pro`

讲解和错题分析默认可以使用：

```text
DEEPSEEK_THINKING=disabled
```

如果后续做更复杂的学习规划，可以开启：

```text
DEEPSEEK_THINKING=enabled
DEEPSEEK_REASONING_EFFORT=high
```
