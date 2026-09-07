"""Build a read-only 100-word review document; never import into the live bank."""
import hashlib
import html
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / 'data/review_samples/beginner_100.json'
OUT = ROOT / 'data/processed/review_samples'
SOURCES = {
    8449: ('https://gramota.ru/poisk?mode=all&query=%D0%98%D0%B4%D0%B5%D1%8F', '词头、重音、阴性及俄文释义'),
    8560: ('https://gramota.ru/meta/kasha', '现词头的重音、阴性及俄文释义；原 PDF 对应仍待核'),
    8691: ('https://gramota.ru/meta/krik', '阳性及俄文核心释义；单音节'),
    10073: ('https://gramota.ru/meta/svobodnyy', '重音及俄文释义；中文由助手概括'),
}


def validate_stress(text):
    assert re.fullmatch('[а-яё\u0301]+', text), text
    vowels = sum(c in 'аеёиоуыэюя' for c in text)
    assert text.count('\u0301') <= 1, text
    assert '\u0301' in text or 'ё' in text or vowels == 1, text
    if '\u0301' in text:
        assert text[text.index('\u0301') - 1] in 'аеёиоуыэюя', text


def main():
    data = json.loads(SAMPLE.read_text(encoding='utf-8'))
    assert len(data['rows']) == len({r[0] for r in data['rows']}) == 100
    records = []
    with sqlite3.connect((ROOT / 'database/russian_ai_tutor.sqlite').as_uri() + '?mode=ro', uri=True) as con:
        con.row_factory = sqlite3.Row
        for values in data['rows']:
            item = dict(zip(data['columns'], values, strict=True))
            validate_stress(item['accent'])
            if item['perfective']:
                validate_stress(item['perfective'])
            old = con.execute('''SELECT v.id,v.word,v.accent,v.part_of_speech,v.meaning_zh,
                v.source_page,v.review_status,e.code AS exam FROM vocabulary_items v
                JOIN exam_systems e ON e.id=v.exam_system_id WHERE v.id=?''', (item['id'],)).fetchone()
            assert old and old['review_status'] == 'approved', item['id']
            original = dict(old)
            canonical = item['accent'].replace('\u0301', '')
            assert canonical == old['word'] or (item['id'] == 8449 and old['word'] == 'идёя')
            item.update(original=original, canonical=canonical,
                review_status='待核原页' if item['id'] == 8560 else '模型审核样本，待用户确认',
                evidence=SOURCES.get(item['id']),
                original_hash=hashlib.sha256(json.dumps(original, ensure_ascii=False, sort_keys=True).encode()).hexdigest())
            records.append(item)
    OUT.mkdir(parents=True, exist_ok=True)
    summary = dict(total=100, verbs=sum(r['part'].startswith('动词') for r in records),
        aspect_links=sum(bool(r['perfective']) for r in records),
        external_spotchecks=len(SOURCES), unresolved_source_ids=[8560], database_written=False)
    (OUT / 'beginner_100_review.json').write_text(json.dumps(dict(summary=summary,records=records),ensure_ascii=False,indent=2),encoding='utf-8')
    esc = lambda value: html.escape(str(value or '未标注'))
    blocks, markdown = [], ['# 100 词审核样本', '', '仅为样本，未写入正式词库。100 条由当前助手逐词拟定；4 条有外部词典抽核。其余未逐词外部核验，不能称为全量词典审核通过。', '',
        '单音节不另标重音；ё 保留。释义是初学核心义，不是删除原词条的全部其他义项。动词配对受所列义项限制，所有新字段仍待确认。', '']
    for index, row in enumerate(records, 1):
        old = row['original']
        source = (f'<a href="{row["evidence"][0]}" target="_blank" rel="noopener">词典抽核依据</a>：{esc(row["evidence"][1])}'
                  if row['evidence'] else '模型逐词对照；未做外部逐词核验')
        pair = f'<p class="pair"><span>完成体（限所述义项）</span> <b lang="ru">{esc(row["perfective"])}</b></p>' if row['perfective'] else ''
        blocks.append(f'''<article><div class="entry-head"><span>{index:03d}</span><h2 lang="ru">{esc(row['accent'])}</h2><span>{esc(row['part'])}</span></div>
          <p class="meaning">{esc(row['meaning'])}</p>{pair}
          {f'<p class="note">{esc(row["note"])}</p>' if row['note'] else ''}
          <details><summary>原词条与审核依据</summary><p>{esc(old['word'])} · {esc(old['part_of_speech'])}</p><p>{esc(old['meaning_zh'])}</p>
          <p>{esc(old['exam'])} · ID {row['id']} · 来源页 {esc(old['source_page'])}</p><p>{source}</p></details>
          <p class="status">{esc(row['review_status'])}</p></article>''')
        markdown += [f"## {index:03d} {row['accent']}", f"- 词性：{row['part']}", f"- 核心义：{row['meaning']}",
            f"- 完成体候选：{row['perfective'] or '不适用或不强配'}", f"- 说明：{row['note'] or '常用核心义整理'}",
            f"- 原记录：{old['word']} / {old['part_of_speech']} / {old['meaning_zh']}",
            f"- 来源定位：{old['exam']}，ID {row['id']}，页 {old['source_page']}",
            f"- 核验：{str(row['evidence']) if row['evidence'] else '模型逐词对照，未外部逐词核验'}", f"- 状态：{row['review_status']}", '']
    (OUT / 'beginner_100_review.md').write_text('\n'.join(markdown),encoding='utf-8')
    document = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>AIeyu · 100词审核样本</title><style>
    *{box-sizing:border-box}body{margin:0;background:#f4f6f8;color:#26313a;font:16px/1.7 "Segoe UI","Microsoft YaHei",sans-serif}
    main{max-width:1160px;margin:auto;padding:28px}header{padding:0 0 24px;border-bottom:2px solid #345777;margin-bottom:24px}
    h1{font-size:26px;margin:0 0 10px}header p{margin:6px 0;color:#596673}.list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
    article{padding:20px;background:white;border:1px solid #dfe5e9;border-radius:6px;min-width:0;overflow-wrap:anywhere}
    .entry-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}.entry-head>span{font-size:13px;color:#637080}
    h2{font-family:Georgia,serif;font-size:29px;font-weight:500;margin:0;color:#203f60;line-height:1.8}
    .meaning{font-size:18px;margin:12px 0}.pair{border-top:1px solid #e6e9ed;padding-top:12px}.pair span{font-size:13px;color:#687480}
    .pair b{font:24px/1.8 Georgia,serif;color:#176958}.note,.status,details{font-size:13px}.note{color:#664d25}.status{color:#667482}
    summary{cursor:pointer;color:#326486}details p{margin:6px 0}a{color:#326486}
    @media(max-width:650px){main{padding:16px}.list{grid-template-columns:1fr}}
    @media print{body{background:white}.list{display:block}article{break-inside:avoid;margin-bottom:12px}details{display:block}}
    </style><main><header><h1>AIeyu · 100 词审核样本</h1>
    <p>重音 · 核心释义 · 动词体 · 原文对照</p>
    <p>这是待确认样本，不影响正式词库或学习记录。100 条模型逐词对照，4 条外部词典抽核；不代表全量词典审核通过。</p>
    <p>单音节不另标重音，ё 保留。释义为初学核心义；体配对只对应注明的用法。第 98 条仍需核对原资料。</p>
    </header><section class="list">''' + '\n'.join(blocks) + '</section></main></html>'
    (OUT / 'beginner_100.html').write_text(document,encoding='utf-8')
    assert len(re.findall('<article>', document)) == 100
    print(json.dumps(summary, ensure_ascii=True))
    print(OUT / 'beginner_100.html')


if __name__ == '__main__':
    main()
