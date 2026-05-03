# Flask Vault (self-hosted password manager demo)

This is a small self-hosted password manager built with **Python + Flask**:

- Multi-user registration + login
- Each user gets their own encrypted vault
- Save / edit / delete credentials (service, username, password, URL)
- Search bar
- Single-run SQLite database (`vault.db`)

## Quickstart

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Notes (security)

- Passwords are encrypted at rest using a key derived from the user’s master password (PBKDF2 + Fernet).
- The derived key is kept **in-process memory** for the active session (suitable for a single-process demo).
- If you expose this over a network, run behind HTTPS (e.g., Caddy/Nginx reverse proxy) and consider adding 2FA, rate limiting, and server-side session storage.

