# Password Manager - Self-Hosted Web Application

A secure, self-hosted password manager built with Python Flask. Store, manage, and retrieve your credentials with strong encryption and multi-user support.

## Features

- **Multi-user Support**: Register and manage multiple user accounts
- **Secure Authentication**: Password hashing with PBKDF2-SHA256
- **End-to-End Encryption**: Credentials encrypted with Fernet (AES-128)
- **User Isolation**: Each user can only access their own credentials
- **Full CRUD Operations**: Create, read, update, and delete credentials
- **Quick Search**: Find credentials by service name or username
- **Modern Web UI**: Clean, responsive interface with dark/light theme support
- **Session Management**: Secure session handling with HTTPS-ready configuration
- **No External Dependencies**: SQLite database (fully self-contained)

## Security Architecture

### Two-Layer Password Protection

1. **Master Password** (User Authentication)
   - Hashed using Werkzeug's PBKDF2-SHA256 with 600,000+ iterations
   - Never stored in plaintext
   - Used to authenticate users

2. **Credential Encryption** (At-Rest Encryption)
   - Master password + unique salt → derives Fernet key (PBKDF2HMAC, 480,000 iterations)
   - Fernet key used to encrypt all stored passwords (AES-128-CBC)
   - Fernet key stored only in server session (cleared on logout)
   - If database is stolen, credentials remain encrypted without the key

### Additional Security Measures

- **CSRF Protection**: Flask-WTF on all POST forms
- **Session Security**: HTTPONLY, SAMESITE=Lax, strong session protection
- **User Isolation**: All queries filtered by `owner_id = current_user.id`
- **Ownership Verification**: Edit/delete/reveal operations check credential ownership
- **Input Validation**: WTForms validators prevent XSS and malformed data
- **Parameterized Queries**: SQLAlchemy prevents SQL injection

## Installation

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Setup

1. **Clone/Download the project**
   ```bash
   cd "c:\MEGA\NYUAD\3-2\Static Program Analysis\vscode\vibe-coding"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Set environment variables**
   ```bash
   # Create a .env file (example provided in .env.example)
   # For production, set a strong SECRET_KEY
   # On Windows:
   # set SECRET_KEY=your-secret-key-here
   # On Linux/Mac:
   # export SECRET_KEY=your-secret-key-here
   ```

4. **Start the server**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser and navigate to: **http://127.0.0.1:5000**

## Usage

### Registration

1. Click "Register here" on the login page
2. Enter a username (3-64 characters)
3. Enter your email address
4. Create a master password (8+ characters, recommended 12+)
5. Confirm your password
6. Click "Register"

### Login

1. Enter your username
2. Enter your master password
3. Click "Login"

**Note**: Your master password is your only access to your encrypted credentials. Losing it means you cannot recover your passwords.

### Adding a Credential

1. Click "+ Add Credential" on the dashboard
2. Fill in the details:
   - **Service Name**: e.g., "Gmail", "GitHub", "AWS"
   - **Username**: Your username or email for that service
   - **Password**: The password for that service (encrypted when stored)
   - **URL**: (Optional) Link to the service website
   - **Notes**: (Optional) Any additional information
3. Click "Save Credential"

### Managing Credentials

**Viewing**:
- Your credentials appear as cards on the dashboard
- Search bar filters by service name or username in real-time

**Revealing Password**:
- Click the "👁️" eye button next to any password to reveal it
- Password auto-hides after 10 seconds for security

**Editing**:
- Click "Edit" on any credential card
- Leave the password field blank to keep the existing password
- Or enter a new password to update it
- Click "Update Credential"

**Deleting**:
- Click "Delete" on any credential card
- Confirm the deletion (cannot be undone)

**Searching**:
- Use the search bar at the top to filter credentials
- Searches by service name or username
- Click "Clear" to reset the search

### Logout

- Click "Logout" in the top-right corner
- Your session will end and the encryption key will be cleared
- You must log in again to access your credentials

## Project Structure

```
password_manager/
├── app.py                  # Flask application factory & entry point
├── config.py               # Configuration settings
├── models.py               # SQLAlchemy database models
├── crypto.py               # Fernet encryption utilities
├── forms.py                # WTForms form definitions
├── routes/
│   ├── auth.py             # Registration, login, logout
│   └── vault.py            # Credential CRUD operations
├── templates/              # HTML templates
│   ├── base.html           # Base layout
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   └── vault/
│       ├── index.html      # Dashboard
│       ├── add.html
│       └── edit.html
├── static/
│   ├── css/style.css       # Styling
│   └── js/vault.js         # Frontend interactivity
├── requirements.txt        # Python dependencies
├── password_manager.db     # SQLite database (auto-created)
└── README.md               # This file
```

## Database

- **Type**: SQLite (no setup required)
- **File**: `password_manager.db` (auto-created on first run)
- **Models**:
  - **User**: username, email, password_hash, salt, created_at
  - **Credential**: service_name, username, encrypted_password, url, notes, created_at, updated_at

## Dependencies

- **Flask**: Web framework
- **Flask-Login**: Session management
- **Flask-WTF**: CSRF protection & form handling
- **Flask-SQLAlchemy**: ORM & database integration
- **Werkzeug**: Password hashing utilities
- **cryptography**: Fernet encryption (AES-128)
- **python-dotenv**: Environment variable loading
- **email-validator**: Email validation

## Testing

Run the included test suite:
```bash
python test_functionality.py
```

This verifies:
- User registration and authentication
- Password encryption/decryption
- User isolation
- Database persistence
- All core functionality

## Performance

- Fast search with indexed queries on `(owner_id, service_name)`
- Lightweight SQLite database suitable for personal use
- Minimal dependencies for quick startup
- Session-based encryption keys (fast decryption)

## Deployment

### For Local Use (Current Setup)
- Run `python app.py` to start the dev server
- Access via `http://127.0.0.1:5000` (local only)

### For Network Access
Edit `app.py`:
```python
app.run(debug=False, host='0.0.0.0', port=5000)  # Accessible on network
```

### For Production Deployment
1. Set `SESSION_COOKIE_SECURE = True` in `config.py` (requires HTTPS)
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Deploy behind a reverse proxy (Nginx, Apache) with SSL/TLS
4. Use strong `SECRET_KEY` from environment variable
5. Use proper environment variable management (.env files)

Example with Gunicorn:
```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 app:create_app()
```

## Security Best Practices

1. **Master Password**: Use a strong, unique master password (16+ characters recommended)
2. **Browser**: Use HTTPS in production environments
3. **Database Backup**: Regularly back up `password_manager.db`
4. **Secrets**: Never commit `.env` file to version control
5. **Updates**: Keep dependencies updated for security patches
6. **Session Timeout**: Consider setting `SESSION_COOKIE_AGE` in production
7. **Access**: Restrict network access to trusted users only

## Troubleshooting

### Port Already in Use
```bash
# Change port in app.py
app.run(debug=False, host='127.0.0.1', port=5001)
```

### Database Locked
- Ensure only one instance of the app is running
- Delete `password_manager.db` to start fresh (loses all data)

### Unicode Errors on Windows
- The app is configured for Windows compatibility
- Run tests: `python test_functionality.py`

### Session Expired
- Log in again to re-establish a session and encryption key
- Your credentials in the database remain encrypted and safe

## Limitations

- Single-server architecture (not distributed)
- No automatic backups (backup `password_manager.db` manually)
- No password reset (lost master password = lost access)
- No TOTP/2FA support (can be added)
- No password sharing between users (by design)

## Contributing

Feel free to fork and submit pull requests for improvements!

## License

This project is provided as-is for educational and personal use.

## Disclaimer

This password manager is designed for personal use. While it includes security best practices, no system is 100% secure. For mission-critical password storage, consider using established password managers like KeePass, Bitwarden, or 1Password.

Always maintain backups of your credentials and never rely on a single password manager as your sole backup.
