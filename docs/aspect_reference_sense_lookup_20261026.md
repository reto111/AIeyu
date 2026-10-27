# 按完整词形查询义项关系

[第83页的27条关系](aspect_reference_sense_relations_20261026.md)可通过独立入口查询：

```powershell
.venv/Scripts/python.exe -X utf8 scripts/aspect_sense_relations.py --lemma бить
.venv/Scripts/python.exe -X utf8 scripts/aspect_sense_relations.py --lemma читать
.venv/Scripts/python.exe -X utf8 scripts/aspect_sense_relations.py --lemma считать
```

бить返回3条按义项分别保存的体词偶；побить可反查1条。читать与считать分别返回“会读书”“会数数”关系，完整词形匹配，不做子串或词形还原。`--kind`可限定体词偶、教材类别或条件性单体用法，默认仅原ready，候选需显式开关，隔离不返回。无结果不表示某体词偶不存在。

[验收记录](../data/processed/aspect_reference/reviews/sense_relations_lookup_verification_20261026_001.json)包括5项功能检查、3次标准库隔离CLI和4项重新签名篡改拒绝，实际项目读取及套接字阻断对照通过。将читать错绑到считать的词内后缀、把“常常”强化为绝对断言、补造未点名的完成体、替换义项对应字段均被拒绝。

[旧缺口实测](../data/processed/aspect_reference/reviews/sense_relation_substring_binding_gap_20261026_001.json)说明：仅有字符、偏移和哈希一致，仍可把читать绑定到считать的后缀；新入口增加完整西里尔词边界约束。真实27条数据未被改动；旧实现的原哈希与[历史源码核验](../data/processed/aspect_reference/reviews/sense_lookup_history_verification_20261026_002.json)另存，避免用修复后的代码冒充旧实验条件。首次文本写入改变了Windows换行而未通过哈希断言，002按原字节保存，失败记录保留。

该入口校验语境、单元和片段来源，不认证所有义项的语言学正确性。它晚于主004生成，未收入冻结主包或27条关系目录；使用项目脚本配合该目录即可。未写学生库，独立专家评价仍0。
