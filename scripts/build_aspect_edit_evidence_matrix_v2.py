"""Describe evidence relations per frozen editorial edit; no correctness scoring."""
from pathlib import Path
from collections import Counter
from contextlib import closing
import argparse,csv,io,json
import build_aspect_example_index as source

WORK=source.WORK
CANDIDATE=WORK/'research_exports/aspect_editorial_candidate_20261023_002'
LABELS={
 'source_text_or_attribution':'外部原作字形或作者归属支持',
 'same_author_later_attribution':'同一作者后续原刊归属支持',
 'model_translation_external_context':'依据外部语境的模型中文改译',
 'model_theory_external_argument':'依据外部论述的模型理论推导',
 'model_internal_or_language':'书内对应或语言判断；无逐编辑外证',
}
# This is a declared model reading of evidence scope, not an inferred hierarchy.
DIRECT='006 034 010 096 028 057 061 078 085 075 088 091 094 095 102 121 110 012 064 005 087 112 089 098 099 003 104'.split()
POLICY={f'AS-TI-{n}':'source_text_or_attribution'for n in DIRECT}
POLICY.update({f'AS-NEW-{n}':'source_text_or_attribution'for n in ('001','003','005','009')})
POLICY.update({f'AS-TI-{n}':'same_author_later_attribution'for n in ('018','038')})
POLICY.update({f'AS-TI-{n}':'model_translation_external_context'for n in ('055','041','119','045')})
POLICY['AS-NEW-008']='model_translation_external_context'
POLICY['AS-TI-029']='model_theory_external_argument'
OVERRIDES={('AS-TI-006',1):'model_internal_or_language',('AS-TI-099',2):'model_translation_external_context',('AS-TI-099',3):'model_translation_external_context'}

LABELS['dictionary_orthography_or_lexeme']='词典拼写/词干支持；词尾及语境仍模型判读'
for n in ('006','007','020','021','033','035','042','059','092','124'):
 if n!='006':POLICY['AS-TI-'+n]='dictionary_orthography_or_lexeme'
POLICY['AS-TI-071']='source_text_or_attribution'
POLICY['AS-NEW-010']='source_text_or_attribution'
OVERRIDES['AS-TI-006',1]='dictionary_orthography_or_lexeme'

def prepare(candidate=CANDIDATE):
 candidate=Path(candidate).resolve();manifest=source.verify_candidate(candidate)
 if source.fsh(candidate/'manifest.json')!='c47859f1c09499149dfdda97ad65f1ab10595b086e75487f3135682a46595404':raise ValueError('This scope policy is frozen to the 93-section edition')
 plan=source.read(candidate/'editorial_plan_20261023_004.json')
 external=source.read(candidate/'source_manifest_20261023_002.json');by_id={s['id']:s for s in external['sources']}
 linked={p['issue_id']for p in plan['proposals']if p.get('external_evidence')}
 if linked!=set(POLICY):raise ValueError('Unclassified or obsolete externally linked proposal')
 rows=[];seen=set()
 with closing(source.connect(candidate/'aspect_reference.sqlite'))as c:
  for p in plan['proposals']:
   unit=c.execute('select * from chunks where code=?',(p['code'],)).fetchone()
   section=c.execute('select * from aspect_candidate_sections where code=?',(p['code'],)).fetchone()
   if source.tsh(unit['body'])!=p['source_body_sha256']:raise ValueError('Source unit changed')
   spans=source.bindings(c,unit)
   for n,edit in enumerate(p['edits'],1):
    key=(p['issue_id'],n)
    if key in seen:raise ValueError('Duplicate edit')
    seen.add(key);lo=edit['start'];hi=lo+len(edit['old'])
    if unit['body'][lo:hi]!=edit['old']:raise ValueError('Edit no longer matches source')
    relation=OVERRIDES.get(key,POLICY.get(p['issue_id'],'model_internal_or_language'))
    proposal_ids=p.get('external_evidence',[])
    used_ids=[] if relation=='model_internal_or_language'else list(proposal_ids)
    # Panova context explains retention of another subissue, not this Gorbatov edit.
    if p['issue_id']=='AS-TI-110':used_ids=['AS-EXT-014']
    if relation=='dictionary_orthography_or_lexeme':used_ids=['AS-EXT-030']
    if p['issue_id']=='AS-TI-071':used_ids=['AS-EXT-020']
    if any(i not in by_id for i in used_ids):raise ValueError('Unknown external source')
    pages=source.pages_for(spans,lo,hi)
    if not pages:raise ValueError('Missing textbook page binding')
    rows.append(dict(issue_id=p['issue_id'],edit_index=n,code=p['code'],state=section['state'],eligible_with_candidates=section['state']!='withheld',source_start=lo,source_end=hi,old=edit['old'],new=edit['new'],source_unit_sha256=p['source_body_sha256'],page_evidence=pages,evidence_relation=relation,evidence_label_zh=LABELS[relation],proposal_source_ids=proposal_ids,edit_relevant_source_ids=used_ids,external_sources=[{k:by_id[i].get(k)for k in ('id','url','locator','review_method','scope','cache_sha256','render_sha256')}for i in used_ids],rationale=p['rationale'],model_scope_classification=True,independent_correctness_assessed=False))
 if len(rows)!=plan['edit_count']:raise ValueError('Incomplete edit coverage')
 counts=Counter(x['evidence_relation']for x in rows)
 states={state:dict(Counter(x['evidence_relation']for x in rows if x['state']==state))for state in sorted({x['state']for x in rows})}
 return dict(schema_version=1,candidate_manifest_sha256=source.fsh(candidate/'manifest.json'),plan_sha256=manifest['plan_sha256'],external_manifest_sha256=source.fsh(candidate/'source_manifest_20261023_002.json'),builder_sha256=source.fsh(Path(__file__)),proposal_count=plan['proposal_count'],edit_count=len(rows),proposals_with_source_links=len(linked),edits_in_source_linked_proposals=sum(bool(x['proposal_source_ids'])for x in rows),edits_with_relevant_external_source=sum(bool(x['edit_relevant_source_ids'])for x in rows),counts_by_evidence_relation=dict(counts),counts_by_state=states,relation_labels_zh=LABELS,records=rows,limitations=['关系分类由同一助手据既有证据说明逐项判读，不是独立专家裁定或错误率。','附链接、原作逐字存在、作者归属、中文改译和理论推导不能互相替代。','source_text_or_attribution包括电子转录及排印版，不等同全部核过原版纸本；逐条保留review_method和scope。','无逐编辑外证不等于修改错误；有外证也不证明所有解释正确。','隔离节中的编辑仅归档，证据分类不改变7节隔离及任何检索入口。'])

def write(output,candidate=CANDIDATE):
 output=Path(output)
 paths=[output,output.with_suffix('.tsv'),output.with_suffix('.md')]
 if any(p.exists()for p in paths):raise FileExistsError('Evidence matrix is immutable')
 r=prepare(candidate)
 output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
 stream=io.StringIO(newline='');fields=['issue_id','edit_index','code','state','pdf_pages','evidence_relation','edit_relevant_source_ids','old','new']
 writer=csv.DictWriter(stream,fields,delimiter='\t');writer.writeheader()
 for x in r['records']:
  row={k:x[k]for k in fields if k not in ('pdf_pages','edit_relevant_source_ids')};row.update(pdf_pages=','.join(str(p['pdf_page'])for p in x['page_evidence']),edit_relevant_source_ids=','.join(x['edit_relevant_source_ids']));writer.writerow(row)
 paths[1].write_text(stream.getvalue(),'utf8',newline='')
 lines=['# 逐编辑证据关系清单','','覆盖119提案128编辑；各关系为模型审核记录，不是独立正确率。当前93节候选与7节隔离不变。','','|证据关系|编辑数|','|---|---:|']
 lines += [f'|{LABELS[k]}|{v}|'for k,v in r['counts_by_evidence_relation'].items()]
 lines += ['',f"50条提案附外证，共含{r['edits_in_source_linked_proposals']}编辑；逐编辑实际关联外证{r['edits_with_relevant_external_source']}处。AS-TI-006的отворилось不沿用同提案陀思妥耶夫斯基署名证据；AS-TI-099俄文人名与两处中文改译分列；AS-TI-110的Панова保留语境不作为Горбатов署名证据。",'','JSON保留旧值/新值、源偏移、PDF/印刷页、证据地址、读取方法和范围；TSV可逐行检查。','','']+r['limitations']
 paths[2].write_text('\n'.join(lines)+'\n','utf8')
 return {k:v for k,v in r.items()if k not in ('records','limitations','relation_labels_zh')}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(write(a.output),ensure_ascii=False,indent=2))
