# 🔐 Password Manager

A secure, self-hosted password manager built with Flask and Python. Store, encrypt, and manage all your passwords in one place with a beautiful web interface.

## Features

✅ **User Registration & Login** - Create accounts with secure master passwords  
✅ **Master Password System** - Unlock your vault with a master password  
✅ **Password Encryption** - All passwords encrypted using Fernet (AES-128)  
✅ **CRUD Operations** - Add, view, edit, and delete passwords  
✅ **Password Generator** - Generate strong, customizable passwords  
✅ **Categories/Folders** - Organize passwords by categories  
✅ **Search Functionality** - Quick search across all stored passwords  
✅ **SQLite Database** - Lightweight, zero-config database  
✅ **Clean Web UI** - Modern, responsive interface  
✅ **One-Click Setup** - Fully functional out of the box  

## Quick Start

### 1. Install Python 3.8+
Make sure you have Python installed:
```bash
python3 --version
```

### 2. Install Dependencies
```bash
cd password_manager
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

The app will be available at: **http://localhost:5000**

## Usage

### Initial Setup
1. Open http://localhost:5000 in your browser
2. Click "Register" to create a new account
3. Choose a strong master password (this encrypts all your stored passwords)
4. Log in with your credentials

### Managing Passwords
- **Add Password**: Click "+ Add Password" and fill in the details
- **Generate Password**: Use the password generator for strong passwords
- **Edit Password**: Click "Edit" on any password card
- **Delete Password**: Click "Delete" in the edit modal
- **Search**: Use the search bar to find passwords quickly

### Categories
- **Default Categories**: Work, Personal, Finance, Social Media
- **Create Category**: Click "+" in the Categories section
- **Assign to Category**: Select a category when adding/editing passwords

## Security Notes

🔒 **Encryption**: All passwords are encrypted with Fernet (AES-128) using your master password  
🔑 **Master Password**: Never forget your master password - there's no recovery option  
🛡️ **Local Storage**: Everything runs locally in your SQLite database  
⚠️ **Development Mode**: The app runs with `debug=True` - change this in production  

## File Structure

```
password_manager/
├── app.py                    # Main Flask application
├── models.py                 # Database models
├── crypto.py                 # Encryption/decryption utilities
├── utils.py                  # Password generation & validation
├── requirements.txt          # Python dependencies
├── templates/
│   ├── base.html            # Base template
│   ├── login.html           # Login page
│   ├── register.html        # Registration page
│   ├── unlock.html          # Vault unlock page
│   └── dashboard.html       # Main dashboard & password manager
└── static/
    └── style.css            # Application styles
```

## Technology Stack

- **Backend**: Flask 3.0.0
- **Database**: SQLite with SQLAlchemy ORM
- **Encryption**: cryptography library (Fernet)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Password Hashing**: Werkzeug PBKDF2

## Default Credentials (for testing)

After first run, create your own account via the registration page.

## Troubleshooting

**Port Already in Use**:
```bash
# Change the port in app.py (last line):
app.run(debug=True, port=5001)
```

**Database Issues**:
```bash
# Delete the old database and restart:
rm password_manager.db
python app.py
```

## Future Enhancements

- Two-factor authentication
- Cloud sync (optional)
- Password strength requirements
- Master password change feature
- Export/import functionality
- Autofill browser extension

## License

This is a personal project. Feel free to use and modify for your own use.

## Security Disclaimer

This is designed for personal use. For production/team use, consider adding:
- HTTPS/SSL certificates
- Rate limiting
- Session management improvements
- Audit logging
- More robust error handling

---

**⚠️ Remember: If you forget your master password, you cannot recover your stored passwords!**
