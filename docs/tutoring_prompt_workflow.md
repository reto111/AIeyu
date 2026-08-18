# Tutoring Prompt Workflow Prototype

> 本文档记录 AI 私教讲解提示词和输入上下文的第一版流程。
> 当前只生成给大模型使用的 prompt 包，还没有真正调用模型 API。

## 1. 提示词模板

```text
prompts\tutoring\tem8_wrong_question_tutor.md
```

核心要求：

- 中文讲解为主。
- 俄语题干、选项和例句保留俄语。
- 必须保留真题来源标签。
- 不编造官方解析、年份、题号或来源。
- 粗知识点要明确说明仍需细化。
- 输出应像私人俄语老师，而不是简单答案表。
- 错题讲解不能停留在“你选了什么、正确答案是什么”。
- 语法题需要包含考察点、易错点、选项逐项辨析；词义辨析题还需要整理选项词义、搭配、用法差异和可靠的同根词/派生词。
- 文学题需要介绍作品、作者、文学时期、流派或术语背景；选项涉及多个作家时，需要列出各作家的代表作品。
- 国情题需要补充历史、地理、政治制度、文化常识或中俄名称对应关系。
- 输入资料不足时必须说明需要核验，不能编造。

## 2. 构建提示词输入包

脚本：

```text
scripts\build_tutor_prompt.py
```

运行：

```text
.venv\Scripts\python.exe scripts\build_tutor_prompt.py --report data\processed\reports\tem8_quiz_20260817_sample_report_persisted.json --remediation data\processed\remediation\tem8_quiz_20260817_sample_report_persisted_remediation.json
```

默认输出：

```text
data\processed\tutor_prompts\
```

输出包括：

- JSON：后续 API 调用可直接使用
- Markdown：便于人工预览 prompt 内容

## 3. 输入内容

输入包包含：

- 测试正确率
- 错题列表
- 学生选择
- 正确答案
- 错题选项
- 阅读题原文
- 粗知识点标签
- 真题来源标签
- 薄弱点统计
- 巩固练习安排

2026-08-17 更新：第一次真实 DeepSeek 调用发现，过于精简的 prompt 会导致模型缺少选项和阅读原文，阅读题讲解不够具体。因此后续 prompt 包会从数据库补全错题上下文：

- 题干
- 选项
- 正确答案
- 学生答案
- 来源年份和来源标签
- 阅读文章全文，若为阅读题

## 4. 后续要做

当前已接入 DeepSeek API。后续需要把网页端“生成 AI 讲解”按钮接入这一套增强提示词：

- 将 `system_prompt` 作为系统提示词。
- 将 `user_payload` 作为用户输入。
- 输出中文错题讲解。
- 保存到 `ai_tutor_threads` 和 `ai_tutor_messages`。
- 支持学生在单题或整份报告下继续追问。
