"""Export actual learning-annotation coverage, not inferred review success."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from vocabulary_learning import annotation, STAGE_NAMES

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / 'data/processed/vocabulary_learning'
    out.mkdir(parents=True, exist_ok=True)
    reviewed, pending = [], []
    with closing(sqlite3.connect((ROOT/'database/russian_ai_tutor.sqlite').as_uri()+'?mode=ro', uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        for row in conn.execute('''SELECT v.*, e.code AS exam FROM vocabulary_items v
            JOIN exam_systems e ON e.id=v.exam_system_id
            WHERE v.review_status='approved' ORDER BY v.id''').fetchall():
            item = annotation(conn, row)
            if item:
                reviewed.append(dict(id=row['id'], exam=row['exam'], original_word=row['word'],
                                     original_part=row['part_of_speech'], original_meaning=row['meaning_zh'],
                                     source_page=row['source_page'], **item))
            else:
                pending.append(dict(id=row['id'], exam=row['exam'], word=row['word'],
                                    meaning_zh=row['meaning_zh'], source_page=row['source_page'],
                                    status='本轮未逐词审核，或旧审核与当前值不一致'))
    summary = dict(total=len(reviewed)+len(pending), model_reviewed=len(reviewed), pending=len(pending),
                   stages={STAGE_NAMES[s]:sum(r['stage']==s for r in reviewed) for s in range(1,5)},
                   external_dictionary_spotchecks=sum(r['evidence_json'].startswith('["https://') for r in reviewed),
                   source_pdf_visual_checks=sum('pdf#page=' in r['evidence_json'] for r in reviewed),
                   next_pending_id=pending[0]['id'] if pending else None)
    (out/'coverage.json').write_text(json.dumps(dict(summary=summary, reviewed=reviewed, pending=pending),
                                               ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# 词库重音与核心释义审核覆盖', '',
             f"现有正式记录：{summary['total']}；本轮模型逐项审核并生效：{len(reviewed)}；尚未覆盖：{len(pending)}。", '',
             '旧 approved 只代表历史入库状态，不代表完成本轮重音、词性、中文和分级审核。',
             '模型逐项审核、词典抽核、PDF视觉核对分别记录，均不能视为绝对正确率证明。',
             '学习阶段为初始教学建议，不是学校课程、大纲等级或考试测得的能力。原记录与学习 ID 保留。', '',
             f"阶段分布：{summary['stages']}。外部词典抽核记录 {summary['external_dictionary_spotchecks']} 条；原 PDF 视觉核对 {summary['source_pdf_visual_checks']} 条。", '',
             '## 本轮已审核', '', '| ID | 考试 | 原词头 / 原义 | 重音 / 核心义 | 级别 |', '|---|---|---|---|---|']
    for r in reviewed:
        clean = lambda x: str(x or '').replace('|',' / ').replace('\n',' ')
        lines.append(f"| {r['id']} | {r['exam']} | {clean(r['original_word'])} / {clean(r['original_meaning'])} | {r['accent']} / {clean(r['core_meaning_zh'])} | {STAGE_NAMES[r['stage']]} |")
    lines += ['', '## 尚未覆盖', '', '完整逐条待办见 coverage.json 的 pending；不要按整批无异常批量改成已审核。',
              f"下一个按 ID 顺序的未审核记录：{summary['next_pending_id']}。"]
    (out/'README.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
