# 编号对应独立评阅准备与主交付009

[编号评阅ZIP](../data/processed/aspect_reference/research_exports/aspect_numbered_translation_review_20261025_001.zip)含1304个双语例组的全部1335个组成部分对应。两份独立表共8010分类格，全空；另32个单语组和117个隔离编号组不作译对评价。与旧22目标、337条行内空包有不同口径及来源重合，不能相加计独立样本。

评阅者分别复制A/B CSV，按review_id查原例组、原转录、候选、原页及实际语言范围，判断边界、译文充分性和语境充分性；不向对方看表。模型评价标签、编校理由、元数据角色判断没有进入上下文，原印星号、比较、书内括注仍可见，属于来源知情评价。候选层是统一评价对象，原转录同时保留；不是对材料出处盲评。对话多句不自动判错，中文先于俄文及只部分对应的语境按实际材料判断，不补译。

[空包验收](../data/processed/aspect_reference/reviews/numbered_translation_review_verification_20261025_001.json)核2670个语言范围、全量对应成员、源文本与候选字段一致、A/B相反顺序、空格和备注均空。空表在禁读原项目/禁网络的解压环境运行，结果no_paired_annotations；各字段共同标注0、一致率和κ为空。独立目录复建相同，包被改写或声明相同评阅ID时拒绝。声明不同ID不证明实际独立，实际专家评价仍0。

[主ZIP009](../data/processed/aspect_reference/research_exports/aspect_research_delivery_20261025_009.zip)收261文件，目录004为16研究包/130包内文件/109证据报告。延续行内030的480组/337对应、编号双语041/单语001；总1933来源组、默认412/显式1816，117隔离。统一入口默认目录004，查询计数未因增加空包改变。[34项隔离验收](../data/processed/aspect_reference/reviews/research_delivery_verification_20261025_009.json)与[字节复建](../data/processed/aspect_reference/reviews/research_delivery_reproducibility_20261025_009.json)通过；运行前后包不变，旧008及更早包保持冻结。

[25日论文方法与工程结果底稿](aspect_reference_thesis_methods_20261025.md)已按当前冻结材料重写，并从11个来源清单重算25项当前统计；[事实核查](../data/processed/aspect_reference/reviews/thesis_methods_verification_20261025_001.json)保存报告指纹。旧检索/消融结果仍保留原版本，不扩大实验分母，不把工程通过当语言学准确率。行内提取未穷尽，独立专家评价与自然语料验证未完成，7疑点不解除。

主ZIP SHA256：`fff3de26b346e2c7040657bc268c0f72068f17986d844793bfb32de61865b7bd`。
