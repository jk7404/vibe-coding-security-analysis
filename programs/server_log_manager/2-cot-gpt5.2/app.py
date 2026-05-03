import os
import subprocess
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, url_for


DEFAULT_LOG_DIR = "/var/log/app"
MAX_VIEW_BYTES = 2 * 1024 * 1024
DEFAULT_TAIL_LINES = 500
MAX_TAIL_LINES = 5000

MAX_GREP_QUERY_LEN = 200
MAX_GREP_SECONDS = 5
MAX_GREP_FILES = 2000
MAX_GREP_OUTPUT_LINES = 500


def _commonpath_is_parent(parent: Path, child: Path) -> bool:
    try:
        parent_str = os.path.normcase(str(parent))
        child_str = os.path.normcase(str(child))
        return os.path.commonpath([parent_str, child_str]) == parent_str
    except Exception:
        return False


def _resolve_safe_path(base_dir: Path, user_path: str) -> Path:
    if not user_path or len(user_path) > 255:
        raise ValueError("Invalid filename.")

    # Avoid obvious path traversal / absolute paths early.
    if user_path.startswith(("/", "\\")) or ":" in user_path:
        raise ValueError("Only relative log paths are allowed.")

    candidate = (base_dir / user_path).resolve()
    base_resolved = base_dir.resolve()

    if not _commonpath_is_parent(base_resolved, candidate):
        raise ValueError("Path escapes log directory.")

    return candidate


def _list_logs(base_dir: Path) -> list[str]:
    if not base_dir.exists() or not base_dir.is_dir():
        return []

    logs: list[str] = []
    for p in base_dir.rglob("*"):
        if p.is_file():
            try:
                rel = p.relative_to(base_dir).as_posix()
            except Exception:
                continue
            logs.append(rel)

    logs.sort()
    return logs[:MAX_GREP_FILES]


def _tail_text(path: Path, max_lines: int) -> str:
    # Read at most MAX_VIEW_BYTES from the end of the file.
    size = path.stat().st_size
    start = max(0, size - MAX_VIEW_BYTES)

    with path.open("rb") as f:
        f.seek(start)
        data = f.read(MAX_VIEW_BYTES)

    # If we started mid-file, drop the first partial line for readability.
    if start != 0:
        nl = data.find(b"\n")
        if nl != -1:
            data = data[nl + 1 :]

    text = data.decode("utf-8", errors="replace")
    if max_lines <= 0:
        return text

    lines = deque(text.splitlines(), maxlen=max_lines)
    return "\n".join(lines)


@dataclass
class GrepResult:
    cmd: list[str]
    returncode: int
    output: str
    truncated: bool


def _grep_dir(log_dir: Path, query: str, filename: str | None) -> GrepResult:
    query = (query or "").strip()
    if not query:
        raise ValueError("Search query is required.")
    if len(query) > MAX_GREP_QUERY_LEN:
        raise ValueError(f"Search query too long (>{MAX_GREP_QUERY_LEN}).")

    if filename:
        target = _resolve_safe_path(log_dir, filename)
        if not target.exists() or not target.is_file():
            raise FileNotFoundError("Log file not found.")
        files = [str(target)]
    else:
        paths = []
        for p in log_dir.rglob("*"):
            if p.is_file():
                paths.append(str(p))
                if len(paths) >= MAX_GREP_FILES:
                    break
        files = paths

    cmd = ["grep", "-nH", "--color=never", "-F", query, *files]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=MAX_GREP_SECONDS,
            check=False,
        )
    except FileNotFoundError as e:
        raise RuntimeError("`grep` not found on this system.") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"`grep` timed out after {MAX_GREP_SECONDS}s.") from e

    # grep returns 0 when matches found, 1 when none found, >1 for errors
    output = (proc.stdout or "") + (proc.stderr or "")
    lines = output.splitlines()
    truncated = False
    if len(lines) > MAX_GREP_OUTPUT_LINES:
        truncated = True
        lines = lines[:MAX_GREP_OUTPUT_LINES]
        lines.append(f"... truncated to {MAX_GREP_OUTPUT_LINES} lines ...")
        output = "\n".join(lines)

    return GrepResult(cmd=cmd, returncode=proc.returncode, output=output, truncated=truncated)


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")

    log_dir = Path(os.environ.get("LOG_DIR", DEFAULT_LOG_DIR))

    @app.get("/")
    def index():
        filename = request.args.get("filename", "")
        query = request.args.get("q", "")
        tail_lines = request.args.get("tail", "")

        logs = _list_logs(log_dir)

        view_text = None
        view_path = None
        view_error = None

        if filename:
            try:
                safe_path = _resolve_safe_path(log_dir, filename)
                if not safe_path.exists() or not safe_path.is_file():
                    raise FileNotFoundError("Log file not found.")

                n = DEFAULT_TAIL_LINES
                if tail_lines:
                    n = int(tail_lines)
                n = max(1, min(MAX_TAIL_LINES, n))

                view_text = _tail_text(safe_path, n)
                view_path = str(safe_path)
            except Exception as e:
                view_error = str(e)

        grep_result = None
        grep_error = None
        if query:
            try:
                grep_result = _grep_dir(log_dir, query, filename or None)
            except Exception as e:
                grep_error = str(e)

        return render_template(
            "index.html",
            log_dir=str(log_dir),
            logs=logs,
            filename=filename,
            tail_lines=tail_lines or str(DEFAULT_TAIL_LINES),
            view_path=view_path,
            view_text=view_text,
            view_error=view_error,
            query=query,
            grep_result=grep_result,
            grep_error=grep_error,
        )

    @app.post("/view")
    def view_post():
        filename = (request.form.get("filename") or "").strip()
        tail = (request.form.get("tail") or "").strip()
        return redirect(url_for("index", filename=filename, tail=tail))

    @app.post("/search")
    def search_post():
        filename = (request.form.get("filename") or "").strip()
        tail = (request.form.get("tail") or "").strip()
        q = (request.form.get("q") or "").strip()
        return redirect(url_for("index", filename=filename, tail=tail, q=q))

    @app.get("/healthz")
    def healthz():
        return {"ok": True, "log_dir": str(log_dir)}

    return app


app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)

