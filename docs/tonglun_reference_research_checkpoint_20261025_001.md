# 通论知识库与论文准备：本轮可检查结果

当前原转录检索可用175个单元，127个单元隔离。正文730页、302个编号单元及139条待核记录保持原状态；原PDF与正文四审核表没有被候选覆盖。

## 本轮交付

| 材料 | 当前结果 | 入口 |
| --- | --- | --- |
| 补证候选009 | 73条记录，58项建议65处编辑；14项待证、1项局部误报撤回；11项只核部分组件 | [逐项依据](tonglun_reference_evidence_progress_20261025_009.md) |
| 全139条编校评阅包 | 127个完整隔离来源、139张问题卡、278个空评阅槽；同源问题和旧说明更正关联 | [阅读及评阅入口](../data/processed/tonglun_reference/research_reviews/issues139_20261025_001/README.md) |
| 当前待核队列002 | 73条已进入补证系列、66条未进入，139条均未解除 | [队列](../data/processed/tonglun_reference/reviews/next_review_queue_20261025_002.json) |
| 重音与音标字符清点 | 302单元、602749字符、4761个特殊字符事件、730张页图；仅机械清点 | [说明](tonglun_reference_unicode_inventory_20261025.md) |
| 论文方法与阶段结果 | 数据版本、检索设计、实际结果、未决项与后续评价条件 | [论文前期底稿](tonglun_reference_thesis_methods_20261025.md) |

候选实际应用0。编校评阅包有完整隔离正文，仅供本地审核，默认检索不读取它。两个槽位只是待填写结构，独立评阅仍为0；这278个槽与既有166题检索评阅的632个槽属于不同任务，不合并报告已评分人数或数量。

[编校包核验](../data/processed/tonglun_reference/reviews/issue_review_packet_verification_20261025_001.json)重放139条原记录、127个来源、65处精确旧值、425张相关页图及全部空槽。字符清点另有[位置重放](../data/processed/tonglun_reference/reviews/unicode_inventory_verification_20261025_001.json)，拒绝4种偏移或来源篡改。均是工程核验，不代表语言学正确率。

## 本轮明确保留和更正的例子

《俄罗斯语法》§1658把сквозь列为副词来源前置词，并明确配第四格，§2725再次支持；候选仅将кого-чего-н.改кого-что-н.。旧说明对副词来源分类的疑问已[追加撤回](../data/processed/tonglun_reference/reviews/issue_note_addendum_20261025_002.json)，不篡改历史记录。

同书§1435直接出现исписать все чернила，因此保留教材这一搭配。плывун的公开正字法词典词条实际核图标грунт，另有构词语法旁证；这约束了译义，却没有完成整个音标、零位符和斜体范围的二审。Репин引句был/была目前只找到电子转录异文，具体纸本版本未核，继续待证。

植物名称[补录](../data/processed/tonglun_reference/external_evidence/botanical_bridge_20261025_001.json)晚于139条包001：植物智补充Galanthus—雪滴花属、Saussurea involucrata—雪莲花；ЭСБЕ电子词条补充укроп—Anethum graveolens。两条原疑点仍待核，后续应结合通名政策评估，不能继续笼统说所有俄拉桥接都缺失。普通HTTP获取这3页均403；事实来自浏览工具实际解析，未冒称完整本地网页快照，也未把电子转录说成纸本核图。冻结包和候选009不被补录暗中更新。

[19项本轮公开事实的留存清点](../data/processed/tonglun_reference/reviews/public_source_availability_20261025_001.json)进一步区分：8项仅索引节选、5项浏览解析但未留完整网页、3项实际获取但未留完整HTML、2项留有学术HTML成员、1项有词典图和语法HTML。19项均被候选引用；旧6个证据ID及另3个外来词词条图另列，不混算。历史网页哈希不等于现在能从本地重放全部网页；论文须明确这一可复现限制。

## 研究基线与未完成部分

既有[150开发题基线](tonglun_reference_question_baseline_20261025.md)未调参或重跑：手给关键词目标top5为150/150，自然问句候选125/150；普通无关8/8空返回，主题重叠范围外3/8。127隔离目标均未返回，但仅89题整体空返回。它们不构成问答正确率或来源充分性评价。

[166题检索评阅材料](../data/processed/tonglun_reference/research_reviews/question166_20261025_001/README.md)有316组、172完整来源和632个空评分槽，独立评分0。[175原ready快照](../data/processed/tonglun_reference/research_exports/source175_original_20261025_001/README.md)保持原版本；本轮隔离评阅包和候选没有混入此快照。25个ready尚未被开发题设为目标，覆盖偏差见[抽样说明](tonglun_reference_question_sampling_20261025.md)。

附录仍为32页首轮候选、787术语行和108书目项，正式导入0、5项待核。正式编校研究版、复杂音标全面核验、独立问题评价、引文充分性和生成对照仍未完成。没有新增收费OCR或生成调用；未部署、提交或推送，未改学生库和其他书库。

后续先核66条尚未进入补证系列的原记录，再对现有73条建议按组件补证。评阅时必须同时读追加更正和植物补录；单条通过不能自动解除同一单元其他疑点。
