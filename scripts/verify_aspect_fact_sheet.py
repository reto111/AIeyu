"""Verify thesis figures against pinned local JSON report paths."""
import argparse,json,hashlib
from pathlib import Path

def verify(root,ledger):
    root=root.resolve();d=json.loads(ledger.read_text('utf8'));seen=set();sources={}
    for fact in d['facts']:
        if fact['id']in seen:raise ValueError('Duplicate fact ID')
        seen.add(fact['id']);path=(root/fact['source_path']).resolve()
        if not path.is_relative_to(root):raise ValueError('Fact source escapes research root')
        h=hashlib.sha256(path.read_bytes()).hexdigest()
        if h!=fact['source_sha256']:raise ValueError('Changed report for '+fact['id'])
        sources[path.as_posix()]=h;value=json.loads(path.read_text('utf8'))
        for key in fact['json_path']:value=value[key]
        if value!=fact['value']:raise ValueError('Unsupported fact value: '+fact['id'])
    return dict(verified=True,facts=len(seen),source_files=len(sources),independent_review_certified=False,semantic_accuracy_certified=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--ledger',type=Path,required=True);a=p.parse_args();print(json.dumps(verify(a.root,a.ledger),ensure_ascii=False))
