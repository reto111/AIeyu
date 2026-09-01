# Database Schema Plan

> 本文档说明俄语 AI 私教项目的数据库建立方式。
> 初始 SQL 位于 `database/schema.sql`。

## 1. 建库原则

第一版采用“结构化题库为主，RAG 知识库为辅”的方式。

数据库负责：

- 真题来源管理
- 历年真题结构化结果
- AI 改写/仿写题目、选项、答案、解析
- 阅读文章和阅读小题
- 知识点标签
- 审核状态
- 组卷、答题、批改
- 错题和薄弱知识点统计
- AI 对话记录

RAGFlow 负责：

- 教材
- 讲义
- 考纲
- 文学国情资料
- 真题解析资料
- 学生追问时的知识检索和引用

## 2. 为什么不直接把 PDF 放进数据库

原始 PDF 是资料来源，不是可直接用于出题的数据。

正确流程是：

```text
PDF 原件
  -> 文本/OCR 提取
  -> 真题结构初步切分
  -> 人工校对
  -> 知识点标注
  -> 标注来源年份和原题号
  -> approved 练习题库
```

只有审核后的题目才能进入正式组卷。

历年真题可以用于学生组卷，但必须显示来源标签。

## 3. 当前 PDF 批次

用户当前已准备并更正为专八资料：

- 2017 年俄语专八真题及答案 PDF
- 2018 年俄语专八真题及答案 PDF
- 2019 年俄语专八真题 PDF
- 2021 年俄语专八真题 PDF
- 2023 年俄语专八真题 PDF
- 2024 年俄语专八真题 PDF

导入注意：

- 曾误上传部分专四资料，现已更正；专四资料不保留。
- 2024 年旧文件曾为专四照片版，现已替换为新的专八题目。
- 登记脚本默认只登记 `TEM8_RU`，检测为非专八的 PDF 会跳过。
- 数据库仍预留 `TEM4_RU`，仅用于后续扩展，不登记当前批次资料。

建议放入：

```text
data/raw_pdfs/
```

推荐命名：

```text
tem8_russian_2017_questions.pdf
tem8_russian_2017_answers.pdf
tem8_russian_2018_questions.pdf
tem8_russian_2018_answers.pdf
tem8_russian_2021_questions.pdf
tem8_russian_2021_answers.pdf
tem8_russian_2023_questions.pdf
tem8_russian_2023_answers.pdf
tem8_russian_2024_questions.pdf
tem8_russian_2024_answers.pdf
```

如果题目和答案在同一个文件中：

```text
tem8_russian_2017_full.pdf
```

## 4. 核心表说明

### 4.1 exam_systems

考试体系表。

第一版默认：

- `TEM8_RU`: 俄语专业八级

后续可增加：

- `TEM4_RU`: 俄语专业四级
- `TORFL`: ТРКИ
- `CEFR_RU`: A1-C2 自定义体系

### 4.2 exam_levels

考试等级表。

专八只有一个默认等级：

- `TEM8`

TORFL 后续可以扩展：

- A1
- A2
- B1
- B2
- C1
- C2

### 4.3 question_types

题型表。

V0.1 默认题型：

- `grammar_choice`: 语法选择题
- `literature_choice`: 文学选择题
- `culture_choice`: 国情选择题
- `reading_choice`: 阅读理解选择题
- `listening_choice`: 听力理解选择题

### 4.4 knowledge_points

知识点树。

每道正式题至少绑定一个知识点。错因分析主要依赖这张表。

示例：

```text
语法
  -> 动词体
  -> 格变化
  -> 运动动词

文学
  -> 作家
  -> 作品
  -> 流派

国情
  -> 历史
  -> 地理
  -> 政治制度

阅读
  -> 主旨题
  -> 细节题
  -> 推断题
```

### 4.5 source_documents

资料来源表。

每个 PDF 都应登记为一条来源记录，记录年份、类型、文件路径和解析状态。

### 4.6 passages

阅读文章表。

阅读理解的文章放在这里，阅读小题通过 `questions.passage_id` 关联。

### 4.7 questions

题目主表。

保存题干、答案、解析、来源年份、题号、审核状态。

正式组卷只从：

```text
review_status = 'approved'
source_usage = 'practice'
```

的题目中抽取。

历年真题题应标记为：

```text
content_origin = 'past_exam_original'
requires_source_label = 1
source_label = '2019 年俄语专八真题'
```

这类题目可以参与组卷，但前端必须展示 `source_label`。

### 4.8 question_options

选择题选项表。

每个选项单独存储，便于解释每个干扰项为什么错。

### 4.9 question_knowledge_points

题目与知识点关联表。

一道题可以对应多个知识点。

### 4.10 question_review_logs

人工审核日志表。

用于记录：

- 审核结论
- 审核备注
- 当次填写的知识点代码
- 审核人标识
- 审核时间

`needs_fix` 不直接进入 `questions.review_status`，而是保留为审核日志中的结论；题目主状态仍保持 `needs_review`。

### 4.11 knowledge_sources / knowledge_chunks

出题依据库和轻量 RAG 知识块。

`knowledge_sources` 记录资料来源，例如考试大纲、语法笔记、文学国情资料、参考书或人工整理资料。

`knowledge_chunks` 记录可检索知识块，用于 AI 生成题目前检索依据。

当前第一版只做结构化标签和关键词检索，不直接上向量库。

注意：

- 知识块不等于题库。
- 知识块只给 AI 出题提供依据。
- AI 生成题必须进入 `needs_review`，人工审核后才能进入学生练习池。
- 人工整理资料必须标注为 `manual_note` 或对应 note 类型，不得伪装成官方大纲。

### 4.12 question_generation_references

AI 生成题与知识块依据的关联表。

用于记录每道 AI 草稿题生成时使用了哪些 `knowledge_chunks`。

用途：

- 人工审核时追溯生成依据。
- 后续检查题目是否照抄资料原题。
- 后续统计哪些知识源支持了哪些题目。

### 4.13 quiz_sessions / quiz_items / user_answers

测试、试卷题目和用户答案。

用于：

- 组卷
- 答题
- 批改
- 记录历史
- 统计正确率

### 4.14 weakness_snapshots

薄弱知识点快照。

每次测试结束后，根据错题统计生成。

### 4.15 ai_tutor_threads / ai_tutor_messages

AI 私教对话记录。

用于支持：

- 单题追问
- 测试结果追问
- 知识点追问

### 4.16 question_exposures

题目曝光记录表。

用于记录某个学生见过某道题几次、最近一次是否答对、最近一次练习时间和累计错对次数。

用途：

- 随机组卷时优先抽未做题。
- 避免近期做对题反复出现。
- 允许旧错题在适当间隔后回流复习。
- 为后续“不重复专项训练”和“错题复现间隔”提供基础。

注意：画像重算只读取该表，不应在读取画像时重复增加曝光次数。只有真实作答或一次性迁移历史记录时才更新曝光记录。

### 4.16.1 wrongbook_preferences

学生错题本的个人操作数据。

题目是否进入错题本、待巩固或已订正仍由 `question_exposures` 动态判断；本表只保存学生主动产生的附加信息：

- `note_text`: 个人复盘笔记。
- `is_favorite`: 是否收藏。

该表按 `user_id + question_id` 唯一，账号之间严格隔离。题干、选项和答案不在这里复制，始终引用正式题库，避免题库修正后错题本保留旧内容。

### 4.17 mastery_snapshots

用户画像快照表。

当前第一版按两类目标计算：

- `question_type`: 题型掌握度，例如语法、文学、国情、阅读。
- `knowledge_point`: 知识点掌握度，例如 Russian grammar、Russian literature 等。

掌握度基于最近 20 次相关作答，并使用 3 天、7 天、10 天、更早四档时间权重。

### 4.18 training_recommendations

训练推荐表。

用于保存当前最高优先级弱项和建议专项训练数量。

第一版只生成本地默认用户的 active 推荐；后续接入多用户后，每个学生独立生成。

### 4.19 listening_assets / listening_transcripts / listening_segments / listening_question_links

听力音频和转写链路。

`listening_assets` 记录听力音频文件，包括年份、路径、文件哈希、整套音频或分段音频、分段顺序和转写状态。

`listening_transcripts` 保存音频转写文本，区分：

```text
asr_raw
human_corrected
```

`listening_segments` 保存带时间范围的听力原文片段，用于后续在 AI 讲解中定位听力依据。

`listening_question_links` 负责把听力题目与音频或音频片段绑定。

当前规则：

- 2019、2024 这类分段音频不合并，每个 mp3 登记为一个 `segment`。
- 2017、2018、2023 这类整套 mp3 先登记为 `full_exam`，后续再切段或人工标记题组时间范围。
- 音频文件不提交到 Git，只提交登记和处理脚本。
- ASR 自动转写只能作为草稿，正式讲解应优先使用人工校对稿。

## 5. 建库步骤

### Step 1: 放入 PDF

把 2017、2018、2021、2023、2024 的真题和答案 PDF 放到：

```text
data/raw_pdfs/
```

### Step 2: 创建数据库

本地原型建议先创建 SQLite 数据库：

```text
database/russian_ai_tutor.sqlite
```

用 `database/schema.sql` 初始化表结构。

如果本机没有安装 `sqlite3` 命令行工具，可以使用：

```text
python scripts/init_sqlite_db.py
```

### Step 3: 登记 PDF 来源

每个 PDF 在 `source_documents` 中登记。

例如：

```text
2017 真题 PDF -> document_type = questions
2017 答案 PDF -> document_type = answers
```

登记脚本：

```text
.venv\Scripts\python.exe scripts\register_source_documents.py --reset-sources
```

### Step 4: 解析 PDF

根据 PDF 类型选择：

- 可复制文字版：直接提取文本
- 扫描版：OCR

解析结果先放到：

```text
data/processed/
```

当前本机 OCR 已采用 Tesseract：

```text
Tesseract: C:\Program Files\Tesseract-OCR\tesseract.exe
Tessdata: C:\Users\Reto\tesseract-tessdata
Languages: rus, eng, osd
```

可用以下脚本检查：

```text
.venv\Scripts\python.exe scripts\check_ocr_setup.py
```

对于带密码的 PDF，脚本从本地环境变量读取密码：

```text
$env:PDF_PASSWORD="your-password"
```

生成 PDF 清单：

```text
.venv\Scripts\python.exe scripts\inspect_raw_pdfs.py
```

提取 PDF 文本：

```text
.venv\Scripts\python.exe scripts\extract_pdf_text.py data\raw_pdfs\tem8_russian_2024_full.pdf data\processed\tem8_russian_2024_full.txt --mode auto
```

### Step 5: 人工校对

检查：

- 题干是否完整
- 俄文字符是否正确
- 选项是否对应
- 答案是否准确
- 阅读文章和小题是否关联正确
- 年份和题号是否正确

### Step 6: 标注知识点

每道题至少标注一个知识点。

如果暂时不确定，可以先保持：

```text
review_status = 'needs_review'
```

### Step 7: 发布正式题库

校对完成后：

```text
review_status = 'approved'
source_usage = 'practice'
content_origin = 'past_exam_original'
requires_source_label = 1
```

这些历年真题可以进入随机组卷，但必须保留并展示来源年份和原题号。

## 6. 下一步要做的事

建议下一步依次完成：

1. 把 PDF 放到 `data/raw_pdfs/`。
2. 确认这些 PDF 是文字版还是扫描版。
3. 建立专八知识点树。
4. 初始化 SQLite 数据库。
5. 写 PDF 来源登记脚本。
6. 抽取 1 年真题做导入试验。
7. 人工校对 20-30 道题，验证表结构是否够用。

当前已完成：

- 2019、2021、2023 年文字版已完成第一轮切分试验。
- 输出 `data/processed/structured/*_review.json`。
- 每年切出综合知识 30 题、阅读理解 20 题，共 50 题。
- 所有题目均为待审核候选，审核后可以进入练习题库。
- 2019、2021、2023 年待审核 JSON 已导入本地 SQLite：
  - 题目：150 道
  - 选项：600 个
  - 阅读文章：15 篇
  - 状态：全部为 `review_status = 'needs_review'`
  - 来源：全部为 `content_origin = 'past_exam_original'`
  - 来源标签：全部要求展示 `source_label`，例如 `2019 年俄语专八真题`
- 2024 OCR 版已试跑，因章节标题、题号和选项排版不同，需要单独的 OCR/新版排版切分规则。
- OCR 解析可以暂时放一放，优先把文字版真题转成可审核题目。

