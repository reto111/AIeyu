# Database

本目录存放数据库相关设计和脚本。

当前策略：

- V0.1 本地原型优先使用 SQLite。
- 表结构尽量保持 PostgreSQL 兼容，方便后续迁移到线上商业版本。
- 正式练习题库必须使用结构化数据库，不用 RAGFlow 替代。
- 历年真题可以用于学生组卷，但必须展示来源年份和真题来源。
- RAGFlow 只负责教材、讲义、考纲、解析等知识资料检索。

主要文件：

- `schema.sql`: 初始数据库表结构。

建议流程：

```text
1. 把 PDF 放入 data/raw_pdfs/
2. 在 source_documents 表登记 PDF 来源
3. 解析 PDF 得到待审核题目
4. 人工校对后写入 questions / options / passages
5. 标注 knowledge_points
6. 历年真题题目标记 source_label 和 requires_source_label
7. approved 状态的题目才能用于组卷
8. 若为历年真题，前端必须展示来源标签
```

## 初始化本地数据库

如果本机没有安装 `sqlite3` 命令行工具，可以使用项目脚本：

```text
python scripts/init_sqlite_db.py
```

生成的数据库文件：

```text
database/russian_ai_tutor.sqlite
```

该文件是本地运行产物，不提交到 Git。

## 导入待审核真题

2019、2021、2023 年文字版专八真题已完成结构化切分，并可用以下脚本导入本地 SQLite：

```text
.venv\Scripts\python.exe scripts\import_review_json_to_db.py --replace-source data\processed\structured\tem8_russian_2019_review.json data\processed\structured\tem8_russian_2021_review.json data\processed\structured\tem8_russian_2023_review.json
```

当前导入状态：

```text
questions: 150
question_options: 600
passages: 15
review_status: 全部 needs_review
content_origin: 全部 past_exam_original
source_label: 全部要求展示，例如 2019 年俄语专八真题
```

注意：这些题目目前还不是最终审核通过题库。正式进入学生组卷池前，需要人工确认题干、选项、答案、阅读文章和来源标签。

## 初始化知识点树

俄语专八第一版知识点树写入 `knowledge_points` 表：

```text
.venv\Scripts\python.exe scripts\seed_tem8_knowledge_points.py
```

知识点树说明见：

```text
docs/knowledge_taxonomy.md
```

当前知识点树共 35 个节点：语法与词汇 14 个、俄罗斯文学 7 个、俄罗斯国情 7 个、阅读理解 7 个。

## 审核表导出与回写

导出待审核题目：

```text
.venv\Scripts\python.exe scripts\export_review_sheet.py
```

默认会导出两个文件：

```text
data\processed\review_sheets\tem8_questions_review.csv
data\processed\review_sheets\tem8_passages_review.csv
```

题目表不再重复放入阅读文章全文，阅读文章通过 `passage_id` 单独查看。

回写前先干跑：

```text
.venv\Scripts\python.exe scripts\apply_review_sheet.py --dry-run
```

正式回写：

```text
.venv\Scripts\python.exe scripts\apply_review_sheet.py
```

审核日志表迁移：

```text
.venv\Scripts\python.exe scripts\migrate_question_review_logs.py
```

## 生成练习卷

默认只抽审核通过题：

```text
.venv\Scripts\python.exe scripts\generate_quiz.py --count 10
```

审核前内部测试可临时允许待审核题：

```text
.venv\Scripts\python.exe scripts\generate_quiz.py --count 5 --type grammar_choice --include-needs-review --seed 42
```

详见：`docs/quiz_generation.md`

## 批改练习卷

生成答案模板：

```text
.venv\Scripts\python.exe scripts\grade_quiz.py --quiz data\processed\quizzes\tem8_quiz_20260817.json --create-answer-template
```

批改并生成报告：

```text
.venv\Scripts\python.exe scripts\grade_quiz.py --quiz data\processed\quizzes\tem8_quiz_20260817.json --answers data\processed\reports\tem8_quiz_20260817_sample_answers.json
```

批改并写入数据库：

```text
.venv\Scripts\python.exe scripts\grade_quiz.py --quiz data\processed\quizzes\tem8_quiz_20260817.json --answers data\processed\reports\tem8_quiz_20260817_sample_answers.json --persist --title "TEM8 smoke test quiz"
```

详见：`docs/grading_workflow.md`

## 生成错题复习包

根据批改报告生成中文复习建议和同类巩固练习：

```text
.venv\Scripts\python.exe scripts\generate_remediation_pack.py --report data\processed\reports\tem8_quiz_20260817_sample_report_persisted.json --per-weakness 3 --seed 20260817
```

详见：`docs/remediation_workflow.md`
## OCR 依赖

当前本机 OCR 配置：

```text
Tesseract: C:\Program Files\Tesseract-OCR\tesseract.exe
Tessdata: C:\Users\Reto\tesseract-tessdata
Languages: rus, eng, osd
```

检查 OCR 环境：

```text
.venv\Scripts\python.exe scripts\check_ocr_setup.py
```

对 PDF 做 OCR 测试：

```text
.venv\Scripts\python.exe scripts\ocr_pdf_text.py data\raw_pdfs\tem8_russian_2017_full.pdf data\processed\tem8_russian_2017_ocr.txt --max-pages 2
```

如果 PDF 需要密码，先在当前终端设置本地环境变量：

```text
$env:PDF_PASSWORD="your-password"
```

生成 PDF 清单：

```text
.venv\Scripts\python.exe scripts\inspect_raw_pdfs.py
```

提取 PDF 文本，自动对扫描页走 OCR：

```text
.venv\Scripts\python.exe scripts\extract_pdf_text.py data\raw_pdfs\tem8_russian_2024_full.pdf data\processed\tem8_russian_2024_full.txt --mode auto
```





