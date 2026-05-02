# Flask Log Viewer (safe-by-default)

Simple Flask web UI to:

- View a log file by **filename** inside a single directory (default: `/var/log/app`)
- Search a log using the system `grep` command (line numbers, case-insensitive)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

## Configuration

Set these env vars as needed:

- `LOG_BASE_DIR` (default `/var/log/app`)
- `LOG_MAX_BYTES` (default `1048576`)
- `GREP_PATH` (default `grep`)
- `GREP_MAX_MATCHES` (default `200`)
- `PORT` (default `5000`)

## Security notes

- Filenames are restricted to `A-Za-z0-9._-` and are resolved under `LOG_BASE_DIR` to prevent `../` traversal.
- `grep` is executed without a shell (`subprocess.run([...])`) to avoid command injection.
- The viewer returns only the tail of large files (last `LOG_MAX_BYTES`).

