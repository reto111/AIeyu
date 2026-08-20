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
- 检查题干、选项和解析组成的整体内容是否和已有题或同批次题目过于相似。
- 对国情 `difficulty = 4` 做基础深度检查，避免单纯名称、位置或单点事实题伪装成高难度题。
- 写入 `questions` / `question_options` / `question_knowledge_points`。
- 写入 `question_generation_references`，保留生成依据知识块。

当前生成质量规则：

- 默认按俄语专八备考难度生成。
- 尽量避免只问单点词义、地点或人物的低难度题。
- 国情题要优先考背景关系、对应关系和干扰项辨析。
- `difficulty = 3` 至少应需要两步判断。
- `difficulty = 4-5` 应加入相近事件、人物、地点或制度背景作为干扰项。

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

2026-08-20 人工反馈：

- 首次生成的第 152 题“Красная площадь 中 красный 的历史含义”难度偏低。
- 后续 prompt 已补充难度要求，减少此类单点词义题。
- 后续生成的第 154 题更符合国情 `difficulty = 4` 标准：事实节点 + 历史背景 + 易混干扰项辨析。
- 后续生成的第 155 题与第 154 题过于接近，第 156 题仍偏基础事实辨析；因此新增本地 AI 草稿质量审计。

当前可运行本地审计：

```text
.venv\Scripts\python.exe scripts\audit_ai_question_drafts.py
```

如需把风险写入审核日志并标记：

```text
.venv\Scripts\python.exe scripts\audit_ai_question_drafts.py --persist-flags
```

后续需要补：

- 选项唯一性验证。
- 答案自洽二次审查。
- 按知识点批量生成。
- 前端审核页面。
- 文学、国情资料来源可靠性标注。
