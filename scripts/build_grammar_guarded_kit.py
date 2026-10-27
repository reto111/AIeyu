"""Export an immutable, local-only grammar research kit; no credentials or API runner."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
from grammar_editorial_rag import DEFAULT_DB, verify_package, sha
from run_grammar_generation_pilot import ROOT, OUT, now, write

DEST = ROOT/'data/processed/grammar_reference/research_exports/guarded_research_20261022_002'
ENTRY = '''"""Local grammar research kit. No network or generation entry points."""
import sys
sys.dont_write_bytecode = True
import argparse, hashlib, json
from pathlib import Path
KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT/'scripts'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify():
    manifest = json.loads((KIT/'manifest.json').read_text(encoding='utf-8'))
    actual = {p.relative_to(KIT).as_posix() for p in KIT.rglob('*')
              if p.is_file() and p.relative_to(KIT).as_posix() != 'manifest.json'}
    if actual != set(manifest['files']):
        raise ValueError('Kit inventory mismatch')
    for rel, expected in manifest['files'].items():
        path = (KIT/rel).resolve()
        if not path.is_relative_to(KIT) or sha(path) != expected:
            raise ValueError('Kit fingerprint mismatch: '+rel)
    return manifest

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['verify','prepare','check','locate'])
    p.add_argument('question', nargs='?')
    p.add_argument('--retriever', choices=['baseline','candidate_v1'], default='baseline')
    p.add_argument('--code')
    p.add_argument('--quote')
    p.add_argument('--packet', type=Path)
    p.add_argument('--response', type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    manifest = verify()
    if a.output and a.output.resolve().is_relative_to(KIT):
        raise ValueError('Save generated artifacts outside the immutable kit')
    from grammar_editorial_guard import prepare, validate_response, verified_database
    db = KIT/'edition/grammar_reference.sqlite'
    verified_database(db)
    if a.command == 'verify':
        result = {'status':'verified','files_verified':len(manifest['files']),
                  'generation_available':False,'edition':manifest['edition']}
    elif a.command == 'prepare':
        if not a.question: p.error('question required')
        result = prepare(a.question, db=db, retriever=a.retriever, code=a.code)
    elif a.command == 'locate':
        if not a.code or not a.quote: p.error('locate requires --code and --quote')
        from grammar_quote_locator import locate
        result = locate(a.code, a.quote, db=db)
    else:
        if not a.question or not a.packet or not a.response:
            p.error('check requires question, --packet and --response')
        packet = json.loads(a.packet.read_text(encoding='utf-8'))
        response = json.loads(a.response.read_text(encoding='utf-8'))
        result = validate_response(packet, response, question=a.question, db=db)
    text = json.dumps(result, ensure_ascii=False, indent=2)+'\\n'
    if a.output:
        with a.output.open('x', encoding='utf-8') as handle: handle.write(text)
    else: print(text, end='')

if __name__ == '__main__': main()
'''

README = '''# 俄语语法本地研究包（2026-10-22）

包含368节编校研究版、可选检索候选、独立证据校验层及已完成的20次实验记录。
1整附表继续隔离，2例仅留原转录归档。原文与编校文字分别保留，不能将编校文字冒称原书逐字原句。
此包没有生成API调用入口，不含.env、密钥、学生库或原PDF。依赖清单在edition/source_code/requirements-research.txt。

在装好依赖的Python环境中运行（引号按所用终端填写）：

    python -I grammar_research.py verify
    python -I grammar_research.py prepare "不定式是否有人称和体的区别？" --retriever candidate_v1 --output ../packet.json
    python -I grammar_research.py check "不定式是否有人称和体的区别？" --packet ../packet.json --response ../response.json
    python -I grammar_research.py locate --code morphology.075 --quote "|四格|同一格|同一格|同一格|" --output ../quote_pages.json

输出须保存到包外；已有输出不覆盖。首次verify会检查包内全部文件及edition子包指纹，不要把输出或缓存放入包内。
--code可显式选择分节；整附表会返回no_evidence。检索是有限词面匹配，candidate_v1只是可选候选，baseline仍为默认。

schema_version=3的包保存原始问题、检索选项、范围判断、来源及提示词；check根据调用者提供的原问题重放全部字段。
prepared只表示有候选证据，不代表语义充分。unsupported_request和no_evidence均不准备生成提示词。
回答JSON是answered+claims[text_zh,citations[source_id,quote]]；材料不足为insufficient_evidence+message_zh。
引用须保留源文重音和ё，去掉Markdown星号及反引号，至少6个非空白字符。机械检查不会证明语义正确。

experiment/保留已完成10题两组20次的输入和原始输出。scope_and_review/保留范围对照、引文上下文与逐条阅读记录。
这些实验由同一助手设计、据源评分，未做独立专家盲评。原生成的引用失败保留，未用本层提示词重新生成。
范围规则对24条先冻结对照符合预期，旧8题范围外拦截7题，仍漏“程序需要多少内存”；不能据此声称通用范围识别。
原27条主张按实际所给引句审阅：14条能覆盖细节、12条需更多上下文、1条无引用；不是事实正确率。
locate按页转录与编校日志定位引句，标出逐字原转录或编校派生。重复引句保留所有位置，不能自动选一页。
字符偏移是转录字符位置，不是PDF字形坐标；编校字符的页锚定不表示原PDF逐字印有该引句。
本轮368节共565855个去排版符号字符通过来源映射，39条实验引句37条定位、1条多处出现、3条涉及编校派生。

manifest.json固定全部文件指纹；本包仅供本地研究复查，未部署到学生端。
'''

def build():
    if DEST.exists(): raise FileExistsError('Choose a new immutable kit directory')
    original = verify_package(DEFAULT_DB.parent)
    DEST.mkdir(parents=True)
    shutil.copytree(DEFAULT_DB.parent, DEST/'edition')
    verify_package(DEST/'edition')
    scripts = DEST/'scripts'
    shutil.copytree(DEFAULT_DB.parent/'source_code/scripts', scripts)
    shutil.copyfile(DEFAULT_DB.parent/'source_code/grammar_editorial_rag.py',scripts/'grammar_editorial_rag.py')
    for name in ['grammar_editorial_guard.py','grammar_editorial_search_candidate.py','grammar_quote_locator.py']:
        shutil.copyfile(ROOT/'scripts'/name,scripts/name)
    for name in ['grammar_editorial_rag.py','grammar_question_search.py']:
        if sha(scripts/name) != sha(ROOT/'scripts'/name):
            raise ValueError('Baseline root differs from frozen edition: '+name)
    shutil.copytree(OUT, DEST/'experiment')
    evidence = DEST/'scope_and_review';evidence.mkdir()
    for source in [ROOT/'data/processed/grammar_reference/rag'/name for name in
                   ['guard_scope_cases_20261022_001.json','guard_run_binding_20261022_001.json',
                    'guard_acceptance_20261022_001.json','editorial_candidate_comparison_20261022_001.json']]:
        shutil.copyfile(source,evidence/source.name)
    for name in ['pilot_claim_review_20261022_001.json','pilot_stratified_summary_20261022_001.json','quote_locations_20261022_001.json']:
        shutil.copyfile(ROOT/'data/processed/grammar_reference/reviews'/name,evidence/name)
    (DEST/'grammar_research.py').write_text(ENTRY,encoding='utf-8')
    (DEST/'README.md').write_text(README,encoding='utf-8')
    files = {p.relative_to(DEST).as_posix():sha(p) for p in DEST.rglob('*') if p.is_file()}
    write(DEST/'manifest.json',{'created_at':now(),'edition':original['edition']['edition'],
         'files':files,'generation_available':False,'source_edition_manifest_sha256':sha(DEFAULT_DB.parent/'manifest.json'),
         'limits':'工程指纹、有限范围规则与来源绑定，不是语义正确率或独立盲评。'})
    print(json.dumps({'directory':str(DEST),'files':len(files),'network_calls':0},ensure_ascii=False))

if __name__=='__main__':build()
