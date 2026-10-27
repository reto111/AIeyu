"""现代俄语体学: isolated, resumable source review using the grammar workflow.

No network calls; OCR is never automatically approved for retrieval.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import sys
import time
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / 'data/knowledge_sources/xiandaieyutixue.pdf'
WORK = ROOT / 'data/processed/aspect_reference'
DB = WORK / 'aspect_reference.sqlite'
TITLE = '现代俄语体学（修订本，张家骅，2004，第2版）'
# A separate module instance keeps the original grammar source/work globals intact.
spec = importlib.util.spec_from_file_location('_aspect_review_core', ROOT/'scripts/grammar_reference.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
core.PDF, core.WORK = PDF, WORK


def ocr(start, end, dpi=220, workers=4):
    fingerprint = core.file_sha256(PDF)
    with pymupdf.open(PDF) as doc:
        count = len(doc)
    if not 1 <= start <= end <= count or not 1 <= workers <= 8:
        raise ValueError('Invalid page range or worker count')
    def process(number, image):
        target = WORK/'ocr'/f'p{number:04d}.json'
        began = time.perf_counter()
        text = core.ocr_image(image, 'chi_sim+rus+eng')
        core.dump(target, dict(pdf_page=number, source_sha256=fingerprint,
            dpi=dpi, engine='tesseract', languages='chi_sim+rus+eng', psm=6,
            status='unreviewed', seconds=round(time.perf_counter()-began,3),
            created_at=core.now(), text=text))
        result = dict(page=number, chars=len(text))
        print(json.dumps(result), flush=True)
        return result
    # PyMuPDF stays on the main thread; only independent Tesseract processes run concurrently.
    futures = []
    with ThreadPoolExecutor(max_workers=workers) as pool, pymupdf.open(PDF) as doc:
        for number in range(start,end+1):
            target = WORK/'ocr'/f'p{number:04d}.json'
            if target.exists():
                old = json.loads(target.read_text(encoding='utf-8'))
                if old['source_sha256'] != fingerprint or old['pdf_page'] != number:
                    raise ValueError('OCR cache belongs to another source/page')
                continue
            image = WORK/'renders'/f'p{number:04d}.png'
            image.parent.mkdir(parents=True, exist_ok=True)
            core.render_page(doc[number-1], image, dpi)
            futures.append(pool.submit(process, number, image))
        for future in futures:
            future.result()
    return status()


def import_batch(batch, apply=False):
    return core.import_batch(batch, db=DB, pdf=PDF, title=TITLE, apply=apply)


def status():
    result = core.status(db=DB)
    result.update(title=TITLE, source_sha256=core.file_sha256(PDF))
    with pymupdf.open(PDF) as doc:
        result['total_pages'] = len(doc)
    done = {int(p.stem[1:]) for p in (WORK/'ocr').glob('p*.json')}
    result['ocr_missing_pages'] = sorted(set(range(1,result['total_pages']+1))-done)
    return result


def export():
    result = core.export_review(db=DB)
    path = Path(result['path'])
    text = path.read_text(encoding='utf-8').replace('# 当代俄语语法：已清洗页与待办', '# 现代俄语体学：已清洗页与待办', 1)
    path.write_text(text,encoding='utf-8')
    return result


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('ocr')
    p.add_argument('--start',type=int,default=1)
    p.add_argument('--end',type=int,default=481)
    p.add_argument('--dpi',type=int,default=220)
    p.add_argument('--workers',type=int,default=4)
    p=sub.add_parser('import')
    p.add_argument('batch',type=Path)
    p.add_argument('--apply',action='store_true')
    p=sub.add_parser('search')
    p.add_argument('query')
    p.add_argument('--limit',type=int,default=5)
    sub.add_parser('status')
    sub.add_parser('export')
    args=parser.parse_args()
    if args.command=='ocr': result=ocr(args.start,args.end,args.dpi,args.workers)
    elif args.command=='import': result=import_batch(args.batch,args.apply)
    elif args.command=='search': result=core.search(args.query,args.limit,db=DB)
    elif args.command=='export': result=export()
    else: result=status()
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
