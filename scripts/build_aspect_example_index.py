"""Index numbered anchor paragraphs, preserving exact original/candidate spans.

This is a textbook illustration index, not a natural-language frequency corpus.
All operations are local. Existing source and candidate databases are read only.
"""
from __future__ import annotations
import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime,timezone
import hashlib,json,re,shutil,sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'data/processed/aspect_reference'
DEFAULT_CANDIDATE=WORK/'research_exports/aspect_editorial_candidate_20261023_002'
DEFAULT_OUTPUT=WORK/'research_exports/aspect_numbered_examples_20261023_002'
ANCHOR=re.compile(r'(?m)^[ \t]*[（(](\d{1,3})[)）]')

def tsh(text):return hashlib.sha256(text.encode('utf8')).hexdigest()
def fsh(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text('utf8'))
def write(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
def connect(path):
    c=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
    return c

def verify_candidate(directory):
    directory=Path(directory).resolve();manifest=read(directory/'manifest.json')
    for rel,pin in manifest['files'].items():
        p=(directory/rel).resolve()
        if not p.is_relative_to(directory)or fsh(p)!=pin:raise ValueError('Candidate file mismatch')
    return manifest

def replay_span(body,start,end,edits):
    """Apply only edits fully contained in a raw half-open interval."""
    if not 0<=start<=end<=len(body):raise ValueError('Invalid source interval')
    selected=[]
    for edit in edits:
        lo=edit['start'];hi=lo+len(edit['old'])
        if not edit['old']or body[lo:hi]!=edit['old']:raise ValueError('Stale editorial edit')
        if lo<end and hi>start:
            if not start<=lo<hi<=end:raise ValueError('Editorial edit crosses anchor boundary')
            selected.append(edit)
    text=body[start:end];boundary=end
    for edit in sorted(selected,key=lambda e:e['start'],reverse=True):
        lo=edit['start'];hi=lo+len(edit['old'])
        if hi>boundary:raise ValueError('Overlapping editorial edits')
        text=text[:lo-start]+edit['new']+text[hi-start:];boundary=lo
    return text,selected

def anchor_intervals(body):
    """Numbered first paragraph only; following dialogue is not guessed."""
    for match in ANCHOR.finditer(body):
        end=body.find('\n\n',match.end())
        yield int(match.group(1)),match.start(),len(body)if end<0 else end

def bindings(c,unit):
    raw=unit['body'];offset=0;spans=[]
    for number in json.loads(unit['pdf_pages']):
        page=c.execute('select * from pages where pdf_page=?',(number,)).fetchone()
        if tsh(page['review_json'])!=page['review_sha256']:raise ValueError('Page review mismatch')
        data=json.loads(page['review_json']);parts=[x for x in data['fragments']if x['code']==unit['code']]
        if len(parts)!=1:raise ValueError('Ambiguous page fragment')
        text=parts[0]['body']
        if raw[offset:offset+len(text)]!=text:raise ValueError('Raw fragment composition mismatch')
        spans.append(dict(start=offset,end=offset+len(text),pdf_page=number,printed_page=page['printed_page'],review_sha256=page['review_sha256'],render_sha256=data['render_sha256']))
        offset+=len(text)
    if offset!=len(raw):raise ValueError('Incomplete raw unit')
    return spans

def pages_for(spans,start,end):
    return [{k:v for k,v in p.items()if k not in ('start','end')}for p in spans if start<p['end']and end>p['start']]

def materialize(candidate):
    candidate=Path(candidate).resolve();manifest=verify_candidate(candidate);rows=[];units=[];warnings=[]
    with closing(connect(candidate/'aspect_reference.sqlite'))as c:
        for section in c.execute('select * from aspect_candidate_sections order by code').fetchall():
            unit=c.execute('select * from chunks where code=?',(section['code'],)).fetchone()
            meta=json.loads(section['metadata_json']);raw=unit['body'];edits=meta['edits']
            if tsh(raw)!=meta['source_body_sha256']or tsh(section['body'])!=meta['body_sha256']:raise ValueError('Unit fingerprint mismatch')
            rebuilt,_=replay_span(raw,0,len(raw),edits)
            if rebuilt!=section['body']:raise ValueError('Candidate replay mismatch')
            spans=bindings(c,unit);occ=Counter();count=0
            cautions=[dict(issue_id=x['issue_id'],note=x['external_quote_adaptation_note'])for x in meta['decisions']if x.get('external_quote_adaptation_note')]
            for number,start,end in anchor_intervals(raw):
                occ[number]+=1;count+=1;text=raw[start:end];edited,selected=replay_span(raw,start,end,edits)
                # Context follows paragraph boundaries, so no edit is sliced in half.
                before=raw.rfind('\n\n',0,max(0,start-1));context_start=0 if before<0 else before+2
                cursor=end
                for _ in range(2):
                    next_end=raw.find('\n\n',min(len(raw),cursor+2))
                    cursor=len(raw)if next_end<0 else next_end
                context_end=cursor
                context,context_edits=replay_span(raw,context_start,context_end,edits)
                row=dict(example_id=f"{unit['code']}.example.{number:03}.{occ[number]:02}",record_kind='numbered_example_anchor_paragraph',source_unit=unit['code'],unit_title=unit['title'],chapter=int(re.search(r'\.ch(\d+)',unit['code']).group(1)),book_number=number,occurrence_in_unit=occ[number],state=section['state'],eligible_original=section['state']=='original_source_ready',eligible_with_candidates=section['state']in ('original_source_ready','model_editorial_candidate'),source_start=start,source_end=end,source_text=text,source_text_sha256=tsh(text),candidate_text=edited,candidate_text_sha256=tsh(edited),source_unit_sha256=meta['source_body_sha256'],candidate_unit_sha256=meta['body_sha256'],page_evidence=pages_for(spans,start,end),edits=selected,contains_cyrillic=bool(re.search('[А-Яа-яЁё]',text)),contains_cjk=bool(re.search('[\u3400-\u9fff]',text)),external_source_cautions=cautions,context_source_start=context_start,context_source_end=context_end,source_context=raw[context_start:context_end],candidate_context=context,context_edits=context_edits,context_page_evidence=pages_for(spans,context_start,context_end),complete_example_boundary_assessed=False,language_alignment_assessed=False,semantic_labels_assessed=False)
                if not row['page_evidence']:raise ValueError('Unbound anchor')
                rows.append(row)
            units.append(dict(code=unit['code'],title=unit['title'],state=section['state'],source_body_sha256=meta['source_body_sha256'],candidate_body_sha256=meta['body_sha256'],anchor_paragraphs=count,page_evidence=spans,external_source_cautions=cautions))
            if not count:warnings.append(dict(code=unit['code'],reason='no_numbered_parenthesis_anchor_found',meaning='不代表该节没有例句；行内、无编号及表格例句不在本索引。'))
    if len(units)!=100 or len({x['example_id']for x in rows})!=len(rows):raise ValueError('Invalid unit or anchor count')
    return manifest,rows,units,warnings

def build(candidate=DEFAULT_CANDIDATE,output=DEFAULT_OUTPUT):
    candidate=Path(candidate).resolve();output=Path(output).resolve()
    if output.exists():raise FileExistsError('Immutable example index; choose a new version')
    manifest,rows,units,warnings=materialize(candidate)
    output.mkdir(parents=True)
    for name,data in [('examples.jsonl',rows),('source_units.jsonl',units)]:
        (output/name).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n'for x in data),'utf8')
    write(output/'extraction_notes.json',dict(warnings=warnings,scope='100理论节中以括号数字起段的锚段；按空行停止，附前一段与后两段上下文，不推定整例边界或俄汉对齐。无编号、行内、表格及练习答案均未计。',not_a_natural_frequency_corpus=True))
    with closing(sqlite3.connect(output/'examples.sqlite'))as c:
        c.executescript('''CREATE TABLE examples(example_id TEXT PRIMARY KEY,source_unit TEXT NOT NULL,chapter INTEGER NOT NULL,book_number INTEGER NOT NULL,state TEXT NOT NULL,source_text TEXT NOT NULL,candidate_text TEXT NOT NULL,metadata_json TEXT NOT NULL);
        CREATE INDEX examples_unit ON examples(source_unit);
        CREATE INDEX examples_state_chapter ON examples(state,chapter);
        CREATE TABLE source_units(code TEXT PRIMARY KEY,state TEXT NOT NULL,metadata_json TEXT NOT NULL);''')
        with c:
            c.executemany('insert into examples values(?,?,?,?,?,?,?,?)',[(r['example_id'],r['source_unit'],r['chapter'],r['book_number'],r['state'],r['source_text'],r['candidate_text'],json.dumps(r,ensure_ascii=False))for r in rows])
            c.executemany('insert into source_units values(?,?,?)',[(u['code'],u['state'],json.dumps(u,ensure_ascii=False))for u in units])
        if c.execute('pragma integrity_check').fetchone()[0]!='ok'or c.execute('pragma foreign_key_check').fetchall():raise ValueError('Example database integrity failed')
    shutil.copy2(Path(__file__),output/Path(__file__).name)
    shutil.copy2(Path(__file__).with_name('aspect_example_index.py'),output/'aspect_example_index.py')
    counts=dict(Counter(r['state']for r in rows));stats=dict(anchor_paragraphs=len(rows),unit_count=len(units),counts=counts,eligible_original=sum(r['eligible_original']for r in rows),eligible_with_candidates=sum(r['eligible_with_candidates']for r in rows),anchor_paragraphs_with_edits=sum(bool(r['edits'])for r in rows),cyrillic_anchor_paragraphs=sum(r['contains_cyrillic']for r in rows),cjk_anchor_paragraphs=sum(r['contains_cjk']for r in rows))
    (output/'README.md').write_text(f'''# 现代俄语体学：书内编号例句锚段索引

{json.dumps(stats,ensure_ascii=False)}

这是教材内部的自动定位索引，不是自然语料频率库，也不是逐句俄汉对齐库。编号锚段可能是整例、多句、公式或对话的第一段；附前一段、后两段上下文，完整例句边界与语义标签尚未逐条审核。无编号、行内、表格和练习答案例句均未统计，禁止把锚段数写成全书例句数或自然语料句数。

原文与编校层各保留精确片段、指纹、原单位偏移、PDF页/印刷页及原图审核指纹。章/节标题只代表来源位置，不给每个例句自动标注体意义。原印库、学生库和旧候选包未改。

JSONL与SQLite为研究归档，含明确标记的隔离材料。查询默认仅原40节；--include-candidates显式纳入候选，隔离节任何模式均不返回。若需要对话的后续译文，请检查所附上下文与原页；上下文可能有邻例，不能计作独立句数。

运行：

    python aspect_example_index.py verify
    python aspect_example_index.py search --contains ловить --include-candidates --limit 5
    python aspect_example_index.py search --chapter 11 --include-candidates --limit 5
    python aspect_example_index.py show --id aspect.ch11.s04.01.example.003.01 --include-candidates

检索采用字面子串，不变换е/ё或词形；不调用网络、OCR或生成API。数据与源码可离线核验，复建需要已指纹绑定的候选包。模型编校不等于专家审定。
''','utf8')
    result=dict(schema_version=1,created_at=datetime.now(timezone.utc).isoformat(),edition=output.name,source_candidate_edition=manifest['edition'],source_candidate_manifest_sha256=fsh(candidate/'manifest.json'),source_original_db_sha256=manifest['source_db_sha256'],statistics=stats,source_unit_counts=dict(Counter(u['state']for u in units)),provisional=True,not_a_natural_frequency_corpus=True,files={p.name:fsh(p)for p in output.iterdir()if p.is_file()})
    write(output/'manifest.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,default=DEFAULT_CANDIDATE);p.add_argument('--output',type=Path,default=DEFAULT_OUTPUT);a=p.parse_args()
    print(json.dumps(build(a.candidate,a.output),ensure_ascii=False,indent=2))
