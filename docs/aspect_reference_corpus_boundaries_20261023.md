# 教材编号例句边界：全量队列与累计核图集

当前累计集为[aspect_corpus_extents_20261023_006](../data/processed/aspect_reference/research_exports/aspect_corpus_extents_20261023_006/README.md)：186条完整例句范围＝185个原索引锚段＋1条异常编号补定位，涉及51张例句来源页，其中13例补入首段后续内容；原索引其余1268锚段尚待边界审核。审核由同一助手完成，非专家金标、随机样本或自然语料频率库。

|范围|数量及含义|
|---|---|
|全索引|1453编号首段锚点，分布84理论单元；不等于全书完整例句数|
|已核边界|186条；原ready40、模型候选143、来源隔离3|
|可查询|默认40，显式纳入候选183；隔离3任何模式均不返回|
|已扩段|13；原22目标中1例，定向新增18条中12例|
|全部编号锚段已核的单元|11单元；第十一章9单元113标准锚段＋1异常补定位，另ch07.s02共12、ch13.s02.01共33|

“单元全部编号锚段已核”不包含无编号、行内例句，也不表示该单元俄汉逐句对齐或全部语义通过。73→104阶段补齐ch13.s02.01余31例；此前已处理跨段例(18)/(32)。例(29)的это его слова保留，不能机械套用例(32)的кто это/эти люди编校。

104→136新增五命令式单元32例；136→186补齐ch11.s01.03余49标准锚段，另补定位PDF326原印“(В43)”。原AS-TI-097候选早已改为“(43)”，原文数字正则却未单列本例，只把它保留在(42)后续语境中。本次新增ID为aspect.ch11.s01.03.supplement.043.01，原异常编号/候选分别保存，不并入(42)，不修改旧1453索引。

[全部100节编号差异核验](../data/processed/aspect_reference/reviews/numbered_marker_delta_20261023_001.json)只发现此一处：原层1453个数字起段、候选层1454个。这个数量仍不涵盖无编号、行内及其他版式例句，不能据此宣称全书例句已数清。

[结构队列002](../data/processed/aspect_reference/research_exports/aspect_extent_queue_20261023_002/README.md)逐条保存到下一同节编号前的完整上下文，仅用于审阅，不把这些范围自动当作完整例句。1453条中568条后面还有独立段落，常为作者分析。原22目标之外，18条“俄文首段无汉字且有后续段落”经阅读/核图后，12条需补对话或译文、6条保持独立俄文范围；该标记不是错误检测器或准确率。

队列还标记跨页、下一段对话/引号及附后脚注。未标记不能保证完整；表格、引文来源、译文中的括号引证需按原页判读。队列001因统计字段名错误只写出JSONL，没有manifest，不作为有效包；002修正后完整构建，JSONL字节相同，失败产物保留。

累计集保留原转录/候选编校、原单位半开偏移、精确文本/指纹、页/原图指纹、编辑和外部异文警示；不会因边界通过解除理论隔离。三个隔离例在ch03.s03，后续радовал术语切换仍未裁定。档案含隔离材料，不能直接整体导入学生端。

[104例验证](../data/processed/aspect_reference/reviews/corpus_extent_verification_20261023_002.json)重建104条JSONL与多行TSV，208次按ID/范围检查通过；前三版40/57/73条的既有记录不变。此前[队列及57例验证](../data/processed/aspect_reference/reviews/corpus_extent_verification_20261023_001.json)重建1453条及4个文件指纹，七类错误输入被拒绝。原PDF及原库SHA保持不变，包内入口已实际运行。

[当前186例验证](../data/processed/aspect_reference/reviews/corpus_extent_verification_20261023_003.json)重建全部JSONL/TSV，372次范围检查通过，旧40/57/73/104/136条记录不变；6类补定位失配被拒绝，包括重算原文指纹后与真实索引例句重叠。36项既有体学回归通过，新增异常编号仅补边界层，不改源正文。

包内运行：

```powershell
python -X utf8 aspect_corpus_extents.py verify
python -X utf8 aspect_corpus_extents.py list --include-candidates
python -X utf8 aspect_corpus_extents.py show --id aspect.ch07.s02.example.003.01 --include-candidates
```

[18条整例俄汉对应](aspect_reference_parallel_illustrations_20261023.md)仍只覆盖原22目标；新增164例尚未建立同等对应层。原22语义试标与待复核空包003不因范围扩容自动扩样。独立标注仍0，来源7项未决隔离仍在，默认RAG、学生库及其他书库均未改。
