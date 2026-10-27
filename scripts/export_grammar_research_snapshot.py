"""Export and verify an immutable, local grammar research snapshot.

The source PDF and student database are never copied. A snapshot is a research
candidate, not certification of transcription or generated-answer accuracy.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import sys

sys.dont_write_bytecode = True

from grammar_reference import DB, WORK, ROOT, file_sha256
from grammar_rag import read_source, section_snapshot, text_hash


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def write_jsonl(path, records):
    with path.open('w', encoding='utf8', newline='\n') as stream:
        for record in records:
            stream.write(canonical(record) + '\n')


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf8').splitlines()]


def readonly(path):
    conn = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def logical_hash(conn):
    """Fingerprint every application table, including page and batch history."""
    digest = hashlib.sha256()
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    for name in tables:
        quoted = '"' + name.replace('"', '""') + '"'
        rows = sorted(canonical(list(row)) for row in conn.execute('SELECT * FROM ' + quoted))
        digest.update(canonical(dict(table=name, rows=rows)).encode('utf8'))
    return digest.hexdigest()


def export_records(conn):
    source = read_source(conn)
    pages = [dict(r) for r in conn.execute('SELECT * FROM pages ORDER BY pdf_page')]
    page_pins = {r['pdf_page']:r['review_sha256'] for r in pages}
    for p in pages:
        if text_hash(p['review_json']) != p['review_sha256']:
            raise ValueError(f"Page hash mismatch: {p['pdf_page']}")
        p['review'] = json.loads(p.pop('review_json'))
    sections, ready, excluded = [], [], []
    for row in conn.execute('SELECT * FROM chunks ORDER BY code'):
        item = dict(row)
        for key in ('pdf_pages', 'printed_pages', 'notes'):
            item[key] = json.loads(item[key])
        item.pop('search_text')
        item['body_sha256'] = text_hash(item['body'])
        item['page_evidence'] = [dict(pdf_page=n, review_sha256=page_pins[n]) for n in item['pdf_pages']]
        item['retrieval_eligible'] = item['status'] == 'ready'
        if item['retrieval_eligible']:
            snapshot = section_snapshot(conn, item['code'], source)
            if snapshot['body_sha256'] != item['body_sha256']:
                raise ValueError('Section snapshot differs')
            ready.append(item)
        else:
            excluded.append(dict(code=item['code'], title=item['title'], status=item['status'],
                notes=item['notes'], pdf_pages=item['pdf_pages'], retrieval_eligible=False))
        sections.append(item)
    batches = []
    for row in conn.execute('SELECT * FROM batches ORDER BY rowid'):
        batches.append(dict(row))
    return source, dict(pages=pages, sections=sections, retrieval_ready=ready,
                       excluded_sections=excluded, batches=batches)


def verify_package(directory):
    directory = Path(directory).resolve()
    manifest = json.loads((directory/'manifest.json').read_text(encoding='utf8'))
    actual_files = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file() and p != directory/'manifest.json'}
    if set(manifest['files']) != actual_files:
        raise ValueError('Package file inventory mismatch')
    for relative, expected in manifest['files'].items():
        path = (directory/relative).resolve()
        if not path.is_relative_to(directory) or not path.is_file() or file_sha256(path) != expected:
            raise ValueError(f'Package file mismatch: {relative}')
    with closing(readonly(directory/'grammar_reference.sqlite')) as conn:
        if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Snapshot integrity check failed')
        if logical_hash(conn) != manifest['database_logical_sha256']:
            raise ValueError('Logical database fingerprint mismatch')
        # No PDF access here: package verification is usable after relocation.
        rows = {r['code']:dict(r) for r in conn.execute('SELECT * FROM chunks')}
        db_pages = {r['pdf_page']:dict(r) for r in conn.execute('SELECT * FROM pages')}
        all_sections = read_jsonl(directory/'sections.jsonl')
        ready = read_jsonl(directory/'retrieval_ready.jsonl')
        excluded = read_jsonl(directory/'excluded_sections.jsonl')
        pages = read_jsonl(directory/'pages.jsonl')
        if len({x['code'] for x in all_sections}) != len(all_sections) or len(rows) != len(all_sections):
            raise ValueError('Duplicate or missing exported section')
        for item in all_sections:
            row = rows[item['code']]
            expected = dict(row)
            for key in ('pdf_pages', 'printed_pages', 'notes'):
                expected[key] = json.loads(expected[key])
            expected.pop('search_text')
            expected['body_sha256'] = text_hash(row['body'])
            expected['retrieval_eligible'] = row['status'] == 'ready'
            expected['page_evidence'] = [dict(pdf_page=n,review_sha256=db_pages[n]['review_sha256']) for n in expected['pdf_pages']]
            if item != expected:
                raise ValueError('Exported section differs from snapshot')
        expected_ready = [x for x in all_sections if x['retrieval_eligible']]
        expected_excluded = [dict(code=x['code'],title=x['title'],status=x['status'],notes=x['notes'],
            pdf_pages=x['pdf_pages'],retrieval_eligible=False) for x in all_sections if not x['retrieval_eligible']]
        if ready != expected_ready or excluded != expected_excluded:
            raise ValueError('Ready/excluded partition mismatch')
        if len(pages) != len(db_pages) or len({p['pdf_page'] for p in pages}) != len(pages):
            raise ValueError('Page export coverage mismatch')
        for p in pages:
            row = db_pages[p['pdf_page']]
            expected_page = dict(row)
            expected_page['review'] = json.loads(expected_page.pop('review_json'))
            if p != expected_page or text_hash(row['review_json']) != row['review_sha256']:
                raise ValueError('Page evidence mismatch')
        batches = read_jsonl(directory/'batches.jsonl')
        if batches != [dict(r) for r in conn.execute('SELECT * FROM batches ORDER BY rowid')]:
            raise ValueError('Batch history export mismatch')
        actual_counts = dict(pages=len(pages), sections=len(all_sections), retrieval_ready=len(ready),
            excluded=len(excluded), batches=len(batches), status_counts=dict(Counter(x['status'] for x in all_sections)))
        if manifest['counts'] != actual_counts:
            raise ValueError('Manifest count mismatch')
        source = dict(conn.execute('SELECT * FROM source WHERE id=1').fetchone())
        expected_source = dict(title=source['title'],filename=Path(source['path']).name,
            sha256=source['sha256'],total_pdf_pages=source['total_pages'])
        if manifest['source'] != expected_source:
            raise ValueError('Manifest source mismatch')
    return dict(status='verified', directory=str(directory), counts=manifest['counts'],
                files_verified=len(manifest['files']), release_status=manifest['release_status'])


def export_snapshot(output, *, db=DB, evidence_paths=(), release_status='research_candidate_not_final_thesis_acceptance'):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(f'Immutable output already exists: {output}')
    if release_status not in ('research_candidate_not_final_thesis_acceptance','research_dataset_v1_scope_accepted'):
        raise ValueError('Unknown research release status')
    output.parent.mkdir(parents=True, exist_ok=True)
    before = file_sha256(Path(db))
    with tempfile.TemporaryDirectory(prefix='.grammar-export-', dir=output.parent) as temp:
        stage = Path(temp)/'package'
        stage.mkdir()
        with closing(readonly(db)) as conn:
            conn.execute('BEGIN')
            source, records = export_records(conn)
            fingerprint = logical_hash(conn)
            with closing(sqlite3.connect(stage/'grammar_reference.sqlite')) as dst:
                conn.backup(dst)
            for name, items in records.items():
                write_jsonl(stage/(name+'.jsonl'), items)
        if file_sha256(Path(db)) != before:
            raise ValueError('Source database changed during export; retry on a stable snapshot')
        proof = {}
        for path in evidence_paths:
            path = Path(path).resolve()
            relative = path.relative_to(WORK.resolve())
            target = stage/'evidence'/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            proof[relative.as_posix()] = file_sha256(target)
        counts = dict(pages=len(records['pages']), sections=len(records['sections']),
            retrieval_ready=len(records['retrieval_ready']), excluded=len(records['excluded_sections']),
            batches=len(records['batches']), status_counts=dict(Counter(x['status'] for x in records['sections'])))
        code_names = ['scripts/grammar_reference.py','scripts/grammar_question_search.py','scripts/grammar_rag.py',
            'scripts/knowledge_base.py','scripts/extract_pdf_text.py','scripts/export_grammar_research_snapshot.py',
            'scripts/evaluate_grammar_retrieval.py','scripts/replay_grammar_research_snapshot.py',
            'tests/test_grammar_research_snapshot.py']
        for name in code_names:
            destination=stage/'source_code'/name
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,destination)
        pymupdf_version=importlib.metadata.version('PyMuPDF')
        (stage/'source_code/requirements-research.txt').write_text('PyMuPDF=='+pymupdf_version+'\n',encoding='utf8')
        readme=f'''# 俄语语法研究快照

来源：{source['title']}。版本状态：{release_status}。研究数据版范围确认不等于导师最终论文验收或全书准确率证明。

## 内容与范围

- 原书{source['total_pages']}个PDF页；pages.jsonl包含{counts['pages']}个正文页的审核记录。前置页、目录等第一轮证据不在这份正文页表中，不把613称作整书页数。
- sections.jsonl包含{counts['sections']}个完整小节，保留原文、原印重音、表格、状态及隔离说明。
- retrieval_ready.jsonl仅含{counts['retrieval_ready']}个ready节；excluded_sections.jsonl列出{counts['excluded']}个隔离节及原因，不能混入可引用检索。
- grammar_reference.sqlite为SQLite backup API创建的一致性快照；batches.jsonl保存已应用批次记录，原始359批审核JSON不全部随包复制。
- pages.jsonl中的review与review_sha256绑定审核版本；小节page_evidence绑定页码和审核指纹。body_sha256对原body UTF-8字节计算，不移除重音或Markdown。
- manifest.json列出来源PDF指纹、输入库文件指纹、库逻辑指纹、导出脚本指纹及全部包内文件校验和。SQLite备份文件的字节指纹可能与输入库不同，逻辑内容另核验。
- evidence/保存本次选定的质量与检索证据；证据中的旧绝对路径是原工作区定位信息。原PDF与渲染图片未复制，逐项历史裁图也未全部复制。

## 本地校验与复现

在原项目目录运行：

    .venv/Scripts/python.exe -X utf8 scripts/export_grammar_research_snapshot.py verify <本包目录>

独立读取JSONL仅需标准库。包内source_code/保存对应检索、导出、评估代码和研究导出测试；运行这些模块需Python和requirements-research.txt中固定的PyMuPDF版本。校验包本身无需原PDF。

如果evidence/rag/中含fresh_retrieval_cases_20261016_001.json，可用包内版本复跑：

    python -B source_code/scripts/evaluate_grammar_retrieval.py --cases evidence/rag/fresh_retrieval_cases_20261016_001.json --snapshot . --output <包外不存在的新结果文件>

无原PDF时，可在本包目录用下面的离线复现命令：

    python -B source_code/scripts/replay_grammar_research_snapshot.py --cases evidence/rag/fresh_retrieval_cases_20261016_001.json --snapshot . --output <包外不存在的新结果文件>

离线复现只校验包、审核页记录和检索结果，不声称本次重新读取或核对过扫描原图。普通evaluate接口仍核验原PDF，要求它在SQLite记载路径且指纹一致；没有重写原库路径来绕过校验。入口脚本关闭Python字节码缓存，命令仍显式使用-B。输出结果必须放在包外，包内测试也应用python -B运行，避免新增文件破坏清单。重导出使用新目录，已有版本禁止覆盖。

## 字段和使用边界

JSONL每行一条记录，UTF-8编码、LF换行、按键排序。code为稳定节键；pdf_pages为扫描PDF页码，printed_pages为书面页码；status保留ready/unresolved/incomplete；notes为原审核隔离说明，不是生成解释。review中fragments保留原页片段、节边界与元数据，normalization是审核说明，不作为原书正文。

固定24页分层抽核和候选处置均有有限范围；不是独立专家盲评，也不是全书第三轮逐字复核。研究中应披露未决节、抽样局限、检索失败和数据来源。新增冻结检索题与历史题材有交集；机械引句验证和目标召回不等于生成答案正确率。包内没有生成模型回答、学生账号或学习历史。
'''
        (stage/'README.md').write_text(readme,encoding='utf8')
        manifest = dict(schema_version=1, created_at=datetime.now(timezone.utc).isoformat(),
            release_status=release_status,
            source=dict(title=source['title'], filename=Path(source['path']).name,
                        sha256=source['sha256'], total_pdf_pages=source['total_pages']),
            input_database_sha256=before, database_logical_sha256=fingerprint, counts=counts,
            export_script_sha256=file_sha256(Path(__file__)), evidence_artifacts=proof,
            runtime=dict(python=sys.version,sqlite=sqlite3.sqlite_version,pymupdf=pymupdf_version),
            included_code=code_names,
            limits='只冻结已审核转录及状态；ready不代表全书零错，隔离节不进入retrieval_ready。原PDF与渲染原图未复制。原图核验、固定目标召回和机械引句检查均不是生成答案准确率。')
        manifest['files'] = {p.relative_to(stage).as_posix():file_sha256(p) for p in sorted(stage.rglob('*')) if p.is_file()}
        (stage/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
        verify_package(stage)
        if not stage.resolve().is_relative_to(output.parent):
            raise ValueError('Staged package escaped the output parent')
        stage.rename(output)
    return verify_package(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    make = sub.add_parser('export')
    make.add_argument('--output', required=True)
    make.add_argument('--evidence', action='append', default=[])
    make.add_argument('--release-status',default='research_candidate_not_final_thesis_acceptance',
        choices=['research_candidate_not_final_thesis_acceptance','research_dataset_v1_scope_accepted'])
    check = sub.add_parser('verify')
    check.add_argument('directory')
    args = parser.parse_args()
    if args.command == 'verify':
        result = verify_package(args.directory)
    else:
        target = Path(args.output).resolve()
        if not target.is_relative_to((WORK/'research_exports').resolve()):
            parser.error('Output must be within the dedicated grammar research_exports directory')
        result = export_snapshot(target, evidence_paths=args.evidence,release_status=args.release_status)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
