# 主张与语境的独立回查入口

推荐使用[15文件离线ZIP](../data/processed/aspect_reference/research_exports/aspect_claim_context_support_20261027_001.zip)，或在项目根目录运行：

```powershell
.venv/Scripts/python.exe -B -X utf8 scripts/aspect_claim_context_lookup.py stats
.venv/Scripts/python.exe -B -X utf8 scripts/aspect_claim_context_lookup.py show --code aspect.ch01.s02.01 --claim 3
.venv/Scripts/python.exe -B -X utf8 scripts/aspect_claim_context_lookup.py show --code aspect.ch01.s04.02 --claim 4 --include-candidates
```

350条学习卡主张全部有历史配对阅读记录；110条有旧关键词筛查，65次针对性语境审核涉及63条不同主张，余287条尚无这种针对性记录。三种阅读维度分开显示，不计算语义正确率。默认119条原ready主张，其中38条有针对性记录；显式候选320条，其中56条有针对性记录。30条隔离主张及其中7条语境审核不由查询返回。

show给出模型主张、原引句、各次语境审核、补充范围和推导限定。第三章§2第3、5条各两次审核全部保留，不以较新备注替换较旧备注。没有针对性记录仍显示已配对阅读，不自动标错。§3.3书内归属张力作为单元备注附上，不表示该单元每条主张均被证伪。

lookup的query只在主张与原引句中作字面AND；不是词形还原、语料频次或语义蕴含判别。可加`--only-targeted`只看已有语境审核的可用主张，或`--code`限定单元。

[验收记录](../data/processed/aspect_reference/reviews/claim_context_support_verification_20261027_001.json)包含6项功能检查、9次解压后的隔离CLI和5种篡改拒绝。实际项目读取、socket创建均被阻止，运行只依赖包内文件与Python标准库，读前后文件一致。350个原引句、124个补充语境范围、另1条书内张力的3个范围按单元指纹和绝对偏移重放；重放通过不证明主张充分或理论正确。

ZIP共15文件/642661字节，SHA256：`475986e286d5e65d14703551ae292b29a19a7508d687a0d4ba05c82707cb8b96`。包内为本地研究保存完整100单元原/候选快照与审核历史，文件本身不是学生访问权限边界；没有接入学生端，也无PDF、页图、SQLite或网络依赖。

主004、原350主张、既有候选和论文42项统计快照保持冻结。本包晚于主004另档，独立专家评阅0，现代自然语料验证未完成。
