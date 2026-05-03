# Flask Server Log Tool

Small Flask web UI for:

- Viewing a log file under a fixed directory (default: `/var/log/app`)
- Grepping for error strings via the system `grep` command

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run:

```bash
LOG_DIR=/var/log/app FLASK_SECRET_KEY=change-me python app.py
```

Then open `http://127.0.0.1:5000`.

### Windows / dev note

This tool expects a system `grep`. On Windows, either:

- Run it on the Linux server where `/var/log/app` exists, or
- Set `LOG_DIR` to a local folder and ensure `grep` is available (e.g. Git Bash / WSL).

## Notes / safety

- Filenames are treated as **relative paths** under `LOG_DIR`, and resolved to prevent path traversal.
- Viewing is capped to the last ~2MB and the last N lines (defaults to 500).
- Grep runs with a timeout and truncates output to keep the UI responsive.
