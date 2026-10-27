"""Offline, explicit-unit access to model study cards, kept separate from RAG."""
from pathlib import Path
import argparse,hashlib,json

DEFAULT_DIRECTORY=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference/research_exports/aspect_study_cards_20261023_002'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text('utf8'))
def directory(path=None):
    if path is not None:return Path(path)
    local=Path(__file__).resolve().parent
    return local if (local/'manifest.json').is_file()else DEFAULT_DIRECTORY
def verify(path=None):
    path=directory(path);m=read(path/'manifest.json')
    if m.get('content_kind')!='model_study_cards_not_original_text':raise ValueError('Wrong artifact type')
    for name,pin in m['files'].items():
        target=(path/name).resolve()
        if target.parent!=path.resolve()or sha(target)!=pin:raise ValueError('Collection file fingerprint mismatch: '+name)
    cards=[json.loads(x)for x in (path/'cards.jsonl').read_text('utf8').splitlines()]
    if len(cards)!=m['card_count']or len({c['code']for c in cards})!=len(cards):raise ValueError('Invalid card membership')
    if sum(len(c['claims'])for c in cards)!=m['claim_count']:raise ValueError('Invalid claim count')
    return m,cards
def show(code,include_candidates=False,path=None):
    m,cards=verify(path);card=next((c for c in cards if c['code']==code),None)
    allowed=card is not None and(card['state']=='original_source_ready'or(include_candidates and card['state']=='model_editorial_candidate'))
    return dict(status='available'if allowed else'no_evidence',edition=m['edition'],content_kind=m['content_kind'],source_candidate_edition=m['source_candidate_edition'],independent_semantic_review=False,rag_integration=False,card=card if allowed else None,notice_zh='模型学习卡须与原书正文分开引用。隔离来源不由本入口返回；提示题非独立留出测试集。')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path);s=p.add_subparsers(dest='command',required=True);s.add_parser('verify');q=s.add_parser('show');q.add_argument('--code',required=True);q.add_argument('--include-candidates',action='store_true');a=p.parse_args()
    result={k:v for k,v in verify(a.directory)[0].items()if k!='files'}if a.command=='verify'else show(a.code,a.include_candidates,a.directory)
    print(json.dumps(result,ensure_ascii=False,indent=2))
