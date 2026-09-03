# TEM8 Knowledge Taxonomy

> 本文档记录俄语专八第一版知识点树。
> 它用于人工审核、题目打标、错题归因、AI 讲解和后续巩固练习生成。

## 1. 设计原则

第一版知识点树服务于两个目标：

- 让题目审核时有稳定标签可选。
- 让学生错题分析能落到具体复习方向。

当前知识点树不是最终版。后续人工审核真题时，如果发现某类考点频繁出现，可以继续拆细；如果某类标签长期不用，可以合并。

## 2. 四大类

### 2.1 语法与词汇

代码前缀：`grammar`

用于标注综合知识中偏语言形式、搭配和语体的题目。

学生画像和专项训练使用三个稳定方向：

- `grammar.forms`: 词形与动词系统
- `grammar.collocation`: 词义、前置词与搭配
- `grammar.sentence`: 句法、连接与表达

以下细标签继续用于内部审核和错题解释，不直接生成学生掌握度：

- `grammar.case`: 名词格与支配关系
- `grammar.preposition`: 前置词搭配
- `grammar.aspect`: 动词体
- `grammar.motion_verbs`: 运动动词
- `grammar.verb_form`: 动词时态、语气与命令式
- `grammar.participle`: 形动词
- `grammar.adverbial_participle`: 副动词
- `grammar.numeral`: 数词与数量结构
- `grammar.pronoun`: 代词与指代
- `grammar.adjective_adverb`: 形容词、副词与比较级
- `grammar.syntax_simple`: 简单句句法
- `grammar.syntax_complex`: 复合句与连接词
- `grammar.lexical_choice`: 词义辨析与固定搭配
- `grammar.style`: 语体与修辞

### 2.2 俄罗斯文学

代码前缀：`literature`

用于标注作家作品、文学史和文学术语相关题目。

学生画像和专项训练统一使用：

- `literature.knowledge`: 作家、作品与文学常识

内部审核仍可区分：

- `literature.author_work`: 作家与作品
- `literature.work_content`: 人物、名句与情节
- `literature.history_movements`: 文学史与流派
- `literature.genre_terms`: 体裁与文学术语

文学知识点按学生需要复习的任务分类，不再按19世纪、白银时代、苏联时期拆分。同一道“作家与作品对应”题不会因为作家所属时代不同而落入不同画像。

### 2.3 俄罗斯国情

代码前缀：`culture`

用于标注俄罗斯历史、地理、政治、社会文化常识。

学生画像和专项训练统一使用：

- `culture.knowledge`: 俄罗斯国情常识

内部审核仍可区分：

- `culture.geography`: 地理与行政区划
- `culture.history`: 历史事件与时代
- `culture.politics`: 政治制度与国家机构
- `culture.symbols`: 国家象征与节日
- `culture.education_science`: 教育、科技与文化机构
- `culture.society`: 社会生活与传统

### 2.4 阅读理解

代码前缀：`reading`

阅读题统一绑定 `reading.comprehension`，学生画像只展示 `reading_choice` 题型级掌握度，不再向学生拆分事实细节、语境词义等机械子标签。阅读专项仍必须按完整文章题组返回。

下列标签只作为题库内部元数据保留，不进入学生细知识画像或弱项推荐：

- `reading.main_idea`: 主旨大意
- `reading.detail`: 事实细节
- `reading.inference`: 推理判断
- `reading.vocabulary_context`: 语境词义
- `reading.structure`: 篇章结构
- `reading.attitude`: 作者态度与语气

## 3. 入库脚本

知识点树通过脚本写入本地 SQLite：

```text
.venv\Scripts\python.exe scripts\seed_tem8_knowledge_points.py
```

脚本是可重复运行的；同一个 `code` 会更新名称、说明和排序，不会重复插入。

如果需要清空并重建：

```text
.venv\Scripts\python.exe scripts\seed_tem8_knowledge_points.py --reset
```

注意：如果已有题目绑定知识点，`--reset` 会拒绝执行，避免破坏题目标签。

## 4. 后续打标规则

每道进入正式题库的题至少应绑定一个知识点。

建议规则：

- 语法、文学、国情选择题至少标一个对应大类下的具体标签。
- 阅读题可以保留内部能力点，但学生侧只按阅读题型统计和训练。
- 如果一道题同时涉及多个点，可以绑定多个知识点。
- 不确定时先标到较粗的父级，人工复核后再细化。
- 错题分析优先使用最细粒度标签；没有细粒度标签时使用父级标签。
