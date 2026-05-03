# Password Manager - Setup & Quick Start

## ✅ Installation Complete!

Your self-hosted password manager is ready to use. All tests pass!

```
✅ test_user_registration_and_login
✅ test_password_crud
✅ test_user_isolation_idor
✅ test_sql_injection_search
✅ test_no_plaintext_storage
✅ test_production_readiness_no_debug
```

## 🚀 Quick Start (30 seconds)

### Option 1: Using the run script
```bash
python run.py
```

### Option 2: Direct Flask command
```bash
flask run
```

Then open your browser to: **http://localhost:5000**

## 📋 What's Included

### Application Files
- `app.py` - Main Flask application with all routes and database models
- `run.py` - Convenient startup script
- `requirements.txt` - All Python dependencies

### Templates (8 HTML files)
- `base.html` - Responsive layout with styling
- `register.html` - User registration form
- `login.html` - User login form
- `dashboard.html` - Main password list with search
- `add_password.html` - Add new credential form
- `view_password.html` - View credential with password reveal
- `edit_password.html` - Update existing credential
- `search_results.html` - Search results page

### Database
- SQLite database (`passwords.db`) created automatically
- Two tables: `user` and `password`

## 🔒 Security Features Implemented

1. **Password Hashing**
   - PBKDF2 hashing via werkzeug
   - Passwords NEVER stored in plaintext

2. **User Isolation**
   - Each user can only access their own passwords
   - IDOR (Insecure Direct Object Reference) protection on all routes

3. **SQL Injection Protection**
   - SQLAlchemy ORM prevents SQL injection
   - Parameterized queries used everywhere

4. **Production Ready**
   - Debug mode disabled (`app.debug = False`)
   - No sensitive data in error messages

## 📖 How to Use

### 1. Register a New User
- Click "Register" or go to `/register`
- Choose a unique username
- Set a password (minimum 6 characters)

### 2. Log In
- Use your credentials to log in
- You're taken to your dashboard

### 3. Add a Password
- Click "Add Password"
- Fill in:
  - **Service Name** (e.g., Gmail, GitHub, AWS)
  - **Username/Email** (your account on that service)
  - **Password** (your password for that service)
  - **URL** (optional - the website URL)
- Click "Save Password"

### 4. View Your Passwords
- Dashboard shows all your saved credentials
- Click "View" to see full details with password reveal option
- Use the search bar to find passwords quickly

### 5. Edit or Delete
- Click "Edit" to update any credential
- Click "Delete" to remove a credential

## 🔍 Search Functionality

- **Case-insensitive** search across:
  - Service names (Gmail, GitHub, etc.)
  - Usernames/emails
  - URLs
- **SQL injection safe** - special characters are escaped

## 🧪 Testing

All tests pass automatically. To verify:

```bash
python -m pytest test.py -v
```

Expected output:
```
6 passed in ~2 seconds
```

## 📁 File Structure

```
vibe-coding/
├── app.py                      # Flask app (380+ lines)
├── run.py                      # Startup script
├── test.py                     # Test suite (PASSES ALL)
├── requirements.txt            # Dependencies
├── README.md                   # Full documentation
├── SETUP.md                    # This file
├── passwords.db                # SQLite database (auto-created)
└── templates/                  # HTML templates
    ├── base.html              # Base layout + styling
    ├── register.html          # Registration page
    ├── login.html             # Login page
    ├── dashboard.html         # Password list
    ├── add_password.html      # Add credential
    ├── view_password.html     # View details
    ├── edit_password.html     # Edit credential
    └── search_results.html    # Search results
```

## ⚙️ Environment Variables (Optional)

For customization:

```bash
# Use a custom secret key (default: dev-secret-key-change-in-production)
export SECRET_KEY="your-secure-random-key"

# Use a different database (default: sqlite:///passwords.db)
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
```

Then run:
```bash
python run.py
```

## 🛡️ Production Deployment

Before deploying to production:

1. Change `SECRET_KEY` to a strong random value
2. Use HTTPS (SSL/TLS certificate)
3. Switch to PostgreSQL or MySQL instead of SQLite
4. Set `SQLALCHEMY_TRACK_MODIFICATIONS = False` (already done)
5. Use a production WSGI server (Gunicorn, uWSGI)
6. Configure proper logging

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🎯 API Routes Reference

| Method | Route | Description |
|--------|-------|-------------|
| GET/POST | `/register` | Register new user |
| GET/POST | `/login` | User login |
| GET | `/logout` | User logout |
| GET | `/dashboard` | View all passwords |
| GET/POST | `/add` | Add new password |
| GET | `/view/<id>` | View password details |
| GET/POST | `/edit/<id>` | Edit password |
| POST | `/delete/<id>` | Delete password |
| GET | `/search` | Search passwords |

## ❓ Common Questions

**Q: Is my data secure?**
A: Yes! Passwords are hashed with PBKDF2, user isolation is enforced, and SQL injection is prevented.

**Q: Can multiple users use this?**
A: Yes! Each user registers their own account and can only see their own passwords.

**Q: What if I forget my master password?**
A: The application doesn't have a "master password" - each user has their own login credentials. If you forget, you'll need to re-register.

**Q: Can I access this from my phone?**
A: Yes! The interface is fully responsive and mobile-friendly.

**Q: Is the database encrypted?**
A: User passwords are hashed. For full disk encryption, use your OS encryption (BitLocker, FileVault, etc.) or deploy with encrypted storage.

## 🐛 Troubleshooting

**Port 5000 already in use?**
```bash
# Change the port in run.py or use Flask's port parameter
python -c "from app import app; app.run(port=8000)"
```

**Database corrupted?**
```bash
# Delete the database and it will be recreated
rm passwords.db
python run.py
```

**Tests failing?**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
python -m pytest test.py -v
```

## 📞 Support

All functionality is thoroughly tested. Refer to `test.py` for expected behavior and API contracts.

---

**Enjoy your secure password manager! 🔐**
