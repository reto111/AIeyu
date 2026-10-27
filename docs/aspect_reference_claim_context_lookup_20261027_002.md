# 主张语境离线回查第二版

当前推荐[24文件离线ZIP002](../data/processed/aspect_reference/research_exports/aspect_claim_context_support_20261027_002.zip)。350条模型主张的历史配对阅读保持；110条旧关键词筛查、176次/174条去重针对性语境记录分别显示。176条尚无针对性记录，不等于未读或错误。独立专家0。

新版纳入15份原审核报告，逐条重放350个原引句、374个补充范围，以及另1条书内张力的3个范围。默认119条原ready主张，其中81条有针对性记录；显式候选320条，其中152条有针对性记录。30条隔离主张及其中22条审核不返回。包内100单元完整原/候选和隔离历史仅供本地研究，文件本身不是学生权限边界。

在项目根目录执行；必须显式选择002，旧脚本无参数默认仍为001：

```powershell
.venv/Scripts/python.exe -B -X utf8 scripts/aspect_claim_context_lookup.py --collection data/processed/aspect_reference/research_exports/aspect_claim_context_support_20261027_002 stats
.venv/Scripts/python.exe -B -X utf8 scripts/aspect_claim_context_lookup.py --collection data/processed/aspect_reference/research_exports/aspect_claim_context_support_20261027_002 show --code aspect.ch03.s01 --claim 2 --include-candidates
.venv/Scripts/python.exe -B -X utf8 scripts/aspect_claim_context_lookup.py --collection data/processed/aspect_reference/research_exports/aspect_claim_context_support_20261027_002 lookup --query "结果 语境" --only-targeted --include-candidates
```

解压后进入该目录，使用系统Python运行：

```powershell
python -B aspect_claim_context_lookup.py --collection . stats
python -B aspect_claim_context_lookup.py --collection . show --code aspect.ch04.s03 --claim 5 --include-candidates
```

show保留各次原审核、补段、理论归属和方法性推导限制。11次需限定的助手推导记录没有变为独立认证；原卡350条不改。词典版本、被讨论观点与本书立场、正文与脚注异议、否定尝试和预料、单数与复数限制分别保留。字面AND查询只搜索主张与原引句，不搜索全部补段，不适合词频估计或自动语义标注。

[验收](../data/processed/aspect_reference/reviews/claim_context_support_verification_20261027_002.json)：8项功能检查、9次解包隔离CLI、5种重新签名的篡改拒绝通过。实际项目读取和socket创建均被阻止，包内文件运行前后不变。重放证明来源绑定与工程一致，不证明所有主张充分或理论正确。

ZIP为795094字节，SHA256：`1e4e9b47ad31787b86ec79b7742c3ca99cc90465dd5e2d3af490dbb1aa0f4c1d`。无PDF、页图、SQLite、学生数据或网络依赖。旧001的63条版本、主004及旧论文统计均保持；新包未纳入主004。自然语料、独立专家评价和本书生成对照仍未完成。
