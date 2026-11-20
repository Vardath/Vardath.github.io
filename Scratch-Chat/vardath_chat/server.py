"""Minimal OpenAI-style local HTTP API. Uses only Python standard library + local weights."""
from __future__ import annotations
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .engine import LocalChatEngine


def serve(weights: Path, host: str = "127.0.0.1", port: int = 8080) -> None:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("This development API binds to loopback only. External access is disabled.")
    engine = LocalChatEngine(weights)
    lock = threading.Lock()  # Don't overlap CPU inference jobs.

    class Handler(BaseHTTPRequestHandler):
        server_version = "VardathScratchChat/0.1"

        def _send(self, status: int, data: dict) -> None:
            content = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):  # noqa: N802
            if self.path == "/health":
                return self._send(200, {"status": "ok", "loaded": True,
                                        "model": "vardath-scratch-1", "local": True,
                                        "training_steps": engine.metadata.get("steps", None)})
            if self.path == "/v1/models":
                return self._send(200, {"object": "list", "data": [{"id": "vardath-scratch-1",
                                        "object": "model", "owned_by": "local"}]})
            return self._send(404, {"error": {"message": "Route not found"}})

        def do_POST(self):  # noqa: N802
            if self.path != "/v1/chat/completions":
                return self._send(404, {"error": {"message": "Route not found"}})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 1024 * 1024:
                    return self._send(413, {"error": {"message": "Invalid or excessive request size"}})
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                if data.get("stream"):
                    return self._send(400, {"error": {"message": "Streaming is not implemented"}})
                model = data.get("model", "vardath-scratch-1")
                if model not in {"vardath-scratch-1", "janus-local"}:
                    return self._send(404, {"error": {"message": "Model unavailable"}})
                messages = data["messages"]
                if not isinstance(messages, list) or not messages or any(
                    not isinstance(m, dict) or not isinstance(m.get("content"), str)
                    or m.get("role") not in {"system", "user", "assistant"} for m in messages
                ):
                    raise ValueError("messages must contain text-only role/content objects")
                max_tokens = int(data.get("max_tokens", 96))
                if not 1 <= max_tokens <= 512:
                    raise ValueError("max_tokens must be between 1 and 512")
                with lock:
                    answer = engine.reply(messages, max_tokens=max_tokens,
                                          temperature=float(data.get("temperature", 0.35)))
                return self._send(200, {
                    "id": "chatcmpl-" + uuid.uuid4().hex,
                    "object": "chat.completion",
                    "created": int(time.time()), "model": "vardath-scratch-1",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": answer},
                                 "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": None, "completion_tokens": None,
                              "total_tokens": None},
                })
            except (KeyError, ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as e:
                return self._send(400, {"error": {"message": str(e)}})

        def log_message(self, fmt, *args):
            print("HTTP", self.address_string(), fmt % args, flush=True)

    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Loaded local weights: {weights}", flush=True)
    print(f"Chat API listening at http://{host}:{port}/v1/chat/completions", flush=True)
    print("No Render, subscriptions, downloaded model weights or internet connections.", flush=True)
    try:
        httpd.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
