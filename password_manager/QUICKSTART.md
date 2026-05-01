# 🚀 Quick Start Guide

## One-Click Setup (macOS/Linux)

### Step 1: Open Terminal
Navigate to the password_manager folder:
```bash
cd ~/Desktop/C/password_manager
```

### Step 2: Run the Application
```bash
./run.sh
```

That's it! The app will:
- ✓ Check for Python installation
- ✓ Create a virtual environment
- ✓ Install all dependencies
- ✓ Start the Flask server

### Step 3: Open in Browser
Open your web browser and go to: **http://localhost:5000**

---

## One-Click Setup (Windows)

### Step 1: Open Command Prompt
Navigate to the password_manager folder:
```cmd
cd %USERPROFILE%\Desktop\C\password_manager
```

### Step 2: Run the Application
Double-click `run.bat` or in command prompt:
```cmd
run.bat
```

### Step 3: Open in Browser
Open your web browser and go to: **http://localhost:5000**

---

## Manual Setup (Alternative)

If the scripts don't work, you can manually set up:

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the App
```bash
python app.py
```

### Step 3: Access
Open http://localhost:5000 in your browser

---

## First Time Use

1. **Register an Account**
   - Click "Register"
   - Choose a username and strong master password
   - Your master password encrypts all stored passwords
   - **Important**: You cannot recover a forgotten master password!

2. **Log In**
   - Use your credentials to log in
   - You'll be taken directly to your password vault

3. **Manage Passwords**
   - Click "+ Add Password" to store a new password
   - Use the password generator for strong passwords
   - Organize with categories (Work, Personal, Finance, Social Media)
   - Search for passwords with the search bar

---

## Keyboard Shortcuts

- **Ctrl+K** or **Cmd+K**: Focus search bar
- **Enter**: Submit forms
- **Esc**: Close modals

---

## Security Tips

🔒 **Master Password**: Make it strong and memorable
- Use a mix of uppercase, lowercase, numbers, and symbols
- At least 12 characters recommended

🛡️ **Session Security**:
- The master password is kept in your session
- Closing the browser doesn't auto-logout for convenience
- Always logout on shared computers

💾 **Backup**:
- Your data is stored locally in `password_manager.db`
- Back it up periodically to a secure location

---

## Troubleshooting

### Issue: Port 5000 is already in use
**Solution**: Edit `app.py` last line:
```python
app.run(debug=True, port=5001)  # Change 5000 to any free port
```

### Issue: "No module named 'flask'"
**Solution**: Make sure dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: Python not found
**Solution**: Install Python from https://www.python.org
- On macOS: `brew install python3`
- On Windows: Download from python.org
- On Linux: `apt-get install python3`

### Issue: Database corruption
**Solution**: Delete the old database and start fresh:
```bash
rm password_manager.db  # macOS/Linux
del password_manager.db  # Windows
python app.py  # Restart
```

---

## What's New?

- ✨ Beautiful modern UI with dark/light support
- 🔐 Military-grade password encryption
- 📱 Responsive design for mobile
- 🔄 Real-time search and filtering
- 🎯 Smart password categorization
- 🔑 Secure password generator

---

## Need Help?

Check the README.md for full documentation:
```bash
cat README.md
```

Enjoy your secure password manager! 🎉
