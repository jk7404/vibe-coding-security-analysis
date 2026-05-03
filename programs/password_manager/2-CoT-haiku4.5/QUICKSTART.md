# Quick Start Guide

## 30-Second Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the server
python app.py

# 3. Open browser
# Navigate to: http://127.0.0.1:5000
```

## First-Time Use

1. **Create your account**
   - Click "Register here"
   - Username: `john_doe`
   - Email: `john@example.com`
   - Password: Create a strong password (8+ characters)
   - Confirm password and submit

2. **Log in**
   - Username: `john_doe`
   - Password: Your password
   - Click "Login"

3. **Add your first credential**
   - Click "+ Add Credential"
   - Service Name: `Gmail`
   - Username: `your_email@gmail.com`
   - Password: Your Gmail password
   - URL: `https://gmail.com` (optional)
   - Click "Save Credential"

4. **View your password**
   - On the dashboard, find the Gmail credential card
   - Click the "👁️" eye button to reveal the password
   - It auto-hides after 10 seconds

5. **Search your credentials**
   - Use the search bar to find credentials by service or username
   - Type "Gmail" to filter

6. **Edit or delete**
   - Click "Edit" to modify a credential
   - Click "Delete" to remove it (cannot be undone)

7. **Log out**
   - Click "Logout" in the top-right corner

## Test Everything Works

Run the test suite:
```bash
python test_functionality.py
```

You should see:
```
[OK] Database initialized
[OK] User registered: testuser
[OK] Password hash verification works
[OK] Fernet key derived successfully
[OK] Password encrypted: gAAAAABp9...
[OK] Credential saved for Gmail
[OK] Credential ownership check passed
[OK] Password decrypted correctly
[OK] User isolation verified (user2 can't see user1's credentials)
[OK] User can retrieve their own credentials
[OK] Database contains 2 users

============================================================
ALL TESTS PASSED!
============================================================
```

## Key Features to Try

- **Multi-user**: Register another user account and verify they can't see the first user's credentials
- **Search**: Type different service names and usernames in the search bar
- **Password reveal**: Click the eye icon and watch the password auto-hide after 10 seconds
- **Edit**: Edit a credential and change only the password (leave blank to keep old)
- **Mobile**: Open on your phone - the UI is fully responsive

## Important Notes

1. **Master Password**: Your master password is like your main key. If you forget it, you cannot recover your credentials.
2. **Database**: All data is stored in `password_manager.db` in the same directory
3. **Encryption**: Credentials are encrypted with your master password using AES-128
4. **No Cloud**: Everything stays on your computer - no data is sent anywhere
5. **Backup**: Make copies of `password_manager.db` to back up your credentials

## Troubleshooting

**"Port 5000 is already in use"**
- Change the port in `app.py` (line: `app.run(...)`)
- Or kill the process using port 5000

**"Module not found" error**
- Run: `pip install -r requirements.txt` again
- Make sure Python 3.7+ is installed

**"Database locked"**
- Close all instances of the app
- Start it fresh: `python app.py`

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Customize the styling in `static/css/style.css`
- Deploy to production (see README.md > Deployment section)
- Add features like TOTP 2FA, password strength meter, etc.

## Support

If you encounter issues:
1. Check the console output for error messages
2. Run `python test_functionality.py` to verify setup
3. Ensure Python 3.7+ is installed: `python --version`
4. Verify dependencies: `pip list | grep Flask`

Enjoy your secure password manager!
