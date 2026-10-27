from __future__ import annotations

import copy
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from grammar_reference import dump, file_sha256, import_batch
from grammar_rag import prepare, validate_response
from grammar_question_search import question_terms


class GrammarRagTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.pdf, self.db = self.root / 'source.pdf', self.root / 'grammar.sqlite'
        with pymupdf.open() as doc:
            for _ in range(3):
                doc.new_page()
            doc.save(self.pdf)
        self.body = '**кни́ж**ный〔书的〕。词根可以发生语音交替。\n限制和例外需结合上下文。'
        self.batch = dict(batch_id='a', source_sha256=file_sha256(self.pdf), pages=[
            dict(pdf_page=1, printed_page='11', review_method='visual_comparison', fragments=[
                dict(code='m.1', title='词根', body=self.body, start=True, end=True)]),
            dict(pdf_page=2, printed_page='12', review_method='visual_comparison', fragments=[
                dict(code='m.2', title='隔离节', body='secret blocked source', start=True, end=True, unresolved=['原书疑点'])]),
        ])
        path = self.root / 'batch.json'
        dump(path, self.batch)
        import_batch(path, db=self.db, pdf=self.pdf, apply=True)

    def tearDown(self):
        self.temp.cleanup()

    def packet(self, **kwargs):
        return prepare('本书如何说明词根？', 'книжный', db=self.db, **kwargs)

    def response(self):
        return dict(status='answered', claims=[dict(text_zh='本书说明词根可以发生语音交替。',
                                                  citations=[dict(source_id='G1', quote='词根可以发生语音交替')])])

    def revise(self, *, body=None, notes=None):
        with closing(sqlite3.connect(self.db)) as conn:
            raw, sha = conn.execute('SELECT review_json,review_sha256 FROM pages WHERE pdf_page=1').fetchone()
        p = json.loads(raw)
        p.update(expected_review_sha256=sha, correction_reason='Test source revision')
        if body is not None:
            p['fragments'][0]['body'] = body
        if notes is not None:
            p['fragments'][0]['unresolved'] = notes
        path = self.root / 'correction.json'
        dump(path, dict(batch_id='b', source_sha256=file_sha256(self.pdf), pages=[p]))
        import_batch(path, db=self.db, pdf=self.pdf, apply=True)

    def test_prepare_preserves_whole_section_and_read_only_database(self):
        before = file_sha256(self.db)
        packet = self.packet()
        self.assertEqual(packet['status'], 'prepared')
        self.assertEqual(packet['sources'][0]['body'], self.body)
        self.assertEqual(packet['sources'][0]['printed_pages'], ['11'])
        self.assertIn('page_evidence', packet['sources'][0])
        self.assertEqual(packet['prompt_package']['user_payload']['retrieved_sources'], packet['sources'])
        self.assertEqual(file_sha256(self.db), before)

    def test_no_evidence_and_budget_never_send_partial_or_blocked_section(self):
        packet = prepare('说明隔离节', 'secret', db=self.db)
        self.assertEqual(packet['status'], 'no_evidence')
        self.assertIsNone(packet['prompt_package'])
        tiny = self.packet(max_context_chars=len(self.body)-1)
        self.assertEqual(tiny['status'], 'context_over_budget')
        self.assertEqual(tiny['sources'], [])
        self.assertEqual(tiny['omitted_sections'][0]['code'], 'm.1')
        self.assertIsNone(tiny['prompt_package'])

    def test_valid_quote_attaches_source_and_preserves_database(self):
        packet = self.packet()
        before = file_sha256(self.db)
        result = validate_response(packet, self.response(), db=self.db)
        ref = result['claims'][0]['citations'][0]
        self.assertEqual(ref['pdf_pages'], [1])
        self.assertEqual(ref['source_sha256'], file_sha256(self.pdf))
        self.assertEqual(result['status'], 'citations_checked')
        self.assertEqual(file_sha256(self.db), before)

    def test_unknown_source_fabricated_quote_and_marker_only_quote_rejected(self):
        packet = self.packet()
        for change in (dict(source_id='G99'), dict(quote='原文未出现的规则'), dict(quote='******``````')):
            response = self.response()
            response['claims'][0]['citations'][0].update(change)
            with self.assertRaises(ValueError):
                validate_response(packet, response, db=self.db)
        bad = self.response()
        bad['answer_zh'] = 'Uncited conclusion'
        with self.assertRaises(ValueError):
            validate_response(packet, bad, db=self.db)

    def test_changed_source_or_new_quarantine_invalidates_old_packet(self):
        packet = self.packet()
        self.revise(notes=['后来发现原书疑点'])
        with self.assertRaisesRegex(ValueError, 'not ready'):
            validate_response(packet, self.response(), db=self.db)
        self.assertEqual(self.packet()['status'], 'no_evidence')

    def test_page_revision_requires_new_packet_even_when_claim_quote_survives(self):
        packet = self.packet()
        self.revise(body=self.body + '\n新增来源限制。')
        with self.assertRaisesRegex(ValueError, 'Stale or altered'):
            validate_response(packet, self.response(), db=self.db)
        validate_response(self.packet(), self.response(), db=self.db)

    def test_altered_packet_or_derived_chunk_is_rejected(self):
        packet = self.packet()
        altered = copy.deepcopy(packet)
        altered['sources'][0]['body'] += ' fabricated'
        with self.assertRaisesRegex(ValueError, 'Stale or altered'):
            validate_response(altered, self.response(), db=self.db)
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute("UPDATE chunks SET body='fabricated' WHERE code='m.1'")
            conn.commit()
        with self.assertRaisesRegex(ValueError, 'Stale section'):
            self.packet()

    def test_source_pdf_change_and_invalid_refusal_are_rejected(self):
        packet = self.packet()
        result = validate_response(packet, dict(status='insufficient_evidence', message_zh='资料不足。'), db=self.db)
        self.assertEqual(result['claims'], [])
        with self.assertRaises(ValueError):
            validate_response(packet, dict(status='insufficient_evidence', message_zh='资料不足。', claims=[]), db=self.db)
        with self.pdf.open('ab') as f:
            f.write(b'changed')
        with self.assertRaisesRegex(ValueError, 'fingerprint changed'):
            self.packet()

    def test_question_retrieval_uses_topics_and_preserves_evidence(self):
        before = file_sha256(self.db)
        packet = prepare('本书怎样说明词根？', db=self.db)
        self.assertEqual(packet['status'], 'prepared')
        self.assertEqual(packet['sources'][0]['code'], 'm.1')
        self.assertEqual(packet['sources'][0]['body'], self.body)
        self.assertEqual(packet['retrieval']['mode'], 'question_lexical')
        self.assertIsNone(packet['query'])
        self.assertEqual(file_sha256(self.db), before)
        self.assertEqual(self.packet()['retrieval']['mode'], 'explicit_keywords')

    def test_question_retrieval_rejects_irrelevant_and_quarantined_content(self):
        for question in ('明天北京天气如何？', '解释secret blocked source', '解释несуществующее'):
            packet = prepare(question, db=self.db)
            self.assertEqual(packet['status'], 'no_evidence')
            self.assertIsNone(packet['prompt_package'])
        self.revise(notes=['后来隔离'])
        packet = prepare('词根是什么？', db=self.db)
        self.assertEqual(packet['status'], 'no_evidence')

    def test_question_retrieval_russian_stress_and_yo_are_distinct(self):
        self.revise(body=self.body + '\nсёла：原书示例；села：另一个示例。')
        packet = prepare('如何理解книжный？', db=self.db)
        self.assertEqual(packet['sources'][0]['code'], 'm.1')
        self.assertNotEqual(prepare('解释сёла', db=self.db)['retrieval']['terms'],
                            prepare('解释села', db=self.db)['retrieval']['terms'])
        tiny = prepare('解释词根', max_context_chars=1, db=self.db)
        self.assertEqual(tiny['status'], 'context_over_budget')
        self.assertEqual(tiny['sources'], [])

    def test_question_retrieval_does_not_confuse_unfinished_with_finished(self):
        p = dict(pdf_page=3,printed_page='13',review_method='visual_comparison',fragments=[
            dict(code='m.3',title='完成体',body='本节仅讨论完成体。',start=True,end=True)])
        dump(self.root/'extra.json',dict(batch_id='extra',source_sha256=file_sha256(self.pdf),pages=[p]))
        import_batch(self.root/'extra.json',db=self.db,pdf=self.pdf,apply=True)
        self.assertEqual(prepare('未完成体如何使用？',db=self.db)['status'],'no_evidence')
        self.assertEqual(prepare('完成体如何使用？',db=self.db)['sources'][0]['code'],'m.3')

    def add_search_sections(self, fragments):
        page = dict(pdf_page=3, printed_page='13', review_method='visual_comparison', fragments=[
            dict(code=code, title=title, body=body, start=True, end=True)
            for code, title, body in fragments])
        path = self.root / 'topics.json'
        dump(path, dict(batch_id='topics', source_sha256=file_sha256(self.pdf), pages=[page]))
        import_batch(path, db=self.db, pdf=self.pdf, apply=True)

    def test_specific_book_topic_beats_generic_word_class(self):
        self.add_search_sections([
            ('m.3', '词法 §26 共性名词', '共性名词根据所指对象确定性。'),
            ('m.4', '词法 §17 名词概述', '名词可以表示事物。名词有性。')])
        packet = prepare('共性名词如何确定性？', db=self.db)
        self.assertEqual(packet['retrieval']['terms'], ['共性名词'])
        self.assertEqual(packet['sources'][0]['code'], 'm.3')
        self.revise(notes=['原书疑点仍需隔离'])
        self.assertNotIn('m.1', [s['code'] for s in prepare('共性名词与词根', db=self.db)['sources']])

    def test_dependency_topic_is_not_reduced_to_verb(self):
        self.add_search_sections([
            ('s.1', '句法 §17 支配联系', '支配联系的主导词可以是动词。从属词使用特定的格。'),
            ('m.3', '词法 §102 动词概述', '动词有时、体、人称和式。')])
        packet = prepare('支配联系的主导词只能是动词吗？', db=self.db)
        self.assertEqual(packet['sources'][0]['code'], 's.1')
        self.assertIn('支配联系', packet['retrieval']['terms'])

    def test_position_cues_distinguish_word_order_from_agreement(self):
        self.add_search_sections([
            ('s.1', '句法 §29 名词做主语时谓语的形式', '主语和谓语一致。主语与谓语在数上对应。'),
            ('s.2', '句法 §83 主语和谓语的位置', '主语通常在谓语前。表语可以在系词之前。')])
        for question in ('主语能放在谓语后面吗？', '表语能放在系词之前吗？'):
            self.assertEqual(prepare(question, db=self.db)['sources'][0]['code'], 's.2')
        self.assertEqual(prepare('名词做主语时谓语的形式如何选择？', db=self.db)['sources'][0]['code'], 's.1')

    def test_adverbial_kind_and_clause_relation_keep_their_specific_topics(self):
        self.add_search_sections([
            ('s.1', '让步状语', '让步状语表示未能阻止现象发生的条件。'),
            ('s.2', '行为方法状语', '状语可以说明行为。'),
            ('s.3', '表达因果关系的无连接词复句', '因果关系包括原因和结果。'),
            ('s.4', '无连接词复句概述', '无连接词复句没有连接词。')])
        for question, code in [('让步状语如何表示？', 's.1'), ('无连接词复句怎样表达因果关系？', 's.3')]:
            self.assertEqual(prepare(question, db=self.db)['sources'][0]['code'], code)

    def test_conversion_and_counterpart_topic_keep_specific_evidence(self):
        self.add_search_sections([
            ('m.3', '词法 §101 代词化', '其他词类取得指称功能时发生代词化。'),
            ('m.4', '词法 §90 代词概述', '代词指称事物。代词的指称功能。'),
            ('m.5', '词法 §112 单体动词', '动词有无对应体，往往与词汇意义有关。'),
            ('m.6', '词法 §102 动词概述', '动词表示动作。动词有体。')])
        for question, code in [('代词化是什么意思？', 'm.3'), ('动词有无对应体只由词义决定吗？', 'm.5')]:
            self.assertEqual(prepare(question, db=self.db)['sources'][0]['code'], code)

    def test_short_russian_words_require_complete_word_matches(self):
        self.add_search_sections([
            ('m.3', '前置词', 'об о до по：本书的前置词用法。'),
            ('m.4', '另一个示例', 'обман побежать домой осень：没有上述完整词。')])
        for word in ('об', 'о', 'до', 'по'):
            packet = prepare('解释' + word, db=self.db)
            self.assertEqual(packet['retrieval']['terms'], [word])
            self.assertEqual([s['code'] for s in packet['sources']], ['m.3'])
        packet = prepare('解释по́', db=self.db)
        self.assertEqual(packet['retrieval']['terms'], ['по'])
        self.assertEqual([s['code'] for s in packet['sources']], ['m.3'])

    def test_sentence_topics_do_not_confuse_word_group_with_composition(self):
        self.assertEqual(question_terms('句子必须由两个词组成吗？'), ['句子'])
        self.assertEqual(question_terms('词组由哪些词组成？'), ['词组'])
        self.assertEqual(question_terms('词组组成句子吗？'), ['词组', '句子'])
        self.add_search_sections([
            ('s.1', '句子及其基本特征', '述谓性不一定包含人称意义。逻辑重音体现说话重点。'),
            ('m.3', '人称', '人称形式需要区分。人称形式有单复数。'),
            ('m.4', '重音', '重音位置影响词形。重音可以移动。')])
        for q in ('述谓性怎样表现？', '逻辑重音改变说话重点吗？'):
            self.assertEqual(prepare(q, db=self.db)['sources'][0]['code'], 's.1')

    def test_foundation_topics_do_not_rank_administrative_title_prefixes(self):
        self.add_search_sections([
            ('m.3', '词法 §1 语法概述', '词法的对象是词，句法的对象是句子。语法这个术语有两个含义。'),
            ('m.4', '词法 §9 词缀', '综合前缀同时有构词与改变语法意义两种功能。'),
            ('m.5', '词法 §102 动词概述', '动词表示动作。有完成体和未完成体。'),
            ('s.1', '句法 §5 停顿', '停顿影响词语之间的联系。')])
        for question, code in [('词法与句法的对象相同吗？', 'm.3'),
                               ('语法这个术语有什么含义？', 'm.3'),
                               ('综合前缀是什么意思？', 'm.4'),
                               ('停顿影响语法联系吗？', 's.1')]:
            self.assertEqual(prepare(question, db=self.db)['sources'][0]['code'], code)
        self.assertEqual(question_terms('语法形式与语法手段相同吗？'), ['语法形式', '语法手段'])
        self.assertEqual(question_terms('生产词干构词时如何使用？'), ['生产词干', '构词'])
        self.assertEqual(question_terms('综合前缀只改变完成体吗？'), ['综合前缀', '完成体'])


    def test_gender_tense_mood_and_command_person_have_scoped_topics(self):
        self.add_search_sections([
            ('m.3', '词法 §23 名词性的概述', '名词分阳性阴性中性，与自然性别不总一致。'),
            ('m.4', '词法 §125 时的概述', '动词的时包括过去现在将来，体时组合需要区别。'),
            ('m.5', '词法 §136 式的概述', '动词的式分三种式。'),
            ('m.6', '词法 §140 第二人称命令式的意义', '第二人称命令式表示要求。'),
            ('m.7', '词法 §142 第三人称命令式', '第三人称命令式可表示希望。')])
        for q, code in [('名词的性与自然性别一定相同吗？', 'm.3'),
                        ('动词的时怎样分类？', 'm.4'),
                        ('动词的式怎样分类？', 'm.5'),
                        ('第二人称命令式怎样使用？', 'm.6'),
                        ('第三人称命令式怎样使用？', 'm.7')]:
            self.assertEqual(prepare(q, db=self.db)['sources'][0]['code'], code)
        self.assertEqual(question_terms('第三人称命令式怎样使用？'), ['第三人称命令式'])
        self.assertEqual(question_terms('名词的数与单、复数如何对应？'), ['名词数', '单复数'])
        for q in ('三种时间安排哪个好？', '什么时候余额更新？', '这个格式怎么改？'):
            self.assertEqual(prepare(q, db=self.db)['status'], 'no_evidence')


    def test_case_categories_and_declension_do_not_match_ordinary_ge(self):
        self.add_search_sections([
            ('m.3', '词法 §33 格的概述', '名词的格区分直接格和间接格，也有非展词格。'),
            ('m.4', '词法 §41 名词变格法概述', '硬变化与软变化取决于词干末尾辅音，另有混合变化。'),
            ('m.5', '词法 §201 连接词概述', '连接词本身无形态变化，也不要求被连接词在形态上一致。')])
        for q, code in [('俄语名词有几个格？', 'm.3'),
                        ('非展词格如何使用？', 'm.3'),
                        ('名词的硬变化和软变化怎么区分？', 'm.4')]:
            self.assertEqual(prepare(q, db=self.db)['sources'][0]['code'], code)
        self.assertEqual(question_terms('非展词格是什么？'), ['非展词格'])
        self.assertEqual(question_terms('不变格名词的数怎么表达？'), ['不变格名词'])
        self.assertEqual(prepare('连接词本身会变格吗？', db=self.db)['sources'][0]['code'], 'm.5')
        for q in ('表格有几个格？', '价格多少？', '格式怎样修改？'):
            self.assertEqual(prepare(q, db=self.db)['status'], 'no_evidence')


    def test_aspect_headings_and_counterpart_surface_variant_keep_scope(self):
        self.add_search_sections([
            ('m.3', '词法 §109 体的概述', '未完成体不指明动作是否完成。完成体指出完成。'),
            ('m.4', '词法 §110 体的对应', '两个形式词汇意义相同，体的语法意义不同。'),
            ('m.5', '词法 §115 体和时间度量', '完成体有时间长度状语的例外。'),
            ('m.6', '词法 §106 动词的两种变位法', '未完成体现在时与完成体将来时人称词尾相同。'),
            ('m.7', '词法 §9 词缀', '后缀可以位于词尾之后。'),
            ('s.1', '句法 §43 状语', '状语可以表示时间。')])
        for q, code in [('未完成体一定表示没完成吗？', 'm.3'),
                        ('体的对应需要词义相同吗？', 'm.4'),
                        ('未完成体现在时和完成体将来时人称词尾相同吗？', 'm.6'),
                        ('后缀一定在词尾之前吗？', 'm.7'),
                        ('时间长度状语只能用未完成体吗？', 'm.5')]:
            self.assertEqual(prepare(q, db=self.db)['sources'][0]['code'], code)
        self.assertEqual(question_terms('体的对应是什么？'), ['对应体'])
        self.assertEqual(question_terms('人称词尾怎样变化？'), ['人称词尾'])
        for q in ('字体的对齐怎么调整？', '余额多久更新？'):
            self.assertEqual(prepare(q, db=self.db)['status'], 'no_evidence')


    def test_reflexive_semantic_categories_keep_the_named_subject(self):
        self.add_search_sections([
            ('m.3', '词法 §155 纯反身意义动词', '纯反身意义动词动作返回主体。'),
            ('m.4', '词法 §156 相互反身意义动词', '相互反身意义要求两个或更多参与者。'),
            ('m.5', '词法 §158 间接反身意义动词', '间接反身意义动作为了自身利益。'),
            ('m.6', '词法 §160 消极感受意义动词', '感受者用第三格。'),
            ('m.7', '词法 §161 包括固定无生物客体意义动词', '词义包含固定客体。'),
            ('m.8', '词法 §102 动词概述', '动词表示动作。')])
        for q, code in [('纯反身意义动词表示什么？', 'm.3'),
                        ('相互反身意义可以用单数主语吗？', 'm.4'),
                        ('间接反身意义与纯反身意义有何区别？', 'm.5'),
                        ('消极感受意义动词的感受者用哪个格？', 'm.6'),
                        ('固定客体带ся动词是什么意思？', 'm.7')]:
            self.assertIn(code, [s['code'] for s in prepare(q, db=self.db)['sources']])
        self.assertEqual(question_terms('相互反身意义动词'), ['相互反身意义', '动词'])
        self.assertEqual(question_terms('无人称形式'), ['无人称形式'])
        self.assertEqual(question_terms('固定无生物客体意义'), ['固定无生物客体意义'])
        self.assertIn('命令意义', question_terms('陈述式第二人称形式能表示命令吗？'))


    def test_syntax_scope_and_constituent_overlap_preserve_limits(self):
        self.add_search_sections([
            ('s.1', '句法 §1 句法的对象和任务', '句法有两个含义，中心对象是句子，也研究词组。'),
            ('s.2', '句法 §2 词组概述', '本书狭义词组是主从联系的实词组合，主谓关系不是词组。'),
            ('s.3', '句法 §52 划分次要成分应注意的问题', '次要成分之间有过渡和兼类现象，定语可有状语意义。'),
            ('s.4', '句法 §53 扩展、说明全句的次要成分', '这类成分说明整个句子结构，通常是状语。'),
            ('s.5', '句法 §83 谓语的位置', '谓语可放在句首。')])
        for q, code in [('句法这个术语仅指学科吗？', 's.1'),
                        ('句法研究对象只有句子吗？', 's.1'),
                        ('主语谓语的组合是狭义词组吗？', 's.2'),
                        ('定语能兼有状语意义吗？', 's.3'),
                        ('句首就证明状语是扩展全句成分吗？', 's.4')]:
            self.assertIn(code, [s['code'] for s in prepare(q, db=self.db)['sources']])
        self.assertNotIn('次要成分兼类', question_terms('形动词兼有形容词特征吗？'))
        self.assertNotIn('词组', question_terms('两个词组成句子吗？'))
        self.assertEqual(prepare('这项工作兼有多种用途吗？', db=self.db)['status'], 'no_evidence')


    def test_clause_subcategories_are_not_reduced_to_generic_clause(self):
        self.add_search_sections([
            ('s.1', '句法 §91 带区分连接词的并列复句', '区分连接词可以列举互相排斥的现象或交替出现。'),
            ('s.2', '句法 §111 表达对比-对别关系的无连接词复句', '分句声调有升降变化。'),
            ('s.3', '句法 §121 主句带若干递序从句的复句', '从属层级不等于言语中的出现顺序。'),
            ('s.4', '句法 §89 带联合连接词的并列复句', '联合连接词包括и。'),
            ('m.3', '词法 §201 连接词概述', '连接词连接句法单位。'),
            ('s.5', '句法 §109 无连接词复句概述', '无连接词复句可表达不同关系。')])
        for q, code in [('区分连接词都表示相互排斥吗？', 's.1'),
                        ('对比对别无连接词复句怎样读？', 's.2'),
                        ('递序从句怎样确定层级？', 's.3'),
                        ('联合连接词有什么用法？', 's.4')]:
            self.assertEqual(prepare(q, db=self.db)['sources'][0]['code'], code)
        self.assertEqual(question_terms('区分连接词'), ['区分连接词'])
        self.assertEqual(question_terms('递序从句'), ['递序从句'])
        self.assertEqual(prepare('区分这些安排的顺序怎样？', db=self.db)['status'], 'no_evidence')


    def test_measure_nouns_imperative_aspect_and_purpose_indicator_keep_scope(self):
        self.add_search_sections([
            ('m.3', '词法 §73 数词概述', '计量名词的间接格仍支配名词，不同于定量数词。'),
            ('m.4', '词法 §33 格的概述', '名词间接格表示多种关系。'),
            ('m.5', '词法 §139 第二人称命令式体的用法', '动作方式的要求与体选择有关。'),
            ('m.6', '词法 §138 第二人称命令式的构成和用法', '第二人称命令式有单复数。'),
            ('s.1', '句法 §101 带目的从句的主从复句', '否定目的时主句应有目的指示词。'),
            ('s.2', '句法 §120 主句带同等从句的复句', '主句否定时需要区分关系。')])
        for q, code in [('计量名词在间接格也和名词一致吗？', 'm.3'),
                        ('强调动作方式时第二人称命令式体怎样选？', 'm.5'),
                        ('否定目的时主句的目的指示词可省吗？', 's.1')]:
            self.assertEqual(prepare(q, db=self.db)['sources'][0]['code'], code)
        self.assertEqual(question_terms('计量名词的间接格'), ['计量名词', '间接格'])
        self.assertEqual(question_terms('第二人称命令式体'), ['第二人称命令式体'])
        self.assertEqual(prepare('计量这台设备的体积和用途', db=self.db)['status'], 'no_evidence')


    def test_number_reading_cues_do_not_turn_arbitrary_numbers_into_topics(self):
        self.add_search_sections([
            ('m.3', '词法 §74 定量数词的构成和读法', '数词三位一单元，内部0不读出。'),
            ('m.4', '词法 §73 数词概述', '数词表示数量。'),
            ('m.5', '另一节', 'ноль是一个俄语词面。')])
        for q in ('读2001时为什么不用ноль？', '读万和亿时俄语与汉语的分组一样吗？',
                  '765 323 125怎样读？', '数字中间的0应该读出吗？', '数词读法有什么特点？'):
            self.assertEqual(prepare(q, db=self.db)['sources'][0]['code'], 'm.3')
        for q in ('2001年发生了什么？', '价格2001元贵吗？', '53/85额度还有多少？',
                  '读2001年的小说要多久？', '读万卷书有什么心得？', '亿万年前地球怎样？'):
            self.assertEqual(prepare(q, db=self.db)['status'], 'no_evidence')
        self.assertNotIn('数词读法', question_terms('解释ноль'))
        self.assertNotIn('数词读法', question_terms('俄语2001年的小说'))


    def test_segmented_number_reading_keeps_bounded_question_scope(self):
        self.add_search_sections([
            ('m.74', '词法 §74 定量数词的构成和读法', '俄语数词以三位数为一单元，内部0不读出。'),
            ('m.75', '词法 §75 定量数词的变格', '数词在间接格中变化。')])
        for question in ('765323125怎么分段读？', '765 323 125怎样分组读？', '2001如何分段读？'):
            self.assertEqual(prepare(question, db=self.db)['sources'][0]['code'], 'm.74')
            self.assertIn('数词读法', question_terms(question))
        for question in ('2001年的小说怎么分段阅读？', '2001年的小说怎么分段读？', '2001年文件怎样分组读？', '价格765323125元怎样分期支付？', '765323125怎么分组统计？'):
            self.assertEqual(prepare(question, db=self.db)['status'], 'no_evidence')

    def test_case_functions_and_compound_surnames_keep_their_specific_source(self):
        self.add_search_sections([
            ('m.3', '词法 §35 第一格的意义和用法', '第一格可作主语，也可作表语和呼语。'),
            ('m.4', '词法 §50 复合名词变格问题', '俄国复合姓两部分都变格。'),
            ('s.1', '句法 §21 主语的表示法', '主语常用第一格。主语需要区分。'),
            ('s.2', '句法 §29 名词做主语时谓语的形式', '主语常用第一格。主语需要区分。'),
            ('s.3', '句法 §34 复合谓语', '主语常用第一格。主语需要区分。')])
        self.assertIn('m.3', [s['code'] for s in prepare('第一格在句中只能作主语吗？', db=self.db)['sources']])
        self.assertEqual(prepare('俄国复合姓两部分都变格吗？', db=self.db)['sources'][0]['code'], 'm.4')
        self.assertEqual(question_terms('复合姓怎么变格？'), ['复合姓', '变格'])
        self.assertEqual(prepare('复合这两个工作安排会怎样？', db=self.db)['status'], 'no_evidence')


    def test_time_preposition_and_strict_command_queries_keep_scope(self):
        self.add_search_sections([
            ('m.199', '词法 §199 表示时间意义的 до、пе́ред、к、до、по、по́сле、по', '前置词结构能表示在某事多少时间之前。'),
            ('m.198', '词法 §198 表示时间意义的 в 与 на', '时间结构说明时期。'),
            ('m.190', '词法 §190 原始前置词', '前置词接不同格，前置词有变体。'),
            ('m.191', '词法 §191 副词前置词', '前置词可以来源于副词。'),
            ('m.195', '词法 §195 来自口语的前置词的特殊用法', '前置词在口语中有变化。'),
            ('m.141', '词法 §141 其他形式表示第二人称命令式意义', '用动词不定式表示严格、断然的命令。'),
            ('m.104', '词法 §104 不定式的句法功能和用法', '不定式做不同成分。不定式可以表示行为。'),
            ('m.117', '词法 §117 不定式句中体的用法', '不定式体有不同意义。'),
            ('m.119', '词法 §119 与意愿动词连用时不定式体的用法', '不定式体的选择有条件。')])
        for q, code in [('某事多少时间之前用什么前置词结构？', 'm.199'),
                        ('严格断然的命令能用不定式吗？', 'm.141')]:
            self.assertIn(code, {s['code'] for s in prepare(q, db=self.db)['sources']})
        self.assertNotIn('时间前置词', question_terms('多少时间之前到达会场？'))
        for q in ('多少时间之前到达会场？', '严格执行这个任务怎样？'):
            self.assertEqual(prepare(q, db=self.db)['status'], 'no_evidence')

    def test_abbreviation_word_queries_preserve_declension_subject(self):
        self.add_search_sections([
            ('m.051', '词法 §51 关于复合缩写词的变格', '词首字母型复合缩写词按字母名读音时不变格，小写普通阳性词按阳性名词变化。'),
            ('m.041', '词法 §41 名词变格法概述', '名词变格有几种变格法，按辅音划分。'),
            ('m.044', '词法 §44 第三变格法', '阴性名词以软音符结尾，名词有单数和复数。'),
            ('m.045', '词法 §45 特殊变格的名词', '有阳性名词和中性名词需要特殊变格。'),
            ('m.024', '词法 §24 变格名词的性', '阳性名词按辅音区分，阴性和中性名词有不同词尾。')])
        for q in ('词首字母型缩写词以辅音结尾就变格吗？', '小写普通阳性名词的缩写词怎么变格？'):
            self.assertIn('m.051', {s['code'] for s in prepare(q, db=self.db)['sources']})
            self.assertIn('复合缩写词', question_terms(q))
        self.assertEqual(question_terms('音节型复合缩写词变格吗？'), ['复合缩写词', '变格'])
        for q in ('给文档缩写起个名字？', '任务缩写怎么写？'):
            self.assertEqual(prepare(q, db=self.db)['status'], 'no_evidence')

    def test_sentence_feature_queries_keep_specific_source_scope(self):
        self.add_search_sections([
            ('s.005', '句法 §5 句子及其基本特征', '述谓性不一定通过主语和谓语结合表现。称名句也有现在时意义。'),
            ('s.013', '句法 §13 单句的结构类别', '只有一种主要成分的句子叫单部句。'),
            ('s.029', '句法 §29 名词做主语时谓语的形式', '主语和谓语一致，名词做主语，动词做谓语。'),
            ('s.033', '句法 §33 动词谓语与主语不一致情形', '主语与谓语不一致，主语谓语位置需区分。'),
            ('s.034', '句法 §34 主语和谓语间的破折号', '主语和谓语需要破折号，名词或动词形式有关。'),
            ('m.052', '词法 §52 由形容词、形动词转化来的名词', '名词和动词不同，名词化条件各异。'),
            ('m.102', '词法 §102 动词概述', '动词有时间范畴，名词和动词不同。')])
        for q, required in [('述谓性一定要主语和谓语结合吗？', 's.005'),
                            ('名词称名句没有动词就没有时间意义吗？', 's.005'),
                            ('仅有一种主要成分的句子属于哪类？', 's.013')]:
            self.assertIn(required, {s['code'] for s in prepare(q, db=self.db)['sources']})
        self.assertIn('单部句', question_terms('句子只有一种主要成分叫什么？'))
        self.assertNotIn('单部句', question_terms('只有一种主要成分的洗面奶叫什么？'))
        self.assertEqual(prepare('只有一种主要成分的洗面奶叫什么？', db=self.db)['status'], 'no_evidence')

    def test_quotation_overview_keeps_source_chapter_scope(self):
        self.add_search_sections([
            ('s.122', '句法 §122 概述', '直接引语放在引号中。直接引语原封不动引用原话，在语法和结构上独立。'),
            ('s.125', '句法 §125 非纯直接引语', '非纯直接引语不放引号，是作者改造的话。直接引语和非纯直接引语有差别。'),
            ('s.095', '句法 §95 带限定从句的主从复句', '从句解释主句。例句可能带引号。'),
            ('s.096', '句法 §96 带行为方法从句的主从复句', '从句解释主句。例句可能带引号。'),
            ('s.099', '句法 §99 概述', '这里描述另一类结构。')])
        packet = prepare('直接引语和非纯直接引语都必须有引号，并作为作者语的从句吗？', db=self.db)
        self.assertLessEqual({'s.122', 's.125'}, {s['code'] for s in packet['sources']})
        self.assertEqual(next(s for s in packet['sources'] if s['code'] == 's.122')['title'], '句法 §122 概述')
        self.assertEqual(prepare('非纯直接引语如何使用？', db=self.db)['sources'][0]['code'], 's.125')
        self.assertNotIn('s.099', {s['code'] for s in packet['sources']})

    def test_compared_forms_keep_aspect_usage_and_negation_sources(self):
        self.add_search_sections([
            ('m.3', '词法 §117 不定式句中体的用法', '否定不定式中完成体与未完成体意义不同。'),
            ('m.4', '词法 §132 “не＋过去时”结构中体的用法', '否定过去时中完成体与未完成体意义不同。'),
            ('m.5', '词法 §139 第二人称命令式体的用法', '否定与邀请时要分清完成体和未完成体。'),
            ('m.6', '词法 §138 第二人称命令式的构成和用法', '第二人称命令式有复数形式。不定式、完成体、未完成体与复数形式。'),
            ('m.7', '词法 §140 第二人称命令式的转义用法', '不定式、完成体、未完成体。'),
            ('m.8', '词法 §141 其他形式表示第二人称命令式意义', '不定式、完成体、未完成体。'),
            ('m.9', '词法 §100 否定代词', '否定不定式与过去时形式也出现在这段说明。')])
        for question, required in [
            ('否定不定式和否定过去时中的未完成体都表示禁止吗？', {'m.3', 'm.4'}),
            ('否定不定式与第二人称命令式怎样选体？', {'m.3', 'm.5'}),
            ('第二人称命令式复数表示尊敬吗，体的用法怎样？', {'m.5', 'm.6'})]:
            self.assertLessEqual(required, {s['code'] for s in prepare(question, db=self.db)['sources']})
        self.assertEqual(prepare('第二人称命令式怎样构成？', db=self.db)['sources'][0]['code'], 'm.6')
        self.assertEqual(prepare('具体工作怎样安排？', db=self.db)['status'], 'no_evidence')


if __name__ == '__main__':
    unittest.main()
