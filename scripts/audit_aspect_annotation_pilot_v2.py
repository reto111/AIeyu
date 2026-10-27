"""Replay source bindings and reject scope/evidence tampering in model pilots."""
from pathlib import Path
from contextlib import closing
from collections import Counter
import argparse,copy,csv,datetime,json,tempfile
import aspect_candidate_rag as rag
import build_aspect_annotation_pilot_v2 as model
import build_aspect_example_index as evidence

def audit(directory,input_path,prior_pilot,index,candidate):
    m=rag.read(directory/'manifest.json');source=rag.read(input_path);old=rag.read(prior_pilot)
    pins=m['source_pins']
    for key,path in [('input_sha256',input_path),('prior_pilot_sha256',prior_pilot),('candidate_manifest_sha256',candidate/'manifest.json'),('index_manifest_sha256',index/'manifest.json')]:
        if rag.fsh(path)!=pins[key]:raise ValueError('Pinned input changed: '+key)
    for name,pin in m['files'].items():
        path=(directory/name).resolve()
        if path.parent!=directory.resolve()or rag.fsh(path)!=pin:raise ValueError('Pilot fingerprint changed')
    rag.verify_package(candidate)
    from aspect_example_index import verify
    verify(index)
    records=[json.loads(x)for x in (directory/'annotations.jsonl').read_text('utf8').splitlines()]
    inputs={x['example_id']:x for x in source['annotations']};previous={x['example_id']:x for x in old['records']};anchors={x['example_id']:x for x in map(json.loads,(index/'examples.jsonl').read_text('utf8').splitlines())}
    if len(records)!=len(inputs)or len({x['example_id']for x in records})!=len(records)or set(inputs)!=set(previous):raise ValueError('Invalid pilot membership')
    checked=Counter()
    with closing(rag.connect(candidate/'aspect_reference.sqlite'))as c:
        for x in records:
            model.validate_labels(x);key=x['example_id'];a=anchors[key];prior=previous[key]
            for name,value in inputs[key].items():
                if x[name]!=value:raise ValueError('Annotation changed after input freeze')
            raw=c.execute('select * from chunks where code=?',(a['source_unit'],)).fetchone();current=c.execute('select * from aspect_candidate_sections where code=?',(a['source_unit'],)).fetchone();spans=evidence.bindings(c,raw)
            if current['state']not in {'original_source_ready','model_editorial_candidate'}or x['state']!=current['state']:raise ValueError('Unavailable annotation source')
            if x['source_unit']!=a['source_unit']or x['source_text']!=a['source_text']or x['candidate_text']!=a['candidate_text']or x['source_unit_sha256']!=rag.tsh(raw['body'])or x['candidate_unit_sha256']!=rag.tsh(current['body']):raise ValueError('Annotation source text changed')
            if x['external_source_cautions']!=a['external_source_cautions']:raise ValueError('Dropped literary variant caution')
            if x['prior_record_sha256']!=rag.tsh(json.dumps(prior,ensure_ascii=False,sort_keys=True)):raise ValueError('Pilot lineage changed')
            if x['target_binding']!=model.bind_span(raw,spans,x['target'],prior['target_source_start']):raise ValueError('Target binding changed')
            checked['target']+=1
            if len(x['basis_bindings'])!=len(x['basis_quotes']):raise ValueError('Interpretation basis count changed')
            for quote,bound in zip(x['basis_quotes'],x['basis_bindings']):
                if current['body'].count(quote)!=1 or bound!=model.bind_span(raw,spans,quote):raise ValueError('Interpretation basis changed')
                checked['basis']+=1
            aux=x['construction']['auxiliary'];want=None if aux is None else model.bind_span(raw,spans,aux,a['source_start']+a['source_text'].index(aux))
            if x['auxiliary_binding']!=want:raise ValueError('Auxiliary binding changed')
            checked['auxiliary']+=aux is not None
            if len(x['marker_bindings'])!=len(x['construction']['markers']):raise ValueError('Marker membership changed')
            for marker,bound in zip(x['construction']['markers'],x['marker_bindings']):
                expected=dict(role=marker['role'],**model.bind_span(raw,spans,marker['text'],a['source_start']+marker['anchor_start']))
                if bound!=expected:raise ValueError('Marker binding changed')
                checked['marker']+=1
            if len(x['quantity_bindings'])!=len(x['quantification']['expressions']):raise ValueError('Quantity membership changed')
            for expression,bound in zip(x['quantification']['expressions'],x['quantity_bindings']):
                if bound!=model.bind_span(raw,spans,expression,a['source_start']+a['source_text'].index(expression)):raise ValueError('Measurement expression changed')
                checked['quantity']+=1
            if any(x[k]is not False for k in ('independent_semantic_review','world_facts_verified','rag_integration','training_pool_import')):raise ValueError('Model pilot status inflated')
            checked['semantic_axes']+=len(x['semantic_axes'])
    with (directory/'selected_readings.tsv').open(encoding='utf-8-sig',newline='')as f:flat=list(csv.DictReader(f,delimiter='\t'))
    if len(flat)!=len(records):raise ValueError('TSV coverage changed')
    for x,row in zip(records,flat):
        form=x['form_analyses'][x['source_selected_analysis']]
        expected=dict(example_id=x['example_id'],language=x['language'],target=x['target'],state=x['state'],analysis_count=str(len(x['form_analyses'])),source_selected_lemma=form['lemma'],source_selected_aspect=form['aspect'],target_morphological_tense=form['morphological_tense'],source_selected_grammatical_tense=form['grammatical_tense'],construction_tense=x['construction']['tense'],event_time=x['event_time'],measurement_object=x['quantification']['kind'],independent_semantic_review='False')
        expected.update({k:v['value']for k,v in x['semantic_axes'].items()})
        if row!=expected:raise ValueError('TSV selected reading changed')
    return dict(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),manifest_sha256=rag.fsh(directory/'manifest.json'),records=len(records),verified_files=len(m['files']),bindings=dict(checked),selected_reading_rows=len(flat),all_source_cautions_preserved=True,independent_semantic_review=False,not_semantic_accuracy_measurement=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('directory','input','prior-pilot','index','candidate','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError('Immutable audit output')
    result=audit(a.directory,a.input,a.prior_pilot,a.index,a.candidate);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(result,ensure_ascii=False,indent=2))
