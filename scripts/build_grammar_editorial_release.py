"""Create an isolated editorial research edition from pinned review evidence.

Raw transcription pages and the source360 database are never rewritten.
"""
from __future__ import annotations
import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'data/processed/grammar_reference'
RELEASE = WORK / 'research_exports/research368_editorial_v2_20261018_003'
EXCLUDED = 'morphology.declension_tables'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def thash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

USER_DECISIONS = {
    'I025': '删除该用例，不替换为另一个比较级例句。',
    'I044': '按省略谓语理解，保留原文，不补造谓语。',
    'I053': '两处统一写历史来源 -кть、-гть（-кти/-гти），保留两种记法。',
    'I070': 'берёг(-ть)完整保留；生产→生长的独立字误按编校处理。',
    'I092': '补入缺少的 друга，其他句子结构不按此前模型候选另行重写。',
    'I104': '研究版继续隔离整附表，检索使用已核对的分节变格表。',
    'I122': '保留 Мне ну́жно ва́ши сове́ты，不改成 нужны。',
    'I151': '保留 пока́ то́лько，不加逗号或 как；用户输入I15按上下文定位I151。',
    'I155': '表述为时体随一次／重复及可能性语义选择，不简单改一般用完成体。',
    'I166': '保留原例，第3点改写为不同从句与主句中不同词语发生关系。',
    'I167': '随I166处理结构问题；图中но→он按已核实的字序错误修正。',
    'I172': '保留原转录，研究检索排除这两个例句，不猜改 объяснима 或斜线。',
}

def replay(raw, changes):
    bodies = {k:r['body'] for k,r in raw.items()}
    for group in changes:
        body = bodies[group['code']]
        for e in reversed(group['edits']):
            start = e['start']
            if body[start:start+len(e['old'])] != e['old']:
                raise ValueError(f"Old value conflict: {group['issue_id']}/{group['code']}")
            body = body[:start]+e['new']+body[start+len(e['old']):]
        bodies[group['code']] = body
    return bodies

def build(output=RELEASE):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError('Editorial edition already exists; do not overwrite it')
    review_path = WORK/'reviews/issue_verification_results_20261017_001.json'
    draft_path = WORK/'reviews/editorial_draft_20261017_001.json'
    review = json.loads(review_path.read_text(encoding='utf-8'))
    draft = json.loads(draft_path.read_text(encoding='utf-8'))
    source_db = WORK/'grammar_reference.sqlite'
    if sha(source_db) != review['database_sha256'] or sha(review_path) != draft['input_review_sha256']:
        raise ValueError('Pinned source or review changed')
    assert not draft['conflicts'] and len(draft['handled_issue_ids']) == 173
    assert set(USER_DECISIONS) == {i['issue_id'] for i in review['items'] if i['review_status']=='human'}
    with closing(sqlite3.connect(f'{source_db.as_uri()}?mode=ro',uri=True)) as source:
        source.row_factory = sqlite3.Row
        source.execute('BEGIN')
        raw = {r['code']:dict(r) for r in source.execute('SELECT * FROM chunks')}
        source_info = dict(source.execute('SELECT * FROM source').fetchone())
        if sha(source_info['path']) != source_info['sha256']:
            raise ValueError('Original PDF fingerprint mismatch')
        bodies = replay(raw, draft['changes'])
        assert bodies == draft['bodies']
        reviewed_codes = {i['code'] for i in review['items']}
        assert {k for k in bodies if bodies[k]!=raw[k]['body']} <= reviewed_codes
        # Build into a new directory. The first SQLite backup is the consistency backup;
        # it remains in the release as the immutable transcription evidence.
        output.mkdir(parents=True)
        with closing(sqlite3.connect(output/'original_source360.sqlite')) as backup:
            source.backup(backup)
    shutil.copyfile(output/'original_source360.sqlite', output/'grammar_reference.sqlite')
    evidence=output/'evidence';evidence.mkdir()
    shutil.copyfile(review_path,evidence/review_path.name)
    shutil.copyfile(draft_path,evidence/draft_path.name)
    user_record={'recorded_on':'2026-10-18','source':'本聊天用户逐项裁定，授权沿用原会话','id_interpretation':{'I15':'I151'},'decisions':USER_DECISIONS,'inferred_link':'I167的结构问题与I166同属一节，按I166裁定处理；но→он沿用已核实字序修正。'}
    write_json(evidence/'user_adjudications.json',user_record)
    changes_by_code={code:[g for g in draft['changes'] if g['code']==code] for code in raw}
    issues_by_code={code:[i for i in review['items'] if i['code']==code] for code in raw}
    normalize=lambda s:__import__('unicodedata').normalize('NFD',s.lower().replace('*','').replace('`','')).replace('\u0301','')
    with closing(sqlite3.connect(output/'grammar_reference.sqlite')) as conn:
        conn.execute('BEGIN IMMEDIATE')
        conn.execute('CREATE TABLE editorial_raw_sections (code TEXT PRIMARY KEY, row_json TEXT NOT NULL)')
        conn.execute('CREATE TABLE editorial_sections (code TEXT PRIMARY KEY, raw_body_sha256 TEXT NOT NULL, body_sha256 TEXT NOT NULL, metadata_json TEXT NOT NULL)')
        conn.execute('CREATE TABLE editorial_issues (issue_id TEXT PRIMARY KEY, code TEXT NOT NULL, resolution_json TEXT NOT NULL)')
        conn.execute('CREATE TABLE editorial_version (id INTEGER PRIMARY KEY CHECK(id=1), metadata_json TEXT NOT NULL)')
        for code,row in raw.items():
            conn.execute('INSERT INTO editorial_raw_sections VALUES (?,?)',(code,json.dumps(row,ensure_ascii=False)))
            if code not in reviewed_codes:continue
            excluded=code==EXCLUDED
            metadata={'edition':'editorial_v2','review_kind':'model_and_source_review_with_user_adjudications','original_status':row['status'],'original_notes':json.loads(row['notes']),'issue_ids':[i['issue_id'] for i in issues_by_code[code]],'user_adjudications':{i:USER_DECISIONS[i] for i in USER_DECISIONS if any(x['issue_id']==i for x in issues_by_code[code])},'changes':changes_by_code[code],'excluded_examples':[e for e in draft['excluded_examples'] if e['code']==code],'label':'编校研究版；修订文字不冒充原书逐字原文；无独立专家正确率结论'}
            conn.execute('INSERT INTO editorial_sections VALUES (?,?,?,?)',(code,thash(row['body']),thash(bodies[code]),json.dumps(metadata,ensure_ascii=False)))
            notes=['按用户裁定，研究版排除整附表；原表结构疑点未消除。'] if excluded else []
            conn.execute('UPDATE chunks SET body=?,status=?,notes=?,search_text=? WHERE code=?',(bodies[code],'unresolved' if excluded else 'ready',json.dumps(notes,ensure_ascii=False),normalize(row['title']+'\n'+bodies[code]),code))
        for issue in review['items']:
            item=dict(issue)
            item['effective_decision']=USER_DECISIONS.get(item['issue_id'],item['decision'])
            item['effective_status']='excluded_by_user' if item['issue_id'] in ('I104','I172') else 'user_adjudicated' if item['issue_id'] in USER_DECISIONS else 'editorial_applied' if item['review_status']=='correct' else 'retained_after_review'
            item['applied_to_original_database']=False
            item['applied_to_editorial_edition']=True
            item['human_question']=None
            conn.execute('INSERT INTO editorial_issues VALUES (?,?,?)',(item['issue_id'],item['code'],json.dumps(item,ensure_ascii=False)))
        version={'edition':output.name,'original_database_sha256':sha(source_db),'review_sha256':sha(review_path),'draft_sha256':sha(draft_path),'user_adjudications_sha256':sha(evidence/'user_adjudications.json'),'total_sections':369,'ready_sections':368,'excluded_sections':[EXCLUDED],'excluded_example_count':2,'pending_human_decisions':0,'limitation':'ready表示本研究版纳入检索，不表示原书无误或全部经专家复审。'}
        conn.execute('INSERT INTO editorial_version VALUES (1,?)',(json.dumps(version,ensure_ascii=False),))
        conn.commit()
        assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert dict(conn.execute('SELECT status,COUNT(*) FROM chunks GROUP BY status'))=={'ready':368,'unresolved':1}
        conn.row_factory=sqlite3.Row
        rows=[dict(r) for r in conn.execute('SELECT * FROM chunks ORDER BY code')]
    for name,selected in [('sections.jsonl',rows),('retrieval_ready.jsonl',[r for r in rows if r['status']=='ready']),('excluded_sections.jsonl',[r for r in rows if r['status']!='ready'])]:
        (output/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in selected),encoding='utf-8')
    code_dir=output/'source_code';code_dir.mkdir()
    # Copy the established v1 dependencies without modifying that frozen package.
    previous=WORK/'research_exports/research232_v1_20261016/source_code'
    for path in previous.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            target=code_dir/path.relative_to(previous);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    for name in ('build_grammar_editorial_release.py','grammar_editorial_rag.py'):
        shutil.copyfile(ROOT/'scripts'/name,code_dir/name)
    (output/'README.md').write_text('# 俄语语法编校研究版 v2\n\n368节可检索，整附表1节隔离，另排除提位节2例。173条原疑点均有处理记录，待用户裁定0条；按范围排除不等于修复了原书。\n\n本版含207处文本编辑，原值与新值在evidence及SQLite编校表中保留。原始source360和232节v1未改。pages表仍为原图转录证据，修订正文另由editorial_sections绑定，不能用旧grammar_rag入口把修订句冒充原书逐字引文。\n\n检索：`.venv/Scripts/python.exe -X utf8 scripts/grammar_editorial_rag.py prepare "问题" --db "本目录/grammar_reference.sqlite"`。精确节号检查可用`--code syntax.129`。此入口不调用生成模型。\n\n编校包括模型判断、外部资料及用户裁定，不是独立专家语义盲评。v1历史40题指标不直接当成本版指标，生成回答实验未完成。\n',encoding='utf-8')
    manifest={'schema_version':1,'edition':version,'files':{p.relative_to(output).as_posix():sha(p) for p in output.rglob('*') if p.is_file()},'built_at_utc':datetime.now(timezone.utc).isoformat()}
    write_json(output/'manifest.json',manifest)
    assert sha(source_db)==review['database_sha256']
    return {'directory':str(output),'ready':368,'excluded':1,'edits':sum(len(g['edits']) for g in draft['changes']),'files':len(manifest['files'])}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=RELEASE)
    args=parser.parse_args();print(json.dumps(build(args.output),ensure_ascii=False,indent=2))
