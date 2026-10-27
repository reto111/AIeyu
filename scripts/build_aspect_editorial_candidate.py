"""Build a separate, explicitly provisional aspectology research layer.

All original tables stay byte-for-byte equivalent at row level. Candidate text
is stored in a new table; existing grammar/aspect search cannot expose it.
"""
from __future__ import annotations
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'data/processed/aspect_reference'
DEFAULT_DB=WORK/'aspect_reference.sqlite'
DEFAULT_PLAN=WORK/'reviews/editorial_plan_20261023_004.json'
DEFAULT_REVIEW=WORK/'reviews/theory_issue_review_20261023_004.json'
DEFAULT_OUTPUT=WORK/'research_exports/aspect_editorial_candidate_20261023_002'

def text_sha(value):return hashlib.sha256(value.encode('utf8')).hexdigest()
def file_sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_json(path):return json.loads(Path(path).read_text('utf8'))
def write_json(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')
def open_readonly(path):
    c=sqlite3.connect(f'{Path(path).resolve().as_uri()}?mode=ro',uri=True);c.row_factory=sqlite3.Row
    return c

def replay(raw,edits):
    """Offsets refer to raw, never to a partially rewritten string."""
    ordered=sorted(edits,key=lambda e:e['start'])
    end=0
    for e in ordered:
        k=e['start'];old=e['old']
        if not isinstance(k,int) or k<end or not old or raw[k:k+len(old)]!=old:
            raise ValueError('Conflicting, overlapping or invalid editorial span')
        if not isinstance(e['new'],str):raise ValueError('Invalid new text')
        end=k+len(old)
    result=raw
    for e in reversed(ordered):result=result[:e['start']]+e['new']+result[e['start']+len(e['old']):]
    return result

def preview(db=DEFAULT_DB,plan_path=DEFAULT_PLAN,review_path=DEFAULT_REVIEW):
    db=Path(db);plan=read_json(plan_path);review=read_json(review_path)
    if file_sha(db)!=plan['database_sha256'] or file_sha(review_path)!=plan['review']['sha256']:
        raise ValueError('Source database or issue review fingerprint changed')
    by_code={u['code']:u for u in review['units']}
    proposals=plan['proposals'];known={z['issue_id']:z for u in review['units']for z in u['issues']}
    if len({p['issue_id']for p in proposals})!=len(proposals):raise ValueError('Duplicate proposal')
    expected={k for k,z in known.items()if z['disposition']=='editorial_proposal'}
    if {p['issue_id']for p in proposals if p['issue_id'].startswith('AS-TI-')}!=expected:
        raise ValueError('Editorial proposal coverage mismatch')
    sections=[]
    with closing(open_readonly(db)) as c:
        c.execute('BEGIN')
        if c.execute('select sha256 from source where id=1').fetchone()[0]!=plan['source_sha256']:
            raise ValueError('Foreign source')
        for row in c.execute("select * from chunks where code like 'aspect.ch%' order by code"):
            raw=dict(row);code=raw['code'];u=by_code.get(code)
            if u and (text_sha(raw['body'])!=u['source_body_sha256'] or raw['body']!=u['source_body']):
                raise ValueError('Stale source unit')
            selected=[p for p in proposals if p['code']==code]
            edits=[]
            for p in selected:
                if p['source_body_sha256']!=text_sha(raw['body']):raise ValueError('Stale proposal')
                edits.extend(dict(**e,issue_id=p['issue_id'])for e in p['edits'])
            body=replay(raw['body'],edits)
            decisions=u['issues']if u else[]
            if raw['status']=='ready' and not decisions:
                state='original_source_ready'
                if body!=raw['body']:raise ValueError('Unexpected edit to a ready source unit')
            elif decisions and all(z['disposition']in ('editorial_proposal','retain_do_not_normalize')for z in decisions):
                state='model_editorial_candidate'
            else:state='withheld'
            # Bind source offsets to the exact page fragments, including joins.
            offset=0;page_spans=[];pins=[]
            for number in json.loads(raw['pdf_pages']):
                pr=c.execute('select * from pages where pdf_page=?',(number,)).fetchone()
                if text_sha(pr['review_json'])!=pr['review_sha256']:raise ValueError('Invalid page evidence')
                data=json.loads(pr['review_json']);hits=[f for f in data['fragments']if f['code']==code]
                if len(hits)!=1:raise ValueError('Invalid fragment binding')
                fragment=hits[0];part=fragment['body']
                if raw['body'][offset:offset+len(part)]!=part:raise ValueError('Fragment composition mismatch')
                page_spans.append((offset,offset+len(part),number));offset+=len(part)
                pins.append(dict(pdf_page=number,review_sha256=pr['review_sha256'],render_sha256=data['render_sha256']))
            if offset!=len(raw['body']):raise ValueError('Fragment length mismatch')
            for e in edits:e['pdf_pages']=[p for lo,hi,p in page_spans if e['start']<hi and e['start']+len(e['old'])>lo]
            sections.append(dict(code=code,title=raw['title'],state=state,source_status=raw['status'],source_body_sha256=text_sha(raw['body']),body_sha256=text_sha(body),body=body,pdf_pages=json.loads(raw['pdf_pages']),printed_pages=json.loads(raw['printed_pages']),page_evidence=pins,decisions=decisions,edits=edits,review_issue_ids=[p['issue_id']for p in selected],content_kind='editorial_candidate'if edits else'original_transcription',source_notes=json.loads(raw['notes'])))
    if len(sections)!=100:raise ValueError('Expected exactly 100 theory units')
    return dict(sections=sections,counts=dict(Counter(s['state']for s in sections)),proposal_count=len(proposals),edit_count=sum(len(s['edits'])for s in sections),source_db_sha256=file_sha(db),plan_sha256=file_sha(plan_path),review_sha256=file_sha(review_path))

def build(output=DEFAULT_OUTPUT,db=DEFAULT_DB,plan_path=DEFAULT_PLAN,review_path=DEFAULT_REVIEW):
    check=preview(db,plan_path,review_path);output=Path(output).resolve()
    review=read_json(review_path)
    remaining=Counter(x['disposition']for u in review['units']for x in u['issues'])
    original_proposals=sum(x['disposition']=='editorial_proposal'for u in review['units']for x in u['issues'])
    original_issues=sum(len(u['issues'])for u in review['units'])
    extra_proposals=sum(not p['issue_id'].startswith('AS-TI-')for p in read_json(plan_path)['proposals'])
    if output.exists():raise FileExistsError('Candidate directory is immutable; choose a new version')
    if not output.is_relative_to(WORK.resolve()):raise ValueError('Output must stay within aspect research workspace')
    output.mkdir(parents=True)
    target=output/'aspect_reference.sqlite'
    with closing(open_readonly(db)) as src,closing(sqlite3.connect(target)) as dst:src.backup(dst)
    with closing(sqlite3.connect(target)) as c:
        c.executescript('''
        CREATE TABLE aspect_candidate_sections(code TEXT PRIMARY KEY,title TEXT NOT NULL,body TEXT NOT NULL,state TEXT NOT NULL,metadata_json TEXT NOT NULL);
        CREATE TABLE aspect_candidate_provenance(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        ''')
        with c:
            for s in check['sections']:
                meta={k:v for k,v in s.items()if k not in ('title','body','state')}
                c.execute('insert into aspect_candidate_sections values(?,?,?,?,?)',(s['code'],s['title'],s['body'],s['state'],json.dumps(meta,ensure_ascii=False)))
            for k in ('source_db_sha256','plan_sha256','review_sha256'):c.execute('insert into aspect_candidate_provenance values(?,?)',(k,check[k]))
        if c.execute('pragma integrity_check').fetchone()[0]!='ok' or c.execute('pragma foreign_key_check').fetchall():raise ValueError('Candidate database integrity failure')
    # A compact export contains every theory unit with its actual state.
    (output/'theory_units.jsonl').write_text(''.join(json.dumps(s,ensure_ascii=False)+'\n'for s in check['sections']),'utf8')
    external_manifest=WORK/review['external_manifest']['path']
    if file_sha(external_manifest)!=review['external_manifest']['sha256']:raise ValueError('External manifest binding mismatch')
    for path in (Path(plan_path),Path(review_path),WORK/'reviews/exercise_semantic_review_20261021_002.json',external_manifest):
        shutil.copy2(path,output/path.name)
    shutil.copy2(Path(__file__),output/Path(__file__).name)
    for name in ('aspect_candidate_rag.py',):shutil.copy2(ROOT/'scripts'/name,output/name)
    readme=f'''# 现代俄语体学：编校研究候选层

这是本地可复查候选，不是正式论文研究版或专家审定版。原印转录数据库及其他知识库没有改动。

- 理论100节：{check['counts']}。
- {check['proposal_count']}条编校提案、{check['edit_count']}处精确修改；包括原{original_issues}条说明中的{original_proposals}条及{extra_proposals}条明确追加项。部分提案引用同一作者后续论文或据原论文推导，不能称为独立专家认证。
- 练习28组262编号父题的逐项模型复核另附，仍不进入理论检索或学生池。不是正确率测量。
- {remaining['needs_primary_source']}条待原著、{remaining['theoretical_or_contextual_undetermined']}条理论/语境未决与{remaining['illegible_source']}条墨迹不可辨仍在其所属节隔离；一条说明可有多个问题。
- 原始SQLite所有既有表逐行保留；新表aspect_candidate_sections存编校文字。原有检索仍只见原40 ready。
- 默认检索只取original_source_ready；显式--include-candidates才纳入模型编校候选。withheld永不返回。
- 编校文字必须称“编校候选表述”，不得当作原书逐字原句；印刷页须按保存的printed_pages引用。
- 外部全文缓存不随候选包分发；附{len(read_json(external_manifest)['sources'])}条来源的链接、指纹、核查位置与证据边界。

运行（仅本地，无生成API）：

    python aspect_candidate_rag.py prepare "未完成体为什么能表示行为已经达到结果？" --db aspect_reference.sqlite --include-candidates
    python aspect_candidate_rag.py verify --db aspect_reference.sqlite

可选--retriever passage使用本地中文字符对与俄文词的段落排序、再与原词项排序融合；默认仍为lexical。此实验模式同样只返回完整且已允许的节，不能绕过隔离或扩大上下文预算。已知开发题上的改善不等于独立召回率或语义正确率。

检索命中与连续引句校验只验证工程约束，不证明回答语义。尚未进行独立专家盲评或生成答案实验。
'''
    (output/'README.md').write_text(readme,'utf8')
    manifest=dict(schema_version=1,created_at=datetime.now(timezone.utc).isoformat(),edition=output.name,provisional=True,counts=check['counts'],source_db_sha256=check['source_db_sha256'],plan_sha256=check['plan_sha256'],review_sha256=check['review_sha256'],proposal_count=check['proposal_count'],edit_count=check['edit_count'],files={p.relative_to(output).as_posix():file_sha(p)for p in output.rglob('*')if p.is_file()})
    write_json(output/'manifest.json',manifest)
    if file_sha(db)!=check['source_db_sha256']:raise ValueError('Source database changed during build')
    return dict(output=str(output),files=len(manifest['files']),counts=check['counts'],edits=check['edit_count'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--output',type=Path,default=DEFAULT_OUTPUT);p.add_argument('--db',type=Path,default=DEFAULT_DB);p.add_argument('--plan',type=Path,default=DEFAULT_PLAN);p.add_argument('--review',type=Path,default=DEFAULT_REVIEW);a=p.parse_args()
    if a.build:result=build(a.output,a.db,a.plan,a.review)
    else:result={k:v for k,v in preview(a.db,a.plan,a.review).items()if k!='sections'}
    print(json.dumps(result,ensure_ascii=False,indent=2))
