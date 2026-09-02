from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import audit_question_bank_quality as question_quality


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "database" / "russian_ai_tutor.sqlite"
DEFAULT_REPORT = ROOT / "data" / "processed" / "health" / "mvp_readiness_latest.json"
STATIC_DIR = ROOT / "apps" / "student_web" / "static"
EXPECTED_POOLS = {
    "TEM4_RU": {"level": "TEM4", "min_questions": 444, "min_words": 3000},
    "TEM8_RU": {"level": "TEM8", "min_questions": 300, "min_words": 3000},
}
REQUIRED_TABLES = {
    "users",
    "user_auth",
    "user_sessions",
    "questions",
    "question_options",
    "passages",
    "vocabulary_items",
    "user_word_progress",
    "quiz_sessions",
    "quiz_items",
    "user_answers",
    "question_exposures",
    "mastery_snapshots",
    "training_recommendations",
    "daily_study_plans",
    "daily_study_tasks",
    "wrongbook_preferences",
    "selection_translation_cache",
}


@dataclass
class Check:
    code: str
    label: str
    ok: bool
    detail: str


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def add(checks: list[Check], code: str, label: str, ok: bool, detail: str) -> None:
    checks.append(Check(code, label, bool(ok), str(detail)))


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def exam_ids(conn: sqlite3.Connection, exam_code: str, level_code: str) -> tuple[int, int]:
    row = conn.execute(
        """
        SELECT es.id AS exam_id, el.id AS level_id
        FROM exam_systems es
        JOIN exam_levels el ON el.exam_system_id = es.id
        WHERE es.code = ? AND el.code = ?
        """,
        (exam_code, level_code),
    ).fetchone()
    if row is None:
        raise ValueError(f"缺少考试定义 {exam_code}/{level_code}")
    return int(row["exam_id"]), int(row["level_id"])


def check_database(db_path: Path, checks: list[Check]) -> None:
    add(checks, "database_file", "数据库文件", db_path.exists(), str(db_path))
    if not db_path.exists():
        return
    try:
        with connect(db_path) as conn:
            integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
            add(checks, "database_integrity", "数据库完整性", integrity == "ok", integrity)

            tables = {
                str(row[0])
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
            }
            missing = sorted(REQUIRED_TABLES - tables)
            add(
                checks,
                "required_tables",
                "核心数据表",
                not missing,
                "完整" if not missing else "缺少: " + ", ".join(missing),
            )
            if missing:
                return

            for exam_code, expected in EXPECTED_POOLS.items():
                exam_id, level_id = exam_ids(conn, exam_code, str(expected["level"]))
                question_count = int(
                    conn.execute(
                        """
                        SELECT COUNT(*) FROM questions
                        WHERE exam_system_id = ? AND level_id = ?
                          AND review_status = 'approved' AND source_usage = 'practice'
                        """,
                        (exam_id, level_id),
                    ).fetchone()[0]
                )
                word_count = int(
                    conn.execute(
                        """
                        SELECT COUNT(*) FROM vocabulary_items
                        WHERE exam_system_id = ? AND level_id = ? AND review_status = 'approved'
                        """,
                        (exam_id, level_id),
                    ).fetchone()[0]
                )
                add(
                    checks,
                    f"{exam_code.lower()}_questions",
                    f"{exam_code} 正式题库",
                    question_count >= int(expected["min_questions"]),
                    f"{question_count} 题，最低要求 {expected['min_questions']}",
                )
                add(
                    checks,
                    f"{exam_code.lower()}_words",
                    f"{exam_code} 正式词库",
                    word_count >= int(expected["min_words"]),
                    f"{word_count} 词，最低要求 {expected['min_words']}",
                )

            questions = question_quality.load_questions(conn)
            options = question_quality.load_options(conn)
            blocking_issues = [
                issue
                for question in questions
                for issue in question_quality.audit_question(question, options.get(question["id"], []))
                if question["review_status"] == "approved"
                and question["source_usage"] == "practice"
                and issue["severity"] in {"high", "medium"}
            ]
            detail = "0 个高/中风险问题"
            if blocking_issues:
                sample = ", ".join(
                    f"Q{item['question_id']}:{item['issue_code']}" for item in blocking_issues[:5]
                )
                detail = f"{len(blocking_issues)} 个问题；示例 {sample}"
            add(checks, "question_quality", "正式题库质量门禁", not blocking_issues, detail)

            vocabulary_rows = conn.execute(
                """
                SELECT id, word, meaning_zh
                FROM vocabulary_items
                WHERE review_status = 'approved'
                """
            ).fetchall()
            invalid_words = []
            for row in vocabulary_rows:
                word = str(row["word"] or "").strip()
                meaning = str(row["meaning_zh"] or "").strip()
                if (
                    not word
                    or not meaning
                    or "\ufffd" in word
                    or "\ufffd" in meaning
                    or not re.search(r"[А-Яа-яЁё]", word)
                    or re.search(r"[А-Яа-яЁё]", meaning)
                ):
                    invalid_words.append(int(row["id"]))
            add(
                checks,
                "vocabulary_quality",
                "正式词库基础质量",
                not invalid_words,
                "0 个基础异常" if not invalid_words else f"{len(invalid_words)} 个异常；示例 ID {invalid_words[:8]}",
            )
    except Exception as exc:
        add(checks, "database_read", "数据库读取", False, str(exc))


def check_runtime(checks: list[Check]) -> None:
    missing_static = [name for name in ("index.html", "app.js", "styles.css") if not (STATIC_DIR / name).exists()]
    add(
        checks,
        "student_web_files",
        "学生端网页文件",
        not missing_static,
        "完整" if not missing_static else "缺少: " + ", ".join(missing_static),
    )
    deepseek = bool(os.environ.get("DEEPSEEK_API_KEY"))
    add(checks, "deepseek_configuration", "DeepSeek 配置", deepseek, "已配置" if deepseek else "缺少 DEEPSEEK_API_KEY")

    morph_spec = importlib.util.find_spec("pymorphy3")
    morph_ok = morph_spec is not None
    morph_detail = "未安装，请执行 python -m pip install -r requirements-web.txt"
    if morph_ok:
        try:
            import pymorphy3

            normal_form = pymorphy3.MorphAnalyzer().parse("студентами")[0].normal_form
            morph_ok = normal_form == "студент"
            morph_detail = f"студентами -> {normal_form}"
        except Exception as exc:
            morph_ok = False
            morph_detail = str(exc)
    add(checks, "russian_morphology", "俄语词形还原", morph_ok, morph_detail)


def get_json(url: str) -> tuple[int, dict[str, Any]]:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return int(response.status), json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            return int(exc.code), json.loads(body)
        except json.JSONDecodeError:
            return int(exc.code), {"error": body}


def check_http(base_url: str, checks: list[Check]) -> None:
    base = base_url.rstrip("/")
    try:
        status, health = get_json(f"{base}/api/health")
        add(
            checks,
            "health_endpoint",
            "服务健康接口",
            status == 200 and health.get("ready") is True,
            f"HTTP {status} / {health.get('status', health.get('error', '未知'))}",
        )
        for exam_code, expected in EXPECTED_POOLS.items():
            query = urllib.parse.urlencode({"exam_system": exam_code, "level": expected["level"]})
            response_status, payload = get_json(f"{base}/api/status?{query}")
            count = int(payload.get("question_count") or 0)
            add(
                checks,
                f"{exam_code.lower()}_status_api",
                f"{exam_code} 题库接口",
                response_status == 200 and count >= int(expected["min_questions"]),
                f"HTTP {response_status} / {count} 题",
            )
        with urllib.request.urlopen(f"{base}/", timeout=10) as response:
            html = response.read().decode("utf-8", errors="replace")
            add(checks, "student_page", "学生端首页", response.status == 200 and "AIeyu" in html, f"HTTP {response.status}")
    except Exception as exc:
        add(checks, "http_access", "本地服务访问", False, str(exc))


def check_tests(checks: list[Check]) -> None:
    result = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "tests.test_adaptive_training"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    output = (result.stdout + "\n" + result.stderr).strip()
    tail = " | ".join(line.strip() for line in output.splitlines()[-4:] if line.strip())
    add(checks, "regression_tests", "核心回归测试", result.returncode == 0, tail or f"exit={result.returncode}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run the AIeyu MVP release-readiness gate.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--skip-http", action="store_true", help="Skip checks against a running web service.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip the automated regression suite.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    checks: list[Check] = []
    check_database(args.db.resolve(), checks)
    check_runtime(checks)
    if not args.skip_http:
        check_http(args.base_url, checks)
    if not args.skip_tests:
        check_tests(checks)

    passed = sum(1 for item in checks if item.ok)
    failed = [item for item in checks if not item.ok]
    report = {
        "ready": not failed,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "database": str(args.db.resolve()),
        "base_url": None if args.skip_http else args.base_url,
        "summary": {"passed": passed, "failed": len(failed), "total": len(checks)},
        "checks": [asdict(item) for item in checks],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("AIeyu MVP 发布前验收")
    for item in checks:
        print(f"[{'PASS' if item.ok else 'FAIL'}] {item.label}: {item.detail}")
    print(f"结果: {passed}/{len(checks)} 通过")
    print(f"报告: {args.report}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
