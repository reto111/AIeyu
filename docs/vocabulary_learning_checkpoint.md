# 统一背词与全库审核检查点

2026-09-08。本任务仍包含未完成的全库审核，不能因功能测试通过而关闭整体任务。

## 已实施功能

- 一个背词页面：常规单词、专四单词、专八单词；与练习考试独立。
- 注册页增加大一至大四选择，注册后仍需单独登录。兼容旧客户端不传年级，旧账号默认入门。
- `user_vocabulary_settings` 保存年级、手选学习起点和已解锁阶段。年级给初始建议，不能伪装成考试画像。学习起点可手动修改。
- `vocabulary_learning_annotations` 保存逐项审核的规范显示词头、重音、词性、核心中文、另一体、义项限制、学习阶段、原值快照、方法及来源。
- 标注不覆盖 `vocabulary_items` 原记录，学生端背词、复习池及划词优先使用仍与原值匹配的标注。原词发生后续人工改动时旧标注失效，避免遮蔽新修改。
- 所有入口复用原词条ID的学习进度。同形异义或未核实的跨来源条目不盲目合并；常规单次抽词去重词头。未来要做跨记录的同义进度合并，先核实对应关系，不能按字符串批量改学生历史。
- 初版分级是教学建议，不是课程频率排名或考试难度认证。当前各级池仍小，不能表示覆盖某一学年全部必学词。
- 保持认识/模糊/不认识、两天或每天复习、上一词、记错了和立即复习。高一级新词不会用于补足低一级缺额；较高阶段允许复习较低阶段基础词。
- 至少20个本级词且80%已标认识、下一阶段已有内容时自动解锁；解锁持久化防止追加词库导致降级，手动改起点可重设。

## 实际内容覆盖

- 全库7019条正式记录，包含不同来源重复词，不能称为7019个独立词头。
- 已确认样本100条，加按ID顺序的3923–4022共100条，首批200条已导入。下一批4023–4122共100条已逐项拟定并生成原值快照，导入结果以 `CURRENT_STATE.md` 后续记录及导出覆盖为准。
- 样本的 каша 原词义串成咳嗽：本次视觉核对 `data/words/tem4_russian_words.pdf` 的PDF117页、印刷110页，确认本词是粥、稀饭，咳嗽属于下一个词 кашель，已解除原页待核状态。
- 保留 е/ё 的区别，例如 идея 局部修正而 лёгкий 保留 ё。`королева` 不机械改成 `королёва`。不因多个正常汉字就默认中文正确。
- 样本原文件保留历史，不覆盖其“样本待确认”文字；当前采纳后的可重放结果在 `learning_catalog.json`。批次源文件与带原值快照的 catalog 分别保留。
- 外部词典抽核只记实际 sources/evidence，不把模型逐词判断、规则检查、用户认可整个样本或回译一致冒充外部全核。
- 剩余未核条目逐条列于生成报告，不批量改状态。下一批完成后重新导出真实数量，不手填一个“全库通过”。

## 文件与增量操作

审核输入：`data/review_samples/beginner_100.json`、`learning_batch_001.json`、`learning_batch_002.json`。

首批快照：`data/review_samples/learning_catalog.json`。第二批快照：`data/review_samples/learning_batch_002_catalog.json`。

先只读验证，后备份并事务导入，重复应用相同记录应跳过；任何原值或已存在标注冲突应停止，不能覆盖后续人工修正。

```powershell
cd C:\AIeyu
python .\scripts\import_vocabulary_learning.py
python .\scripts\import_vocabulary_learning.py --apply
python .\scripts\import_vocabulary_learning.py --patch .\data\review_samples\learning_batch_002_catalog.json
python .\scripts\import_vocabulary_learning.py --patch .\data\review_samples\learning_batch_002_catalog.json --apply
python .\scripts\export_vocabulary_learning_coverage.py
```

本段是未来上传包含这些文件的新版包后的操作，不表示已经部署到服务器。必须保留服务器 `.env` 和 `database/russian_ai_tutor.sqlite`。有冲突时保留完整报错定位词条，不用本地数据库覆盖服务器。

新批次在实际逐词填写后，使用新文件名准备快照，不重新生成已使用快照来绕过旧值检查：

```powershell
python .\scripts\import_vocabulary_learning.py --prepare --review-file learning_batch_003.json --patch .\data\review_samples\learning_batch_003_catalog.json
```

覆盖导出：`data/processed/vocabulary_learning/README.md`（原义/新义对照）、`coverage.json`（已核与完整未核列表）。它们由脚本根据实际生效标注生成，不是额外人工审批流程。

## 验证与后续

- Python回归涵盖年级、账号隔离、低级池不越级补词、共享记录、即时复习、间隔、重音划词、补丁幂等与原值冲突。
- `tests/check_vocabulary_browser.cjs` 使用临时数据库和全新无头浏览器，测试真实注册再登录、词库切换、背词、上一词、保存阶段和立即复习；不写真实学生记录、不调用收费AI。
- 本次浏览器资源工具不可用，已用项目独立Playwright与Edge验证桌面1440、手机390及320宽度；重音字体曾出现组合符号空隙，已改用兼容字体并复查截图。
- 剩余工作：继续逐词审核其余正式记录，补齐各级数量；对不能确认的核心词头或词義标为待核，不臆造。全部词库审核尚未完成。
