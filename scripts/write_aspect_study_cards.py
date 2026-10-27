"""Bind manually written model study cards to exact, pinned textbook evidence.

This validates provenance and scope only. It cannot judge a summary's meaning.
"""
from pathlib import Path
from contextlib import closing
import argparse,datetime,json,re
import aspect_candidate_rag as rag
import build_aspect_example_index as evidence

WORK=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference'
DEFAULT_CANDIDATE=WORK/'research_exports/aspect_editorial_candidate_20261022_005'
def write_cards(input_path,output,candidate=DEFAULT_CANDIDATE):
    output=Path(output);candidate=Path(candidate);items=rag.read(input_path)['cards'];manifest=rag.verify_package(candidate)
    if output.exists():raise FileExistsError('Study-card batches are immutable')
    if not items:raise ValueError('Empty study-card batch')
    cards=[];seen=set()
    with closing(rag.connect(candidate/'aspect_reference.sqlite'))as c:
        for item in items:
            code=item['code']
            if code in seen:raise ValueError('Duplicate unit in batch')
            seen.add(code)
            row=c.execute('select * from aspect_candidate_sections where code=?',(code,)).fetchone()
            raw=c.execute('select * from chunks where code=?',(code,)).fetchone()
            if row is None or raw is None:raise ValueError('Unknown study-card source')
            meta=json.loads(row['metadata_json']);spans=evidence.bindings(c,raw);claims=[]
            for claim in item['claims']:
                quote=claim['quote'];text=claim['text_zh']
                if not isinstance(text,str)or len(text)<8 or not isinstance(quote,str)or len(quote)<12:raise ValueError('Claim and exact quote required')
                if raw['body'].count(quote)!=1 or row['body'].count(quote)!=1:raise ValueError('Quote must uniquely match both original and candidate: '+code+' '+quote)
                start=raw['body'].index(quote);end=start+len(quote)
                claims.append(dict(text_zh=text,quote=quote,quote_sha256=rag.tsh(quote),source_start=start,source_end=end,page_evidence=evidence.pages_for(spans,start,end),claim_kind='model_paraphrase_of_source_position',quote_layer='unchanged_original_text',independent_semantic_review=False))
            if not claims or not item.get('questions_zh'):raise ValueError('Missing claims or retrieval prompts')
            cards.append(dict(code=code,title=row['title'],state=row['state'],source_allowed_original=row['state']=='original_source_ready',source_allowed_with_candidates=row['state']in ('original_source_ready','model_editorial_candidate'),source_body_sha256=meta['source_body_sha256'],candidate_body_sha256=meta['body_sha256'],claims=claims,questions_zh=item['questions_zh'],cautions_zh=item.get('cautions_zh',[]),content_kind='model_study_card_not_original_prose',summary_completeness='not_claimed',independent_semantic_review=False,external_source_cautions=[dict(issue_id=x['issue_id'],note=x['external_quote_adaptation_note'])for x in meta['decisions']if x.get('external_quote_adaptation_note')]))
    result=dict(schema_version=1,created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate_manifest_sha256=rag.fsh(candidate/'manifest.json'),source_original_db_sha256=manifest['source_db_sha256'],input_sha256=rag.fsh(input_path),card_count=len(cards),claim_count=sum(len(x['claims'])for x in cards),cards=cards,review_method='same_assistant_reading_of_full_source_units_with_exact_quote_binding',limitations='模型学习卡，非原书逐字正文或独立专家评议；工程只验证引句、原页、哈希和来源状态，不证明摘要语义或穷尽全部内容。隔离卡仅研究归档，不进入默认或候选检索。')
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    return dict(path=str(output),cards=len(cards),claims=result['claim_count'],sha256=rag.fsh(output))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--candidate',type=Path,default=DEFAULT_CANDIDATE);a=p.parse_args();print(json.dumps(write_cards(a.input,a.output,a.candidate),ensure_ascii=False))
