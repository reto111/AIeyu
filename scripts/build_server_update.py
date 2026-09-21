"""Build an existing-server update without secrets or student databases."""
import json
import sqlite3
import subprocess
import zipfile
from contextlib import closing
from datetime import datetime
from pathlib import Path

from import_vocabulary_learning import apply_catalog
from vocabulary_learning import annotation

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    catalog = output / 'vocabulary_release_catalog.json'
    records = []
    with closing(sqlite3.connect((ROOT / 'database/russian_ai_tutor.sqlite').as_uri() + '?mode=ro', uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        for row in conn.execute('''SELECT v.*, e.code AS exam, l.code AS level
            FROM vocabulary_items v JOIN exam_systems e ON e.id=v.exam_system_id
            JOIN exam_levels l ON l.id=v.level_id WHERE v.review_status='approved' ORDER BY v.id''').fetchall():
            item = annotation(conn, row)
            if not item:
                continue
            records.append(dict(id=row['id'], exam=row['exam'], level=row['level'],
                original=json.loads(item['original_json']), canonical=item['canonical_word'],
                accent=item['accent'], part=item['part'], meaning=item['core_meaning_zh'],
                perfective=item['aspect_partner'], note=item['note'], stage=item['stage'],
                method=item['review_method'], evidence=json.loads(item['evidence_json'])))
    catalog.write_text(json.dumps(dict(schema_version=1, records=records), ensure_ascii=False, indent=2), encoding='utf-8')
    apply_catalog(ROOT / 'database/russian_ai_tutor.sqlite', catalog)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    allowed = ('apps/', 'scripts/', 'packages/', 'prompts/', 'tests/', 'docs/')
    roots = {'README.md', 'UPDATE_README.md', 'requirements-web.txt', 'Start_AIeyu_Server.ps1'}
    names = [name for name in tracked if name and (name.startswith(allowed) or name in roots or
             (name.startswith('database/') and name.endswith('.sql')))]
    # Newly added release entry points are included before their first commit.
    names = sorted(set(names + ['scripts/build_server_update.py', 'scripts/update_release.py',
                               'data/review_samples/learning_header_archives.json']))
    target = output / f'AIeyu_update_{datetime.now():%Y%m%d_%H%M%S}.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            if name.endswith(('.pyc', '.sqlite', '.db', '.pdf')) or '/__pycache__/' in name:
                continue
            archive.write(ROOT / name, name)
        archive.write(catalog, 'data/review_samples/vocabulary_release_catalog.json')
    with zipfile.ZipFile(target) as archive:
        if archive.testzip():
            raise ValueError('ZIP integrity failure')
        if any(Path(n).name == '.env' or n.endswith(('.sqlite', '.sqlite-wal', '.sqlite-shm')) for n in archive.namelist()):
            raise ValueError('Private file in release')
    print(json.dumps(dict(package=str(target), annotations=len(records), bytes=target.stat().st_size), ensure_ascii=False))


if __name__ == '__main__':
    main()
