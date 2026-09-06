# 内容更新与审核覆盖记录

2026-09-05。本轮实现针对 2026-09-03 多模态修正的定向补丁；不是全功能数据同步系统，不补建服务器缺失的题目，也不重跑旧词库修正。

## 可靠的内容更新

服务器数据库既有题库，也有学生账号、答题、错题及背词进度。更新题目时仅更新指定内容字段，服务器整库保留。

补丁包含考试、年份、原题号、字段、旧值校验摘要、新值及修正依据。例：专八 2017 第 16 题补回填空线；服务器仍是已知旧题干则更新，已经是修正题干则跳过，存在另一版题干则列冲突。内部数据库 ID 不作为跨机器定位依据。

本次文件：

- `database/content_patches/multimodal_20260903.json`：139 个字段的固定清单，仅含内容。
- `scripts/content_patch.py`：检查、事务更新、一致性备份、追加更新回执。
- `scripts/apply_multimodal_question_fixes.py`：保留旧命令入口，现转到上述保护流程；不再改写历史审核日志。

有任一冲突时整批不写入，返回码为 2，并保存冲突来源键及字段。缺少题目或文章绑定变化同样阻止更新。没有“强制覆盖”开关；应对照来源处理冲突并形成新补丁。

## 服务器操作

上传本次代码和清单后，保留服务器原 `.env` 和 `database/russian_ai_tutor.sqlite`。停止学生服务，避免核验、备份与更新期间产生新的学习写入。先在服务器数据库副本预演；通过后在正式库执行同一清单。

```powershell
cd C:\AIeyu
python -B scripts\content_patch.py --db database\russian_ai_tutor.sqlite
```

检查输出：`conflicts` 必须为空，`changed_fields` 是待改字段数，`skipped_fields` 是已更新字段数。若有冲突，将输出报告交回排查，不执行历史修正脚本凑数。

确认预览符合本次发布清单后：

```powershell
python -B scripts\content_patch.py --db database\russian_ai_tutor.sqlite --apply
python -B scripts\content_patch.py --db database\russian_ai_tutor.sqlite
python -B scripts\serve_student_app.py --host 0.0.0.0 --port 8765
```

写入前使用 SQLite backup API 保存一致性备份，位置在输出的 `backup`；执行记录保存于 `database/content_update_reports/`，每次独立命名。正常重复预览应为待改 0、冲突 0。服务启动后另开窗口：

```powershell
cd C:\AIeyu
python -B scripts\check_mvp_readiness.py --base-url http://127.0.0.1:8765
```

补丁检查的是本次内容更新，不替代完整发布验收。上线前还应比较服务器账号、学习记录和关联数据。该补丁本地通过旧备份副本回放；本轮没有连接服务器，实际服务器兼容性须以上述预演为准。

回滚：停止服务，保留故障库和报告，恢复本次输出的数据库备份及匹配的代码版本，再验收。只有停服期间且未产生新学习数据时适合恢复整库；若更新后已有学生新作答，应制作内容反向补丁，避免恢复旧库抹掉新数据。

## 审核覆盖记录

它回答“哪些内容、哪些字段、在什么版本上有审核依据”，不是简单的通过/未通过标签，也不是正确率。

当前导出命令：

```powershell
python -B scripts\export_content_review_coverage.py
```

输出在 `data/processed/review_coverage/`：

- `questions.csv`：考试、年份、题号、来源页、使用状态、文章绑定、历史修正字段、内容摘要及上次规则提示。
- `passages.csv`：文章、来源页范围、全部关联题目、正文摘要和历史正文修正证据。
- `summary.json`：本次导出范围与证据数量。

本次导出为 778 条题目、58 篇文章；76 道题有历史字段修正证据，9 篇文章有历史正文修正证据。其余记录标为缺少本清单对应证据，不能解释成全部未审核，也不能解释成有问题。所有题目的全字段视觉审核暂标 `not_established_by_this_manifest`，避免用局部修正冒充整题核验。

`prior_rule_flags` 来自之前审计 CSV，没有在本轮重跑，不能当作当前新检出的错误；字段匹配只表示当前值与历史补丁一致。正文或题目后来变化会改变摘要，需重新检查相关范围。

后续逐批审核时，追加审核人/方式、源文件摘要、原页位置、字段覆盖（题干/选项/答案/文章）、结论及时间，绑定当时的内容摘要。原图无法确认的保留未决，阅读同时验证整篇和所属题组。只有覆盖记录齐全才能统计对应范围的审核完成率；要报告准确率，还需独立可靠的标注样本。

词库不在本次覆盖导出范围内。后续词汇复核应采用词源+页码+词条坐标，并单列词头、词性、核心词义和词典依据，不能直接沿用题号。
