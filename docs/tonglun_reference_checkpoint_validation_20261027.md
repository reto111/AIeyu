# 27日检查点与复核入口

当前研究材料以[项目当前状态](CURRENT_STATE.md)、[89处候选](tonglun_reference_current89_20261027.md)和[论文方法底稿](tonglun_reference_thesis_preparation_20261027_001.md)接续。原302单元、175 ready、127隔离、139原待核保持；候选139补证、79提案/60待证、89建议，72局部组件重叠，应用0、独立复核0。

[227快照](../data/processed/tonglun_reference/research_exports/editorial227_preview_20261027_001/README.md)为175＋47编校未批准＋5规范化未批准、61快照编辑、395096码位；已完成冻结开发检索，旧150在225→227名次逐条不变，新两开发题均第1。没有新生成实验，不把开发命中称正确率；原四组沿用记录及本批重算部分已分列。

可以先检查[两个本地示例](../data/processed/tonglun_reference/rag/local_review_examples_20261027_001/README.md)：[表音法证据包](../data/processed/tonglun_reference/rag/local_review_examples_20261027_001/prepared_packet.json)显式开启225包规范化层；[逐字引句页定位](../data/processed/tonglun_reference/rag/local_review_examples_20261027_001/literal_validation.json)回到上册PDF277/印261；[原书斜体恢复请求](../data/processed/tonglun_reference/rag/local_review_examples_20261027_001/blocked_packet.json)被规则阻止准备提示词。响应为人工编写的确定性夹具，不是模型输出，不用于算问答正确率。225包继续固定自己的来源，不自动换为227。

已处理两个书库入口的陈旧顶部：当前入口移到最前，历史批次原文保留，链接按各自目录重定位；不会把旧105条补证、79处编辑或旧“220未测”当作当前状态。项目CURRENT_STATE只替换通论部分，其他书部分保持。

截至封存028，[递归验证](../data/processed/tonglun_reference/reviews/recursive_chain_verification_20261027_001.json)通过51级封存及1681个唯一文件指纹；[链接验证](../data/processed/tonglun_reference/reviews/current_documents_links_with_origins_20261026_002.json)通过113份Markdown/2316个本地目标。这些计数对应检查时的范围；本批新外层将另实跑，不冒称旧报告覆盖未加入的文件。

旧原样Markdown摘录继续使用其已记录的原目录作为链接基准。新的入口摘录保存为JSON字符串，明确记录相对链接基准目录，不把搬移后的相对路径当原页路径。文件指纹清单无数字签名，不证明发行者身份；工程重放也不证明所有语义、字形或专家正确率。

继续工作时读取[最新检查点别名](../data/processed/tonglun_reference/latest_evidence_checkpoint.json)，不重写旧封存包。当前评阅材料139case/278空槽仍未盲化、实际独立评分0；需求第二版新20压力题漏6/误2，逐字引文仍不验证语义支持。原字形/词内斜体/调核、剩余组件与整单元、独立专家及生成评价尚未完成。

本批新增收费OCR/生成调用0，未读学生数据库，未改其他书库或原PDF，未部署、提交或推送。用量是会话日志中的额度比例采样，不是财务余额；接近窗口上限时保存可续接状态，不声称整体任务完成。
