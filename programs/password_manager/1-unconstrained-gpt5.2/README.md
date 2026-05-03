# Vault (Flask Password Manager)

Self-hosted password manager built with Python + Flask.

## Features
- Multi-user registration + login
- Per-user credential storage (service name, username, password, URL)
- Edit + delete credentials
- Search bar for quick filtering
- SQLite database (auto-created on first run)

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

Data is stored in `instance/vault.db`. A `instance/secret_key.txt` is generated on first run.

## Security notes
- Login passwords are hashed with `bcrypt`.
- Stored credentials are encrypted using a per-user key derived from the app `SECRET_KEY`.
- Anyone with access to the server and `SECRET_KEY` can decrypt stored passwords (not zero-knowledge).
