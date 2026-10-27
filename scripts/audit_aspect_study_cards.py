"""Audit immutable model study cards against both pinned source layers.

Provenance validation only; no test here establishes paraphrase correctness.
"""
from pathlib import Path
from contextlib import closing
import argparse,collections,copy,datetime,json
import aspect_candidate_rag as rag
import build_aspect_example_index as evidence

WORK=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference'
PINNED=WORK/'research_exports/aspect_editorial_candidate_20261022_005'

def validate_card(card,row,raw,spans):
    meta=json.loads(row['metadata_json']);state=row['state']
    expected=dict(code=row['code'],title=row['title'],state=state,
                  source_allowed_original=state=='original_source_ready',
                  source_allowed_with_candidates=state in ('original_source_ready','model_editorial_candidate'),
                  source_body_sha256=meta['source_body_sha256'],candidate_body_sha256=meta['body_sha256'],
                  content_kind='model_study_card_not_original_prose',summary_completeness='not_claimed',independent_semantic_review=False)
    if any(card.get(k)!=v for k,v in expected.items()):raise ValueError('Card source or scope mismatch')
    cautions=[dict(issue_id=x['issue_id'],note=x['external_quote_adaptation_note'])for x in meta['decisions']if x.get('external_quote_adaptation_note')]
    if card['external_source_cautions']!=cautions:raise ValueError('Source caution mismatch')
    if not card['claims']or not card['questions_zh']:raise ValueError('Empty study card')
    for claim in card['claims']:
        q=claim['quote'];start=claim['source_start'];end=claim['source_end']
        if len(q)<12 or raw['body'].count(q)!=1 or row['body'].count(q)!=1:raise ValueError('Quote not unique in both layers')
        if raw['body'][start:end]!=q or end-start!=len(q) or rag.tsh(q)!=claim['quote_sha256']:raise ValueError('Quote offset or hash mismatch')
        if claim['page_evidence']!=evidence.pages_for(spans,start,end):raise ValueError('Quote page binding mismatch')
        if claim['claim_kind']!='model_paraphrase_of_source_position'or claim['quote_layer']!='unchanged_original_text'or claim['independent_semantic_review']is not False:raise ValueError('Unsupported semantic certification')
        if not isinstance(claim['text_zh'],str)or len(claim['text_zh'])<8:raise ValueError('Missing model paraphrase')
    return True

def audit(cards_dir,output,candidate=PINNED):
    cards_dir=Path(cards_dir);output=Path(output);candidate=Path(candidate)
    if output.exists():raise FileExistsError('Audit outputs are immutable')
    manifest=rag.verify_package(candidate);files=sorted(cards_dir.glob('study_cards_*.json'))
    if not files:raise ValueError('No study cards')
    seen=set();counts=collections.Counter();claims=collections.Counter();pins={};pages=set();forged=scope=page_tampered=caution_removed=0
    with closing(rag.connect(candidate/'aspect_reference.sqlite'))as c:
        theory={r['code']for r in c.execute('select code from aspect_candidate_sections')}
        for path in files:
            batch=rag.read(path);pins[path.name]=rag.fsh(path)
            if batch['candidate_manifest_sha256']!=rag.fsh(candidate/'manifest.json')or batch['source_original_db_sha256']!=manifest['source_db_sha256']:raise ValueError('Wrong pinned edition')
            if batch['card_count']!=len(batch['cards'])or batch['claim_count']!=sum(len(x['claims'])for x in batch['cards']):raise ValueError('Incorrect batch counts')
            for card in batch['cards']:
                code=card['code']
                if code in seen:raise ValueError('Repeated unit across batches')
                seen.add(code)
                row=c.execute('select * from aspect_candidate_sections where code=?',(code,)).fetchone();raw=c.execute('select * from chunks where code=?',(code,)).fetchone()
                if row is None or raw is None:raise ValueError('Unknown theory source')
                spans=evidence.bindings(c,raw);validate_card(card,row,raw,spans)
                counts[card['state']]+=1;claims[card['state']]+=len(card['claims'])
                for claim in card['claims']:pages.update(x['pdf_page']for x in claim['page_evidence'])
                tests=[]
                fake=copy.deepcopy(card);fake['claims'][0]['quote']='此为故意伪造的引文，不存在于原书。';tests.append(('quote',fake))
                fake=copy.deepcopy(card);fake['source_allowed_original']=not fake['source_allowed_original'];tests.append(('scope',fake))
                fake=copy.deepcopy(card);fake['claims'][0]['page_evidence']=[];tests.append(('page',fake))
                if card['external_source_cautions']:
                    fake=copy.deepcopy(card);fake['external_source_cautions']=[];tests.append(('caution',fake))
                for kind,fake in tests:
                    try:validate_card(fake,row,raw,spans)
                    except ValueError:
                        forged+=kind=='quote';scope+=kind=='scope';page_tampered+=kind=='page';caution_removed+=kind=='caution'
                    else:raise AssertionError('Tampering accepted: '+kind)
        missing=sorted(theory-seen)
    report=dict(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate=candidate.as_posix(),candidate_manifest_sha256=rag.fsh(candidate/'manifest.json'),batch_files=len(files),batch_pins=pins,card_count=len(seen),claim_count=sum(claims.values()),cards_by_state=dict(counts),claims_by_state=dict(claims),quote_evidence_pdf_page_union=len(pages),all_quote_offsets_hashes_and_pages_verified=True,forged_quote_cards_rejected=forged,altered_scope_cards_rejected=scope,altered_page_cards_rejected=page_tampered,removed_source_cautions_rejected=caution_removed,missing_theory_units=missing,remaining=len(missing),independent_semantic_review=False,rag_integration=False,limitations=['同一助手读源文后归纳，不是独立专家评议。','全量验证引句、偏移、页图指纹、来源状态和两层未改原文，不证明350条摘要的语义准确性或穷尽性。','隔离来源卡仅归档；提问提示不是独立测试集，不能当作留出集测召回。'])
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    return {k:v for k,v in report.items()if k not in ('batch_pins','limitations')}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cards',type=Path,default=WORK/'study_cards');p.add_argument('--candidate',type=Path,default=PINNED);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(audit(a.cards,a.output,a.candidate),ensure_ascii=False,indent=2))
