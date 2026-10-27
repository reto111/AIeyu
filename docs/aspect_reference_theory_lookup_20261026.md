# 细化理论资料的独立查询与离线包

[18文件离线包001](../data/processed/aspect_reference/research_exports/aspect_theory_relations_support_20261026_001.zip)包含27条义项/词类来源关系和6个辞书释义论证案例，默认返回27条原ready，显式启用候选共33条。它晚于主004冻结，未收入主004；这些是来源关系和案例，不是新增自然语料或俄汉译对。

在项目根目录执行：

```powershell
.venv/Scripts/python.exe -X utf8 scripts/aspect_theory_reference.py stats
.venv/Scripts/python.exe -X utf8 scripts/aspect_theory_reference.py lookup --lemma бить
.venv/Scripts/python.exe -X utf8 scripts/aspect_theory_reference.py lookup --lemma решать --include-candidates
```

解压离线包后去掉路径前缀，使用`python -B -X utf8 aspect_theory_reference.py ...`即可。按完整词形标签查询，不做词形还原；читать与считать分开，побить可反查对应义项。`show --id`读取稳定ID及完整原段，`--kind`区分来源关系和论证案例。没有命中不能推断某体词偶或理论关系不存在。

加载时重核集合清单、审核报告、原/候选单元与片段范围，并逐条比较实际数据与冻结审核。六个辞书案例都是候选来源，默认隐藏；不能因原段局部没有修改就将整个单元升级为原ready。旧书目转引不冒称已亲查原辞书，条件性单体用法不强化为无条件词条规则。

[查询验收](../data/processed/aspect_reference/reviews/theory_reference_lookup_verification_20261026_001.json)通过6项功能检查、5次标准库隔离CLI和4种重新签名篡改拒绝：擅自提升候选状态、交换施为论证角色、自洽修改原/候选单元、替换体词偶字段。原ready/候选/隔离边界与完整词形查询均保留。

[ZIP验收](../data/processed/aspect_reference/reviews/theory_relations_support_verification_20261026_001.json)从解压包实跑3次CLI，每次实际阻断项目读取和套接字，目录/ZIP文件一致，运行后包不变。包为46194字节，SHA256：`efab327c22c2b4cf2aa33d1e98b19f27f56d65b0a54aae9eac51740968f414b4`。

这验证可追溯访问，不是语义正确率或词典全义项认证。独立专家评价仍0，主004的2178来源组及435行内对应保持不变。
