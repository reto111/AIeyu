# 通论研究数据卡与附录查询材料

[研究数据卡](../data/processed/tonglun_reference/research_exports/dataset_card_20261025_001/README.md)固定当前版本和计数口径。175、219、220三个快照原始正文Unicode字符数分别为260817、382420、386504，含标点、组合符和转录标记，不是词数、模型token或去排版字符数。三快照175个原ready正文逐项不变。

本材料是元语言参考语料/知识库准备。书内摘引和标记不是独立抽样的自然使用语料，不能据603个调型标记推断口语频次，也不能据教材内容推断学生能力。603标记、540星号对、精选例组、短语跨度、修订位置各有口径，不叠加成“语料数”或“错误数”。

[附录895条研究包](../data/processed/tonglun_reference/research_exports/appendix895_preview_20261025_001/README.md)将787术语行、108书目项的原首轮值与5处既有字段提案并列。原首轮不是PDF逐字认证，提案预览不是正式导入；保留译项列表和两册来源行，Николаева1985/2005原值不统一。

包内lookup.py须显式使用--firstpass-research，original/proposal分别决定匹配层，提案模式仍附原值和改动。未传研究开关时返回空，不改变175默认检索。[核验](../data/processed/tonglun_reference/reviews/appendix895_preview_verification_20261025_001.json)核32页图像指纹、全部895记录与5字段重放，验证两种词典名对应交换及平行系列来源行保留，4类构造修改拒绝、-I进程CLI通过；独立内容审核仍0。

[编校增量评阅002](../data/processed/tonglun_reference/research_reviews/issues_incremental_20261025_002/README.md)补齐013→017新增7条材料、14个空槽。基包009的73条、增量001的10条和本包7条共同覆盖当前90个补证case；不是新增90个原问题，也不是90条已解决。实际独立评分0。

原库仍175 ready、127隔离、139待核；附录5待核、正式导入0。220固定015且未做新检索/生成评价，旧175/219成绩分别保留。本轮候选编校回写0，不表示原始转录库从未导入过数据。
