"""Build a source-bound, multi-axis model pilot; never import it into training."""
from pathlib import Path
from contextlib import closing
from collections import Counter
import argparse,csv,datetime,json
import aspect_candidate_rag as rag
import build_aspect_example_index as evidence

WORK=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference'
AXES={
 'discourse_status':{'asserted_instance','presupposed_instance','confirmed_in_response','announced_intention','questioned_intention','generic_claim','permitted','commanded','requested','modal_possibility','normative'},
 'event_realization':{'presented_as_occurred','not_committed','generic_only','not_applicable','unknown'},
 'lexical_goal_attainment':{'established_in_source_reading','not_asserted','unknown','not_applicable'},
 'reference_result_state':{'holds_in_source_reading','cancelled_explicitly','unknown','not_applicable'},
 'consequence_relevance':{'relevant_in_source_reading','unknown','not_applicable'},
}
ANALYSIS_KEYS={'lemma','aspect','form_class','morphological_tense','grammatical_tense','vocalized_form'}

def validate_labels(item):
    analyses=item['form_analyses']
    if not analyses or type(item['source_selected_analysis'])is not int or not 0<=item['source_selected_analysis']<len(analyses):raise ValueError('Missing joint analysis selection')
    if len({json.dumps(x,sort_keys=True)for x in analyses})!=len(analyses):raise ValueError('Repeated analysis')
    for x in analyses:
        if set(x)!=ANALYSIS_KEYS or not x['lemma']:raise ValueError('Joint analysis schema mismatch')
        if x['aspect']not in {'perfective','imperfective','not_lexically_marked'}:raise ValueError('Invalid aspect')
        if x['form_class']not in {'indicative','infinitive','imperative','unmarked_chinese_clause'}:raise ValueError('Invalid form class')
        if x['morphological_tense']not in {'past','nonpast','none','not_encoded'}:raise ValueError('Invalid morphological tense')
        if x['grammatical_tense']not in {'past','present','future','none','not_encoded'}:raise ValueError('Invalid grammatical tense')
        if x['form_class']in {'infinitive','imperative'}and(x['morphological_tense']!='none'or x['grammatical_tense']!='none'):raise ValueError('Nonfinite/imperative target cannot inherit auxiliary time')
        if x['form_class']=='unmarked_chinese_clause'and(x['morphological_tense']!='not_encoded'or x['grammatical_tense']!='not_encoded'or x['aspect']!='not_lexically_marked'):raise ValueError('Chinese form cannot inherit Russian morphological aspect/time')
    if set(item['semantic_axes'])!=set(AXES):raise ValueError('Semantic axes mismatch')
    for key,allowed in AXES.items():
        axis=item['semantic_axes'][key]
        if set(axis)!={'value','basis','explanation_zh'}or axis['value']not in allowed or not axis['explanation_zh']or not axis['basis']:raise ValueError('Invalid semantic axis')
        if any(type(n)is not int or not 0<=n<len(item['basis_quotes'])for n in axis['basis']):raise ValueError('Missing axis evidence')
    status=item['semantic_axes']['discourse_status']['value'];real=item['semantic_axes']['event_realization']['value']
    if status in {'announced_intention','questioned_intention','permitted','commanded','requested','modal_possibility','normative'}and real!='not_committed':raise ValueError('Speech/modal context cannot certify execution')
    if status=='generic_claim'and real!='generic_only':raise ValueError('Generic example is not a dated observed instance')
    if item['construction']['tense']not in {'past','present','future','not_encoded','none'}:raise ValueError('Invalid construction time')
    if item['construction']['kind']=='analytic_future'and(item['construction']['tense']!='future'or not item['construction']['auxiliary']):raise ValueError('Analytic future needs auxiliary')
    if item['quantification']['kind']not in {'none','event_count','rate','activity_duration','state_duration','elapsed_interval'}:raise ValueError('Invalid measurement object')
    if item['quantification']['kind']=='none'and item['quantification']['expressions']:raise ValueError('Unassigned quantity')

def bind_span(raw,spans,text,start=None):
    if not text:raise ValueError('Empty evidence')
    if start is None:
        if raw['body'].count(text)!=1:raise ValueError('Evidence must be unique or have an explicit source offset')
        start=raw['body'].index(text)
    if raw['body'][start:start+len(text)]!=text:raise ValueError('Evidence offset mismatch')
    return dict(text=text,source_start=start,source_end=start+len(text),sha256=rag.tsh(text),page_evidence=evidence.pages_for(spans,start,start+len(text)))

def build(input_path,old_pilot,index,candidate,output):
    output=Path(output)
    if output.exists():raise FileExistsError('Pilot editions are immutable')
    data=rag.read(input_path);old=rag.read(old_pilot);rag.verify_package(candidate)
    from aspect_example_index import verify as verify_index
    verify_index(index)
    if data['source_candidate_manifest_sha256']!=rag.fsh(candidate/'manifest.json')or data['source_index_manifest_sha256']!=rag.fsh(index/'manifest.json'):raise ValueError('Pinned edition mismatch')
    previous={x['example_id']:x for x in old['records']};anchors={x['example_id']:x for x in map(json.loads,(index/'examples.jsonl').read_text('utf8').splitlines())};records=[];seen=set()
    with closing(rag.connect(candidate/'aspect_reference.sqlite'))as c:
        for item in data['annotations']:
            validate_labels(item);key=item['example_id']
            if key in seen or key not in previous:raise ValueError('Unknown or repeated pilot target')
            seen.add(key);prior=previous[key];anchor=anchors[key]
            if not anchor['eligible_with_candidates']:raise ValueError('Withheld source cannot be annotated as eligible')
            raw=c.execute('select * from chunks where code=?',(anchor['source_unit'],)).fetchone();current=c.execute('select * from aspect_candidate_sections where code=?',(anchor['source_unit'],)).fetchone();spans=evidence.bindings(c,raw)
            if prior['source_text']!=anchor['source_text']or prior['target']!=item['target']or prior['source_unit_sha256']!=rag.tsh(raw['body']):raise ValueError('Pilot source changed')
            target=bind_span(raw,spans,item['target'],prior['target_source_start'])
            if anchor['source_text'].count(item['target'])!=1 or anchor['candidate_text'].count(item['target'])!=1:raise ValueError('Target became ambiguous in anchor')
            basis=[]
            for quote in item['basis_quotes']:
                if current['body'].count(quote)!=1:raise ValueError('Interpretive quote changed or ambiguous in candidate')
                basis.append(bind_span(raw,spans,quote))
            auxiliary=item['construction']['auxiliary']
            auxiliary_bound=None
            if auxiliary:
                if anchor['source_text'].count(auxiliary)!=1:raise ValueError('Auxiliary must occur once in same anchor')
                auxiliary_bound=bind_span(raw,spans,auxiliary,anchor['source_start']+anchor['source_text'].index(auxiliary))
            marker_bounds=[]
            for marker in item['construction']['markers']:
                pos=marker['anchor_start'];text=marker['text']
                if anchor['source_text'][pos:pos+len(text)]!=text:raise ValueError('Chinese marker anchor offset mismatch')
                marker_bounds.append(dict(role=marker['role'],**bind_span(raw,spans,text,anchor['source_start']+pos)))
            quantity=[]
            for text in item['quantification']['expressions']:
                if anchor['source_text'].count(text)!=1:raise ValueError('Quantity must occur once in same anchor')
                quantity.append(bind_span(raw,spans,text,anchor['source_start']+anchor['source_text'].index(text)))
            records.append(dict(**item,language=prior['language'],source_unit=anchor['source_unit'],state=anchor['state'],source_text=anchor['source_text'],candidate_text=anchor['candidate_text'],source_unit_sha256=rag.tsh(raw['body']),candidate_unit_sha256=rag.tsh(current['body']),target_binding=target,basis_bindings=basis,auxiliary_binding=auxiliary_bound,marker_bindings=marker_bounds,quantity_bindings=quantity,external_source_cautions=anchor['external_source_cautions'],prior_record_sha256=rag.tsh(json.dumps(prior,ensure_ascii=False,sort_keys=True)),annotation_kind='same_assistant_source_informed_multiaxis_pilot_not_gold',independent_semantic_review=False,world_facts_verified=False,rag_integration=False,training_pool_import=False))
    if seen!=set(previous):raise ValueError('Pilot target coverage changed')
    output.mkdir(parents=True)
    (output/'annotations.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n'for x in records),'utf8')
    with (output/'selected_readings.tsv').open('w',encoding='utf-8-sig',newline='')as f:
        fields=['example_id','language','target','state','analysis_count','source_selected_lemma','source_selected_aspect','target_morphological_tense','source_selected_grammatical_tense','construction_tense','event_time']+list(AXES)+['measurement_object','independent_semantic_review']
        writer=csv.DictWriter(f,fieldnames=fields,delimiter='\t');writer.writeheader()
        for x in records:
            form=x['form_analyses'][x['source_selected_analysis']]
            row=dict(example_id=x['example_id'],language=x['language'],target=x['target'],state=x['state'],analysis_count=len(x['form_analyses']),source_selected_lemma=form['lemma'],source_selected_aspect=form['aspect'],target_morphological_tense=form['morphological_tense'],source_selected_grammatical_tense=form['grammatical_tense'],construction_tense=x['construction']['tense'],event_time=x['event_time'],measurement_object=x['quantification']['kind'],independent_semantic_review=False)
            row.update({k:v['value']for k,v in x['semantic_axes'].items()});writer.writerow(row)
    source_pins=dict(input_sha256=rag.fsh(input_path),prior_pilot_sha256=rag.fsh(old_pilot),candidate_manifest_sha256=rag.fsh(candidate/'manifest.json'),index_manifest_sha256=rag.fsh(index/'manifest.json'),builder_sha256=rag.fsh(Path(__file__)))
    (output/'source_pins.json').write_text(json.dumps(source_pins,ensure_ascii=False,indent=2)+'\n','utf8')
    (output/'README.md').write_text('''# 现代俄语体学：多轴语义试标002

22个既有教材目标重新拆分字段，18俄语、4汉语；只含可显式使用的源节，保留文学异文警示。固定候选007与锚段索引005，不修改试标001、原书转录或学生数据。

每条分别记录联合词形候选、作者选定读法、助动词、构式时态、事件时间、话语地位、发生承诺、词汇目标达成、参照时结果状态、后果相关性及量度对象。узнаешь保留两组相互约束的词元/体/时态分析；不把作者的选择变成无歧义词形识别。заказывать本身无形态时，будете定位于同一锚段，组合表达将来。汉语了₁/了₂逐字定位，不套用俄语词汇体分类。

五个语义轴各有精确依据编号和模型说明；引句绑定原节Unicode偏移、PDF/印刷页和审核指纹。语义标签为同一助手参考教材立场的解释，机械存在的引句不能证明标签正确，未知与不适用保留。所有发生承诺只在教材话语内部解释，不核实小说或新闻世界事实。

annotations.jsonl保存完整候选与依据。selected_readings.tsv仅为作者选定读法的便览，analysis_count=2的行不能作为无歧义词形金标。22条是有意选择的开发试样，不能估计自然语料分布、独立一致率、准确率或因果效应。未接RAG、未入学生池，未做独立专家复核。正式研究仍须另定自然语料、抽样协议、双人标注及分歧裁决。
''','utf8')
    files={p.name:rag.fsh(p)for p in sorted(output.iterdir())if p.is_file()}
    result=dict(schema_version=2,created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),annotation_count=len(records),languages=dict(Counter(x['language']for x in records)),source_states=dict(Counter(x['state']for x in records)),ambiguous_form_targets=sum(len(x['form_analyses'])>1 for x in records),basis_quote_count=sum(len(x['basis_bindings'])for x in records),axis_counts={k:dict(Counter(x['semantic_axes'][k]['value']for x in records))for k in AXES},files=files,source_pins=source_pins,independent_semantic_review=False,not_natural_frequency_sample=True,rag_integration=False,training_pool_import=False)
    (output/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--prior-pilot',type=Path,required=True);p.add_argument('--index',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(build(a.input,a.prior_pilot,a.index,a.candidate,a.output),ensure_ascii=False,indent=2))
