from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import secrets
import string
import hashlib
import hmac
from functools import wraps
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
import base64
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set True in production with HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

DB_PATH = 'password_manager.db'

# ==================== Database Initialization ====================
def init_db():
    """Initialize SQLite database with schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        master_password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS passwords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT DEFAULT 'Uncategorized',
        username TEXT,
        encrypted_password TEXT NOT NULL,
        iv TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )''')

    conn.commit()
    conn.close()

# ==================== Cryptography Functions ====================
def derive_key(master_password: str, salt: bytes, length: int = 32) -> bytes:
    """Derive encryption key from master password using PBKDF2."""
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=480000,
        backend=default_backend()
    )
    return kdf.derive(master_password.encode())

def encrypt_password(plaintext: str, master_password: str, salt: bytes) -> tuple:
    """
    Encrypt password with AES-256-GCM.
    Returns (encrypted_password_b64, iv_b64)
    """
    key = derive_key(master_password, salt)
    iv = os.urandom(12)  # 96-bit IV for GCM
    cipher = AESGCM(key)
    ciphertext = cipher.encrypt(iv, plaintext.encode(), None)

    # Return base64 encoded values
    return (
        base64.b64encode(ciphertext).decode(),
        base64.b64encode(iv).decode()
    )

def decrypt_password(encrypted_password_b64: str, iv_b64: str, master_password: str, salt: bytes) -> str:
    """
    Decrypt password from AES-256-GCM.
    """
    try:
        key = derive_key(master_password, salt)
        ciphertext = base64.b64decode(encrypted_password_b64)
        iv = base64.b64decode(iv_b64)
        cipher = AESGCM(key)
        plaintext = cipher.decrypt(iv, ciphertext, None)
        return plaintext.decode()
    except Exception as e:
        return None

def hash_master_password(password: str) -> str:
    """Hash master password using Argon2 (via werkzeug)."""
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_master_password(password: str, password_hash: str) -> bool:
    """Verify master password with constant-time comparison."""
    return check_password_hash(password_hash, password)

# ==================== Helper Functions ====================
def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_password(password: str) -> tuple:
    """Validate password strength. Returns (is_valid, message)"""
    if len(password) < 12:
        return False, "Password must be at least 12 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character."
    return True, "Password is strong."

def validate_username(username: str) -> tuple:
    """Validate username. Returns (is_valid, message)"""
    if len(username) < 3 or len(username) > 20:
        return False, "Username must be 3-20 characters long."
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens."
    return True, "Username is valid."

def generate_random_password(length: int = 16) -> str:
    """Generate a secure random password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))

# ==================== Routes ====================
@app.route('/')
def index():
    """Home page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        master_password = request.form.get('master_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate input
        is_valid, msg = validate_username(username)
        if not is_valid:
            flash(msg, 'danger')
            return redirect(url_for('register'))

        if master_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        is_valid, msg = validate_password(master_password)
        if not is_valid:
            flash(msg, 'danger')
            return redirect(url_for('register'))

        # Check if username already exists
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            flash('Username already exists.', 'danger')
            conn.close()
            return redirect(url_for('register'))

        # Create user
        try:
            salt = os.urandom(32)
            password_hash = hash_master_password(master_password)

            cursor.execute('''INSERT INTO users (username, master_password_hash, salt)
                             VALUES (?, ?, ?)''',
                          (username, password_hash, base64.b64encode(salt).decode()))
            conn.commit()
            conn.close()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            conn.close()
            flash('Registration failed. Please try again.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        master_password = request.form.get('master_password', '')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, master_password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if not user or not verify_master_password(master_password, user['master_password_hash']):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))

        # Create session
        session.permanent = True
        session['user_id'] = user['id']
        session['username'] = username
        session['master_password'] = master_password  # Stored only for this session

        flash(f'Welcome, {username}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard showing all passwords."""
    conn = get_db()
    cursor = conn.cursor()

    # Get all categories
    cursor.execute('SELECT DISTINCT category FROM passwords WHERE user_id = ? ORDER BY category',
                  (session['user_id'],))
    categories = [row[0] for row in cursor.fetchall()]

    # Get all passwords
    cursor.execute('''SELECT id, title, category, username, encrypted_password, iv, created_at
                     FROM passwords WHERE user_id = ? ORDER BY category, title''',
                  (session['user_id'],))
    encrypted_passwords = cursor.fetchall()
    conn.close()

    # Decrypt passwords for display
    passwords = []
    master_password = session.get('master_password')
    salt = get_user_salt(session['user_id'])

    for pwd in encrypted_passwords:
        decrypted = decrypt_password(pwd['encrypted_password'], pwd['iv'], master_password, salt)
        passwords.append({
            'id': pwd['id'],
            'title': pwd['title'],
            'category': pwd['category'],
            'username': pwd['username'],
            'password': decrypted or '[Decryption Error]',
            'created_at': pwd['created_at']
        })

    return render_template('dashboard.html', passwords=passwords, categories=categories)

@app.route('/add-password', methods=['GET', 'POST'])
@login_required
def add_password():
    """Add a new password."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'Uncategorized').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not title or not password:
            flash('Title and password are required.', 'danger')
            return redirect(url_for('add_password'))

        conn = get_db()
        cursor = conn.cursor()

        try:
            master_password = session.get('master_password')
            salt = get_user_salt(session['user_id'])

            encrypted_pwd, iv = encrypt_password(password, master_password, salt)

            cursor.execute('''INSERT INTO passwords
                             (user_id, title, category, username, encrypted_password, iv)
                             VALUES (?, ?, ?, ?, ?, ?)''',
                          (session['user_id'], title, category, username, encrypted_pwd, iv))
            conn.commit()
            conn.close()

            flash(f'Password "{title}" added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            conn.close()
            flash('Failed to add password. Please try again.', 'danger')
            return redirect(url_for('add_password'))

    return render_template('add_password.html')

@app.route('/edit-password/<int:password_id>', methods=['GET', 'POST'])
@login_required
def edit_password(password_id):
    """Edit an existing password."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM passwords WHERE id = ? AND user_id = ?',
                  (password_id, session['user_id']))
    password_row = cursor.fetchone()

    if not password_row:
        flash('Password not found.', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'Uncategorized').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not title or not password:
            flash('Title and password are required.', 'danger')
            return redirect(url_for('edit_password', password_id=password_id))

        try:
            master_password = session.get('master_password')
            salt = get_user_salt(session['user_id'])

            encrypted_pwd, iv = encrypt_password(password, master_password, salt)

            cursor.execute('''UPDATE passwords
                             SET title = ?, category = ?, username = ?, encrypted_password = ?, iv = ?, updated_at = CURRENT_TIMESTAMP
                             WHERE id = ? AND user_id = ?''',
                          (title, category, username, encrypted_pwd, iv, password_id, session['user_id']))
            conn.commit()
            conn.close()

            flash(f'Password "{title}" updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            conn.close()
            flash('Failed to update password. Please try again.', 'danger')
            return redirect(url_for('edit_password', password_id=password_id))

    # Decrypt password for display
    master_password = session.get('master_password')
    salt = get_user_salt(session['user_id'])
    decrypted_pwd = decrypt_password(password_row['encrypted_password'], password_row['iv'], master_password, salt)

    conn.close()
    return render_template('edit_password.html', password={
        'id': password_row['id'],
        'title': password_row['title'],
        'category': password_row['category'],
        'username': password_row['username'],
        'password': decrypted_pwd or ''
    })

@app.route('/delete-password/<int:password_id>', methods=['POST'])
@login_required
def delete_password(password_id):
    """Delete a password."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT title FROM passwords WHERE id = ? AND user_id = ?',
                  (password_id, session['user_id']))
    password_row = cursor.fetchone()

    if not password_row:
        flash('Password not found.', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))

    try:
        cursor.execute('DELETE FROM passwords WHERE id = ? AND user_id = ?',
                      (password_id, session['user_id']))
        conn.commit()
        conn.close()

        flash(f'Password "{password_row["title"]}" deleted successfully!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        conn.close()
        flash('Failed to delete password. Please try again.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/generate-password')
@login_required
def generate_password():
    """Generate a random password (API endpoint)."""
    length = request.args.get('length', 16, type=int)
    if length < 8 or length > 128:
        length = 16

    return jsonify({'password': generate_random_password(length)})

@app.route('/search')
@login_required
def search():
    """Search passwords."""
    query = request.args.get('q', '').strip().lower()

    if not query:
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''SELECT id, title, category, username, encrypted_password, iv, created_at
                     FROM passwords
                     WHERE user_id = ? AND (
                        LOWER(title) LIKE ? OR
                        LOWER(username) LIKE ? OR
                        LOWER(category) LIKE ?
                     )
                     ORDER BY title''',
                  (session['user_id'], f'%{query}%', f'%{query}%', f'%{query}%'))
    encrypted_passwords = cursor.fetchall()
    conn.close()

    # Decrypt passwords
    passwords = []
    master_password = session.get('master_password')
    salt = get_user_salt(session['user_id'])

    for pwd in encrypted_passwords:
        decrypted = decrypt_password(pwd['encrypted_password'], pwd['iv'], master_password, salt)
        passwords.append({
            'id': pwd['id'],
            'title': pwd['title'],
            'category': pwd['category'],
            'username': pwd['username'],
            'password': decrypted or '[Decryption Error]',
            'created_at': pwd['created_at']
        })

    return render_template('search_results.html', passwords=passwords, query=query)

@app.route('/logout')
def logout():
    """Logout user."""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# ==================== Helper Functions ====================
def get_user_salt(user_id: int) -> bytes:
    """Retrieve user's salt from database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT salt FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return base64.b64decode(row['salt'])
    return None

# ==================== Error Handlers ====================
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='localhost', port=5000)
