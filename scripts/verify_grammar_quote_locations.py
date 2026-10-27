"""Rebuild per-character page provenance for all ready sections and pilot quotes."""
from collections import Counter
from contextlib import closing
import json
import sqlite3
from grammar_editorial_rag import DEFAULT_DB, verify_package, sha
from grammar_quote_locator import trace_section,locate_in_trace
from run_grammar_generation_pilot import ROOT, OUT, now, write

def main():
    target=ROOT/'data/processed/grammar_reference/reviews/quote_locations_20261022_001.json'
    if target.exists():raise FileExistsError('Use a new immutable output')
    before=sha(DEFAULT_DB);manifest=verify_package(DEFAULT_DB.parent)
    traces={};section_rows=[]
    with closing(sqlite3.connect(DEFAULT_DB.as_uri()+'?mode=ro',uri=True))as conn:
        conn.row_factory=sqlite3.Row
        codes=[r[0]for r in conn.execute("select code from chunks where status='ready' order by code")]
        for code in codes:
            trace=trace_section(conn,code);source=trace['source'];original=0;revised=0
            assert len(trace['normalized_body'])==len(trace['labels'])
            for char,label in zip(trace['normalized_body'],trace['labels']):
                assert label[0] and label[0]<=set(source['pdf_pages'])
                if label[2]is not None:
                    assert trace['raw_normalized_body'][label[2]]==char
                    original+=1
                else:revised+=1
            traces[code]=trace
            section_rows.append({'code':code,'normalized_characters':len(trace['labels']),
                'retained_original_characters':original,'replacement_characters':revised,
                'body_sha256':source['body_sha256'],'pdf_pages':source['pdf_pages']})
    assert len(codes)==368
    citations=[]
    for path in sorted((OUT/'responses').glob('*_rag.json')):
        response=json.loads(path.read_text(encoding='utf-8'));cid=path.stem.split('_')[1]
        packet=json.loads((OUT/'packets'/f'{cid}.json').read_text(encoding='utf-8'))
        sources={s['source_id']:s for s in packet['sources']}
        for index,claim in enumerate(response['parsed'].get('claims',[]),1):
            for number,citation in enumerate(claim['citations'],1):
                source=sources[citation['source_id']]
                located=locate_in_trace(traces[source['code']],citation['quote'])
                citations.append({'request_id':path.stem,'claim':index,'citation':number,
                    'source_id':citation['source_id'],**located})
    summary={'ready_sections_traced':len(section_rows),'normalized_characters':sum(s['normalized_characters']for s in section_rows),
        'replacement_characters':sum(s['replacement_characters']for s in section_rows),
        'pilot_citations':len(citations),'quotes_found':sum(c['quote_found']for c in citations),
        'ambiguous_quotes':sum(c['ambiguous']for c in citations),
        'quotes_with_editorial_derived_occurrence':sum(any(o['provenance_kind']=='editorial_derived_span'for o in c['occurrences'])for c in citations)}
    assert len(citations)==39 and summary['quotes_found']==37
    assert sha(DEFAULT_DB)==before
    write(target,{'verified_at':now(),'database_sha256':before,'edition_files_verified':len(manifest['files']),
        'locator_sha256':sha(ROOT/'scripts/grammar_quote_locator.py'),'summary':summary,
        'sections':section_rows,'citations':citations,'api_calls':0,
        'limitations':['字符位置为已核页转录位置，未生成PDF字形坐标。',
                       '编校字符的来源页是日志重放的锚点，不是声称原印逐字有该内容。',
                       '重复引句保留所有位置，未擅自选定唯一页；来源定位不能证明语义充分性。']})
    print(json.dumps({'artifact':str(target),'summary':summary,
        'ambiguous':[{'request_id':c['request_id'],'claim':c['claim'],'quote':c['quote'],
                     'pages':[o['pdf_pages']for o in c['occurrences']]}for c in citations if c['ambiguous']]},ensure_ascii=False))

if __name__=='__main__':main()
