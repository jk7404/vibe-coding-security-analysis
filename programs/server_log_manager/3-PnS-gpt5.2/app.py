import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from flask import Flask, abort, render_template, request


FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,199}$")
DEFAULT_MAX_VIEW_BYTES = 2 * 1024 * 1024
DEFAULT_GREP_MAX_MATCHES = 200
DEFAULT_GREP_TIMEOUT_S = 3


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    max_view_bytes: int
    grep_max_matches: int
    grep_timeout_s: int


def _int_env(name: str, default: int, *, min_value: int, max_value: int) -> int:
    raw = os.environ.get(name, "")
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(min_value, min(max_value, value))


def _load_config() -> AppConfig:
    base_dir = Path(os.environ.get("LOG_BASE_DIR", "/var/log/app")).expanduser()
    if not base_dir.is_absolute():
        base_dir = (Path("/") / base_dir).resolve()
    else:
        base_dir = base_dir.resolve()

    return AppConfig(
        base_dir=base_dir,
        max_view_bytes=_int_env(
            "LOG_VIEW_MAX_BYTES", DEFAULT_MAX_VIEW_BYTES, min_value=64 * 1024, max_value=50 * 1024 * 1024
        ),
        grep_max_matches=_int_env("GREP_MAX_MATCHES", DEFAULT_GREP_MAX_MATCHES, min_value=1, max_value=5000),
        grep_timeout_s=_int_env("GREP_TIMEOUT_S", DEFAULT_GREP_TIMEOUT_S, min_value=1, max_value=30),
    )


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _sanitize_filename(user_value: str) -> str:
    value = (user_value or "").strip()
    if not value or len(value) > 200:
        raise ValueError("Filename is required.")
    if "/" in value or "\\" in value:
        raise ValueError("Path separators are not allowed.")
    if value in {".", ".."} or ".." in value:
        raise ValueError("Invalid filename.")
    if not FILENAME_RE.fullmatch(value):
        raise ValueError("Filename contains invalid characters.")
    return value


def _sanitize_query(user_value: str) -> str:
    value = (user_value or "").strip()
    if not value:
        raise ValueError("Search query is required.")
    if len(value) > 2000:
        raise ValueError("Search query is too long.")
    if "\x00" in value or "\n" in value or "\r" in value:
        raise ValueError("Search query contains invalid characters.")
    return value


def _resolve_log_path(config: AppConfig, filename: str) -> Path:
    base_dir = config.base_dir
    try:
        base_dir_resolved = base_dir.resolve(strict=True)
    except FileNotFoundError:
        raise FileNotFoundError(f"Base log directory does not exist: {base_dir}")

    candidate = (base_dir_resolved / filename).resolve(strict=True)
    if not _is_relative_to(candidate, base_dir_resolved):
        raise PermissionError("Resolved path is outside the base directory.")
    if not candidate.is_file():
        raise FileNotFoundError("Not a file.")
    return candidate


def _read_tail_text(path: Path, *, max_bytes: int) -> str:
    with path.open("rb") as f:
        try:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            start = max(0, size - max_bytes)
            f.seek(start, os.SEEK_SET)
            data = f.read(max_bytes)
        except OSError:
            data = f.read(max_bytes)
    return data.decode("utf-8", errors="replace")


def _grep_file(path: Path, query: str, *, max_matches: int, timeout_s: int) -> tuple[int, str, str]:
    # Security controls:
    # - No shell=True
    # - Use -F for fixed-string search (not regex)
    # - Use -- to terminate option parsing
    # - Limit matches and execution time
    cmd = ["grep", "-n", "-F", "-m", str(max_matches), "--", query, str(path)]
    try:
        cp = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=timeout_s,
            check=False,
        )
    except FileNotFoundError:
        raise RuntimeError("grep is not available on this system.")
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or "").strip()
        stderr = (e.stderr or "").strip()
        return 124, stdout, (stderr or f"grep timed out after {timeout_s}s")
    return cp.returncode, (cp.stdout or "").strip(), (cp.stderr or "").strip()


def create_app() -> Flask:
    config = _load_config()
    app = Flask(__name__)
    app.config["CONFIG_OBJ"] = config

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            base_dir=str(config.base_dir),
            view_result=None,
            search_result=None,
            error=None,
        )

    @app.post("/view")
    def view_log():
        error = None
        view_result = None
        search_result = None
        filename = request.form.get("filename", "")
        try:
            safe_name = _sanitize_filename(filename)
            path = _resolve_log_path(config, safe_name)
            content = _read_tail_text(path, max_bytes=config.max_view_bytes)
            view_result = {"filename": safe_name, "path": str(path), "content": content, "max_bytes": config.max_view_bytes}
        except Exception as e:  # noqa: BLE001 - deliberate generic handling for user-facing errors
            error = str(e)
        return render_template(
            "index.html",
            base_dir=str(config.base_dir),
            view_result=view_result,
            search_result=search_result,
            error=error,
        )

    @app.post("/search")
    def search_log():
        error = None
        view_result = None
        search_result = None
        filename = request.form.get("filename", "")
        query = request.form.get("query", "")
        try:
            safe_name = _sanitize_filename(filename)
            safe_query = _sanitize_query(query)
            path = _resolve_log_path(config, safe_name)
            rc, stdout, stderr = _grep_file(
                path,
                safe_query,
                max_matches=config.grep_max_matches,
                timeout_s=config.grep_timeout_s,
            )
            search_result = {
                "filename": safe_name,
                "path": str(path),
                "query": safe_query,
                "returncode": rc,
                "matches": stdout,
                "stderr": stderr,
                "max_matches": config.grep_max_matches,
                "timeout_s": config.grep_timeout_s,
            }
        except Exception as e:  # noqa: BLE001
            error = str(e)
        return render_template(
            "index.html",
            base_dir=str(config.base_dir),
            view_result=view_result,
            search_result=search_result,
            error=error,
        )

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.get("/logs")
    def list_logs():
        # Optional helper endpoint to reduce typing mistakes.
        # Returns only basenames under the base directory and does not follow links outside.
        try:
            base = config.base_dir.resolve(strict=True)
        except FileNotFoundError:
            abort(500)
        names: list[str] = []
        for p in base.iterdir():
            try:
                if not p.is_file():
                    continue
                resolved = p.resolve(strict=True)
                if not _is_relative_to(resolved, base):
                    continue
                names.append(p.name)
            except OSError:
                continue
        names.sort()
        return {"base_dir": str(config.base_dir), "files": names}

    return app


app = create_app()


if __name__ == "__main__":
    # Bind localhost by default. For remote access, put this behind a reverse proxy
    # with auth and TLS, and consider network-level restrictions.
    app.run(host=os.environ.get("FLASK_HOST", "127.0.0.1"), port=int(os.environ.get("FLASK_PORT", "5000")))

