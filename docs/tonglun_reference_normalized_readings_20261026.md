# 整单元规范化复读与223研究快照

本批完整复读TL-V1-066/067/069的全部正文范围（PDF311–313、313、315–316），共2537归档Unicode码位；列出93处括号/竖线记法、27个教学分组和6裁片。066沿用“常向→常问”的既有建议，无新增编辑。复读是同一助手据源工作，不是独立专家二审或逐印刷字模认证。

[完整复读包](../data/processed/tonglun_reference/unit_readings/accent_short_units_20261026_001/README.md)保留转写约定：12个送气h按上标编码；软号及引号不冒称原字形等价；脚注包装为助手线性化。069的6个送气例和5个二合元音例是参考→错误实现，不能反转为纠错箭头。原175默认、127隔离、139待核保持。

[223研究快照](../data/processed/tonglun_reference/research_exports/normalized223_preview_20261026_001/README.md)由旧220条完整记录原样保留，另加3个`normalized_visual_preview`。后者依整单元规范化复读进入显式研究层，仍有字形/语义限制，不冒称通过旧“完整提案、无局部待核”筛选。旧220固定25日015，新3节固定26日012；85处当前建议并未全量应用到该包。默认只175，旧45和新3分别开关；同时打开才223。

## 冻结的本地检索开发对照

先冻结[四层协议](../data/processed/tonglun_reference/rag/normalized223_protocol_20261026_001.json)，再以相同词面排序运行旧150自然开发题、16负例、127原隔离标题题及新3道同一助手开发题。未调参、未生成回答，题目不独立。

| 研究层 | 单元 | 旧150 top1 | top3 | top5 | 新3题目标名次 |
|---|---:|---:|---:|---:|---|
| 原默认层 | 175 | 101 | 121 | 125 | 均未返回 |
| 旧编校层 | 220 | 98 | 121 | 126 | 均未返回 |
| 仅加规范化3节 | 178 | 100 | 121 | 125 | 4、1、1 |
| 两层扩展均打开 | 223 | 97 | 121 | 126 | 4、1、1 |

新增3节使旧150的top1下降1题，top3/top5不变；不能只报告新3题进入前5。四层普通无关8题均空返回8/8，主题重叠范围外8题均仅3/8空返回。非入选隔离目标返回0；题目返回别的合法来源仍不等于证据充分。

这是旧220的首次本轮检索运行结果，不能据数值与旧219一致就称为同一版。新3题来自同一助手读源后的开发设计，3/3进入前5不是独立测试正确率。完整结果见[运行记录](../data/processed/tonglun_reference/rag/normalized223_evaluation_20261026_001.json)；[统计与名次重放](../data/processed/tonglun_reference/reviews/normalized223_evaluation_verification_20261026_001.json)覆盖612条命中表名次，不证明理论或问答正确。

[复读验证](../data/processed/tonglun_reference/reviews/short_unit_readings_verification_20261026_001.json)与[快照验证](../data/processed/tonglun_reference/reviews/normalized223_snapshot_verification_20261026_001.json)检查来源、正文、层开关、角色及隔离Python入口。默认入口与旧快照不改，独立评分0，收费OCR/外部生成0。
