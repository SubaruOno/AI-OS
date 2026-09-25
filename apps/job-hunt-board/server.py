#!/usr/bin/env python3
"""就活ボードのローカルサーバー。

外部ライブラリを使わない。127.0.0.1 だけで待ち受け、同じネットワークの
他の機器からは見えない。元データの Markdown は読むだけで、書き込むのは
private/job-hunt/board-state.json（対応済みの記録）だけ。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_feed  # noqa: E402
import parse  # noqa: E402

APP_DIR = Path(__file__).resolve().parent
WORKSPACE = APP_DIR.parents[1]
STATIC_DIR = APP_DIR / "static"
STATE_PATH = WORKSPACE / "private" / "job-hunt" / "board-state.json"
MYPAGES_PATH = APP_DIR / "data" / "mypages.json"

_cache = {"data": None, "stamp": None}
_lock = threading.Lock()


def read_state():
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"items": {}}
    return {"items": {}}


def read_mypages():
    """集めたマイページ一覧を返す。無ければ None。"""
    if MYPAGES_PATH.exists():
        try:
            return json.loads(MYPAGES_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def write_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state["updated"] = datetime.now().isoformat(timespec="seconds")
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE_PATH)


def load_data():
    sources = [WORKSPACE / s["file"] for s in parse.SOURCES]
    stamp = tuple(p.stat().st_mtime for p in sources if p.exists())
    with _lock:
        if _cache["data"] is None or _cache["stamp"] != stamp:
            _cache["data"] = parse.load(WORKSPACE)
            _cache["stamp"] = stamp
        return _cache["data"]


CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
}


class Handler(BaseHTTPRequestHandler):
    server_version = "JobHuntBoard/1.0"

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body: bytes, content_type: str):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, payload, code=200):
        self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _file(self, path: Path):
        if not path.exists() or not path.is_file():
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        ctype = CONTENT_TYPES.get(path.suffix, "application/octet-stream")
        self._send(200, path.read_bytes(), ctype)

    def do_GET(self):
        route = self.path.split("?", 1)[0]
        if route == "/api/data":
            try:
                payload = load_data()
            except Exception as exc:  # 解析失敗を画面で気づけるようにする
                self._json({"error": f"{type(exc).__name__}: {exc}"}, 500)
                return
            payload = dict(payload)
            payload["state"] = read_state().get("items", {})
            self._json(payload)
            return
        if route == "/api/feed":
            try:
                self._json(build_feed.build())
            except Exception as exc:
                self._json({"error": f"{type(exc).__name__}: {exc}"}, 500)
            return
        if route == "/api/mypages":
            payload = read_mypages()
            if payload is None:
                self._json({"error": "data/mypages.json がありません"}, 404)
                return
            self._json(payload)
            return
        if route == "/api/state":
            self._json(read_state())
            return
        if route in ("/", "/index.html"):
            self._file(STATIC_DIR / "index.html")
            return
        if route.startswith("/static/"):
            target = (STATIC_DIR / route[len("/static/"):]).resolve()
            if STATIC_DIR.resolve() in target.parents:
                self._file(target)
                return
        self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self):
        route = self.path.split("?", 1)[0]
        if route != "/api/state":
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._json({"error": "invalid json"}, 400)
            return
        item_id = body.get("id")
        value = body.get("value")
        if not isinstance(item_id, str) or not item_id:
            self._json({"error": "id is required"}, 400)
            return
        state = read_state()
        items = state.setdefault("items", {})
        if value in ("done", "dismissed", "open"):
            items[item_id] = {"status": value, "at": datetime.now().isoformat(timespec="seconds")}
        else:
            self._json({"error": "value must be done, dismissed, or open"}, 400)
            return
        write_state(state)
        self._json(state)


def main():
    ap = argparse.ArgumentParser(description="就活ボード")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-open", action="store_true", help="ブラウザを自動で開かない")
    args = ap.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"就活ボード: {url}")
    print("止めるときは Control-C。")
    if not args.no_open:
        subprocess.Popen(["open", url])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止しました。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
