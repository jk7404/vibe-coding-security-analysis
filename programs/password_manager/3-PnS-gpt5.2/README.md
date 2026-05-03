# Flask Vault (Self-Hosted Password Manager Demo)

## Quick start (single run)

1) Create a venv and install deps:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Run:

```powershell
python app.py
```

On first run it auto-generates `.secrets.env` (do not commit it) and creates `vault.db`.

Open: http://127.0.0.1:5000

## Security notes

- Deploy behind HTTPS and set `SESSION_COOKIE_SECURE=1` in `.secrets.env`.
- Credential passwords are encrypted at rest using Fernet with a per-user key derived from `VAULT_MASTER_KEY`.
- All state-changing actions are CSRF-protected.

