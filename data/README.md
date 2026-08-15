# Data Directory

本目录用于存放项目资料和中间处理结果。

## raw_pdfs

放原始 PDF 真题和答案文件。

建议命名：

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

注意：

- 原始 PDF 不提交到 Git。
- 如果题目和答案在同一个 PDF，可命名为 `tem8_russian_2017_full.pdf`。
- 如果是扫描版 PDF，后续需要 OCR。

## processed

放 PDF 解析后的中间结果，例如：

- 提取文本
- OCR 文本
- 初步切分题目
- 人工校对前的 JSON / CSV

这些文件通常也不提交到 Git，除非是脱敏后的示例数据。

建议将待审核题目 JSON 放入：

```text
data/processed/structured/
```

这些 JSON 仍属于中间处理结果，不直接作为正式题库。
