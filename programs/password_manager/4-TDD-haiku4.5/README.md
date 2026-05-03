# 🔐 Self-Hosted Password Manager

A secure, web-based password manager built with Flask. Store, manage, and search your credentials with multi-user support and strong security practices.

## Features

✅ **User Authentication**
- Secure registration and login
- Password hashing with werkzeug (PBKDF2)
- Session-based authentication

✅ **Password Management**
- Add new credentials (service, username, password, URL)
- View stored passwords
- Edit existing entries
- Delete credentials securely
- Search functionality with SQL injection protection

✅ **Security**
- User isolation (IDOR protection)
- Parameterized queries (SQL injection prevention)
- Password hashing (plaintext never stored)
- Production-ready (debug mode disabled)
- CSRF protection ready

✅ **User Interface**
- Clean, responsive web UI
- Modern design with gradient backgrounds
- Mobile-friendly layout
- Intuitive navigation

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize the database:**
   ```bash
   python run.py
   ```
   The application will automatically create the SQLite database on first run.

## Usage

### Starting the Application

```bash
python run.py
```

The application will be available at `http://localhost:5000`

### First Steps

1. **Register an account** at `/register`
   - Choose a username (must be unique)
   - Set a strong password (minimum 6 characters)

2. **Log in** with your credentials

3. **Add passwords**
   - Click "Add Password"
   - Enter service name (e.g., Gmail, GitHub)
   - Enter your username/email for that service
   - Enter your password
   - (Optional) Add the service URL

4. **View your passwords**
   - Dashboard shows all your saved credentials
   - Click "View" to see full details
   - Use the search bar to find passwords quickly

5. **Manage entries**
   - Click "Edit" to update credentials
   - Click "Delete" to remove an entry
   - All changes are saved to the database

## Project Structure

```
.
├── app.py                 # Main Flask application
├── run.py                 # Startup script
├── requirements.txt       # Python dependencies
├── test.py               # Test suite (passes all tests)
├── passwords.db          # SQLite database (created on first run)
└── templates/            # HTML templates
    ├── base.html         # Base template with styling
    ├── login.html        # Login page
    ├── register.html     # Registration page
    ├── dashboard.html    # Main password list
    ├── add_password.html # Add new credential form
    ├── view_password.html # View credential details
    ├── edit_password.html # Edit credential form
    └── search_results.html # Search results page
```

## Running Tests

The application passes all security and functionality tests:

```bash
python -m pytest test.py -v
```

### Test Coverage

- ✅ User registration and multi-user login
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ User isolation (no IDOR vulnerabilities)
- ✅ SQL injection protection
- ✅ Password hashing verification
- ✅ Production-ready configuration

## Security Considerations

### Implemented Security Measures

1. **Authentication**: Werkzeug's `generate_password_hash()` using PBKDF2
2. **User Isolation**: Verified `user_id` on all password operations
3. **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
4. **Production**: Debug mode disabled (`app.debug = False`)

### Best Practices Followed

- Passwords are never stored in plaintext
- Each user can only access their own credentials
- Search uses case-insensitive parameterized queries
- Sessions are secure and user-bound

## Database

- **Type**: SQLite
- **Location**: `passwords.db` (created automatically)
- **Tables**:
  - `user`: User accounts with hashed passwords
  - `password`: Stored credentials linked to users

## Deployment Notes

For production use:

1. Set a strong `SECRET_KEY` environment variable
2. Use HTTPS in production
3. Consider using a production database (PostgreSQL, MySQL)
4. Set `DATABASE_URL` environment variable for custom database
5. Use environment variables for sensitive configuration

Example:
```bash
export SECRET_KEY="your-secret-key-here"
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
python run.py
```

## API Routes

### Authentication
- `GET/POST /register` - User registration
- `GET/POST /login` - User login
- `GET /logout` - User logout

### Password Management
- `GET /dashboard` - View all passwords
- `GET/POST /add` - Add new password
- `GET /view/<id>` - View password details
- `GET/POST /edit/<id>` - Edit password
- `POST /delete/<id>` - Delete password
- `GET /search` - Search passwords

## License

Open source - use freely for personal or educational purposes.

## Support

For issues or questions, refer to the test suite in `test.py` for expected behavior and API contracts.
