from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from models import db, User, Password, Category
from crypto import encrypt_password, decrypt_password, derive_key
from utils import generate_password, validate_password_strength
import os
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///password_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

db.init_app(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        master_password = data.get('master_password', '')
        confirm_password = data.get('confirm_password', '')

        if not username or not master_password:
            return jsonify({'success': False, 'error': 'Username and master password required'}), 400

        if master_password != confirm_password:
            return jsonify({'success': False, 'error': 'Passwords do not match'}), 400

        if len(master_password) < 8:
            return jsonify({'success': False, 'error': 'Master password must be at least 8 characters'}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'error': 'Username already exists'}), 400

        user = User(username=username)
        user.set_master_password(master_password)
        db.session.add(user)
        db.session.commit()

        default_categories = ['Work', 'Personal', 'Finance', 'Social Media']
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']

        for cat_name, color in zip(default_categories, colors):
            category = Category(user_id=user.id, name=cat_name, color=color)
            db.session.add(category)
        db.session.commit()

        session['user_id'] = user.id
        session['username'] = user.username
        session['master_password_key'] = master_password
        return jsonify({'success': True, 'redirect': url_for('dashboard')})

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        master_password = data.get('master_password', '')

        user = User.query.filter_by(username=username).first()
        if user and user.verify_master_password(master_password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['master_password_key'] = master_password
            return jsonify({'success': True, 'redirect': url_for('dashboard')})

        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    categories = Category.query.filter_by(user_id=session['user_id']).all()
    passwords = Password.query.filter_by(user_id=session['user_id']).all()

    return render_template('dashboard.html', user=user, categories=categories, passwords=passwords)

@app.route('/api/passwords', methods=['GET'])
@login_required
def get_passwords():
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '').strip()

    query = Password.query.filter_by(user_id=session['user_id'])

    if category_id:
        query = query.filter_by(category_id=category_id)

    if search:
        query = query.filter(
            db.or_(
                Password.title.ilike(f'%{search}%'),
                Password.username.ilike(f'%{search}%'),
                Password.email.ilike(f'%{search}%'),
                Password.url.ilike(f'%{search}%')
            )
        )

    passwords = query.all()
    result = []

    for pwd in passwords:
        result.append({
            'id': pwd.id,
            'title': pwd.title,
            'username': pwd.username,
            'email': pwd.email,
            'url': pwd.url,
            'category_id': pwd.category_id,
            'category_name': pwd.category.name if pwd.category else 'Uncategorized',
            'notes': pwd.notes,
            'created_at': pwd.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': pwd.updated_at.strftime('%Y-%m-%d %H:%M')
        })

    return jsonify(result)

@app.route('/api/password/<int:password_id>/decrypt', methods=['POST'])
@login_required
def decrypt_password_route(password_id):
    pwd = Password.query.filter_by(id=password_id, user_id=session['user_id']).first()
    if not pwd:
        return jsonify({'error': 'Password not found'}), 404

    user = User.query.get(session['user_id'])
    try:
        decrypted = decrypt_password(pwd.encrypted_password,
                                    session.get('master_password_key'),
                                    user.get_encryption_salt())
        return jsonify({'password': decrypted})
    except Exception as e:
        return jsonify({'error': 'Failed to decrypt password'}), 400

@app.route('/api/password/add', methods=['POST'])
@login_required
def add_password():
    data = request.get_json()
    title = data.get('title', '').strip()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    url = data.get('url', '').strip()
    notes = data.get('notes', '').strip()
    category_id = data.get('category_id', type=int)

    if not title or not password:
        return jsonify({'error': 'Title and password required'}), 400

    user = User.query.get(session['user_id'])

    try:
        encrypted = encrypt_password(password, session.get('master_password_key'), user.get_encryption_salt())
    except Exception as e:
        return jsonify({'error': 'Encryption failed'}), 400

    pwd = Password(
        user_id=session['user_id'],
        category_id=category_id if category_id else None,
        title=title,
        username=username,
        email=email,
        encrypted_password=encrypted,
        url=url,
        notes=notes
    )

    db.session.add(pwd)
    db.session.commit()

    return jsonify({'success': True, 'id': pwd.id})

@app.route('/api/password/<int:password_id>/update', methods=['POST'])
@login_required
def update_password(password_id):
    pwd = Password.query.filter_by(id=password_id, user_id=session['user_id']).first()
    if not pwd:
        return jsonify({'error': 'Password not found'}), 404

    data = request.get_json()
    pwd.title = data.get('title', pwd.title).strip()
    pwd.username = data.get('username', pwd.username).strip()
    pwd.email = data.get('email', pwd.email).strip()
    pwd.url = data.get('url', pwd.url).strip()
    pwd.notes = data.get('notes', pwd.notes).strip()
    pwd.category_id = data.get('category_id')

    if data.get('password'):
        user = User.query.get(session['user_id'])
        try:
            encrypted = encrypt_password(data.get('password'),
                                        session.get('master_password_key'),
                                        user.get_encryption_salt())
            pwd.encrypted_password = encrypted
        except Exception as e:
            return jsonify({'error': 'Encryption failed'}), 400

    pwd.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True})

@app.route('/api/password/<int:password_id>/delete', methods=['POST'])
@login_required
def delete_password(password_id):
    pwd = Password.query.filter_by(id=password_id, user_id=session['user_id']).first()
    if not pwd:
        return jsonify({'error': 'Password not found'}), 404

    db.session.delete(pwd)
    db.session.commit()

    return jsonify({'success': True})

@app.route('/api/categories', methods=['GET'])
@login_required
def get_categories():
    categories = Category.query.filter_by(user_id=session['user_id']).all()
    return jsonify([{'id': c.id, 'name': c.name, 'color': c.color} for c in categories])

@app.route('/api/category/add', methods=['POST'])
@login_required
def add_category():
    data = request.get_json()
    name = data.get('name', '').strip()
    color = data.get('color', '#3498db')

    if not name:
        return jsonify({'error': 'Category name required'}), 400

    category = Category(user_id=session['user_id'], name=name, color=color)
    db.session.add(category)
    db.session.commit()

    return jsonify({'success': True, 'id': category.id})

@app.route('/api/generate-password', methods=['POST'])
@login_required
def generate_pwd():
    data = request.get_json()
    length = data.get('length', 16)
    include_uppercase = data.get('include_uppercase', True)
    include_lowercase = data.get('include_lowercase', True)
    include_numbers = data.get('include_numbers', True)
    include_symbols = data.get('include_symbols', True)

    password = generate_password(length, include_uppercase, include_lowercase, include_numbers, include_symbols)
    strength = validate_password_strength(password)

    return jsonify({'password': password, 'strength': strength})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.before_request
def check_master_password():
    if 'user_id' in session and 'master_password_key' not in session:
        if request.endpoint not in ['login', 'register', 'logout', 'static']:
            return redirect(url_for('unlock'))

@app.route('/unlock', methods=['GET', 'POST'])
def unlock():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        master_password = data.get('master_password', '')

        user = User.query.get(session['user_id'])
        if user.verify_master_password(master_password):
            session['master_password_key'] = master_password
            return jsonify({'success': True, 'redirect': url_for('dashboard')})

        return jsonify({'success': False, 'error': 'Invalid master password'}), 401

    return render_template('unlock.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
