from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

import tag_config as cfg

_UI_DIR = Path(__file__).resolve().parent.parent / "ui"


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_jsonl(path: Path) -> list[dict]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        result = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    result.append(json.loads(line))
                except Exception:
                    pass
        return result
    except Exception:
        return []


def _governance_state() -> dict:
    matrix = _read_json(cfg.AUTHORITY_MATRIX_FILE)
    governed = bool(matrix.get("governed") or matrix.get("governed_mode"))
    return {
        "governed": governed,
        "authority_matrix_loaded": cfg.AUTHORITY_MATRIX_FILE.exists(),
        "runtime_path": str(cfg.RUNTIME_DIR),
        "config_dir": str(cfg.RUNTIME_CONFIG_DIR),
    }


def _heartbeat_state() -> dict:
    data = _read_json(cfg.HEARTBEAT_FILE)
    last_pulse = data.get("timestamp") or data.get("last_pulse")
    session_id = data.get("session_id")
    session_alive = data.get("session_alive")
    return {
        "last_pulse": last_pulse,
        "session_id": session_id,
        "session_alive": session_alive,
    }


def _engram_state() -> dict:
    entries = _read_jsonl(cfg.ENGRAM_FILE)
    recent_tag = None
    if entries:
        last = entries[-1]
        recent_tag = last.get("tag") or last.get("type") or last.get("kind")
    return {
        "entry_count": len(entries),
        "recent_tag": recent_tag,
    }


def _hindsight_state() -> dict:
    entries = _read_jsonl(cfg.HINDSIGHT_FILE)
    sources: set[str] = set()
    for e in entries:
        src = e.get("source") or e.get("origin")
        if src:
            sources.add(str(src))
    return {
        "total": len(entries),
        "source_count": len(sources),
    }


def _hooks_state() -> list[dict]:
    hooks = []
    try:
        for p in sorted(cfg.HOOKS_DIR.iterdir()):
            if p.is_file() and not p.name.startswith("."):
                hooks.append({"name": p.stem, "active": True, "file": p.name})
    except Exception:
        pass
    return hooks


def _recent_decisions(limit: int = 20) -> list[dict]:
    decisions: list[dict] = []
    try:
        for p in sorted(cfg.AUDIT_DIR.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True):
            entries = _read_jsonl(p)
            for e in reversed(entries):
                if "verdict" in e or "decision" in e:
                    if "verdict" not in e and "decision" in e:
                        e = dict(e)
                        e["verdict"] = e["decision"]
                    decisions.append(e)
                    if len(decisions) >= limit:
                        break
            if len(decisions) >= limit:
                break
    except Exception:
        pass
    decisions.sort(key=lambda d: d.get("timestamp") or d.get("ts") or "", reverse=True)
    return decisions[:limit]


def _build_status() -> dict:
    return {
        "governance": _governance_state(),
        "heartbeat": _heartbeat_state(),
        "engram": _engram_state(),
        "hindsight": _hindsight_state(),
        "hooks": _hooks_state(),
        "recent_decisions": _recent_decisions(),
    }


_MIME = {
    ".html": "text/html; charset=utf-8",
    ".css":  "text/css; charset=utf-8",
    ".js":   "application/javascript; charset=utf-8",
    ".json": "application/json",
    ".ico":  "image/x-icon",
    ".png":  "image/png",
    ".svg":  "image/svg+xml",
}


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # silence default request logging
        pass

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, path: str) -> None:
        if path == "/":
            path = "/index.html"
        file_path = _UI_DIR / path.lstrip("/")
        try:
            file_path = file_path.resolve()
            _UI_DIR.resolve()
            if not str(file_path).startswith(str(_UI_DIR.resolve())):
                self.send_error(403)
                return
        except Exception:
            self.send_error(403)
            return

        if not file_path.exists() or not file_path.is_file():
            self.send_error(404)
            return

        ext  = file_path.suffix.lower()
        mime = _MIME.get(ext, "application/octet-stream")
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/health":
            gov = _governance_state()
            self._send_json({"status": "ok", "governed": gov["governed"]})
        elif path == "/api/status":
            self._send_json(_build_status())
        else:
            self._serve_static(path)


def serve(port: int = 18800) -> None:
    server = HTTPServer(("127.0.0.1", port), _Handler)
    print(f"TaG dashboard running at http://localhost:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def build_setup_snapshot(state: dict) -> dict:
    """Kept for backwards compatibility."""
    return {
        "mode": state.get("mode"),
        "runtime_path": state.get("runtime_path"),
        "governed": bool(state.get("governed")),
        "health": state.get("health", "unknown"),
    }
