"""Build a hierarchy from visually transcribed contents; never approve body text."""
import csv
import hashlib
import json
import re
from pathlib import Path

import tonglun_reference as corpus

PARTS = {'第一编': 'introduction', '第二编': 'lexicology', '第三编': 'phonetics',
         '第四编': 'wordformation', '第五编': 'morphology', '第六编': 'syntax'}
DIGITS = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}


def number(label):
    text = re.match(r'第([一二三四五六七八九十]+)', label)[1]
    if text == '十':
        return 10
    if text.startswith('十'):
        return 10 + DIGITS[text[1:]]
    return DIGITS[text]


def build():
    summary = []
    for volume in (1, 2):
        work = corpus.volume_work(volume)
        path = work / 'reviews/toc_visual_20261018.tsv'
        rows = list(csv.DictReader(path.open(encoding='utf8', newline=''), delimiter='\t'))
        expected_pages = set(range(8, 17) if volume == 1 else range(5, 14))
        if {int(r['toc_pdf_page']) for r in rows} != expected_pages:
            raise ValueError('Contents-page coverage differs')
        source = json.loads((work / 'source.json').read_text(encoding='utf8'))
        evidence = dict(volume=volume, source_sha256=source['source_sha256'],
            transcription_sha256=corpus.file_sha256(path), method='assistant_visual_comparison',
            pages=[dict(pdf_page=p, render_sha256=corpus.file_sha256(work / 'renders' / f'p{p:04d}.png')) for p in sorted(expected_pages)],
            limits='目录逐行转写；正文标题、首尾和印刷页位置仍需另核。目录音素中同形字符按西里尔字母编码，标点排版统一。')
        evidence_path = work / 'reviews/toc_evidence_20261018.json'
        if evidence_path.exists() and json.loads(evidence_path.read_text(encoding='utf8')) != evidence:
            raise ValueError('Frozen contents evidence changed; append a correction instead')
        if not evidence_path.exists():
            corpus.dump(evidence_path, evidence)
        items, identifiers = [], set()
        part = chapter = section = None
        previous_printed = 0
        for index, row in enumerate(rows, 1):
            level, title = row['level'], row['title']
            printed = int(row['printed_page']) if row['printed_page'] else None
            if printed is not None and level != 'frontmatter':
                if printed < previous_printed:
                    raise ValueError(f'Non-monotonic contents: {volume}/{title}')
                previous_printed = printed
            if level == 'part':
                part, chapter, section = title, None, None
            elif level == 'chapter':
                chapter, section = title, None
            elif level == 'section':
                section = title
            code = None
            if level == 'unit':
                prefix = f'v{volume}.{PARTS[part.split()[0]]}'
                if chapter:
                    prefix += f'.ch{number(chapter):02d}'
                if section:
                    prefix += f'.sec{number(section):02d}'
                code = prefix + f'.unit{int(re.match(r"(\d+)", title)[1]):02d}'
                if code in identifiers:
                    raise ValueError(f'Duplicate knowledge unit code: {code}')
                identifiers.add(code)
            items.append(dict(toc_entry_id=f'v{volume}.toc.{index:03d}', volume=volume,
                toc_pdf_page=int(row['toc_pdf_page']), level=level, title=title,
                printed_start=printed,
                pdf_start_candidate=printed + (16 if volume == 1 else 13) if printed is not None and level != 'frontmatter' else None,
                unit_code=code, part=part, chapter=chapter, section=section,
                status='toc_visual_checked', body_boundary_status='not_checked'))
        catalog = dict(volume=volume, source_sha256=source['source_sha256'],
            toc_transcription_sha256=evidence['transcription_sha256'], entries=items,
            counts={level: sum(i['level'] == level for i in items) for level in ('part', 'chapter', 'section', 'unit', 'frontmatter', 'endmatter')},
            limits='候选知识单元目录，不是已审核正文或精确结束边界。编级标题在原目录未列起页，不补造原印页码。')
        corpus.dump(work / 'toc_catalog.json', catalog)
        summary.append(dict(volume=volume, **catalog['counts']))
    corpus.dump(corpus.WORK / 'toc_summary.json', summary)
    return summary


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2))
