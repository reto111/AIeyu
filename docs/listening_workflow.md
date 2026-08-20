# Listening Workflow

> 本文档记录俄语专八听力题接入规则。当前目标是先把音频材料登记、转写、校对，再与已存在的听力题目文字绑定。

## 1. 当前材料形态

当前听力音频放在：

```text
data/listening/raw_audio/tem8/
```

已看到两种形态：

- 整套音频：例如 `2017.mp3`、`2018.mp3`、`2023.mp3`
- 分段音频：例如 `2019/1(1).mp3` 到 `2019/7(1).mp3`，以及 `2024/1(1).MP3` 到 `2024/7.MP3`

分段音频不需要合并。第一版应把每个分段登记为一个 `listening_asset`，后续再绑定到对应题组或题目。

## 2. 处理原则

- 音频文件属于原始资料，不提交到 Git。
- 数据库只登记路径、年份、分段编号、哈希、来源标签和转写状态。
- 没有听力文字稿时，先用 ASR 生成 `asr_draft`，再人工校对为 `human_verified`。
- AI 讲解听力题时，应优先使用人工校对后的听力原文；如果只有 ASR 草稿，前端或审核区应明确标记。
- 分段文件优先按文件顺序作为题组音频；整套音频后续需要自动切段或人工标记时间范围。

## 3. 数据库设计

新增表：

- `listening_assets`: 听力音频资产。记录年份、路径、文件哈希、整套/分段、分段顺序和转写状态。
- `listening_transcripts`: 音频转写文本。区分 `asr_raw` 和 `human_corrected`。
- `listening_segments`: 带时间范围的小段文本，用于后续定位原文依据。
- `listening_question_links`: 听力题与音频或音频片段的绑定关系。

听力选择题仍进入 `questions` 主表，题型为：

```text
listening_choice
```

## 4. 登记音频

先执行迁移：

```text
.venv\Scripts\python.exe scripts\migrate_listening_assets.py
```

再登记本地音频：

```text
.venv\Scripts\python.exe scripts\register_listening_assets.py
```

只预览不写库：

```text
.venv\Scripts\python.exe scripts\register_listening_assets.py --dry-run
```

## 5. ASR 方案

第一版建议优先本地处理：

```text
音频 mp3
  -> faster-whisper / Whisper 俄语转写
  -> 导出带时间戳的校对表
  -> 人工修正俄文文本
  -> 写回 human_corrected
```

后续如果需要更精细定位，可增加 WhisperX 做词级时间轴。

云端 ASR 可以作为备选，但需要用户明确同意发送音频到外部服务，并注意听力材料版权边界。

### 5.1 本地 ASR 小样本

安装本地 ASR 依赖：

```text
.venv\Scripts\python.exe -m pip install -r requirements-asr.txt
```

先转写 2019 年第 1 段，不写数据库：

```text
.venv\Scripts\python.exe scripts\transcribe_listening_audio.py --year 2019 --segment-order 1 --model-size base
```

转写并写入数据库：

```text
.venv\Scripts\python.exe scripts\transcribe_listening_audio.py --year 2019 --segment-order 1 --model-size base --persist
```

如果某个模型只识别出“Текст 1/2/3”等提示词，说明语音可能被 VAD 过滤过度，可以关闭 VAD 对比：

```text
.venv\Scripts\python.exe scripts\transcribe_listening_audio.py --year 2019 --segment-order 1 --model-size small --no-vad
```

输出校对文件位于：

```text
data/processed/listening_asr/
```

`base` 模型用于快速验证流程；如果俄语准确率不够，再试 `small` 或 `medium`。模型越大，下载和转写耗时越长。

当前 2019 年第 1 段样本结论：

- `base` 能识别主体，但专有名词和格形错误较多。
- `small` 默认 VAD 会过度过滤，只识别出“Текст 1/2/3”等提示词。
- `small --no-vad` 明显更适合作为校对底稿，但仍会错识年份、人名、地名和专有术语。
- 第一版建议听力 ASR 默认使用 `small --no-vad` 生成草稿，再人工校对。

### 5.2 导出和回写听力转写校对表

导出 2019 年第 1 段校对表：

```text
.venv\Scripts\python.exe scripts\export_listening_transcript_review.py --asset-id 3
```

默认输出：

```text
data/processed/review_sheets/tem8_listening_transcripts_review.csv
```

校对时填写：

- `corrected_text_ru`: 修正后的俄语原文
- `review_decision`: 填 `reviewed` / `approved` / `human_verified`
- `review_notes`: 可选备注

回写前预览：

```text
.venv\Scripts\python.exe scripts\apply_listening_transcript_review.py --dry-run
```

确认后回写：

```text
.venv\Scripts\python.exe scripts\apply_listening_transcript_review.py
```

## 6. 后续接入顺序

1. 登记所有听力音频资产。
2. 选 2019 或 2024 的一个分段做 ASR 小样本。
3. 导出听力转写校对表。
4. 人工校对一小段，验证识别质量。
5. 从现有试卷文字中导入听力题目。
6. 绑定题目与对应音频分段。
7. 前端增加听力播放控件和听力专项入口。
8. 批改后 AI 根据题目、选项、学生答案、正确答案和校对文本解释。
