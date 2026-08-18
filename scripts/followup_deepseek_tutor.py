from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "processed" / "tutor_outputs"
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def thread_messages(thread_id: int) -> list[dict[str, str]]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT role, content
            FROM ai_tutor_messages
            WHERE thread_id = ?
            ORDER BY id
            """,
            (thread_id,),
        ).fetchall()
    if not rows:
        raise ValueError(f"No messages found for ai_tutor_threads.id = {thread_id}.")
    return [{"role": role, "content": content} for role, content in rows]


def chat_completion(
    *,
    api_key: str,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    thinking: str,
    reasoning_effort: str,
    max_tokens: int | None,
    timeout: int,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "thinking": {"type": thinking},
        "reasoning_effort": reasoning_effort,
        "stream": False,
    }
    if max_tokens is not None:
        body["max_tokens"] = max_tokens

    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API error {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"DeepSeek API connection failed: {exc}") from exc


def assistant_content(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        raise ValueError("DeepSeek response has no choices.")
    content = (choices[0].get("message") or {}).get("content")
    if not content:
        raise ValueError("DeepSeek response has no assistant content.")
    return str(content)


def save_followup(
    thread_id: int,
    user_message: str,
    assistant_text: str,
    raw_response: dict[str, Any],
) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            INSERT INTO ai_tutor_messages (thread_id, role, content)
            VALUES (?, 'user', ?)
            """,
            (thread_id, user_message),
        )
        conn.execute(
            """
            INSERT INTO ai_tutor_messages (thread_id, role, content, rag_references_json)
            VALUES (?, 'assistant', ?, ?)
            """,
            (
                thread_id,
                assistant_text,
                json.dumps({"provider": "deepseek", "raw_response": raw_response}, ensure_ascii=False),
            ),
        )
        conn.execute(
            "UPDATE ai_tutor_threads SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (thread_id,),
        )
        conn.commit()


def write_output(
    output_path: Path,
    thread_id: int,
    model: str,
    user_message: str,
    assistant_text: str,
    raw_response: dict[str, Any],
) -> dict[str, str | int]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "thread_id": thread_id,
        "model": model,
        "user_message": user_message,
        "assistant_text": assistant_text,
        "raw_response": raw_response,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path = output_path.with_suffix(".md")
    markdown_path.write_text(
        "# DeepSeek Tutor Follow-up\n\n"
        f"Thread ID: `{thread_id}`\n\n"
        f"Model: `{model}`\n\n"
        "## User\n\n"
        f"{user_message}\n\n"
        "## Assistant\n\n"
        f"{assistant_text}\n",
        encoding="utf-8",
    )
    return {
        "json_output": str(output_path),
        "markdown_output": str(markdown_path),
        "thread_id": thread_id,
    }


def main() -> None:
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="Ask a follow-up question in an existing DeepSeek tutor thread.")
    parser.add_argument("--thread-id", type=int, required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model", default=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--thinking", default=os.environ.get("DEEPSEEK_THINKING", "disabled"), choices=["enabled", "disabled"])
    parser.add_argument("--reasoning-effort", default=os.environ.get("DEEPSEEK_REASONING_EFFORT", "high"), choices=["high", "max"])
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key or api_key == "your_deepseek_api_key_here":
        print(json.dumps({"error": "Missing DEEPSEEK_API_KEY."}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(2)

    messages = thread_messages(args.thread_id)
    messages.append({"role": "user", "content": args.message})
    response = chat_completion(
        api_key=api_key,
        base_url=args.base_url,
        model=args.model,
        messages=messages,
        thinking=args.thinking,
        reasoning_effort=args.reasoning_effort,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
    )
    text = assistant_content(response)
    save_followup(args.thread_id, args.message, text, response)

    output_path = args.output or DEFAULT_OUTPUT_DIR / f"thread_{args.thread_id}_followup_deepseek_output.json"
    result = write_output(output_path, args.thread_id, args.model, args.message, text, response)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
