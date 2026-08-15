# Database

本目录存放数据库相关设计和脚本。

当前策略：

- V0.1 本地原型优先使用 SQLite。
- 表结构尽量保持 PostgreSQL 兼容，方便后续迁移到线上商业版本。
- 正式题库必须使用结构化数据库，不用 RAGFlow 替代。
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
6. approved 状态的题目才能用于组卷
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
