# 来源需求规则的同义与否定压力检验

已封存[第一版225本地包](../data/processed/tonglun_reference/research_exports/traceable225_local_20261027_001/README.md)的原20条开发题均符合预期。另冻结20条同义表达、否定语句及书内判断题，结果出现10条不支持需求漏拦8条、10条解释需求误拦4条，详见[原始挑战结果](../data/processed/tonglun_reference/reviews/traceable225_capability_challenge_results_20261027_001.json)。这说明针对规则编写的开发题不能当作总体准确率。

另存[第二版225本地包](../data/processed/tonglun_reference/research_exports/traceable225_local_20261027_002/README.md)，只改assess需求函数和README；六个数据/来源映射/词面核心文件逐字保持，其余运行时代码AST相同。增加“倾斜印刷”“重建”“几回”“名次”“cosine similarity”等表达，处理少量显式否定请求，区分按书内定义解释与要求当代理论认证。没有改排序、来源范围、候选状态或默认入口。

在再运行前冻结两版及新20条压力题，[协议](../data/processed/tonglun_reference/rag/traceable225_v2_protocol_20261027_001.json)明确原40题已用于开发，新20题仍由同一助手有意构造，不是独立自然样本。[完整比较](../data/processed/tonglun_reference/reviews/traceable225_v2_comparison_20261027_001.json)如下：

| 题组 | 第一版漏拦/误拦 | 第二版漏拦/误拦 |
| --- | --- | --- |
| 原20开发题（10不支持、10解释） | 0/0 | 0/0 |
| 第二组20开发题（10不支持、10解释） | 8/4 | 0/0 |
| 新20压力题（10不支持、10解释） | 8/2 | 6/2 |

第二版仍不能稳妥处理所有措辞：俄语курсивом、部分“倾斜字母”、每百万词多少例、自然语料百分比、向量余弦值及今天研究表述仍可能漏判；“请不要恢复斜体”以及不评价我的排名仍可误拦。没有按本次压力结果继续调规则后重报同一成绩。允许不等于证据充分，拒绝也不代表用户需求一定错误。

第二版[8次移目录隔离命令](../data/processed/tonglun_reference/reviews/traceable225_isolated_cli_verification_20261027_002.json)通过；原包及副本字节不变，无网络、数据库连接或原PDF读取。Python审计钩子不是操作系统沙箱。本工具仍可让无关主张搭配有效引句通过字面引用校验，尚未解决语义支持。

两版均保持可选，不进入学生默认流程；生成调用0、独立专家评价0。原139待核、127隔离、175默认ready及87条候选编辑不变。后续优先继续正文证据和完整单元审核，不以不断扩张词面规则替代来源与语义评价。
