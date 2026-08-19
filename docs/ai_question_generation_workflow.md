# AI 生成题草稿流程

> 本文档记录 AIeyu 第一版 AI 生成选择题草稿流程。

## 1. 目标

AI 生成题用于补充弱项训练题库，但不能直接进入学生练习池。

第一版先支持选择题草稿，重点验证：

- 从出题依据库检索知识块。
- 生成符合格式的单项选择题。
- 做基础格式校验和防照抄检查。
- 写入数据库为 `needs_review`。
- 后续通过人工审核后才进入练习池。

## 2. 默认安全模式

生成脚本默认是 dry run。

dry run 只会：

- 检索知识块。
- 生成待发送给 DeepSeek 的 prompt 包。
- 保存到 `data/processed/ai_question_generation/`。

dry run 不会：

- 调用 DeepSeek。
- 发送扫描书内容。
- 写入题库。

## 3. Dry Run

示例：

```text
.venv\Scripts\python.exe scripts\generate_ai_question_drafts.py --question-type culture_choice --knowledge-point culture --query "卫国战争" --count 2 --chunks-limit 3
```

输出会包含：

```text
status = dry_run
prompt_path = ...
retrieved_chunk_ids = ...
```

## 4. 真实调用

只有在确认允许把检索到的知识块发送给 DeepSeek 后，才运行：

```text
.venv\Scripts\python.exe scripts\generate_ai_question_drafts.py --question-type culture_choice --knowledge-point culture --query "卫国战争" --count 2 --chunks-limit 3 --confirm-external-send --persist
```

真实调用会：

- 调用 DeepSeek。
- 校验返回 JSON。
- 检查每题是否有题干、四个选项、唯一正确答案和中文解析。
- 检查题干是否直接出现在知识块正文里。
- 检查题干是否和已有题过于相似。
- 写入 `questions` / `question_options` / `question_knowledge_points`。
- 写入 `question_generation_references`，保留生成依据知识块。

## 5. 入库状态

AI 生成题入库状态固定为：

```text
review_status = needs_review
generation_status = ai_draft
content_origin = ai_generated
source_label = AI 生成题草稿
requires_source_label = 0
similarity_review_status = not_checked
```

因此不会被学生端随机组卷抽到。

学生端只抽：

```text
review_status = approved
source_usage = practice
```

## 6. 人工审核

AI 生成题可以继续使用现有审核表导出流程：

```text
.venv\Scripts\python.exe scripts\export_review_sheet.py
```

审核通过后再回写为 `approved`。

## 7. 当前限制

第一版只是基础链路，还不是最终质检系统。

后续需要补：

- 更强的相似度检查。
- 选项唯一性验证。
- 答案自洽二次审查。
- 按知识点批量生成。
- 前端审核页面。
- 文学、国情资料来源可靠性标注。
