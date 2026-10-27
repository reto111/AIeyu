import sys,json,sqlite3,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import grammar_editorial_rag as rag
from export_grammar_research_snapshot import verify_package as verify_v1
db=Path(sys.argv[1]) if len(sys.argv)>1 else rag.DEFAULT_DB
manifest=rag.verify_package(db.parent)
plain=lambda s:__import__('unicodedata').normalize('NFC',s).replace('\u0301','').replace('*','')
with sqlite3.connect(f'{db.resolve().as_uri()}?mode=ro',uri=True) as c:
    c.row_factory=sqlite3.Row
    ready=[r[0] for r in c.execute("SELECT code FROM chunks WHERE status='ready' ORDER BY code")]
    snapshots={code:rag.snapshot(c,code) for code in ready}
    assert len(snapshots)==368
    for code,s in snapshots.items():
        assert len(s['body'])>0
    # Broad replacements must not damage lawful neighbouring examples.
    assert 'Российская Федерация' in plain(snapshots['morphology.027']['body'])
    assert 'ошибиться' in plain(snapshots['morphology.107']['body'])
    assert 'ошибисься' not in plain(snapshots['morphology.107']['body'])
    assert plain(snapshots['morphology.179']['body']).startswith('限定副词')
    assert '1. 性质副词' in plain(snapshots['morphology.179']['body'])
    assert '1）只第三人称分性' in snapshots['morphology.092']['body']
    assert 'более последние произведения' not in plain(snapshots['morphology.069']['body'])
    assert 'друг друга на ошибку' in plain(snapshots['morphology.200']['body'])
    assert 'берёг（-ть）' in plain(snapshots['morphology.165']['body'])
    assert 'Мне нужно ваши советы' in plain(snapshots['syntax.035']['body'])
    assert 'пока только' in plain(snapshots['syntax.100']['body'])
    assert '谓语时体随一次／重复及可能性语义选择' in snapshots['syntax.103']['body']
    assert '不同从句可分别与主句中的不同词语发生关系' in snapshots['syntax.119']['body']
    assert 'что но испугался' not in plain(snapshots['syntax.119']['body'])
    for code in ('morphology.103','morphology.108'):
        assert '-кть、-гть（-кти/-гти）' in snapshots[code]['body']
    body=plain(snapshots['syntax.129']['body'])
    assert 'Эта позиция Франции' not in body and 'что/я' not in body
    assert 'Этот ученик' in body
    assert c.execute('SELECT COUNT(*) FROM editorial_issues').fetchone()[0]==173
    assert sum(bool(json.loads(r[0])['human_question']) for r in c.execute('SELECT resolution_json FROM editorial_issues'))==0
    # Original pages/batches/source rows must remain byte-for-byte the same.
    old=sqlite3.connect(ROOT/'data/processed/grammar_reference/grammar_reference.sqlite')
    old.row_factory=sqlite3.Row
    for original_row in old.execute('SELECT * FROM chunks'):
        archived=json.loads(c.execute('SELECT row_json FROM editorial_raw_sections WHERE code=?',(original_row['code'],)).fetchone()[0])
        assert archived==dict(original_row),original_row['code']
    for table in ('source','pages','batches','page_revisions'):
        assert sorted(tuple(r) for r in c.execute(f'SELECT * FROM {table}'))==sorted(tuple(r) for r in old.execute(f'SELECT * FROM {table}')),table
    for code,body_text in old.execute("SELECT code,body FROM chunks WHERE status='ready'"):
        assert c.execute('SELECT body FROM chunks WHERE code=?',(code,)).fetchone()[0]==body_text
    old.close()
excluded=rag.prepare('汇总变格表',db=db,code='morphology.declension_tables')
assert excluded['status']=='no_evidence' and not excluded['sources']
packet=rag.prepare('提位复指',db=db,code='syntax.129')
assert packet['status']=='prepared'
packaged=json.loads((ROOT/'data/processed/grammar_reference/reviews/editorial_packaged_probe_20261018_001.json').read_text(encoding='utf-8'))
assert packet['sources']==packaged['sources'] and packet['manifest_sha256']==packaged['manifest_sha256']
assert 'объяснила' not in json.dumps(packet,ensure_ascii=False) and 'что/я' not in json.dumps(packet,ensure_ascii=False)
quote=rag.strip_search_formatting(packet['sources'][0]['body'])[:24]
response={'status':'answered','claims':[{'text_zh':'机械引用验证样例','citations':[{'source_id':'G1','quote':quote}]}]}
assert rag.validate_response(packet,response,db=db)['valid']
bad=json.loads(json.dumps(packet));bad['sources'][0]['body']+='tampered'
try:rag.validate_response(bad,response,db=db)
except ValueError:pass
else:raise AssertionError('Tampered evidence accepted')
assert rag.prepare('星际飞船量子咖啡机维修',db=db)['status']=='no_evidence'
questions=['俄语形容词怎么构成比较级','俄语动词命令式有哪些不规则形式','俄语时间从句的连接词有哪些','俄语主从复句怎样表示条件','俄语名词如何变格']
retrieval=[{'question':q,'status':(p:=rag.prepare(q,db=db))['status'],'codes':[s['code'] for s in p['sources']],'context_characters':p['context_characters']} for q in questions]
assert all(p['status']=='prepared' for p in retrieval)
old_hash=hashlib.sha256((ROOT/'data/processed/grammar_reference/grammar_reference.sqlite').read_bytes()).hexdigest()
assert old_hash=='38f778ec83a741c0ea90742c591d1d59567a3ea8502c9ee0c1d31ecd287d6af8'
v1=verify_v1(ROOT/'data/processed/grammar_reference/research_exports/research232_v1_20261016')
result={'package':str(db.parent),'verified_files':len(manifest['files']),'all_ready_sections_replayed':len(snapshots),'original_ready_232_unchanged':True,'raw_evidence_tables_unchanged':True,'original_database_sha256':old_hash,'excluded_whole_sections':1,'excluded_examples':2,'pending_human_decisions':0,'tamper_rejected':True,'v1_verification':v1,'smoke_retrieval':retrieval,'limitations':'工程、范围与机械引用检查；不是语义正确率、独立专家盲评或生成实验。'}
out=ROOT/'data/processed/grammar_reference/reviews/editorial_verification_20261018_001.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
