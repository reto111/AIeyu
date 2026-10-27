"""Create unfilled source-informed forms for the complete available numbered correspondence layer."""
import argparse,json,csv,shutil
from pathlib import Path
from build_aspect_example_index import fsh,tsh,write

def verified(root):
    m=json.loads((root/'manifest.json').read_text('utf8'))
    for rel,h in m['files'].items():
        p=(root/rel).resolve()
        if p.parent!=root.resolve()or fsh(p)!=h:raise ValueError('Changed source collection')
    return m

def build(parallel,examples,monolingual,output):
    if output.exists():raise FileExistsError('Immutable translation review packet')
    pm=verified(parallel);verified(examples);mm=verified(monolingual)
    if mm['source_pins']['parallel_manifest_sha256']!=fsh(parallel/'manifest.json'):raise ValueError('Monolingual version mismatch')
    if pm['source_pins']['numbered_manifest_sha256']!=fsh(examples/'manifest.json'):raise ValueError('Pair example edition mismatch')
    grouped=list(map(json.loads,(parallel/'groups.jsonl').read_text('utf8').splitlines()));pairs=[dict(example_id=g['example_id'],source_unit=g['source_unit'],state=g['state'],**p)for g in grouped for p in g['pairs']];groups={r['example_id']:r for r in map(json.loads,(examples/'examples.jsonl').read_text('utf8').splitlines())};rows=[]
    for p in pairs:
        if p['state']=='withheld':raise ValueError('Withheld pair cannot enter a review packet')
        g=groups[p['example_id']]
        if p['source_unit']!=g['source_unit']or p['state']!=g['state']:raise ValueError('Changed pair provenance')
        row=dict(review_id='AST-'+tsh(p['pair_id'])[:12],pair_id=p['pair_id'],example_id=p['example_id'],source_unit=p['source_unit'],source_state=p['state'],assessed_text_layer='candidate_text',source_group=g['source_text'],candidate_group=g['candidate_text'],group_page_evidence=g['page_evidence'])
        for language in ['ru','zh']:
            part=p[language];lo=part['source_start']-g['source_start'];hi=part['source_end']-g['source_start']
            if not 0<=lo<hi<=len(g['source_text'])or g['source_text'][lo:hi]!=part['source_text']:raise ValueError('Pair outside archived group')
            row[language]={k:part[k]for k in ['source_start','source_end','source_text','candidate_text','page_evidence']}
        rows.append(row)
    if len({r['review_id']for r in rows})!=len(rows):raise ValueError('Duplicate review ID')
    rows.sort(key=lambda r:tsh('translation-review-order-v1|'+r['review_id']))
    fields=dict(pair_boundary=dict(values=['adequate','needs_split','needs_merge','not_a_pair','unknown'],definition_zh='针对所示俄汉范围判断整例对应边界；多句整例不自动判错，需拆分/合并应说明范围。'),translation_adequacy=dict(values=['adequate','partial','meaning_mismatch','not_judgeable','unknown'],definition_zh='评价candidate_text的现成教材译文是否传达所示俄文在该例中的意义；不要求形态逐项直译。无法判断与未知分别保留。'),context_sufficiency=dict(values=['enough','need_full_unit','undecidable'],definition_zh='所示例组是否足够判断；不足请查完整源节及原页，勿以章题推测填满。'))
    codebook=dict(schema_version=1,fields=fields,blank_means='尚未标注，不等于unknown或not_judgeable。',assessed_text_layer='candidate_text',review_is_source_informed=True,model_labels_masked=True,author_explanations_may_occur_in_context=True,source_transcription_visible=True)
    output.mkdir(parents=True);(output/'source_contexts.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in rows),'utf8');write(output/'codebook.json',codebook)
    for name,order in [('review_A_blank.csv',rows),('review_B_blank.csv',list(reversed(rows)))]:
        with(output/name).open('w',encoding='utf-8-sig',newline='')as stream:
            w=csv.DictWriter(stream,fieldnames=['review_id',*fields,'notes_zh']);w.writeheader()
            for r in order:w.writerow(dict(review_id=r['review_id']))
    shutil.copy2(Path(__file__).with_name('aspect_annotation_agreement.py'),output/'aspect_annotation_agreement.py')
    (output/'README.md').write_text(f'''# 俄汉整例对应：待独立复核

{len(rows)}组现成教材对应，绑定{examples.name}及{parallel.name}；{mm['statistics']['reviewed_groups']}个已核编号单语组未进入本译对评价；117隔离组不进入。全部1304双语例组的1335个组成部分对应在本包内，不按句子拆分，也不与旧22目标或行内空包相加计独立样本。评价对象统一为candidate_text，原转录、原例组、原始范围与页证据一并可见；不让两位复核者分别评价不同版本。

两份CSV共{len(rows)*len(fields)*2}个分类格全部为空。评阅者判断整例范围、翻译充分性与语境充分性，模型评价标签、元数据角色判断、单位级警示与编校理由未随包提供；正文中的原印比较提示、尖括号语境与署名保留。俄文内可能有原印“试比较”提示，两处汉语在前的例证仍按实际范围显示。原书星号、问号、改写、署名及比较形式可见，不声称对作者观点或材料来源盲评。例组由同一助手定向圈定，非随机自然平行语料；重复与多句例不自动删除。

各自复制A、B表，按review_id查source_contexts.jsonl，独立填写、记录人员和日期。需要全节时填need_full_unit，原PDF未附，返回原项目查对应页。空白是未做，unknown是明确未决。修改范围或认为不是译对应写notes_zh；分歧裁决另存，不能覆写独立原表。

python -X utf8 aspect_annotation_agreement.py --packet . --left A_completed.csv --right B_completed.csv --left-reviewer reviewer_A --right-reviewer reviewer_B --output agreement.json

空表运行应为no_paired_annotations、逐字段共同填写0、一致率与κ为空。已声明不同ID不证明实际独立，高一致率不等于翻译正确率。此包没有已完成独立标注，不回写RAG或训练池，也不代替原22目标体意义试标与复核包。
''','utf8')
    m=dict(schema_version=1,content_kind='pending_source_informed_human_review_not_gold',item_count=len(rows),fields=list(fields),annotations_filled=0,independent_review_completed=False,model_labels_included=False,assessed_text_layer='candidate_text',parallel_manifest_sha256=fsh(parallel/'manifest.json'),examples_manifest_sha256=fsh(examples/'manifest.json'),monolingual_manifest_sha256=fsh(monolingual/'manifest.json'),source_group_count=len(grouped),excluded_monolingual_groups=mm['statistics']['reviewed_groups'],files={p.name:fsh(p)for p in sorted(output.iterdir())if p.is_file()});write(output/'manifest.json',m);return m

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parallel',type=Path,required=True);p.add_argument('--examples',type=Path,required=True);p.add_argument('--monolingual',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();m=build(a.parallel,a.examples,a.monolingual,a.output);print(json.dumps(dict(items=m['item_count'],blank_classification_cells=m['item_count']*len(m['fields'])*2,independent_review_completed=False)))
