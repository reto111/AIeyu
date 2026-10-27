# 语境证据离线补充包001

[下载46文件补充包](../data/processed/aspect_reference/research_exports/aspect_context_support_20261026_001.zip)，用于配合主交付003和论文附件002。它包含16段否定/理论限定备注及22页核图记录、两个被排除读法、两处后置译文、5小句原译/作者改写关系和3条责备改写关系。范围有交叠、单位不同，不相加为新句对或错误数，新增来源组0。

包内保留11个完整来源单元的原转录、候选与编辑，按冻结审核记录绑定单元指纹。[构建重放](../data/processed/aspect_reference/reviews/context_support_build_verification_20261026_001.json)通过79处原转录范围及55处候选范围；原页图像未打包，核图记录包含页号和原渲染指纹，不能称为包内重新核图。

[隔离验收](../data/processed/aspect_reference/reviews/context_support_acceptance_20261026_001.json)从ZIP解压，仅依赖包内文件和Python标准库，4项CLI检查通过；每次均实测阻断项目读取和套接字创建，运行后文件不变。另在临时副本中重新签名外层文件清单后，以下四种变更被来源约束拒绝：自洽改写完整单元及其哈希、调换第一/第二句汉译及指示、调换叙事小句俄文、伪造候选汉译。

解压后执行：

```powershell
python -B -X utf8 scripts/aspect_context_support_verify.py
python -B -X utf8 scripts/aspect_context_scope_lookup.py --example-id aspect.ch02.s02.02.example.004.01 --include-candidates
```

语境查询默认只读原ready，候选显式启用；它只查询16段备注。后置译文、叙事变体及责备改写分别保存于包内对应目录，未直接扩入该查询的返回范围。段落备注不传播为例证标签；区间交叠、作者例号回指、语境允许改写和意义偏移各自标明。

主包003的2176来源组/435行内对应和论文附件002的42项统计均保持冻结。此补充晚于二者，引用时单列版本；独立专家评价0，不报告语义正确率、自然语料频率或新增生成实验。

ZIP为1190832字节，SHA256：`0c0ca457854edf84891631762476fa5d8db8d79385356eff9e431a9014b99100`。
