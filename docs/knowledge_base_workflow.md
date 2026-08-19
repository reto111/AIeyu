# 出题依据库与轻量 RAG 流程

> 本文档记录 AIeyu 第一版 AI 出题前的知识库准备流程。

## 1. 定位

出题依据库用于给 AI 生成题目草稿提供材料依据。

它不替代正式题库，也不直接面向学生展示。

当前第一版采用：

```text
Markdown 资料
-> knowledge_sources
-> knowledge_chunks
-> 结构化标签 + 关键词检索
-> AI 生成题目草稿
-> 自动质检
-> 人工审核
-> 正式题库
```

后续资料量变大后，可以在 `knowledge_chunks` 基础上接入向量索引或 RAGFlow。

## 2. 当前目录

知识源文件放在：

```text
data/knowledge_sources/tem8/
```

当前已有：

```text
grammar_outline_manual.md
```

说明：该文件是基于项目知识点树整理的语法出题依据草稿，不是官方考试大纲。

## 3. 数据表

新增两张表：

```text
knowledge_sources
knowledge_chunks
```

`knowledge_sources` 记录资料来源、资料类型、可信等级和文件路径。

`knowledge_chunks` 记录可检索知识块，并标注：

- 题型
- 知识点
- 来源位置
- 审核状态
- 是否已建立向量索引

## 4. 导入资料

导入命令：

```text
.venv\Scripts\python.exe scripts\import_knowledge_sources.py
```

导入脚本会跳过 `README.md`，只导入同目录下的知识源 Markdown。

## 4.1 扫描 PDF 资料

扫描书籍 PDF 可以先放在：

```text
data/knowledge_sources/
```

PDF 原件可能包含版权资料，不提交到 Git。

扫描 PDF 需要先 OCR：

```text
.venv\Scripts\python.exe scripts\extract_pdf_text.py data\knowledge_sources\your_reference.pdf data\processed\knowledge_sources\ocr\your_reference.txt --mode ocr --lang chi_sim+rus+eng --dpi 220
```

OCR 文本也不提交到 Git。

OCR 完成后导入知识块：

```text
.venv\Scripts\python.exe scripts\import_ocr_text_knowledge_source.py data\processed\knowledge_sources\ocr\your_reference.txt --source-pdf data\knowledge_sources\your_reference.pdf --title "资料标题" --question-type culture_choice --knowledge-point culture
```

当前 Tesseract 已安装：

```text
rus
eng
chi_sim
osd
```

当前已处理的扫描 PDF：

```text
tem8_countryknowledge_reference_scan.pdf
```

状态：

- 页数：161 页。
- OCR 输出：`data/processed/knowledge_sources/ocr/tem8_countryknowledge_reference_scan.txt`
- 已导入知识块：159 个。
- 题型标签：`culture_choice`
- 知识点标签：`culture`

当前已抽样验证但尚未全量 OCR 的扫描 PDF：

```text
Russian_grammar_reference_scan.pdf
```

状态：

- 页数：641 页。
- 已抽样确认 `chi_sim+rus+eng` 可识别中俄混排正文。
- 因页数较多，建议后续改用分批 OCR 或带进度 OCR。

## 5. 检索资料

按关键词和知识点检索：

```text
.venv\Scripts\python.exe scripts\search_knowledge_chunks.py 动词体 --question-type grammar_choice --knowledge-point grammar.aspect --reviewed-only --limit 2
```

后续 AI 出题脚本应先调用检索，拿到相关知识块后再生成题目。

## 6. 添加正式考试大纲

拿到正式大纲或可靠资料后，不要覆盖现有文件，建议新建文件并标注来源类型：

```text
source_type: syllabus
trust_level: 4 或 5
review_status: reviewed
```

如果资料来自教材、论文、网页或人工整理，应如实标注为：

```text
reference_book
web_article
manual_note
```

不要把人工整理资料标成官方大纲。

## 7. 进入 AI 出题前的规则

AI 生成题必须满足：

- 不能照搬历年真题。
- 不能只换词改写原题。
- 必须引用本地知识块作为生成依据。
- 必须进入 `review_status = needs_review`。
- 人工审核前不能进入学生练习池。
