# 编号例组俄汉对应扩展018

本层累计475个编号例组、503个例证组成部分对应；默认128组/131对应，显式候选共475组。全1453组中还有978组未在本层审核。分章已核例组：{'ch01': 125, 'ch02': 98, 'ch04': 15, 'ch05': 207, 'ch06': 30}。这是对应范围审核，未确定逐句对齐、翻译正确率或体意义金标。

[材料包](../data/processed/aspect_reference/research_exports/aspect_numbered_parallel_20261025_018/README.md)与[独立ZIP](../data/processed/aspect_reference/research_exports/aspect_numbered_parallel_20261025_018.zip)保留原转录、候选、原页、a/b组成部分、编号标签、署名和作者插语。不同对话回合未强制拆成句子。没有新增译文；括号невозможно、ср.词形替换和转引书目另存。单位级异文警示随新版本继承，范围不是单条引文核证；前三版文件保留，其旧内容字段在新版本逐项不变。

[验收015](../data/processed/aspect_reference/reviews/numbered_parallel_verification_20261025_015.json)重放全部语言范围与TSV，核5项禁读原项目/禁网络的离线查询。基础验收003拒绝版本、重叠、越界、旧文、未知元数据、缺页与真实隔离来源等9类错误；当前验收另核句内元数据6类非法关系。允许的句内标注重叠须经显式声明、完整位于同一俄文主体内，不能跨汉译或相互重叠。独立评阅0。早期[验收撤回记录](../data/processed/aspect_reference/reviews/numbered_parallel_verification_withdrawal_20261025_001.json)说明负例ID错误，不能采用001的隔离拒绝结论；002已按实际来源重测。[ZIP独立运行](../data/processed/aspect_reference/reviews/numbered_parallel_zip_verification_20261025_018.json)核解压文件逐项相同及两种默认/候选查询。

旧22目标对应包与本扩展存在相同ID，不相加作为独立语料数量。现有统一目录014及主离线ZIP005继续固定469行内例组/285对应，本扩展单独运行，不自动改变检索范围。7原有疑点保持隔离，自然语料与独立专家评价尚未完成。

```powershell
python -X utf8 aspect_numbered_parallel.py stats
python -X utf8 aspect_numbered_parallel.py stats --include-candidates
python -X utf8 aspect_numbered_parallel.py show --id aspect.ch01.s02.03.example.003.01
```

独立ZIP SHA256：`8537fc5e53c93db54e4e3d72adbe83c4748d1350847f0aa748acf6c1b9efdc89`。在解压目录运行以上命令。
