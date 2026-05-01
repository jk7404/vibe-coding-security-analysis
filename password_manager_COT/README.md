# 🔐 Secure Password Manager

A self-hosted, fully encrypted password manager built with Flask and SQLite. All passwords are encrypted with AES-256-GCM, and the master password is never stored in plaintext.

## Features

✅ **User Authentication** - Secure registration and login with master password  
✅ **Master Password System** - PBKDF2-derived encryption keys, Argon2 password hashing  
✅ **Password Encryption** - AES-256-GCM authenticated encryption  
✅ **Full CRUD** - Store, retrieve, edit, and delete passwords  
✅ **Password Generation** - Cryptographically secure random password generator  
✅ **Categories/Folders** - Organize passwords by category  
✅ **Search Functionality** - Search by title, username, or category  
✅ **Clean Web UI** - Modern, responsive Bootstrap interface  
✅ **SQLite Database** - Lightweight, self-contained storage  
✅ **Session Management** - Secure sessions with httponly cookies  
✅ **Input Validation** - Protection against SQL injection and XSS  

---

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The app will start on `http://localhost:5000`

### 3. Create Your Account

- Navigate to the **Register** page
- Choose a strong master password (12+ chars, uppercase, lowercase, numbers, special chars)
- **⚠️ IMPORTANT:** If you forget your master password, all your passwords are lost forever. Write it down somewhere safe!

### 4. Start Adding Passwords

- Click "Add Password" to save new credentials
- Use the password generator for strong random passwords
- Organize passwords into categories
- Search through your passwords anytime

---

## Architecture & Security

### Master Password & Key Derivation

- **Master Password Hashing:** Argon2 (via werkzeug) - resistant to GPU/ASIC attacks
- **Encryption Key Derivation:** PBKDF2 with 480,000 iterations
- **Key Material:** 32-byte (256-bit) key derived from master password + user salt

### Password Encryption

- **Algorithm:** AES-256-GCM (authenticated encryption)
- **IV:** Unique 96-bit IV per password (stored alongside ciphertext)
- **Authentication:** GCM mode prevents tampering; decryption fails if data is modified
- **Storage:** Ciphertext and IV stored in base64 encoding in SQLite

### Session Management

- **Cookies:** HTTPOnly, Secure (in production), SameSite=Lax
- **Validation:** Master password verified once per login, never stored in cookies
- **Regeneration:** New session created on each login
- **Timeout:** 1 hour inactivity timeout

### Input Validation & Security

- **SQL Injection:** Parameterized queries throughout
- **XSS Prevention:** Template auto-escaping enabled
- **CSRF Protection:** Can be added with Flask-WTF if needed
- **Password Strength:** Enforced via regex validation
- **Password Comparison:** Constant-time comparison (werkzeug's `check_password_hash`)

### Database Schema

```sql
users:
  - id (PK)
  - username (UNIQUE)
  - master_password_hash
  - salt (base64-encoded)
  - created_at

passwords:
  - id (PK)
  - user_id (FK)
  - title
  - category
  - username
  - encrypted_password (base64)
  - iv (base64)
  - created_at
  - updated_at
```

---

## Security Considerations

### What's Protected
✅ Passwords are encrypted with AES-256-GCM  
✅ Master password uses Argon2 hashing  
✅ Each user has unique salt for key derivation  
✅ SQLite database stores only encrypted data  
✅ Secure session cookies  

### What You Need to Do
- **Keep your master password safe** - there's no recovery mechanism
- **Use HTTPS in production** - set `SESSION_COOKIE_SECURE = True`
- **Keep the database file secure** - restrict file permissions on `password_manager.db`
- **Change the `SECRET_KEY` in production** - use `os.environ.get('SECRET_KEY', ...)`

### Known Limitations
⚠️ No password recovery if master password is forgotten  
⚠️ This is a self-hosted local app (not cloud-backed)  
⚠️ No two-factor authentication (could be added)  
⚠️ No audit logging (could be added)  
⚠️ SQLite is single-user (not suitable for multi-user production)  

---

## File Structure

```
B/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── password_manager.db    # SQLite database (created on first run)
├── README.md             # This file
└── templates/
    ├── base.html         # Base template with navbar & styling
    ├── login.html        # Login page
    ├── register.html     # Registration page
    ├── dashboard.html    # Password dashboard
    ├── add_password.html # Add password form
    ├── edit_password.html # Edit password form
    ├── search_results.html # Search results page
    ├── 404.html          # 404 error page
    └── 500.html          # 500 error page
```

---

## Usage Examples

### Adding a Password
1. Click "Add Password"
2. Enter title (e.g., "Gmail")
3. Enter username/email
4. Either enter password manually or click "Generate Random Password"
5. Optionally assign to a category
6. Click "Save Password"

### Viewing a Password
- Passwords are hidden by default (shown as dots)
- Click the eye icon to reveal
- Click the clipboard icon to copy to clipboard

### Searching
- Use the search bar in the navbar
- Search by password title, username, or category
- Results update in real-time

### Generating a Password
- Click "Generate Random Password" when adding/editing
- Random password uses: A-Z, a-z, 0-9, special characters

---

## Development & Customization

### Adding Two-Factor Authentication
You could extend the `users` table to include 2FA secrets and add verification routes.

### Adding Audit Logging
Create an `audit_log` table to track access/modifications with timestamps and user IDs.

### Adding Cloud Sync
Implement optional cloud backup with E2E encryption (master password never sent to cloud).

### Adding TOTP Support
Store encrypted TOTP seeds and generate one-time codes in the UI.

---

## Security Audit Checklist

- [x] Master password hashing with Argon2
- [x] AES-256-GCM encryption with unique IVs
- [x] Parameterized SQL queries (no injection)
- [x] Template auto-escaping (no XSS)
- [x] Secure session cookies
- [x] Input validation (username, password strength)
- [x] Constant-time password comparison
- [x] No plaintext passwords in logs/memory
- [x] Proper error handling (generic error messages)

---

## Testing the Application

### Test Account
You can create a test account with:
- **Username:** `testuser`
- **Master Password:** `TestPassword123!`

Then add test passwords to verify all functionality:
- Add / Edit / Delete
- Search
- Categories
- Password visibility toggle
- Copy to clipboard

---

## Troubleshooting

### "Port 5000 already in use"
```bash
# Change the port in app.py:
app.run(debug=True, host='localhost', port=5001)
```

### "ModuleNotFoundError: No module named 'cryptography'"
```bash
pip install -r requirements.txt
```

### "Database locked"
- Make sure only one instance of the app is running
- Delete `password_manager.db` and restart to reset

### Decryption errors
- Check that your master password is correct
- The encryption key won't match if password is wrong
- Database may be corrupted if manually edited

---

## License

MIT - Feel free to use and modify as needed.

---

## ⚠️ Disclaimer

This is a reference implementation for educational purposes. For production use with sensitive data:
- Conduct a professional security audit
- Use industry-standard password managers (Bitwarden, 1Password, etc.)
- Consider regulatory requirements (HIPAA, PCI-DSS, etc.)
- Add proper logging, monitoring, and backup strategies

---

**Created:** 2026  
**Author:** Security-Focused Python Developer  
**Last Updated:** May 1, 2026
