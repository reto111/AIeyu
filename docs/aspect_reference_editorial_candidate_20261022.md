# 现代俄语体学：本地编校研究候选（2026-10-22）

当前可检查的候选包为[20261022_002](../data/processed/aspect_reference/research_exports/aspect_editorial_candidate_20261022_002/README.md)：理论100节中40节原ready正文保留、48节模型编校候选显式启用、12节继续隔离。不是正式论文冻结版或专家审定版。

## 本轮新增及证据边界

原印库仍471页记录、470整页与PDF39局部、135批、40历史修订；100理论节仍40 ready/60 unresolved，另60非理论单元隔离。481页原始OCR仍全部unreviewed，118份二轮核图记录不变。本轮只增加独立编校层、原著查证与检索验证。

[125条理论说明最新逐项结论](../data/processed/aspect_reference/reviews/theory_issue_review_20261022_005.md)：104条具体方案、11条待来源、2条理论/语境未决、7条保留原文、1条墨迹不可辨。一条可含多个问题，不是125个独立错误。104条方案与4条当前追加项组成108提案、115处精确编辑，见[修改预览](../data/processed/aspect_reference/reviews/editorial_change_preview_20261022_001.md)。AS-NEW-004的署名编辑已归回AS-TI-110，不重复计数；旧版本均保留。

[22条外部来源清单](../data/processed/aspect_reference/external_evidence/source_manifest_20261022_005.json)含原刊扫描、原作电子转录、电子排印版、同一作者后续论文及仅索引线索，分别披露。原作确认В. Андеев应对应В. Авдеев，撤回按邻例猜Андреев；原刊确认Головин复数谓语；Шатуновский原文确认第一阶段是原先不在说话地点。ловить的目的/实际结果修订是据Апресян原论文作出的模型推导。

Панова原作的术后病人语境支持撤回职业能力差式的“无能”改译。教材引例与所查原作在名词、时态、护理员性别上有异文；原教材俄文保留。此警示进入该节检索证据包，移除警示的篡改也会被拒绝，不能把教材例句冒称所查小说逐字原句。外部全文缓存不随候选包分发。

练习仍为28组262编号父题：233预期读法可成立、8需语境、9具体差异、12题干/标注问题；[9题12处方案](../data/processed/aspect_reference/reviews/exercise_editorial_plan_20261021_001.md)与[当前索引](../data/processed/aspect_reference/reviews/exercise_current_index_20261021_001.json)沿用本轮之前的冻结结果，不因理论候选扩充就加入学生池。

## 运行

在项目根目录执行：

```powershell
.venv/Scripts/python.exe scripts/aspect_candidate_rag.py verify
.venv/Scripts/python.exe scripts/aspect_candidate_rag.py prepare "为什么ловить不一定意味着已经抓住？" --include-candidates --code aspect.ch04.s03 --output tmp/aspect_packet.json
```

默认仅40节原ready；加`--include-candidates`才纳入48节模型候选。上例显式指定节键用于可重复检查；自然问题检索可省略`--code`，但存在下述漏检。超预算整节列入`omitted_sections`，不截短冒算命中。候选包内入口可用标准库离线运行，无需原PDF或网络。输出是证据包，未调用生成API。

原书张家骅《现代俄语体学》第2版，高等教育出版社2004；原页引用使用printed_pages。候选改写必须标明编校候选层；转引文献需说明实际查阅层级。教学例句用于理论分析，不能代替自然语料的频率样本。

## 验收结果

[整包验收002](../data/processed/aspect_reference/reviews/candidate_verification_20261022_002.json)：9包文件指纹、五张原表逐行保留、100理论节完整重建、115编辑重放、88节连续引句与伪造/证据包篡改拒绝、12理论及60非理论隔离通过；SQLite ok、外键0。Панова警示移除拒绝1/1，13项相关unittest通过。

旧冻结32道开发自然问句：原40节入口10/32（仅10个目标可用，10/10命中），显式88节入口32/32。算法已针对其中两道漏题调整表面词形，不能据此宣称泛化召回率。旧4道指定隔离题中两节现经查证进入候选，原预期不改，按旧预期只有2/4拒绝；按当前真实启用范围4/4匹配，全部12个实际隔离节另已拒绝验证。4道无关题均无证据。

[另冻24道补充自然问句](../data/processed/aspect_reference/rag/supplement_question_acceptance_20261022_001.json)：本组冻结后未再调检索算法。原40节5/24（8目标可用），候选88节17/24（23目标可用，17/23命中）；另1目标仍隔离，6个可用目标漏检，见[失败明细](../data/processed/aspect_reference/rag/supplement_failure_analysis_20261022_001.json)。补充组4当前隔离/4无关均符合预期。问题由同一助手按已知资料编写，预定来源未必唯一；尚未独立判断替代支持、专家盲评或生成回答语义，以上不是生成正确率。

对六道可用目标漏检题又做了[实际返回片段支持复核](../data/processed/aspect_reference/reviews/supplement_semantic_support_review_20261022_001.md)：2题存在能支持核心问题的替代段、3题仅选出部分支持、1题无证据。原17/24与17/23目标命中数不改；这是同一助手定性片段判断，不能据此换算为生成准确率或完整上下文语义通过率。

## 仍未完成

[14条当前未决记录](../data/processed/aspect_reference/reviews/remaining_source_queue_20261022_001.md)跨12节；继续核11条原著、2条理论/语境，并保留PDF39遮挡。其余工作为补充组6处可用目标漏检、独立引文语义评价、研究版冻结及论文生成对照实验。未改学生库、其他书库、原PDF，未外发本地PDF、收费OCR/生成、部署、提交或推送。

[原印一致性备份](../data/processed/aspect_reference/reviews/backup_verification_20261022_001.json)、[当前检查点](../data/processed/aspect_reference/checkpoint.json)。此前原印全审计verification_20261021_002仍为原印层证据；本次确认数据库指纹相同，未冒称重新核完全部原页。
