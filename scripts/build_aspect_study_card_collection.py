"""Freeze model cards as a source-pinned, explicitly scoped research sidecar."""
from pathlib import Path
from collections import Counter
import argparse,datetime,json,shutil
import aspect_study_cards as cli
import audit_aspect_study_cards as audit

WORK=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference'
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def build(output,cards_dir=WORK/'study_cards',report_path=WORK/'reviews/study_card_verification_20261022_001.json',candidate=audit.PINNED):
    output=Path(output)
    if output.exists():raise FileExistsError('Research collections are immutable')
    report_path=Path(report_path);cards_dir=Path(cards_dir);candidate=Path(candidate);report=cli.read(report_path)
    if report['candidate_manifest_sha256']!=cli.sha(candidate/'manifest.json'):raise ValueError('Audit candidate mismatch')
    if report['remaining']or report['card_count']!=100:raise ValueError('Reading coverage incomplete')
    cards=[]
    for name,pin in report['batch_pins'].items():
        path=cards_dir/name
        if cli.sha(path)!=pin:raise ValueError('Study batch changed after audit')
        cards.extend(cli.read(path)['cards'])
    if len(cards)!=100 or len({x['code']for x in cards})!=100:raise ValueError('Duplicate card')
    output.mkdir(parents=True)
    (output/'cards.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n'for x in cards),'utf8')
    claims=[dict(code=c['code'],title=c['title'],state=c['state'],claim_number=i,content_kind='model_paraphrase_with_original_quote',**x)for c in cards for i,x in enumerate(c['claims'],1)]
    (output/'claims.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n'for x in claims),'utf8')
    shutil.copy2(report_path,output/'source_verification.json');shutil.copy2(Path(cli.__file__),output/'aspect_study_cards.py')
    dump(output/'source_pins.json',dict(candidate_edition=candidate.name,candidate_manifest_sha256=cli.sha(candidate/'manifest.json'),original_db_sha256=cli.read(candidate/'manifest.json')['source_db_sha256'],batch_pins=report['batch_pins'],source_audit_sha256=cli.sha(report_path)))
    lines=['# 现代俄语体学学习卡目录','','模型摘要与原书逐字引句分层。全100节均有卡；9节隔离仅归档，不能由查询入口返回。原页列仅为卡内引句覆盖，非整节页范围。','','|来源节|状态|引句主张数|引句PDF页|','|---|---|---:|---|']
    for c in cards:
        pages=sorted({p['pdf_page']for x in c['claims']for p in x['page_evidence']})
        lines.append('|'+c['code']+' '+c['title']+'|'+c['state']+'|'+str(len(c['claims']))+'|'+','.join(map(str,pages))+'|')
    (output/'catalog.md').write_text('\n'.join(lines)+'\n','utf8')
    (output/'README.md').write_text('''# 现代俄语体学：模型学习卡研究附层

100理论单元、350条来源主张、29个不可变批次。每条模型中文归纳与未改变的原书连续引句分开保存，附原节偏移、PDF页/印刷页和页图审核指纹。

这是同一助手逐节阅读形成的研究导航，未独立专家盲评，未作350条语义准确率测量，也不声称穷尽所有内容。学习卡、提示题和原书正文不可混作同一种语料。提示题不是独立测试集。

固定来源为aspect_editorial_candidate_20261022_005：40原ready卡/119主张，51模型候选卡/195主张，9隔离卡/36主张。JSONL为完整研究归档，包含明确标记的隔离卡。默认入口仅返回40原ready；显式--include-candidates后可返回91卡，隔离任何查询模式均不返回。未接入RAG排序或生成、学生训练池。

引句覆盖266个PDF页的并集，仅表示350条引句的位置，不能说全书只有266页或全页均经独立语义验证。原印481页PDF、已审核471来源页等口径见主知识库。

本目录可用标准Python离线查询及检查指纹：

    python aspect_study_cards.py verify
    python aspect_study_cards.py show --code aspect.ch11.s01.03 --include-candidates

引用论文时应回到原书对应印刷页；模型归纳只能标作本研究的阅读笔记。后续编校版本的兼容性须另有报告，不覆盖这版卡片的来源指纹和原有待核说明。
''','utf8')
    counts=Counter(c['state']for c in cards);claim_counts=Counter(x['state']for x in claims)
    rp=output/'README.md';body=rp.read_text('utf8')
    body=body.replace('100理论单元、350条来源主张、29个不可变批次。',f"{len(cards)}理论单元、{len(claims)}条来源主张、{report['batch_files']}个不可变批次。")
    body=body.replace('固定来源为aspect_editorial_candidate_20261022_005：40原ready卡/119主张，51模型候选卡/195主张，9隔离卡/36主张。',f"固定来源为{candidate.name}：{counts['original_source_ready']}原ready卡/{claim_counts['original_source_ready']}主张，{counts['model_editorial_candidate']}模型候选卡/{claim_counts['model_editorial_candidate']}主张，{counts['withheld']}隔离卡/{claim_counts['withheld']}主张。")
    body=body.replace('显式--include-candidates后可返回91卡',f"显式--include-candidates后可返回{counts['original_source_ready']+counts['model_editorial_candidate']}卡")
    body=body.replace('9节隔离仅归档',f"{counts['withheld']}节隔离仅归档")
    rp.write_text(body,'utf8')
    catalog=output/'catalog.md';body=catalog.read_text('utf8').replace('9节隔离仅归档',f"{counts['withheld']}节隔离仅归档");catalog.write_text(body,'utf8')
    m=dict(schema_version=1,edition=output.name,created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),content_kind='model_study_cards_not_original_text',source_candidate_edition=candidate.name,source_candidate_manifest_sha256=cli.sha(candidate/'manifest.json'),card_count=len(cards),claim_count=len(claims),cards_by_state=dict(counts),claims_by_state=dict(claim_counts),independent_semantic_review=False,rag_integration=False,files={p.name:cli.sha(p)for p in output.iterdir()if p.is_file()})
    dump(output/'manifest.json',m);cli.verify(output);return {k:v for k,v in m.items()if k!='files'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=WORK/'research_exports/aspect_study_cards_20261022_001');p.add_argument('--cards',type=Path,default=WORK/'study_cards');p.add_argument('--verification',type=Path,default=WORK/'reviews/study_card_verification_20261022_001.json');p.add_argument('--candidate',type=Path,default=audit.PINNED);a=p.parse_args();print(json.dumps(build(a.output,a.cards,a.verification,a.candidate),ensure_ascii=False,indent=2))
