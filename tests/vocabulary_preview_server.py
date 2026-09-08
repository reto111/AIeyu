"""Isolated browser-test server; newline on stdin shuts it down."""
import sqlite3
import sys
import tempfile
import threading
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import serve_student_app as app

with tempfile.TemporaryDirectory(prefix='aieyu_browser_') as folder:
    target_path = Path(folder) / 'test.sqlite'
    with closing(sqlite3.connect(ROOT / 'database/russian_ai_tutor.sqlite')) as source:
        with closing(sqlite3.connect(target_path)) as target:
            source.backup(target)
    app.DB_PATH = target_path
    server = app.ThreadingHTTPServer(('127.0.0.1', 0), app.StudentAppHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f'http://127.0.0.1:{server.server_port}', flush=True)
    try:
        sys.stdin.readline()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
