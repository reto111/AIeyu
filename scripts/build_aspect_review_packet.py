"""Prepare blank model-masked review materials, without filling annotations."""
from pathlib import Path
import argparse,csv,datetime,json,shutil
import aspect_candidate_rag as rag
from build_aspect_annotation_pilot_v2 import AXES

def build(pilot,output,index=None,candidate=None,extents=None):
    if output.exists():raise FileExistsError('Review packets are immutable')
    m=rag.read(pilot/'manifest.json')
    for name,pin in m['files'].items():
        if rag.fsh(pilot/name)!=pin:raise ValueError('Pilot changed')
    rows=[json.loads(x)for x in (pilot/'annotations.jsonl').read_text('utf8').splitlines()];contexts=[]
    for x in rows:
        if x['state']=='withheld':raise ValueError('Withheld target cannot enter review packet')
        rid='ASR-'+rag.tsh(x['example_id']+'|'+str(x['target_binding']['source_start']))[:12]
        contexts.append(dict(review_id=rid,source_unit=x['source_unit'],source_state=x['state'],target=x['target'],language=x['language'],source_anchor=x['source_text'],candidate_anchor=x['candidate_text'],candidate_context=x.get('candidate_context'),target_binding=x['target_binding'],source_unit_sha256=x['source_unit_sha256'],candidate_unit_sha256=x['candidate_unit_sha256'],external_source_cautions=x['external_source_cautions']))
    # The v2 keeps exact source anchors; its context is obtained from its pinned
    # index, not regenerated or silently replaced with a later edition.
    root=Path(__file__).resolve().parents[1];work=root/'data/processed/aspect_reference';idx=Path(index)if index is not None else work/'research_exports/aspect_numbered_examples_20261022_005';candidate=Path(candidate)if candidate is not None else work/'research_exports/aspect_editorial_candidate_20261022_007'
    if rag.fsh(idx/'manifest.json')!=m['source_pins']['index_manifest_sha256']or rag.fsh(candidate/'manifest.json')!=m['source_pins']['candidate_manifest_sha256']:raise ValueError('Pinned source edition mismatch')
    anchors={x['example_id']:x for x in map(json.loads,(idx/'examples.jsonl').read_text('utf8').splitlines())}
    for source,original in zip(contexts,rows):
        anchor=anchors[original['example_id']]
        if anchor['source_unit']!=source['source_unit']or anchor['source_text']!=source['source_anchor']:raise ValueError('Review source changed')
        source['candidate_context']=anchor['candidate_context']
    extent_pin=None
    if extents is not None:
        from build_aspect_example_extents import materialize_extents,verified_files
        extents=Path(extents);verified_files(extents)
        rebuilt,_=materialize_extents(candidate,idx,pilot,extents/'boundary_review.json')
        saved=[json.loads(line)for line in (extents/'extents.jsonl').read_text('utf8').splitlines()]
        if rebuilt!=saved:raise ValueError('Extent source replay mismatch')
        full={x['example_id']:x for x in rebuilt};extent_pin=rag.fsh(extents/'manifest.json')
        for source,original in zip(contexts,rows):
            x=full[original['example_id']]
            source.update(complete_source_example=x['source_text'],complete_candidate_example=x['candidate_text'],complete_example_source_start=x['source_start'],complete_example_source_end=x['source_end'],complete_example_page_evidence=x['page_evidence'],boundary_review='same_assistant_visual_not_independent',boundary_note_zh=x['boundary_reason_zh'],layout_note_zh=x['layout_note_zh'])
    contexts.sort(key=lambda x:rag.tsh('review-order-v1|'+x['review_id']))
    fields={k:dict(values=sorted(values|({'unknown','other'}if k=='discourse_status'else set())),definition_zh={'discourse_status':'目标在话语中的断言、预设、提问、指令、许可、情态等地位；unknown允许未决，other须注释。','event_realization':'片段是否呈现为已发生；泛指和实际个例分开，仅指教材话语内部。','lexical_goal_attainment':'词汇所指目标结果是否被源文确立；不自动由完成体推断。','reference_result_state':'参照时结果状态是否保持、明确取消，或未知/不适用。','consequence_relevance':'行为后果是否被源文作为当前讨论相关信息；与物理状态保持分别判断。'}[k])for k,values in AXES.items()}
    fields['context_sufficiency']=dict(values=['enough','need_full_unit','undecidable'],definition_zh='当前窗口是否足够判读；需要完整源节时标need_full_unit，不用猜测填满其他字段。')
    codebook=dict(schema_version=1,fields=fields,blank_means='尚未标注，不等于unknown或not_applicable。',review_is_source_informed=True,model_labels_masked=True,author_explanations_may_occur_in_context=True,cross_axis_model_constraints_enforced=False,reason='允许复核者批评模型分类及约束，不用模型预期强行修正人的分歧。')
    output.mkdir(parents=True)
    (output/'source_contexts.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n'for x in contexts),'utf8')
    (output/'codebook.json').write_text(json.dumps(codebook,ensure_ascii=False,indent=2)+'\n','utf8')
    for name,order in [('review_A_blank.csv',contexts),('review_B_blank.csv',list(reversed(contexts)))]:
        with (output/name).open('w',encoding='utf-8-sig',newline='')as f:
            writer=csv.DictWriter(f,fieldnames=['review_id']+list(fields)+['notes_zh']);writer.writeheader()
            for row in order:writer.writerow({'review_id':row['review_id']})
    shutil.copyfile(root/'scripts/aspect_annotation_agreement.py',output/'aspect_annotation_agreement.py')
    (output/'README.md').write_text('''# 体学22目标复核空表

这是一份待填写的研究材料：22个既有教材目标，模型词形分析、作者选定项及全部模型语义标签已遮蔽。原文、编校候选、邻近语境、目标页绑定及文学异文警示保留。上下文本身可能含作者解释，因此只对模型标签遮蔽，不是对作者观点盲评，也不是随机自然语料样本。没有任何独立标注已完成。

两位复核者各复制一份空CSV，按review_id查source_contexts.jsonl；A、B顺序相反，目标集合相同。不要相互查看标签；疑点写notes_zh，语境不足填need_full_unit，必要时查完整源节与原PDF页。未知填unknown，不适用填not_applicable，尚未判断留空。若模型标签集不适用，discourse_status可填other并说明。不要用最终裁决覆盖两份原始独立记录，另存裁决表。

标注后可用标准Python运行包内脚本：

    python aspect_annotation_agreement.py --packet . --left A_completed.csv --right B_completed.csv --left-reviewer reviewer_A --right-reviewer reviewer_B --output agreement.json

每字段单列双方填写数、空白、不确定标签数、共同填写分母、原始一致率、名义Cohen kappa和分歧ID。空表应返回no_paired_annotations，kappa为空。相同常数标签的边际分布使kappa未定义，不伪填1。两ID不同不能证明独立，高一致率也不是准确率；没有标准答案或模型金标参与评分。源状态仍仅为原ready或模型候选，专家标签不会自动入RAG或学生池。
''','utf8')
    if extent_pin is not None:
        with (output/'README.md').open('a',encoding='utf8')as f:
            f.write('\n本版另附complete_source_example与complete_candidate_example：22例经同一助手19页核图确认边界，例(15)含完整俄文回答及两段译文；跨页例(7)含PDF51–52。边界不是独立金标；作者解释仍可能存在于另列candidate_context中。完整例与邻近语境分别使用，不能把邻例或作者分析当作本例话语。模型语义标签和依据选择未附入复核材料。\n')
    result=dict(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),content_kind='pending_source_informed_human_review_not_gold',item_count=len(contexts),fields=list(fields),model_labels_included=False,annotations_filled=0,independent_review_completed=False,pilot_manifest_sha256=rag.fsh(pilot/'manifest.json'),index_manifest_sha256=rag.fsh(idx/'manifest.json'),candidate_manifest_sha256=rag.fsh(candidate/'manifest.json'),builder_sha256=rag.fsh(Path(__file__)),files={p.name:rag.fsh(p)for p in sorted(output.iterdir())if p.is_file()})
    if extent_pin is not None:result['extent_manifest_sha256']=extent_pin
    (output/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pilot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--index',type=Path);p.add_argument('--candidate',type=Path);p.add_argument('--extents',type=Path);a=p.parse_args();print(json.dumps(build(a.pilot,a.output,a.index,a.candidate,a.extents),ensure_ascii=False,indent=2))
