import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for


@dataclass(frozen=True)
class Config:
    base_log_dir: Path
    max_bytes: int
    grep_path: str
    grep_max_matches: int


def load_config() -> Config:
    base = Path(os.environ.get("LOG_BASE_DIR", "/var/log/app")).resolve()
    max_bytes = int(os.environ.get("LOG_MAX_BYTES", "1048576"))  # 1 MiB
    grep_path = os.environ.get("GREP_PATH", "grep")
    grep_max_matches = int(os.environ.get("GREP_MAX_MATCHES", "200"))
    return Config(
        base_log_dir=base,
        max_bytes=max_bytes,
        grep_path=grep_path,
        grep_max_matches=grep_max_matches,
    )


app = Flask(__name__)
cfg = load_config()

_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _resolve_log_path(filename: str) -> Path:
    if not filename or not _SAFE_NAME_RE.fullmatch(filename):
        abort(400, "Invalid filename. Use only letters, numbers, dot, underscore, dash.")

    candidate = (cfg.base_log_dir / filename).resolve()
    try:
        candidate.relative_to(cfg.base_log_dir)
    except ValueError:
        abort(400, "Invalid path.")

    return candidate


def _read_tail_bytes(path: Path, max_bytes: int) -> str:
    # Read at most max_bytes from the end of the file to keep responses fast.
    # If the file is smaller, read the whole thing.
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        abort(404, "Log file not found.")
    except OSError:
        abort(403, "Unable to access log file.")

    start = max(0, size - max_bytes)
    try:
        with path.open("rb") as f:
            f.seek(start)
            data = f.read(max_bytes)
    except IsADirectoryError:
        abort(400, "Not a file.")
    except OSError:
        abort(403, "Unable to read log file.")

    # Best-effort decode; logs are typically utf-8 but may contain odd bytes.
    return data.decode("utf-8", errors="replace")


@app.get("/")
def index():
    filename = request.args.get("file", "").strip()
    q = request.args.get("q", "").strip()
    return render_template(
        "index.html",
        base_dir=str(cfg.base_log_dir),
        filename=filename,
        q=q,
    )


@app.get("/view")
def view_log():
    filename = request.args.get("file", "").strip()
    if not filename:
        return redirect(url_for("index"))

    path = _resolve_log_path(filename)
    if not path.exists():
        abort(404, "Log file not found.")
    if not path.is_file():
        abort(400, "Not a file.")

    content = _read_tail_bytes(path, cfg.max_bytes)
    return render_template(
        "view.html",
        base_dir=str(cfg.base_log_dir),
        filename=filename,
        bytes_limit=cfg.max_bytes,
        content=content,
    )


@app.get("/search")
def search():
    filename = request.args.get("file", "").strip()
    q = request.args.get("q", "").strip()
    if not filename or not q:
        return redirect(url_for("index", file=filename, q=q))

    path = _resolve_log_path(filename)
    if not path.exists():
        abort(404, "Log file not found.")
    if not path.is_file():
        abort(400, "Not a file.")

    # Run grep safely (no shell). -n for line numbers, -i for case-insensitive by default.
    # -- to end options so queries starting with '-' are treated as patterns.
    cmd = [
        cfg.grep_path,
        "-n",
        "-i",
        f"--max-count={cfg.grep_max_matches}",
        "--",
        q,
        str(path),
    ]

    try:
        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
            check=False,
        )
    except FileNotFoundError:
        abort(500, "grep not found on this system. Set GREP_PATH or install grep.")
    except subprocess.TimeoutExpired:
        abort(504, "Search timed out.")

    # grep exit codes: 0 match, 1 no match, 2 error.
    results = completed.stdout
    error = None
    if completed.returncode == 2:
        error = completed.stderr.strip() or "grep error"

    return render_template(
        "search.html",
        base_dir=str(cfg.base_log_dir),
        filename=filename,
        q=q,
        cmd=" ".join(cmd),
        results=results,
        error=error,
        max_matches=cfg.grep_max_matches,
    )


@app.get("/healthz")
def healthz():
    return {"ok": True, "base_log_dir": str(cfg.base_log_dir)}


if __name__ == "__main__":
    # For development only; use gunicorn/uwsgi in production.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)

