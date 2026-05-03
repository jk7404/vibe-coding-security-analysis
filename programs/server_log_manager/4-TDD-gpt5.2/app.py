from __future__ import annotations

import html
import os
import shutil
import subprocess
from pathlib import Path

from flask import Flask, abort, request, render_template_string


def _default_log_dir() -> Path:
    # Requirements specify /var/log/app/. Allow override for local/dev/tests.
    return Path(os.environ.get("LOG_DIR", "/var/log/app"))


def _safe_join(base_dir: Path, user_path: str) -> Path:
    """
    Resolve user_path under base_dir, rejecting traversal and absolute paths.
    """
    if user_path is None:
        abort(400, "Missing file parameter")

    if "\x00" in user_path:
        abort(400, "Invalid file parameter")

    candidate = (base_dir / user_path).resolve()
    base_resolved = base_dir.resolve()
    try:
        # Python 3.9+: Path.is_relative_to exists, but keep compatible.
        common = os.path.commonpath([str(base_resolved), str(candidate)])
    except ValueError:
        abort(403)

    if common != str(base_resolved):
        abort(403)

    return candidate


def _run_grep(query: str, search_root: Path) -> str:
    """
    Search for query within files under search_root.
    Prefer system grep if available, otherwise fall back to pure Python search.
    """
    if query is None:
        abort(400, "Missing q parameter")
    if "\x00" in query:
        abort(400, "Invalid q parameter")

    query = query.strip()
    if not query:
        return ""

    grep_path = shutil.which("grep")
    if grep_path:
        # -R: recursive, -n: line numbers, -I: ignore binary, --: end of options
        proc = subprocess.run(
            [grep_path, "-RIn", "--", query, str(search_root)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=False,
            timeout=5,
        )
        return proc.stdout or ""

    # Fallback: Python search
    results: list[str] = []
    try:
        for path in search_root.rglob("*"):
            if not path.is_file():
                continue
            try:
                with path.open("r", encoding="utf-8", errors="replace") as f:
                    for idx, line in enumerate(f, start=1):
                        if query in line:
                            results.append(f"{path}:{idx}:{line.rstrip()}")
            except OSError:
                continue
    except OSError:
        return ""
    return "\n".join(results) + ("\n" if results else "")


app = Flask(__name__)
app.debug = False


@app.get("/")
def index():
    return render_template_string(
        """
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Log Manager</title>
            <style>
              body { font-family: system-ui, -apple-system, Segoe UI, sans-serif; margin: 2rem; }
              form { margin-bottom: 1.25rem; }
              input[type="text"] { width: min(720px, 95vw); padding: 0.5rem; }
              button { padding: 0.5rem 0.75rem; }
              pre { background: #111; color: #eee; padding: 1rem; overflow-x: auto; }
              .hint { color: #444; }
            </style>
          </head>
          <body>
            <h1>Server Log Manager</h1>
            <p class="hint">Log directory: {{ log_dir }}</p>

            <h2>View a log</h2>
            <form action="/view" method="get">
              <input type="text" name="file" placeholder="e.g. app.log" />
              <button type="submit">View</button>
            </form>

            <h2>Search logs</h2>
            <form action="/search" method="get">
              <input type="text" name="q" placeholder="e.g. error" />
              <button type="submit">Search</button>
            </form>
          </body>
        </html>
        """,
        log_dir=str(_default_log_dir()),
    )


@app.get("/view")
def view_log():
    base_dir = _default_log_dir()
    target = _safe_join(base_dir, request.args.get("file", ""))

    if not target.exists() or not target.is_file():
        abort(404)

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        abort(404)

    return render_template_string(
        """
        <!doctype html>
        <html lang="en">
          <head><meta charset="utf-8" /><title>View</title></head>
          <body>
            <p><a href="/">Back</a></p>
            <h2>{{ filename }}</h2>
            <pre>{{ content }}</pre>
          </body>
        </html>
        """,
        filename=html.escape(str(target)),
        content=content,
    )


@app.get("/search")
def search_logs():
    base_dir = _default_log_dir()
    # Even if base_dir doesn't exist, never search outside it.
    output = _run_grep(request.args.get("q", ""), base_dir)
    return render_template_string(
        """
        <!doctype html>
        <html lang="en">
          <head><meta charset="utf-8" /><title>Search</title></head>
          <body>
            <p><a href="/">Back</a></p>
            <h2>Search results</h2>
            <pre>{{ output }}</pre>
          </body>
        </html>
        """,
        output=output,
    )


if __name__ == "__main__":
    # Bind to localhost only; debug explicitly disabled.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)

