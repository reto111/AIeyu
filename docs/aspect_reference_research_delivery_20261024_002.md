# 研究移交002：全量余段角色与新增行内例

[研究ZIP002](../data/processed/aspect_reference/research_exports/aspect_research_delivery_20261024_002.zip)共137文件、6493310字节。SHA-256：`52c46da5a48eaecceb3d6f1bbea5e2b779ef9c5863db1e14b7a436dd66c4edfd`。它采用[研究目录002](../data/processed/aspect_reference/research_catalog_20261024_002.json)，12包106个包内文件、15份证据报告；原001目录与ZIP保持冻结。

新增[材料角色包001](../data/processed/aspect_reference/research_exports/aspect_material_roles_20261024_001/README.md)含1333段、100理论单元的原转录/候选正文、偏移、页证据及角色记录。默认316原ready段，显式候选1216段，117隔离段在所有查询模式下排除；链接57个明确例组、10张表。空链接不表示段内没有例句，角色全覆盖不表示行内例全抽。

[无编号004](../data/processed/aspect_reference/research_exports/aspect_unnumbered_examples_20261024_004/README.md)累计57例组，28原ready、29候选，26个来源页。原001的20、002的28、003的47逐条保持。新增10例核PDF427–431、434，含俄汉比较、问号替换形式、词典跨页引文及两个相同汉译的不同位置。`антену→антенну`仅重放既有编校，不新改原库。

[整例对应004](../data/processed/aspect_reference/research_exports/aspect_unnumbered_parallel_20261024_004/pairs.tsv)累计57组、覆盖44例组，另13例组仅俄文。例组和译对同为57只是数量巧合，不能互换分母。原教材星号、问号、括号改写和多作者署名保留；中文先行或后行均按原偏移绑定，不把教材对照升级为自然平行语料或翻译金标。

[材料验收](../data/processed/aspect_reference/reviews/material_roles_verification_20261024_001.json)核1333正文/TSV、117隔离ID双模式、57例和10表链接、8次隔离CLI以及路径越界/文件篡改拒绝。[移交验收002](../data/processed/aspect_reference/reviews/research_delivery_verification_20261024_002.json)在项目外解压，审计钩子拒绝联网及读项目，16入口场景通过，运行前后包内文件不变。[可重现验收](../data/processed/aspect_reference/reviews/research_delivery_reproducibility_20261024_002.json)证明重新打包字节完全相同，414张来源图文件指纹与原PDF、原库一致；页图指纹检查不是新一轮414页视觉审核。

解压后运行：

```powershell
python -X utf8 aspect_research_catalog.py verify --catalog research_catalog_20261024_002.json
python -X utf8 research_exports/aspect_material_roles_20261024_001/aspect_material_roles.py search --text 结果存在 --include-candidates
python -X utf8 research_exports/aspect_unnumbered_examples_20261024_004/aspect_unnumbered_examples.py show --id aspect.ch14.s03.03.unnumbered.002 --include-candidates
```

旧编号边界044、100学习卡、22目标语义试标及264空格复核包不变。独立标注仍0，7项来源疑点仍隔离。没有原PDF、外证原件、学生数据、密钥或API配置；完整重建需原项目，现成包只读入口可离线独立运行。
