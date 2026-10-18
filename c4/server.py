"""Localhost HTTP server for the C4 workbench (standard library only).

Serves the static frontend from ``c4/web`` and a small JSON API:

    GET  /api/health    generator availability
    GET  /api/meta      targets, learner presets, scenarios, config defaults
    GET  /api/results   committed evaluation artefacts
    POST /api/verify    run the C4 pipeline
    POST /api/generate  draft an explanation (template or Ollama)

The server binds to 127.0.0.1 by default; it has no authentication and must not be
exposed to a network.
"""

from __future__ import annotations

import json
import mimetypes
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .service import Workbench

WEB_DIR = Path(__file__).resolve().parent / "web"
MAX_BODY_BYTES = 64 * 1024
OLLAMA_TAGS = "http://localhost:11434/api/tags"


def ollama_status(model: str = "qwen3:4b", timeout: float = 1.5) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(OLLAMA_TAGS, timeout=timeout) as response:
            names = [item.get("name") for item in json.load(response).get("models", [])]
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return {"online": False, "model": model, "model_installed": False}
    return {"online": True, "model": model, "model_installed": model in names}


class ApiError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def make_handler(bench: Workbench, web_dir: Path = WEB_DIR):
    class Handler(BaseHTTPRequestHandler):
        server_version = "C4Workbench/1.0"

        # -- helpers ---------------------------------------------------------
        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, data: Any) -> None:
            self._send(status, json.dumps(data).encode("utf-8"), "application/json; charset=utf-8")

        def _read_json(self) -> dict[str, Any]:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                raise ApiError(400, "Invalid Content-Length") from None
            if length <= 0:
                raise ApiError(400, "Request body is required")
            if length > MAX_BODY_BYTES:
                raise ApiError(413, "Request body too large")
            try:
                data = json.loads(self.rfile.read(length))
            except ValueError:
                raise ApiError(400, "Body must be valid JSON") from None
            if not isinstance(data, dict):
                raise ApiError(400, "Body must be a JSON object")
            return data

        def _static(self, path: str) -> None:
            name = "index.html" if path in ("", "/") else path.lstrip("/")
            target = (web_dir / name).resolve()
            if web_dir.resolve() not in target.parents or not target.is_file():
                raise ApiError(404, "Not found")
            kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            charset = "; charset=utf-8" if kind.startswith("text/") or kind.endswith("javascript") else ""
            self._send(200, target.read_bytes(), kind + charset)

        # -- routing ---------------------------------------------------------
        def do_GET(self) -> None:  # noqa: N802
            try:
                path = self.path.split("?", 1)[0]
                if path == "/api/health":
                    self._json(200, {"status": "ok", "ollama": ollama_status()})
                elif path == "/api/meta":
                    self._json(200, bench.meta())
                elif path == "/api/results":
                    self._json(200, bench.results())
                elif path.startswith("/api/"):
                    raise ApiError(404, "Unknown endpoint")
                else:
                    self._static(path)
            except ApiError as exc:
                self._json(exc.status, {"error": str(exc)})

        def do_POST(self) -> None:  # noqa: N802
            try:
                path = self.path.split("?", 1)[0]
                if path not in ("/api/verify", "/api/generate"):
                    raise ApiError(404, "Unknown endpoint")
                payload = self._read_json()
                try:
                    if path == "/api/verify":
                        self._json(200, bench.verify(payload))
                    else:
                        self._json(200, bench.generate(payload))
                except ValueError as exc:
                    raise ApiError(400, str(exc)) from None
                except RuntimeError as exc:
                    raise ApiError(503, str(exc)) from None
            except ApiError as exc:
                self._json(exc.status, {"error": str(exc)})

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return  # keep the demo terminal quiet

    return Handler


def create_server(host: str = "127.0.0.1", port: int = 8765, bench: Workbench | None = None) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(bench or Workbench()))
