# 轻量审核覆盖记录

按用户 2026-09-06 的决定，暂缓扩展可靠发布流程。审核只维护现有导出表和一份独立登记，不增加管理后台或复杂审批。

## 日常查看

执行 `python -B scripts/export_content_review_coverage.py`，只读取题库，不修改内容及入库状态。

查看 `data/processed/review_coverage/README.md`：按考试、年份汇总题量、历史字段修正证据及旧规则提示，并列出优先核对题号。
`questions.csv` 包含题干、选项、答案、页码和登记状态；`passages.csv` 单独记录正文覆盖和所属题组。

“未登记”只表示没有本登记文件的证据，不表示题目有错或从未审核。“已核对”只针对 reviewed_fields 列列出的字段，不代表全题通过。正式可练状态仍以数据库为准。旧规则提示不是本次重新扫描的结果。

## 每次审核怎么记

由开发助手完成记录，用户不需要手填 JSON：

1. 从覆盖表定位题号/文章，回看来源，核对实际涉及的字段。
2. 在 `data/review_records/content_reviews.jsonl` 末尾追加一条记录，原记录保留。首次实际审核时才创建该文件，不填造假的示例结果。
3. 记录 key（取导出表 record_key）、content_hash（文章取 body_hash）、fields、verdict、reviewer、method、source 和 reviewed_at。
4. fields 使用 stem、option:A 至 option:D、correct_answer、passage_binding、body 等具体字段名；verdict 为“已核对”“待确认”或“弃用”。source 写原资料及页码或可核查词典链接，method 写实际采用的方式，不能把规则检查写成视觉审核。
5. 再次导出。程序只读取登记文件，不会清空或重写它。同一对象使用文件中最后追加的结论；内容指纹改变时显示“内容已变化，需复核”。

真题以考试、年份、原题号和来源类型定位。非真题及未绑定题目的文章额外使用本地 ID，不将这些登记直接迁移到不同 ID 的服务器。文章正文独立登记，题目修正不替代文章审核。

本轮是在完善记录工具，没有执行新一轮逐题视觉审核，也未全量复核词库。历史 76 道题、9 篇文章的修正证据与独立审核登记分开统计。
