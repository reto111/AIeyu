"""Bind an explicitly model-annotated pilot to exact source occurrences."""
from pathlib import Path
from contextlib import closing
from collections import Counter
import argparse,datetime,json
import aspect_candidate_rag as rag
import build_aspect_example_index as evidence

WORK=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference'
INDEX=WORK/'research_exports/aspect_numbered_examples_20261022_004'
CANDIDATE=WORK/'research_exports/aspect_editorial_candidate_20261022_006'
REQUIRED={'example_id','target','lemma','language','aspect','tense','mood','polarity','event_time','reading','occurrence','result','repetition','time_measure','note'}
def write(input_path,selection_path,output):
    output=Path(output)
    if output.exists()or output.with_suffix('.md').exists():raise FileExistsError('Pilot outputs are immutable')
    annotations=rag.read(input_path)['annotations'];selection=rag.read(selection_path)
    if selection['source_index_manifest_sha256']!=rag.fsh(INDEX/'manifest.json'):raise ValueError('Selection edition changed')
    rag.verify_package(CANDIDATE)
    actual={x['example_id']:x for x in map(json.loads,(INDEX/'examples.jsonl').read_text('utf8').splitlines())}
    selected={x['example_id']:x for x in selection['examples']};seen=set();records=[]
    with closing(rag.connect(CANDIDATE/'aspect_reference.sqlite'))as c:
        for item in annotations:
            if set(item)!=REQUIRED:raise ValueError('Pilot schema fields mismatch')
            key=item['example_id']
            if key in seen or key not in selected:raise ValueError('Repeated or unselected annotation')
            seen.add(key);source=selected[key]
            if source!=actual[key]or not source['eligible_with_candidates']:raise ValueError('Selection source or eligibility mismatch')
            target=item['target']
            if source['source_text'].count(target)!=1 or source['candidate_text'].count(target)!=1:raise ValueError('Target must uniquely match both layers')
            if item['language']not in ('ru','zh')or not item['reading']or not all(isinstance(x,str)for x in item['reading']):raise ValueError('Missing language or model reading')
            raw=c.execute('select * from chunks where code=?',(source['source_unit'],)).fetchone();spans=evidence.bindings(c,raw)
            start=source['source_start']+source['source_text'].index(target);end=start+len(target)
            if raw['body'][start:end]!=target:raise ValueError('Target raw offset mismatch')
            records.append(dict(**item,source_unit=source['source_unit'],state=source['state'],source_text=source['source_text'],candidate_text=source['candidate_text'],source_text_sha256=source['source_text_sha256'],candidate_text_sha256=source['candidate_text_sha256'],source_unit_sha256=source['source_unit_sha256'],candidate_unit_sha256=source['candidate_unit_sha256'],target_source_start=start,target_source_end=end,target_page_evidence=evidence.pages_for(spans,start,end),candidate_context=source['candidate_context'],external_source_cautions=source['external_source_cautions'],annotation_kind='same_assistant_source_informed_model_pilot_not_gold',independent_semantic_review=False,rag_integration=False,training_pool_import=False,semantic_confidence='requires_independent_review',evidence_reading_scope='full_source_unit_read_and_anchor_context_checked'))
    if seen!=set(selected):raise ValueError('Selected examples left unannotated')
    result=dict(schema_version=1,created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),selection_sha256=rag.fsh(selection_path),annotation_input_sha256=rag.fsh(input_path),source_index_manifest_sha256=rag.fsh(INDEX/'manifest.json'),source_candidate_manifest_sha256=rag.fsh(CANDIDATE/'manifest.json'),annotation_count=len(records),languages=dict(Counter(x['language']for x in records)),source_states=dict(Counter(x['state']for x in records)),selection_method=selection['selection_method'],not_independent_test_set=True,not_natural_frequency_sample=True,independent_semantic_review=False,rag_integration=False,records=records,limitations=['22条为有意选择的教材对照，不是自然语料随机样本、金标准或准确率测量。','只在每锚段选一个明确定位的目标；未给整段或邻段的全部动词标注，不声称完整俄汉对齐。','读法参考完整源节，邻接窗口可能不含全部解释；作者解释和模型标签均待独立审核。','形态歧义、未知结果、意愿许可与实际实现分列；不能把模型标签回填为原书文字或学生训练真值。'])
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    lines=['# 体学语义标注试样：22个定位目标','','同一助手依据已知教材对照试标，用于检验字段和发展规范。非金标准、非自然频率样本，未接RAG或学生池。形态、事件时间、结果和情态分列；原页列仅为目标词形所在页。','','|锚段|目标|形态体|形式时间/式|解释标签|目标PDF/印刷页|','|---|---|---|---|---|---|']
    for x in records:
        pages=', '.join(str(p['pdf_page'])+'/'+str(p['printed_page'])for p in x['target_page_evidence'])
        lines.append('|'+x['example_id']+'|'+x['target']+'|'+x['aspect']+'|'+x['tense']+' / '+x['mood']+'|'+', '.join(x['reading'])+'|'+pages+'|')
    lines+=['','## 逐条说明','']
    for x in records:lines +=['- **'+x['example_id']+'**：'+x['note']]
    lines+=['','## 限制','']+['- '+x for x in result['limitations']]
    output.with_suffix('.md').write_text('\n'.join(lines)+'\n','utf8')
    return {k:v for k,v in result.items()if k not in ('records','limitations')}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--selection',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(write(a.input,a.selection,a.output),ensure_ascii=False,indent=2))
