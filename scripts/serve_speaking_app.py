"""Optional localhost speech gateway; IIS routes /api/speaking/* here."""
from __future__ import annotations

import argparse
import asyncio
import os
from contextlib import suppress
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
from aiohttp import web

from speaking_runtime import Conversation, LEVELS, Providers, SCENES, authenticated_id, initialize_usage, reserve_session

ROOT = Path(__file__).resolve().parents[1]


def load_env():
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def ready():
    return (os.environ.get("SPEAKING_ENABLED") == "1" and
            all(os.environ.get(key) for key in ("DASHSCOPE_API_KEY", "SPEAKING_ASR_URL", "DEEPSEEK_API_KEY")) and
            os.environ.get("SPEAKING_ASR_URL", "").startswith("wss://"))


async def status(request):
    try:
        user_id = authenticated_id(request.app["db"], request.cookies.get("aieyu_session", ""))
    except (PermissionError, OSError, Exception):
        user_id = None
    return web.json_response({"ready": ready(), "authenticated": user_id is not None,
                              "session_seconds": request.app["seconds"], "tts": "device",
                              "message": "" if ready() else "口语服务尚未配置完成，请联系管理员。"})


async def socket_handler(request):
    app = request.app
    if request.headers.get("Origin") not in app["origins"]:
        raise web.HTTPForbidden(text="来源不允许")
    if not ready():
        raise web.HTTPServiceUnavailable(text="语音服务未配置")
    try:
        user_id = authenticated_id(app["db"], request.cookies.get("aieyu_session", ""))
    except PermissionError:
        raise web.HTTPUnauthorized(text="请先登录") from None
    if user_id in app["active"] or len(app["active"]) >= app["concurrency"]:
        raise web.HTTPTooManyRequests(text="已有口语会话或当前名额已满")
    app["active"].add(user_id)
    ws = web.WebSocketResponse(heartbeat=15, max_msg_size=8192)
    conversation = None
    watcher = None
    try:
        await ws.prepare(request)
        first = await ws.receive_json(timeout=15)
        if (first.get("type") != "start" or first.get("consent") is not True or
                first.get("scene") not in SCENES or first.get("level") not in LEVELS):
            await ws.send_json({"type": "notice", "text": "请选择场景、水平并同意语音处理后开始。"})
            return ws
        reserve_session(app["db"], user_id, app["seconds"], app["user_limit"], app["total_limit"])
        conversation = Conversation(ws, app["providers"], first["scene"], first["level"])

        async def check_login():
            while True:
                await asyncio.sleep(10)
                try:
                    authenticated_id(app["db"], request.cookies.get("aieyu_session", ""))
                except Exception:
                    await ws.close(code=1008, message=b"Session expired")
                    return

        watcher = asyncio.create_task(check_login())
        await conversation.listen()
        async with asyncio.timeout(app["seconds"]):
            async for message in ws:
                if message.type == aiohttp.WSMsgType.BINARY:
                    if len(message.data) > 6400 or len(message.data) % 2:
                        raise ValueError("无效的音频帧")
                    if conversation.phase == "listening":
                        try:
                            conversation.audio.put_nowait(message.data)
                        except asyncio.QueueFull:
                            raise ValueError("网络拥堵，请稍后重试。") from None
                elif message.type == aiohttp.WSMsgType.TEXT:
                    event = message.json()
                    command = event.get("type")
                    if command == "pause":
                        await conversation.cancel()
                        await conversation.emit("state", value="paused")
                    elif command in {"resume", "interrupt"}:
                        # Do not let repeated commands repeatedly open paid upstream sockets.
                        if conversation.phase in {"paused", "playing", "thinking"}:
                            await conversation.listen()
                    elif command == "played":
                        await conversation.played(event.get("turn"))
                    elif command == "end":
                        await conversation.feedback()
                        await conversation.emit("state", value="ended")
                        break
                    else:
                        raise ValueError("不支持的口语操作")
                else:
                    break
    except asyncio.TimeoutError:
        with suppress(Exception):
            await ws.send_json({"type": "notice", "text": "本次练习时间已到，对话已结束。"})
    except ValueError as exc:
        with suppress(Exception):
            await ws.send_json({"type": "notice", "text": str(exc)})
    except Exception:
        with suppress(Exception):
            await ws.send_json({"type": "notice", "text": "连接暂时不可用，请稍后重试。"})
    finally:
        if watcher:
            watcher.cancel()
            with suppress(asyncio.CancelledError):
                await watcher
        if conversation:
            await conversation.cancel()
        app["active"].discard(user_id)
        await ws.close()
    return ws


async def preview_proxy(request):
    # Optional local preview only; destination is fixed by server configuration.
    url = request.app["preview"] + request.rel_url.path_qs
    headers = {key: request.headers[key] for key in ("Content-Type", "Cookie") if key in request.headers}
    try:
        async with request.app["http"].request(request.method, url, data=await request.read(), headers=headers,
                                               allow_redirects=False) as response:
            result = web.Response(body=await response.read(), status=response.status)
            for key in ("Content-Type", "Set-Cookie", "Location"):
                for value in response.headers.getall(key, []):
                    result.headers.add(key, value)
            return result
    except aiohttp.ClientError:
        raise web.HTTPBadGateway(text="请先启动学生端服务。") from None


def create_app(db_path=None, origins=None, preview="", providers=None):
    app = web.Application(client_max_size=2 * 1024 * 1024)
    app["db"] = Path(db_path or ROOT / "database" / "russian_ai_tutor.sqlite").resolve()
    app["origins"] = set(origins or os.environ.get("SPEAKING_ALLOWED_ORIGINS", "http://127.0.0.1:8767").split(","))
    app["seconds"] = min(600, max(30, int(os.environ.get("SPEAKING_SESSION_SECONDS", "180"))))
    app["user_limit"] = int(os.environ.get("SPEAKING_DAILY_SECONDS", "540"))
    app["total_limit"] = int(os.environ.get("SPEAKING_TOTAL_DAILY_SECONDS", "3600"))
    app["concurrency"] = max(1, min(5, int(os.environ.get("SPEAKING_CONCURRENCY", "2"))))
    app["active"] = set()
    app["preview"] = preview.rstrip("/")

    async def lifespan(application):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=75, sock_connect=10)) as http:
            application["http"] = http
            application["providers"] = providers or Providers(http)
            yield

    app.cleanup_ctx.append(lifespan)
    app.router.add_get("/api/speaking/status", status)
    app.router.add_get("/api/speaking/ws", socket_handler)
    if preview:
        target = urlparse(preview)
        if target.scheme != "http" or target.hostname not in {"127.0.0.1", "localhost"}:
            raise ValueError("预览代理只能连接本机学生端。")
        app.router.add_route("*", "/{path:.*}", preview_proxy)
    return app


def main():
    load_env()
    parser = argparse.ArgumentParser(description="AIeyu optional real-time speaking gateway")
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--db", type=Path, default=ROOT / "database" / "russian_ai_tutor.sqlite")
    parser.add_argument("--preview-upstream", default="")
    parser.add_argument("--initialize", action="store_true", help="Back up and create the usage table")
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error("数据库不存在；不要初始化新的学生库。")
    if args.initialize:
        initialize_usage(args.db)
    web.run_app(create_app(args.db, preview=args.preview_upstream), host="127.0.0.1", port=args.port,
                access_log=None)


if __name__ == "__main__":
    main()
