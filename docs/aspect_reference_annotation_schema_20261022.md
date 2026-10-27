# 体学语义试标字段说明与下一版规范

本说明对应[22目标试标](../data/processed/aspect_reference/reviews/semantic_annotation_pilot_20261022_001.md)。它是发展规范的教材试验，不是正式自然语料标注标准。每条只定位一个目标，不标邻句所有动词；形态、语义解释和来源状态应分别保留。

|字段|本版含义|标注边界|
|---|---|---|
|example_id / source_unit|编号锚段及所属节|锚段不是完整例句边界或独立观察样本保证|
|target / lemma|精确目标字形、模型判读词元|词元尚未词典全量复核；同形歧义须保留候选|
|target_source_start/end|目标在原节中的Unicode偏移，左闭右开|按原印层计，不按候选改译后的字符位置计|
|target_page_evidence|目标字形实际落页、印刷页及图文指纹|不是整锚段页集，更不是整个单元覆盖证明|
|language|ru或zh|汉语的体理论标签不等同俄语形态分类|
|aspect|目标体的模型解释|俄语明确两体与书写歧义分开；汉语了₁标签标作来源框架|
|tense / mood|目标形式及其构式信息|命令式和独立不定式无形态时，不直接标将来|
|polarity|目标所处肯定、否定或否定情态辖域|нельзя否定情态不等于不定式词形有否定词缀|
|event_time|相对言语或叙事参照点的时间解释|和词形时态分开；无依据填写不能定位|
|reading|多个来源知情的解释标签|允许多标签，不以章标题给全部例句自动赋值|
|occurrence|片段中断言、提问、预设、命令、许可等地位|断言指教材话语内部断言，不是研究者核实世界事实|
|result|片段是否承诺结果、结果状态或后果|说了话不等于劝说生效；许可不等于执行|
|repetition|实际有限总和、单位时间频率、一般反复等|未确定次数与只有一次不同；能力不等于真实反复|
|time_measure|次数、行动持续、事后间隔或状态持续|将时间短语的量度对象与其表面长短分开|
|note|读法依据、反例及未决部分|不能用注释消除正文未知或歧义字段|
|state / external_source_cautions|源节状态及文学异文警示|语义标签不解除来源隔离，警示随记录保留|

## 本版暴露的字段限制

`tense`在多数俄语人称形式中记录形态时间，但在`будете заказывать`中使用了包含助动词环境的编码，在`узнаешь`中记录作者选择的现在读法。这些值不能直接混入纯形态时态分布统计。下一版宜拆成`target_morphological_tense`、`auxiliary_form`、`construction_tense`和`source_selected_reading`。汉语`not_morphologically_encoded`不是“没有时间意义”。

`aspect`中无ё/重音的`узнаешь`保留书写歧义，而不强行按作者解释当作词形工具的确定答案。若需要词元计数，下一版把`lemma`中的候选说明拆成词元候选数组与作者选择项。当前自由文本字段只适合阅读和规范讨论。

`result`和`occurrence`的值当前较具体，用来暴露不同情况，尚未形成互斥、穷尽的正式标签集。后续可拆为“事件发生性”“内在结果达成”“参照时结果状态”“后果相关性”四轴，并在每轴允许未知和不适用。不能把所有带`asserted`的值一并计成完成结果。

语言形式支持与事实支持也应分列。教材可以支持命令式措辞，却不能证明某校本周菜单；这一差别已见[8道范围外取证复核](../data/processed/aspect_reference/rag/out_of_scope_support_review_20261022_001.md)。即使引句机械存在，仍可能不支持问题真正所求。

## 下一轮标注的最小步骤

1. 固定论文实际使用的自然语料来源、抽样时间及单位；保持与教材开发试样分离。
2. 保留目标字符偏移及足够语境，先判词形，允许词元、体、时/式歧义；再判来源所指事件，不以模型解释补事实。
3. 将断言、预设、提问、命令、许可及能力分别处理，再标结果与重复；没有足够证据时保留未知。
4. 在对检索器输出不知情的条件下另行复核，记录分歧及裁决依据。至少报告逐字段覆盖和未决比例，不用来源定位通过率代替语义一致率。

这些是后续研究规范建议，目前没有自然语料实验、独立人员标注、一致率结果或生成答案实验。原22条保持不可变，不因本说明而静默改变标签或重新计算冻结题成绩。

## 2026-10-23多轴002实现

[多轴试标002](../data/processed/aspect_reference/research_exports/aspect_annotation_pilot_20261022_002/README.md)在独立目录实现上述拆分，原22条001不变。联合form_analyses保存词元、体、形式类、形态时、语法时及带重音/ё候选；source_selected_analysis仅记本书立场。形态时用past/nonpast/none/not_encoded，语法时另记past/present/future/none/not_encoded，防止未来PFV非过去词形与语义时间混淆。construction另记助动词、组合时态和汉语标记。

semantic_axes分为discourse_status、event_realization、lexical_goal_attainment、reference_result_state、consequence_relevance；每轴指定依据引句和模型说明。未知、未断言与不适用不是同一值。发生承诺仅指教材话语内部，world_facts_verified始终false。quantification分别记录次数、单位时间频率、活动/状态持续与事后间隔，时量表达也有精确偏移。

当前22目标、39解释引句、1助动词、5汉语标记和7量度短语已机械绑定验证；这些不是39条语义已被独立证明。selected_readings.tsv仅为阅读导出，不能删除analysis_count后当成词形金标。后续正式标注仍需独立评阅、分歧记录和另定自然语料抽样。

多轴002的词形附核另存[词典支持记录](../data/processed/aspect_reference/reviews/annotation_form_lexicographic_support_20261023_001.json)：[узнавать词典页](https://gramota.ru/meta/uznavat)、[узнать词典页](https://gramota.ru/meta/uznat)支持两组词形候选，不证明教材实际语境选择。该2项为附层词典记录，不混入候选007固定的28项来源。

## 2026-10-23接续：当前重绑定版

当前使用[试标23日001](../data/processed/aspect_reference/research_exports/aspect_annotation_pilot_20261023_001/README.md)及[空包23日002](../data/processed/aspect_reference/research_exports/aspect_review_packet_20261023_002/README.md)，绑定候选23日002和索引23日002。原22标签、39依据、词形及目标不变；2条所在源节的字形/警示元数据更新。旧22日002与旧空包001固定旧来源保留，不能按当前全兼容引用。264格仍空，独立标注0；重绑定不算新的语义审核。
