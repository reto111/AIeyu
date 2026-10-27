"""Audit immutable predecessor links and the newest pin for each research file."""
import argparse,hashlib,json
from pathlib import Path

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify(workspace,work):
    workspace=workspace.resolve();work=work.resolve();cp=json.loads((work/'checkpoint.json').read_text('utf8'));path=(work/cp['delivery_addendum']).resolve()
    if not path.is_relative_to(work)or sha(path)!=cp['delivery_addendum_sha256']:raise ValueError('Checkpoint head mismatch')
    byhash={sha(p):p for p in work.glob('delivery_addendum_*.json')};seen=set();pins={};chain=[];historical=0;superseded=0
    while path is not None:
        if path.name in seen:raise ValueError('Repeated predecessor')
        seen.add(path.name);d=json.loads(path.read_text('utf8'));chain.append(dict(path=path.name,sha256=sha(path),file_pins=len(d.get('files',{}))))
        for relative,h in d.get('files',{}).items():
            target=(workspace/relative).resolve()
            if not target.is_relative_to(workspace)or not isinstance(h,str):raise ValueError('Invalid historical file pin')
            historical+=1;name=target.relative_to(workspace).as_posix()
            if name not in pins:pins[name]=dict(sha256=h,latest_pin_file=path.name)
            elif pins[name]['sha256']!=h:superseded+=1
        oldhash=d.get('previous_addendum_sha256')
        if oldhash:
            previous=byhash.get(oldhash)
            if previous is None:raise ValueError('Unresolved predecessor hash')
            if d.get('previous_addendum')and previous.name!=Path(d['previous_addendum']).name:raise ValueError('Predecessor name/hash mismatch')
            path=previous
        else:path=None
    for name,pin in pins.items():
        target=workspace/name
        if not target.is_file()or sha(target)!=pin['sha256']:raise ValueError('Current file differs from latest pin: '+name)
    return dict(checkpoint_head=cp['delivery_addendum'],checkpoint_head_sha256=cp['delivery_addendum_sha256'],chain_nodes=len(chain),chain=chain,current_pinned_files=len(pins),current_file_pins=pins,historical_file_pin_records=historical,superseded_historical_version_records=superseded,all_predecessor_hashes_resolved=True,all_current_latest_pins_matched=True,interpretation_zh='由当前指针沿可解析前驱追到本链起点；同路径较旧版本按较新固定记录解释，不要求历史版本等于当前版本。只验证链与文件一致，不认证语义或所有项目文件。')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args();result=verify(a.workspace,a.work)
    if a.output:
        if a.output.exists():raise FileExistsError('Immutable chain report')
        a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({k:v for k,v in result.items()if k not in ['chain','current_file_pins']},ensure_ascii=False))
