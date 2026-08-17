from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime
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
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_prompt_package(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "system_prompt" not in payload or "user_payload" not in payload:
        raise ValueError("Prompt package must contain system_prompt and user_payload.")
    return payload


def chat_completion(
    *,
    api_key: str,
    base_url: str,
    model: str,
    system_prompt: str,
    user_payload: dict[str, Any],
    thinking: str,
    reasoning_effort: str,
    max_tokens: int | None,
    timeout: int,
) -> dict[str, Any]:
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    body: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False, indent=2),
            },
        ],
        "thinking": {"type": thinking},
        "reasoning_effort": reasoning_effort,
        "stream": False,
    }
    if max_tokens is not None:
        body["max_tokens"] = max_tokens

    request = urllib.request.Request(
        endpoint,
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
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        raise ValueError("DeepSeek response has no assistant content.")
    return str(content)


def persist_conversation(
    prompt_package: dict[str, Any],
    assistant_text: str,
    raw_response: dict[str, Any],
) -> int:
    grading_report = prompt_package.get("user_payload", {}).get("grading_report", {})
    quiz_session_id = grading_report.get("quiz_session_id")
    title = f"TEM8 tutor feedback {datetime.now().isoformat(timespec='minutes')}"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.execute(
            """
            INSERT INTO ai_tutor_threads (quiz_session_id, title)
            VALUES (?, ?)
            """,
            (quiz_session_id, title),
        )
        thread_id = int(cursor.lastrowid)
        conn.execute(
            """
            INSERT INTO ai_tutor_messages (thread_id, role, content)
            VALUES (?, 'system', ?)
            """,
            (thread_id, prompt_package["system_prompt"]),
        )
        conn.execute(
            """
            INSERT INTO ai_tutor_messages (thread_id, role, content)
            VALUES (?, 'user', ?)
            """,
            (
                thread_id,
                json.dumps(prompt_package["user_payload"], ensure_ascii=False, indent=2),
            ),
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
        conn.commit()
    return thread_id


def write_outputs(
    *,
    output_path: Path,
    prompt_path: Path,
    model: str,
    assistant_text: str,
    raw_response: dict[str, Any],
    thread_id: int | None,
) -> dict[str, str | int | None]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "prompt_path": str(prompt_path),
        "model": model,
        "thread_id": thread_id,
        "assistant_text": assistant_text,
        "raw_response": raw_response,
    }
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    markdown_path = output_path.with_suffix(".md")
    markdown_path.write_text(
        "# DeepSeek Tutor Output\n\n"
        f"Model: `{model}`\n\n"
        f"Thread ID: `{thread_id}`\n\n"
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
    parser = argparse.ArgumentParser(description="Call DeepSeek API for TEM8 tutor feedback.")
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model", default=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--thinking", default=os.environ.get("DEEPSEEK_THINKING", "disabled"), choices=["enabled", "disabled"])
    parser.add_argument("--reasoning-effort", default=os.environ.get("DEEPSEEK_REASONING_EFFORT", "high"), choices=["high", "max"])
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key or api_key == "your_deepseek_api_key_here":
        print(
            json.dumps(
                {
                    "error": "Missing DEEPSEEK_API_KEY.",
                    "setup": "Set it in PowerShell with: $env:DEEPSEEK_API_KEY=\"your_key\" or create D:\\AIeyu\\.env from .env.example.",
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        raise SystemExit(2)

    prompt_package = load_prompt_package(args.prompt)
    response = chat_completion(
        api_key=api_key,
        base_url=args.base_url,
        model=args.model,
        system_prompt=prompt_package["system_prompt"],
        user_payload=prompt_package["user_payload"],
        thinking=args.thinking,
        reasoning_effort=args.reasoning_effort,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
    )
    text = assistant_content(response)
    thread_id = persist_conversation(prompt_package, text, response) if args.persist else None

    output_path = args.output or DEFAULT_OUTPUT_DIR / f"{args.prompt.stem}_deepseek_output.json"
    result = write_outputs(
        output_path=output_path,
        prompt_path=args.prompt,
        model=args.model,
        assistant_text=text,
        raw_response=response,
        thread_id=thread_id,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
