"""Local question retrieval using book topics and literal Russian words.

This is bounded lexical retrieval, not semantic understanding or answer generation.
Only ready sections are returned; the reviewed body and database are never changed.
"""
from contextlib import closing
import json
import math
from pathlib import Path
import re
import sqlite3

from grammar_reference import DB, normalize

# Topic labels from this book. Longer matches consume their spans, so 未完成体
# does not also become 完成体 and 无人称动词 does not also become 动词.
TOPICS = tuple('词根 同根词 同族词 词素 词缀 前缀 后缀 词尾 词干 构词 名词 动物名词 非动物名词 '
               '形容词 性质形容词 关系形容词 物主形容词 长尾 短尾 比较级 最高级 '
               '数词 定量数词 不定量数词 集合数词 分数词 顺序数词 代词 否定代词 '
               '动词 及物动词 不及物动词 不定式 完成体 未完成体 兼体 陈述式 '
               '假定式 条件式 命令式 现在时 过去时 将来时 人称 无人称动词 无人称句 '
               '形动词 副动词 副词 前置词 连接词 关联词 语气词 感叹词 '
               '主语 主体 谓语 补语 直接补语 间接补语 定语 状语 同位语 同等 独立 '
               '单部句 双部句 主从复句 并列复句 从句 直接引语 间接引语 '
               '第一格 第二格 第三格 第四格 第五格 第六格 单数 复数 重音 否定 '
               '标点 逗号 冒号 分号 破折号 引号 括号'.split())

# Cover the book's narrower categories, rather than reducing every question to
# its broad word class. These are source labels, not new definitions or synonyms.
TOPICS += tuple('语法意义 语法手段 语法形式 语法范畴 词类 语音交替 构词法 '
                '生产词 派生词 构词模式 形态 词组 句法联系 并列联系 主从联系 '
                '一致联系 支配联系 依附联系 主导词 从属词 '
                '普通名词 专有名词 具体名词 抽象名词 集合名词 物质名词 共性名词 '
                '不变格名词 复合名词 复合缩写词 动名词 主观评价 姓氏 地名 '
                '变格法 第一变格法 第二变格法 第三变格法 长尾形式 短尾形式 '
                '人称代词 反身代词 物主代词 疑问代词 关系代词 指示代词 限定代词 不定代词 '
                '变位法 变位形式 非变位形式 单体动词 反身动词 运动动词 '
                '主动形动词 被动形动词 被动态 主动态 相对时间 '
                '限定副词 性质副词 疏状副词 代副词 状态词 原始前置词 '
                '副词前置词 动词前置词 名词前置词 并列连接词 主从连接词 解说连接词 '
                '疑问语气词 肯定语气词 否定语气词 指示语气词 限制语气词 加强语气词 拟声词 '
                '陈述句 疑问句 祈使句 感叹句 肯定句 否定句 单句 复句 '
                '简单谓语 动词性合成谓语 静词性合成谓语 复合谓语 系词 表语 次要成分 '
                '一致定语 非一致定语 确定人称句 不定人称句 泛指人称句 不定式句 称名句 存现句 '
                '同等成分 同等定语 同等主语 总括词 独立成分 独立定语 独立同位语 '
                '独立状语 独立补语 比较短语 呼语 插入语 插入句 嵌入结构 不完全句 独词句 '
                '词序 非纯直接引语 无连接词复句 说明从句 限定从句 行为方法从句 '
                '程度与度量从句 比较从句 处所从句 时间从句 目的从句 原因从句 条件从句 '
                '让步从句 结果从句 接续从句 主句 分句 简缩结构 提位 分割结构 '
                '句号 问号 感叹号 省略号'.split())

TOPICS += tuple('行为方法状语 程度状语 度量状语 处所状语 时间状语 原因状语 目的状语 '
                '条件状语 让步状语 方面状语 因果关系 条件制约关系 联合关系 列举关系 '
                '对比关系 对别关系 从句形式 动词谓语缺位句 代词化 对应体'.split())

TOPICS += tuple('句子 述谓性 情态性 时间性 逻辑重音 停顿 交际目的 '
                '特指问句 是非问句 选择问句 修辞疑问句 祈使疑问句 祈使意义 '
                '扩展句 非扩展句 繁化句 非繁化句 完全否定句 部分否定 '
                '比拟语气词 表示言语方式的语气词'.split())

TOPICS += tuple('语法 词法 句法 实词 虚词 静词 词类转化 临时性转化 永久性转化 '
                '综合前缀 构词前缀 构词后缀 构形后缀 尾缀 中缀 零位词缀 零词尾 '
                '生产词干 形态构词法 语义构词法 词汇-句法构词法'.split())

TOPICS += tuple('名词性 名词数 动词的时 动词的式 第二人称命令式 第三人称命令式 '
                '变位 阳性 阴性 中性 性属 自然性别 软音符 单复数 时间形式'.split())

TOPICS += tuple('名词格 直接格 间接格 展词格 非展词格 主体意义 客体意义 限定意义 '
                '信息补足意义 变格 硬变化 软变化 混合变化 隐现元音'.split())

TOPICS += tuple('时间度量 时间长度 持续时间 人称词尾'.split())

TOPICS += tuple('人称形式 无人称形式 纯反身意义 相互反身意义 一般反身意义 '
                '间接反身意义 能动无客体意义 消极感受意义 固定无生物客体意义 命令意义'.split())

TOPICS += tuple('句法对象 句法术语 狭义词组 广义词组 次要成分兼类 扩展全句'.split())

TOPICS += tuple('联合连接词 区分连接词 对比-对别关系 递序从句'.split())

TOPICS += tuple('计量名词 第二人称命令式体 目的指示词'.split())
TOPICS += ('数词读法',)
TOPICS += ('复合姓',)
TOPICS += ('时间前置词',)

# Bounded surface variants of named grammatical categories. Single 时/式/性/数
# are not topics: they also occur in ordinary language and unrelated questions.
TOPIC_FORMS = {
    '复合缩写词': ('复合缩写词', '缩写词'),
    '名词性': ('名词性', '名词的性'),
    '名词数': ('名词数', '名词的数'),
    '名词格': ('名词格', '名词的格'),
    '动词的时': ('动词的时', '动词时', '俄语时', '体时', '时的范畴', '三种时', '四种时', '五种时'),
    '动词的式': ('动词的式', '动词式', '式的范畴', '三种式'),
    '单复数': ('单复数', '单、复数'),
    '对应体': ('对应体', '体的对应'),
    '纯反身意义': ('纯反身意义', '纯反身动词', '直接反身意义'),
    '相互反身意义': ('相互反身意义', '相互反身动词'),
    '一般反身意义': ('一般反身意义', '一般反身动词'),
    '间接反身意义': ('间接反身意义', '间接反身动词'),
    '能动无客体意义': ('能动无客体意义', '能动无客体动词'),
    '消极感受意义': ('消极感受意义', '消极感受动词'),
    '固定无生物客体意义': ('包括固定无生物客体意义', '固定无生物客体意义', '包括固定客体意义', '固定客体'),
    '命令意义': ('命令意义', '命令式意义', '表示命令', '表达命令'),
    '句法对象': ('句法对象', '句法研究对象'),
    '句法术语': ('句法术语', '句法这个术语'),
    '次要成分兼类': ('次要成分兼类', '兼类现象'),
    '扩展全句': ('扩展全句', '说明全句', '扩展、说明全句'),
    '对比-对别关系': ('对比-对别关系', '对比对别关系', '对比对别'),
}

POSITION_TERMS = frozenset(('主语', '谓语', '表语', '系词', '定语', '补语', '状语'))
POSITION_CUES = ('词序', '位置', '前后', '先后', '在前', '在后', '之前', '之后',
                 '前面', '后面', '句首', '句末')
RUSSIAN_WORD = re.compile(r'[а-яё\u0308\u0306]+')


def term_count(term, text):
    if RUSSIAN_WORD.fullmatch(term):
        # Short function words are grammar subjects too. Match complete words:
        # об must not match обман, and по must not match every verb prefix.
        return len(re.findall(r'(?<![а-яё\u0308\u0306])' + re.escape(term) +
                              r'(?![а-яё\u0308\u0306])', text))
    return sum(text.count(form) for form in TOPIC_FORMS.get(term, (term,)))


def question_terms(question):
    text = normalize(question)
    occupied, found = set(), []
    forms = [(form, term) for term in TOPICS for form in TOPIC_FORMS.get(term, (term,))]
    # Recognize an explicitly named noun case category without treating the
    # single character 格 (价格/格式/表格) as a grammatical query on its own.
    forms.extend((m.group(), '名词格') for m in re.finditer(
        r'名词.{0,8}?(?:有几个格|各格|格属性)', text))
    # Only constituent categories provide the scope for 兼有/兼具. A word class
    # can have several features too; that is not the book's constituent 兼类.
    forms.extend((m.group(), '次要成分兼类') for m in re.finditer(
        r'(?:定语|补语|状语|次要成分).{0,8}?(?:兼有|兼具|兼类|过渡)', text))
    # A time phrase only identifies a preposition topic when the question
    # explicitly names prepositions; ordinary scheduling questions stay out.
    if '前置词' in text:
        forms.extend((m.group(), '时间前置词') for m in re.finditer(
            r'(?:时间|时刻|时期).{0,4}?(?:之前|之后|以前|以后|意义)', text))
    forms.extend((m.group(), '命令意义') for m in re.finditer(
        r'(?:严格(?:、|和|又)?断然|严格|断然)(?:的)?命令', text))
    # The book defines a single-part sentence by one kind of principal
    # constituent. Require the sentence noun so ordinary product ingredients
    # do not become grammatical queries.
    forms.extend((m.group(), '单部句') for m in re.finditer(
        r'(?:只有|仅有)一种主要成分(?:的)?句子|句子.{0,4}?(?:只有|仅有)一种主要成分', text))
    # Readings of written numbers are the subject of this book's numeral
    # chapter. Do not treat an arbitrary year, price or score as a topic.
    forms.extend((m.group(), '数词读法') for m in re.finditer(
        r'(?:数字|数目|数词).{0,8}?(?:读法|怎么读|怎样读|读出)|'
        r'[0-9]+(?:[ ,，.][0-9]+)*(?:(?!小说|文章|文件|课文|书籍|书本).){0,8}?(?:怎么|怎样|如何)(?:分段|分组)?读', text))
    if '俄语' in text or RUSSIAN_WORD.search(text):
        forms.extend((m.group(), '数词读法') for m in re.finditer(
            r'读(?:作|成|做)?\s*[0-9]+(?:[ ,，.][0-9]+)*|读.{0,8}?(?:万|亿)', text))
    for form, term in sorted(forms, key=lambda pair: (-len(pair[0]), pair)):
        for match in re.finditer(re.escape(form), text):
            if term == '动词的时' and form.endswith('时') and text[match.end():match.end()+1] in ('间', '刻', '候'):
                continue
            # 词组成 in 两个词组成 contains a verb, not the topic 词组.
            # Keep genuine 词组 and 词组组成 intact.
            if term == '词组' and text[match.end():match.end()+1] == '成':
                continue
            span = set(range(match.start(), match.end()))
            if not span & occupied:
                found.append((match.start(), term))
                occupied |= span
    # No Russian stemming or е/ё substitution. Surface words must occur in the book.
    found.extend((m.start(), m.group()) for m in RUSSIAN_WORD.finditer(text))
    return list(dict.fromkeys(t for _, t in sorted(found)))


def search_question(question, limit=3, db=DB):
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 2000:
        raise ValueError('Question must contain 1–2000 characters')
    if not 1 <= limit <= 10:
        raise ValueError('Invalid evidence limit')
    terms = question_terms(question)
    if not terms:
        return [], terms
    with closing(sqlite3.connect(f'{Path(db).resolve().as_uri()}?mode=ro', uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        source = dict(conn.execute('SELECT * FROM source').fetchone())
        rows = [dict(r) for r in conn.execute("SELECT * FROM chunks WHERE status='ready'")]
    # 词法/句法 in the administrative prefix is not the section's topic title.
    def topic_title(raw):
        title = re.sub(r'^(词法|句法)\s+§\d+\s+', '', raw)
        # §122 is under the source chapter 直接引语与间接引语, but its
        # section heading is only 概述. Retain that chapter scope for search.
        if raw == '句法 §122 概述':
            title = '直接引语与间接引语概述'
        # These two headings occur within 动词 in this book; retain that scope
        # in the retrieval title without altering the source title or body.
        title = {'时的概述': '动词的时概述', '式的概述': '动词的式概述',
                 '名词性的概述': '名词性概述', '格的概述': '名词格概述',
                 '格的意义和用法概述': '名词格的意义和用法概述',
                 '体的概述': '完成体与未完成体概述',
                 '体和时间度量': '完成体与未完成体的时间度量、时间长度、持续时间',
                 '数词概述': '数词概述（计量名词）',
                 '句法的对象和任务': '句法对象、句法术语及任务',
                 '词组概述': '词组概述（广义词组与狭义词组）',
                 '句子及其基本特征': '句子及其基本特征（述谓性、情态性、时间性、称名句时间意义）',
                 '单句的结构类别': '单句的结构类别（单部句与双部句）',
                 '划分次要成分应注意的问题': '划分次要成分应注意的问题（次要成分兼类）'}.get(title, title)
        if title.startswith('表示时间意义的') and '时间前置词' in terms:
            title += '（时间前置词）'
        if title == '动词的两种变位法' and '人称词尾' in terms:
            title += '（人称词尾）'
        if title == '带目的从句的主从复句' and '目的指示词' in terms:
            title += '（目的指示词）'
        if title == '定量数词的构成和读法' and '数词读法' in terms:
            title += '（数词读法）'
        return normalize(title)
    documents = [(r, topic_title(r['title']), normalize(r['body'])) for r in rows]
    matches = [(row, title, {t: (term_count(t, title), term_count(t, body)) for t in terms})
               for row, title, body in documents]
    weights = {t: 1 + math.log((len(rows)+1) / (1+sum(any(counts[t]) for _,_,counts in matches))) for t in terms}
    # Generic discipline names help when asked alone, but should not overwhelm
    # a concrete topic such as 停顿 merely because introductory titles name 语法.
    general = frozenset(('语法', '词法', '句法'))
    if any(t not in general for t in terms):
        weights = {t: weight * (0.25 if t in general else 1) for t, weight in weights.items()}
    # A broad operation such as declension should not drown out the named
    # subject (e.g. 连接词会变格吗) merely because many noun titles mention it.
    if len(terms) > 1 and '变格' in weights:
        weights['变格'] *= 0.5
    # Concrete case functions should remain visible beside constituent titles.
    cases = frozenset(('第一格', '第二格', '第三格', '第四格', '第五格', '第六格'))
    if cases & weights.keys():
        for term in POSITION_TERMS & weights.keys():
            weights[term] *= 0.5
    # Aspect is the subject when asked alone; with a named operation such as
    # 综合前缀 or a form feature such as 词尾, keep that narrower topic visible.
    aspect = frozenset(('完成体', '未完成体'))
    if any(t not in aspect for t in terms):
        for term in aspect & weights.keys():
            weights[term] *= 0.5
    aspect_cue = bool(re.search(r'完成体|选体|体的|什么体|哪种体|哪个体|体怎样|体如何', question))
    negative_infinitive = bool(re.search(r'否定(?:的)?不定式|不定式(?:句)?(?:的)?否定', question))
    negative_past = bool(re.search(r'否定(?:的)?过去时|过去时(?:的)?否定', question))
    scored = []
    for row,title,counts in matches:
        hits = [t for t in terms if any(counts[t])]
        if not hits:
            continue
        # Repeated mentions are bounded so a long section cannot win by length alone.
        score = sum(weights[t] * (3 * bool(counts[t][0]) + 1 + min(counts[t][1], 3)/3) for t in hits)
        section_title = re.sub(r'^\S+\s+§\d+\s+', '', title)
        # A named form's aspect/negation question needs its usage section as
        # well as the general form. Keep these source headings visible when
        # two structures are compared; this does not infer an answer.
        if '不定式' in weights and (aspect_cue or negative_infinitive) and section_title == '不定式句中体的用法':
            score += 3 * weights['不定式']
        if '过去时' in weights and negative_past and section_title == normalize('“не＋过去时”结构中体的用法'):
            score += 3 * weights['过去时']
        if '第二人称命令式' in weights and aspect_cue and section_title == '第二人称命令式体的用法':
            score += 3 * weights['第二人称命令式']
        if any(word in question for word in ('定义', '是什么', '主要', '概述', '含义')):
            score += sum(3 * weights[t] for t in hits if section_title in (t, t+'概述'))
        # Placement questions compete with many agreement/form sections. Promote
        # a source's placement title only when the question names a constituent
        # and a position cue; this does not infer a grammatical answer.
        if any(cue in question for cue in POSITION_CUES) and any(t in POSITION_TERMS for t in terms):
            if '位置' in section_title or '词序' in section_title:
                score += sum(5 * weights[t] for t in hits if t in POSITION_TERMS)
        pages = json.loads(row['pdf_pages'])
        scored.append(dict(code=row['code'], title=row['title'], body=row['body'], score=round(score,6),
                           matched_terms=hits, pdf_pages=pages, printed_pages=json.loads(row['printed_pages']),
                           citation=f"{source['title']}，PDF {pages[0]}–{pages[-1]} 页",
                           source_path=source['path'],source_sha256=source['sha256'],review_status='visual_checked'))
    return sorted(scored,key=lambda r: (-r['score'],r['code']))[:limit], terms
