# Tutor Follow-up Workflow Prototype

> 本文档记录 AI 私教讲解后的追问流程。
> 当前是脚本原型，后续会接入学生端对话窗口。

## 1. 脚本位置

```text
scripts\followup_deepseek_tutor.py
```

## 2. 输入

需要已有对话线程 ID，例如：

```text
ai_tutor_threads.id = 1
```

这个线程由 `scripts\call_deepseek_tutor.py --persist` 创建。

## 3. 追问

示例：

```text
.venv\Scripts\python.exe scripts\followup_deepseek_tutor.py --thread-id 1 --message "第2题为什么不能选A？请再用更简单的话解释。"
```

脚本会：

- 读取该线程下已有 system/user/assistant 历史消息。
- 追加学生追问。
- 调用 DeepSeek。
- 将学生追问和模型回答写回 `ai_tutor_messages`。
- 输出 JSON 和 Markdown 结果到 `data\processed\tutor_outputs\`。

## 4. 隐私与授权

追问调用会把该对话线程历史和学生新问题发送到 DeepSeek。

如果线程中包含真题题干、选项、阅读原文或学生学习表现，正式调用前需要确认用户同意发送这些内容到外部模型服务。

## 5. 后续接入网页端

网页端对话窗口可以复用这个流程：

- 打开某次测试报告。
- 展示 AI 初始讲解。
- 学生继续追问。
- 前端提交 `thread_id` 和 `message`。
- 后端调用 DeepSeek 并保存回复。
