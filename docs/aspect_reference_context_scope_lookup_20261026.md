# 例证的否定语境与理论限定查询

独立入口 `scripts/aspect_context_scope_lookup.py` 按已有例证ID或残余段ID返回完整段落、出处、原转录/候选与同一助手的范围备注。它固定16段筛查、22页核图和PDF87显式回指案例，不改变主检索排序、例证标签或候选批准状态。此工具尚未收入冻结主包003或论文附件002。

```powershell
.venv/Scripts/python.exe -X utf8 scripts/aspect_context_scope_lookup.py --residual-id aspect.ch02.s02.02.residual.017 --include-candidates
.venv/Scripts/python.exe -X utf8 scripts/aspect_context_scope_lookup.py --example-id aspect.ch02.s02.02.example.004.01 --include-candidates
```

默认只返回原ready备注；候选必须显式加开关。第一个命令显示完整“不能认为……而把例句理解为”段。第二个通过书中例号回指关联例(4)，即使段落与例(4)在文本区间上不交叠，也返回限定语境；关系字段明确为 `explicit_author_example_reference`。

其他65个已有例证的关联只源于区间交叠，字段为 `geometric_overlap_only`。这不证明段中否定词作用于指定例证；理论限定、释义不等值和某些受条件限制的用法不能统一转成“不合语法”。每条输出明确 `category_is_example_label=false`。查询无结果只表示本次有限筛查没有可用备注，不表示可接受或没有上下文限制。

[来源筛查](../data/processed/aspect_reference/reviews/negative_scope_screen_20261026_001.json)、[原页补核](../data/processed/aspect_reference/reviews/negative_scope_visual_review_20261026_001.json)及[显式回指案例](../data/processed/aspect_reference/reviews/rejected_reading_context_case_20261026_001.json)用固定哈希绑定。运行时重核三份报告、残余段清单、行内041和编号044的JSONL指纹；不读取原PDF、SQLite、图像或学生库，也不调用网络。

[功能验收](../data/processed/aspect_reference/reviews/context_scope_lookup_verification_20261026_001.json)通过8项检查和6份来源文件变更拒绝；[隔离验收](../data/processed/aspect_reference/reviews/context_scope_isolation_verification_20261026_002.json)仅复制七份文件即运行成功，实际项目读取与套接字创建阻断对照通过，目录越界请求在读取前拒绝，文件不变。这是工程约束验证，独立专家评价仍0，不是语义正确率。
