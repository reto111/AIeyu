"""Offline comparison of pending human annotations; no model gold labels."""
from pathlib import Path
from collections import Counter
import argparse,csv,hashlib,json,datetime

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))

def nominal_agreement(left,right):
    """Cohen's unweighted kappa on pairs with both categorical values present."""
    if len(left)!=len(right):raise ValueError('Different annotation lengths')
    pairs=[(a,b)for a,b in zip(left,right)if a and b];n=len(pairs)
    if not n:return dict(paired=0,agreement=None,expected_agreement=None,kappa=None,undefined_reason='no_paired_annotations',left_labels={},right_labels={})
    a=Counter(x for x,_ in pairs);b=Counter(y for _,y in pairs);agree=sum(x==y for x,y in pairs)/n;expected=sum(a[k]*b[k]for k in a.keys()|b.keys())/(n*n)
    # Exact integer arithmetic decides the degenerate marginal case.
    constant=sum(a[k]*b[k]for k in a.keys()|b.keys())==n*n
    return dict(paired=n,agreement=agree,expected_agreement=expected,kappa=None if constant else(agree-expected)/(1-expected),undefined_reason='no_marginal_variation'if constant else None,left_labels=dict(a),right_labels=dict(b))

def verify_packet(directory):
    m=read(directory/'manifest.json')
    if m['content_kind']!='pending_source_informed_human_review_not_gold':raise ValueError('Wrong packet kind')
    for name,pin in m['files'].items():
        p=(directory/name).resolve()
        if p.parent!=directory.resolve()or sha(p)!=pin:raise ValueError('Review packet changed')
    contexts=[json.loads(x)for x in (directory/'source_contexts.jsonl').read_text('utf8').splitlines()]
    if len(contexts)!=m['item_count']or len({x['review_id']for x in contexts})!=len(contexts):raise ValueError('Packet membership changed')
    return m,contexts,read(directory/'codebook.json')

def read_annotations(path,ids,codebook):
    with Path(path).open(encoding='utf-8-sig',newline='')as f:
        reader=csv.DictReader(f);rows=list(reader)
        if reader.fieldnames!=['review_id']+list(codebook['fields'])+['notes_zh']:raise ValueError('Annotation columns changed')
    if len(rows)!=len(ids)or {r['review_id']for r in rows}!=set(ids):raise ValueError('Missing, duplicate or foreign review ID')
    result={}
    for r in rows:
        if None in r or None in r.values():raise ValueError('Malformed CSV row')
        for key,definition in codebook['fields'].items():
            r[key]=r[key].strip()
            if r[key]and r[key]not in definition['values']:raise ValueError('Unrecognized annotation label: '+key)
            if r[key]=='other'and not r['notes_zh'].strip():raise ValueError('Other requires a note')
        result[r['review_id']]=r
    return result

def compare(directory,left_path,right_path,left_reviewer,right_reviewer):
    if not left_reviewer.strip()or not right_reviewer.strip()or left_reviewer.strip()==right_reviewer.strip():raise ValueError('Distinct declared reviewer IDs are required')
    m,contexts,codebook=verify_packet(directory);ids=[x['review_id']for x in contexts];a=read_annotations(left_path,ids,codebook);b=read_annotations(right_path,ids,codebook);fields={}
    for field in codebook['fields']:
        left=[a[i][field]for i in ids];right=[b[i][field]for i in ids];score=nominal_agreement(left,right)
        score.update(left_filled=sum(bool(x)for x in left),right_filled=sum(bool(x)for x in right),left_blank=sum(not x for x in left),right_blank=sum(not x for x in right),left_unknown=sum(x=='unknown'for x in left),right_unknown=sum(x=='unknown'for x in right),paired_ids=[i for i in ids if a[i][field]and b[i][field]],disagreements=[dict(review_id=i,left=a[i][field],right=b[i][field])for i in ids if a[i][field]and b[i][field]and a[i][field]!=b[i][field]])
        fields[field]=score
    any_pairs=any(x['paired']for x in fields.values())
    return dict(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),packet_manifest_sha256=sha(directory/'manifest.json'),left_csv_sha256=sha(left_path),right_csv_sha256=sha(right_path),declared_reviewers=[left_reviewer,right_reviewer],status='paired_annotations_available'if any_pairs else'no_paired_annotations',item_count=len(ids),fields=fields,reviewer_identity_verified=False,independence_verified=False,model_gold_used=False,semantic_accuracy_assessed=False,limitations=['只比较相同目标上双方均填写的名义类别；逐字段报告缺标和分母，不把空白当一致。','unknown是明确的不确定标签，计入类别；与未填写不同。','Kappa在单一边际分布时未定义，不能用1替代。','声明两个不同ID不能证明两位独立人员；高一致率也不证明标签正确。',f'{len(ids)}项为教材开发试样，不估计自然语料分布或正式研究准确率。'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--packet',type=Path,required=True);p.add_argument('--left',type=Path,required=True);p.add_argument('--right',type=Path,required=True);p.add_argument('--left-reviewer',required=True);p.add_argument('--right-reviewer',required=True);p.add_argument('--output',type=Path);a=p.parse_args()
    if a.output and a.output.exists():raise FileExistsError('Comparison reports are immutable')
    result=compare(a.packet,a.left,a.right,a.left_reviewer,a.right_reviewer)
    if a.output:a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
