# 🔐 Password Manager - Complete Project Index

## Overview
A fully functional, self-hosted password manager built with Flask and Python. Features military-grade encryption, user authentication, and a beautiful modern UI.

## Project Structure

```
password_manager/
├── app.py                      # Main Flask application (300 lines)
├── models.py                   # Database models (SQLAlchemy ORM)
├── crypto.py                   # Encryption/decryption utilities
├── utils.py                    # Password generation & strength validation
├── requirements.txt            # Python dependencies
├── run.sh                       # Unix/macOS startup script
├── run.bat                      # Windows startup script
├── README.md                    # Full documentation
├── QUICKSTART.md               # Quick start guide
├── INDEX.md                     # This file
├── .gitignore                  # Git ignore rules
├── templates/
│   ├── base.html               # Base HTML template
│   ├── login.html              # Login page
│   ├── register.html           # Registration page
│   ├── unlock.html             # Master password unlock page
│   └── dashboard.html          # Main password manager UI (500+ lines)
└── static/
    └── style.css               # Modern CSS styling (600+ lines)
```

## Core Features

### 1. User Management
- **Registration**: Create account with username and master password
- **Login**: Authenticate users securely
- **Master Password**: Unlock vault on each session
- **Session Management**: Automatic timeout support

### 2. Password Security
- **Fernet Encryption**: AES-128 military-grade encryption
- **PBKDF2**: Key derivation from master password
- **Per-User Salt**: Unique encryption salt per user
- **Secure Hashing**: Werkzeug password hashing for master password

### 3. Password Management
- **Add Password**: Store new passwords with metadata
- **View Passwords**: List all stored passwords with search
- **Edit Password**: Modify existing password records
- **Delete Password**: Securely remove passwords
- **Copy Password**: One-click copy to clipboard
- **Password Generator**: Create strong random passwords

### 4. Organization
- **Categories**: Create custom folders/categories
- **Default Categories**: Work, Personal, Finance, Social Media
- **Color Coding**: Visual organization with custom colors
- **Search & Filter**: Find passwords instantly

### 5. User Interface
- **Responsive Design**: Works on desktop, tablet, mobile
- **Modern Styling**: Clean, professional appearance
- **Dark/Light Theme**: Easy on the eyes
- **Modal Dialogs**: Intuitive password management
- **Real-time Updates**: Instant search and filtering

## Technical Stack

| Component | Technology |
|-----------|-----------|
| **Web Framework** | Flask 3.0.0 |
| **Database** | SQLite + SQLAlchemy ORM |
| **Encryption** | cryptography library (Fernet) |
| **Authentication** | Werkzeug (PBKDF2 + bcrypt) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Python Version** | 3.8+ |

## File Details

### app.py (Main Application)
- Flask app initialization and configuration
- 13 route endpoints:
  - `/` - Home redirect
  - `/register` - User registration
  - `/login` - User login
  - `/dashboard` - Main UI
  - `/api/passwords` - Get passwords (with search/filter)
  - `/api/password/add` - Create password
  - `/api/password/<id>/update` - Edit password
  - `/api/password/<id>/delete` - Delete password
  - `/api/categories` - Get user categories
  - `/api/category/add` - Create category
  - `/api/generate-password` - Generate random password
  - `/unlock` - Master password unlock
  - `/logout` - Clear session
- Middleware: login_required decorator, session validation

### models.py (Database)
- **User Model**: username, master_password_hash, encryption_salt
- **Category Model**: name, color, user_id
- **Password Model**: title, username, email, encrypted_password, url, notes, category_id
- Relationships: One-to-many (User → Categories, User → Passwords)

### crypto.py (Encryption)
- `derive_key()`: Generate encryption key from master password using PBKDF2
- `encrypt_password()`: Encrypt password with Fernet
- `decrypt_password()`: Decrypt encrypted password

### utils.py (Utilities)
- `generate_password()`: Create random passwords with configurable options
- `validate_password_strength()`: Rate password strength (0-6 score)

### templates/dashboard.html (UI)
- Main password manager interface
- Sidebar with categories
- Search bar
- Passwords grid with cards
- 5 Modal dialogs:
  - Add Password
  - Edit Password
  - Add Category
  - Password Generator
- 100+ lines of JavaScript for interactivity

### static/style.css (Styling)
- Modern CSS with CSS variables
- Responsive grid layout
- Modal styling
- Card components
- Form elements
- Mobile-optimized

## How It Works

### User Flow
1. **Registration**: User creates account with master password
   - Master password hashed and stored
   - Unique encryption salt generated
   - Default categories created

2. **Login**: User authenticates
   - Username/password verified
   - User ID stored in session
   - Master password temporarily stored in session

3. **Password Storage**: User adds a password
   - Master password derives encryption key
   - Password encrypted with key and salt
   - Encrypted password stored in database
   - Plaintext never stored

4. **Password Retrieval**: User views stored password
   - Encrypted password retrieved from database
   - Master password key derived
   - Password decrypted in memory
   - Plaintext displayed to user only

5. **Logout**: User clears session
   - Session cleared
   - Master password key removed from memory
   - User redirected to login

## Security Model

### What's Encrypted
- ✅ All stored passwords
- ✅ Each password individually
- ✅ Data at rest in SQLite

### What's NOT Encrypted
- ❌ Username (needed for login)
- ❌ User metadata (titles, URLs, notes)
- ❌ Category information (for organization)
- ℹ️ These could be encrypted but would prevent searching

### Master Password Flow
```
Master Password (User Input)
    ↓
PBKDF2 Key Derivation + Salt
    ↓
32-byte Encryption Key
    ↓
Fernet Cipher
    ↓
Encrypted Passwords
```

## Database Schema

### users table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    master_password_hash VARCHAR(255) NOT NULL,
    encryption_salt VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### categories table
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#3498db',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

### passwords table
```sql
CREATE TABLE passwords (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    category_id INTEGER,
    title VARCHAR(255) NOT NULL,
    username VARCHAR(255),
    email VARCHAR(255),
    encrypted_password TEXT NOT NULL,
    url VARCHAR(500),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(category_id) REFERENCES categories(id)
);
```

## API Endpoints

### Authentication
- `POST /register` - Create new account
- `POST /login` - Authenticate user
- `GET /unlock` - Unlock vault
- `POST /unlock` - Submit master password
- `GET /logout` - Clear session

### Passwords
- `GET /api/passwords` - List passwords (with search)
- `POST /api/password/add` - Add new password
- `POST /api/password/<id>/update` - Update password
- `POST /api/password/<id>/delete` - Delete password
- `POST /api/password/<id>/decrypt` - Get plaintext password

### Categories
- `GET /api/categories` - List categories
- `POST /api/category/add` - Create category

### Utilities
- `POST /api/generate-password` - Generate random password

## Running the Application

### Quick Start (Automated)
```bash
cd ~/Desktop/C/password_manager

# macOS/Linux
./run.sh

# Windows
run.bat
```

### Manual Start
```bash
pip install -r requirements.txt
python app.py
```

### Access
Open http://localhost:5000 in your browser

## Configuration

### Debug Mode
In app.py, line 300:
```python
app.run(debug=True, port=5000)
```

Change `port=5000` to use a different port if 5000 is busy.

### Database
SQLite file: `password_manager.db` (auto-created)

## Testing Credentials
After setup, create your own account via the registration page.

## Performance Considerations

- **Small database**: Suitable for 1000s of passwords
- **Encryption overhead**: ~10-50ms per encrypt/decrypt
- **Search performance**: O(n) linear search (suitable for <10k passwords)
- **Concurrent users**: Single-user by default (each has own account)

## Future Enhancements

- [ ] Two-factor authentication
- [ ] Master password change feature
- [ ] Bulk import/export
- [ ] Cloud sync option
- [ ] Browser auto-fill extension
- [ ] TOTP/OTP support
- [ ] Password sharing with other users
- [ ] Audit log/history
- [ ] Master password strength meter
- [ ] Duplicate password detection

## Limitations & Known Issues

1. **Single User Session**: Only one login per user at a time
2. **No Recovery**: Lost master password = lost passwords
3. **No Backup**: Database loss = data loss
4. **No Sync**: Data is local only
5. **No HTTPS**: Dev mode is HTTP only (add SSL in production)

## License & Usage

This is a personal project for educational and personal use. Modify and use as needed.

---

**Created**: 2026  
**Status**: Fully Functional ✓  
**Ready for**: Personal use, self-hosting, learning

For detailed documentation, see:
- `README.md` - Full feature documentation
- `QUICKSTART.md` - Setup instructions
- Code comments - Implementation details
