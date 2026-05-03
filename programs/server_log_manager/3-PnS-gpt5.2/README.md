# Flask Log Tool (Security-First)

This is a small Flask web UI to:

- View log files by **basename** under a fixed base directory (default: `/var/log/app`)
- Search within a specific log file using the system `grep` command (fixed-string search)

## Run

1. Install deps:
   - `python -m venv .venv`
   - `./.venv/bin/pip install -r requirements.txt` (Linux/macOS) or `.\.venv\Scripts\pip install -r requirements.txt` (Windows)
2. Start:
   - `python app.py`
3. Open:
   - `http://127.0.0.1:5000`

## Configuration

- `LOG_BASE_DIR` (default `/var/log/app`)
- `LOG_VIEW_MAX_BYTES` (default `2097152`)
- `GREP_MAX_MATCHES` (default `200`)
- `GREP_TIMEOUT_S` (default `3`)
- `FLASK_HOST` (default `127.0.0.1`)
- `FLASK_PORT` (default `5000`)

## Notes

Put this behind a reverse proxy with TLS and authentication if exposed beyond localhost.

