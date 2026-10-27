# 通论RAG：可选证据需求检查候选

新增独立入口[scripts/tonglun_requirements_guard_candidate.py](../scripts/tonglun_requirements_guard_candidate.py)，默认检索与排序不变。它只检查几类明确超出本书证据的请求：外部语料统计、个人作答/排名、当前价格和考试安排、无音频/标定轴的声学数值、当前词面检索未计算的余弦分数。

规则命中时保留本地检索来源作审计，但抑制prompt_package，outbound_prompt_allowed=false。规则未命中时保留原提示词和来源，不将“未拦截”解释为证据充分。没有读取学生库、查询实时商店/考试信息或调用生成服务。

[协议](../data/processed/tonglun_reference/rag/requirements_guard_protocol_20261025_001.json)在实现前冻结，[执行绑定](../data/processed/tonglun_reference/rag/requirements_guard_execution_binding_20261025_001.json)在运行前固定实现和评价脚本指纹。评价使用同一175原ready、原词面prepare、top5和16000字符完整单元预算，不调整既有排序。

| 材料 | 原提示词可用 | 检查后提示词可用 | 规则命中 |
| --- | --- | --- | --- |
| 旧16负例 | 5 | 0 | 8 |
| 新20开发题 | 6 | 4 | 10 |

旧16中的8个普通无关题原本就没有提示词；8个主题重叠范围外题全部命中需求规则，其中5个原有提示词被抑制。不是把检索结果改成空，也不是生成模型回答正确了16题。

旧150开发题只重放需求判断，拦截0；没有重新检索、重写旧125/150等成绩。新20题由同一助手设计，预期需求决策20/20，是规则开发材料，不是独立泛化或问答正确率。[完整结果](../data/processed/tonglun_reference/rag/requirements_guard_evaluation_20261025_001.json)保留前后包及来源不变证据。

来源按当前审核库重放，问题、来源、系统提示词及guard输出共同校验；改问题、改系统提示词、改来源正文、重启被阻提示词、抹掉需求理由等5类构造修改被拒绝。[CLI实跑](../data/processed/tonglun_reference/rag/requirements_guard_cli_smoke_20261025_001.json)检出5个来源而不导出生成提示词。指纹不是数字签名，全部文件和声明共同重写时仍需外置可信封存发现。

自然语言需求判别仍依赖有限规则，没覆盖的表达可能漏检，也可能误拦。没有独立专家评价或生成验收，入口保持可选，不改变175默认检索或220未批准快照的状态。
