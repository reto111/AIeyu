# 编号语言范围与统一查询交付007

当前推荐[离线ZIP007](../data/processed/aspect_reference/research_exports/aspect_research_delivery_20261025_007.zip)，含245文件、15研究包/124包内文件/100份既有证据报告，解压后仅需Python标准库。新目录为[20261025_001](../data/processed/aspect_reference/research_catalog_20261025_001.json)，旧目录014及ZIP005保持冻结。

例组总量仍为1922（1453编号＋469行内）；默认原ready404，显式启用候选1805，117隔离不返回。新增语言层按同一来源ID挂接，不额外计算例组。其中全部1336可用编号组完成语言范围核对：1304双语组/1335组成部分对应，另32单语（29汉/3俄）；默认269编号组/272对应。编号旧22目标重合16个ID，不能相加作独立样本。行内029仍固定469例组/285对应；未声称行内例全部提取。

在解压目录运行：

```powershell
python -X utf8 aspect_corpus_language_lookup.py stats
python -X utf8 aspect_corpus_language_lookup.py stats --include-candidates
python -X utf8 aspect_corpus_language_lookup.py show --id aspect.ch14.s02.02.example.012.01 --include-candidates
python -X utf8 aspect_corpus_language_lookup.py search --term диссертацию --match cyrillic_form --include-candidates
```

项目内运行同名scripts入口，默认选择新目录。show保留原引文全部字段，并追加编号语言层；两处汉语在前的例证保持方向；单语的pairs为空，不补译。search搜整例，含书号、署名、译文、比较和语境，匹配不是纯俄文词次；仍无词形还原、ё或重音规范化。偏移为线性化文本范围，不是PDF字形坐标。

[挂接验收](../data/processed/aspect_reference/reviews/corpus_language_lookup_verification_20261025_001.json)核1805条可用引文旧字段完全保留、1336编号挂接、候选默认隐藏、117隔离排除及8类目录/重签数据失配拒绝。[离线验收](../data/processed/aspect_reference/reviews/research_delivery_verification_20261025_007.json)31项禁读原项目/禁网络检查通过，245文件运行前后不变。[复建](../data/processed/aspect_reference/reviews/research_delivery_reproducibility_20261025_007.json)在独立目录逐字节一致，原PDF、原库、候选及旧主ZIP005指纹不变。

006只读一致性验收未通过，原因是首次导入产生Python缓存；[未发布记录](../data/processed/aspect_reference/reviews/research_delivery_nonrelease_20261025_006.json)保留失败及替代版，不把其31项查询通过当作完整验收。007已在入口导入前禁止字节码缓存写入。

论文中可表述为“教材例证范围整理与可重现检索”，不能写成自然语料库频次、逐句平行语料金标、专家审定译文或正确率100%。独立专家标注仍0，7来源疑点未解除，无新增付费OCR、生成或外发教材。下一步继续行内未提取片段及独立评价；当前语言覆盖只针对固定编号总体。

ZIP SHA256：`153e394085c813b4a13e4a9e05149678d25332692aa6857e028ac65cb1ec35c4`。
