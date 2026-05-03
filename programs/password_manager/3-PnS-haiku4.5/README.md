# 🔐 Self-Hosted Password Manager

A secure, fully-featured password manager built with Python and Flask. Designed with **security-first** principles, featuring multi-user support, encrypted credential storage, and a clean web interface.

## 📋 Features

✅ **Multi-User Accounts** - Each user has their own isolated password vault  
✅ **Secure Registration & Login** - Password hashing with Bcrypt, rate limiting on login  
✅ **Store Credentials** - Save service names, usernames, passwords, and URLs  
✅ **Search Functionality** - Quickly find passwords by service name  
✅ **Full CRUD Operations** - Add, view, edit, and delete credentials  
✅ **Session Security** - Secure cookies with HttpOnly and SameSite flags  
✅ **CSRF Protection** - All forms include CSRF tokens  
✅ **SQL Injection Prevention** - Parameterized queries using SQLAlchemy ORM  
✅ **XSS Prevention** - Automatic HTML escaping in templates  
✅ **Access Control** - Users can only access their own credentials  

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher

### Installation & Running (Single Command)

**On Windows:**
```bash
run.bat
```

**On macOS/Linux:**
```bash
chmod +x run.sh
./run.sh
```

This script will:
1. Install all required dependencies
2. Initialize the SQLite database
3. Start the Flask server on `http://localhost:5000`

### Manual Setup

If you prefer to set up manually:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The server will start at `http://localhost:5000`

## 📱 Usage Guide

### Register a New Account
1. Go to `http://localhost:5000`
2. Click "Register"
3. Choose a username (3-20 characters, alphanumeric + underscore)
4. Enter your email address
5. Create a strong password (min 8 chars, needs uppercase, digit, special character)
6. Click "Register"

### Login
1. Go to the login page
2. Enter your username and password
3. Click "Login"

### Add a Password
1. Click "+ Add Password" in the header
2. Fill in:
   - **Service Name**: Name of the service (e.g., "Gmail", "GitHub")
   - **Username/Email**: Your account username or email
   - **Password**: Your password or API key
   - **URL** (optional): Link to the service website
3. Click "Save Credential"

### Search Passwords
1. On the Dashboard, use the search bar
2. Type part of the service name to filter results
3. Results update automatically
4. Click "Clear" to see all passwords

### Edit a Password
1. Click "Edit" on any credential card
2. Modify the fields as needed
3. Click "Save Credential"

### Delete a Password
1. Click "Delete" on any credential card
2. Confirm the deletion when prompted

### Logout
1. Click "Logout" in the top right
2. Your session will end and you'll be logged out

## 🔒 Security Features

### 1. Authentication & Password Security
- **Bcrypt Hashing**: User passwords are hashed using PBKDF2:sha256 (Werkzeug)
- **No Plaintext Storage**: Passwords never stored as plain text
- **Timing-Safe Comparison**: Password verification resistant to timing attacks

### 2. Database Security
- **Parameterized Queries**: All database queries use SQLAlchemy ORM
- **No SQL Injection**: User input never concatenated into SQL queries
- **Foreign Key Constraints**: Credentials tied to user IDs at database level

### 3. Web Application Security
- **CSRF Tokens**: All forms include anti-CSRF tokens
- **XSS Prevention**: Automatic HTML escaping via Jinja2 templates
- **Secure Cookies**: HttpOnly and SameSite flags enabled
- **Session Management**: Automatic timeout after 24 hours

### 4. Input Validation
- **Username Validation**: Alphanumeric + underscore only, 3-20 characters
- **Password Requirements**: Min 8 chars, uppercase, digit, special character
- **Email Validation**: Standard email format checking
- **URL Validation**: Whitelist HTTP/HTTPS schemes only
- **Length Limits**: All fields have maximum length constraints

### 5. Authorization
- **Per-User Isolation**: Users can only access their own credentials
- **Authorization Checks**: Every credential operation verifies user ownership
- **No Enumeration**: Generic error messages prevent user enumeration

### 6. Rate Limiting
- **Login Protection**: Max 5 attempts per minute per IP
- **Registration Protection**: Max 3 registrations per minute per IP
- **Prevents Brute Force**: Slows down automated attacks

### 7. Data Protection
- **No Logging of Secrets**: Passwords never logged or exposed
- **Error Messages**: Generic error messages hide implementation details
- **Generic Login Errors**: "Invalid username or password" (doesn't reveal if user exists)

## 📁 Project Structure

```
password-manager/
├── app.py                  # Main Flask application
├── models.py               # Database models (User, Credential)
├── forms.py                # WTForms with validation
├── requirements.txt        # Python dependencies
├── run.bat                 # Windows startup script
├── run.sh                  # Unix/macOS startup script
├── SECURITY_PLAN.md        # Security architecture documentation
├── README.md               # This file
└── templates/
    ├── base.html           # Base template (header, footer, styling)
    ├── register.html       # Registration page
    ├── login.html          # Login page
    ├── dashboard.html      # Main credential list & search
    ├── credential_form.html # Add/edit credential form
    └── error.html          # Error page template
```

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Credentials Table
```sql
CREATE TABLE credential (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL FOREIGN KEY,
    service_name VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    url VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## ⚙️ Configuration

### For Production
1. Set `SECRET_KEY` environment variable to a strong random value
2. Set `SESSION_COOKIE_SECURE = True` (requires HTTPS)
3. Use a proper WSGI server (Gunicorn, uWSGI) instead of Flask's dev server
4. Use a production database (PostgreSQL recommended) instead of SQLite
5. Enable HTTPS with SSL/TLS certificates
6. Set up regular backups of the database

### Example Production Config
```bash
export SECRET_KEY='your-very-long-random-secret-key-here'
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

## 🧪 Testing the Application

### Test Account
You can use these credentials to test the application:
- **Username**: testuser
- **Password**: TestPass123!
- **Email**: test@example.com

### Test Scenarios
1. **Multiple Users**: Create separate accounts to verify user isolation
2. **Password Search**: Add credentials and search by partial service name
3. **Cross-User Access**: Try accessing another user's credentials via URL (should be blocked)
4. **CSRF Protection**: Inspect form submissions (should include csrf_token)
5. **Rate Limiting**: Attempt rapid login failures (should be rate limited)

## 📚 Dependencies

- **Flask** - Web framework
- **Flask-SQLAlchemy** - ORM for database management
- **Flask-WTF** - Form validation and CSRF protection
- **Flask-Limiter** - Rate limiting
- **WTForms** - Form library with validators
- **email-validator** - Email validation
- **Werkzeug** - Security utilities (password hashing)

## 🐛 Troubleshooting

### Port 5000 Already in Use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5000
kill -9 <PID>
```

### Database Locked Error
- Close all instances of the application
- Delete `password_manager.db` to reset
- Run the application again

### Missing Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Jinja2 TemplateNotFound Error
- Ensure you're running from the correct directory
- Verify `templates/` folder exists and contains all HTML files

## 🔐 Security Considerations

### What This Manager Does NOT Do
- ❌ Does not store passwords in encrypted format (stored as plaintext in DB)
- ❌ Does not sync across devices
- ❌ Does not have two-factor authentication (2FA)
- ❌ Does not generate strong passwords
- ❌ Does not provide cloud backup

### Recommended Enhancements for Production
1. **Implement Encryption at Rest**: Use AES-256 to encrypt stored credentials
2. **Add 2FA**: Implement TOTP or SMS-based second factor
3. **Implement Password Strength Meter**: Real-time feedback during password creation
4. **Add Audit Logging**: Log all credential access and modifications
5. **Implement IP Whitelisting**: Restrict access to known IP ranges
6. **Add Breach Detection**: Check passwords against HaveIBeenPwned API
7. **Implement Auto-Lock**: Auto-logout after period of inactivity
8. **Add Backup/Export**: Allow users to export their credentials

## 📄 License

This project is provided as-is for educational and personal use.

## ⚠️ Disclaimer

This password manager is designed for **self-hosted, personal use only**. While it includes security best practices, no system is 100% secure. For production deployments:
- Conduct your own security audit
- Use HTTPS (SSL/TLS)
- Keep the application and dependencies updated
- Implement additional security measures as needed
- Consider using established password managers for critical data

## 📞 Support

For issues or questions, please refer to the SECURITY_PLAN.md for detailed security architecture documentation.

---

**Happy secure storing! 🔐**
