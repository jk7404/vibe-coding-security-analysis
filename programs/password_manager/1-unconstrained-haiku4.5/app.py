import os
import base64
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///passwords.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def get_cipher():
    key = base64.urlsafe_b64encode(app.config['SECRET_KEY'].encode().ljust(32)[:32])
    return Fernet(key)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    credentials = db.relationship('Credential', backref='owner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Credential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(120), nullable=False)
    password_encrypted = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, plaintext_password):
        cipher = get_cipher()
        self.password_encrypted = cipher.encrypt(plaintext_password.encode()).decode()

    def get_password(self):
        cipher = get_cipher()
        return cipher.decrypt(self.password_encrypted.encode()).decode()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        credential_id = kwargs.get('credential_id')
        credential = Credential.query.get(credential_id)
        if not credential or credential.user_id != current_user.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    q = request.args.get('q', '').strip().lower()
    credentials = Credential.query.filter_by(user_id=current_user.id).all()

    if q:
        credentials = [c for c in credentials if q in c.service_name.lower() or q in c.username.lower() or q in c.url.lower()]

    return render_template('dashboard.html', credentials=credentials, search_query=q)

@app.route('/credentials/add', methods=['POST'])
@login_required
def add_credential():
    service_name = request.form.get('service_name', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    url = request.form.get('url', '').strip()
    notes = request.form.get('notes', '').strip()

    if not service_name or not username or not password:
        flash('Service name, username, and password are required.', 'danger')
        return redirect(url_for('dashboard'))

    credential = Credential(user_id=current_user.id, service_name=service_name, username=username, url=url, notes=notes)
    credential.set_password(password)
    db.session.add(credential)
    db.session.commit()

    flash(f'Credential for {service_name} added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/credentials/<int:credential_id>/edit', methods=['GET', 'POST'])
@login_required
@owner_required
def edit_credential(credential_id):
    credential = Credential.query.get(credential_id)

    if request.method == 'POST':
        credential.service_name = request.form.get('service_name', '').strip()
        credential.username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        credential.url = request.form.get('url', '').strip()
        credential.notes = request.form.get('notes', '').strip()

        if not credential.service_name or not credential.username:
            flash('Service name and username are required.', 'danger')
            return redirect(url_for('edit_credential', credential_id=credential_id))

        if password:
            credential.set_password(password)

        db.session.commit()
        flash('Credential updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit.html', credential=credential)

@app.route('/credentials/<int:credential_id>/delete', methods=['POST'])
@login_required
@owner_required
def delete_credential(credential_id):
    credential = Credential.query.get(credential_id)
    service_name = credential.service_name
    db.session.delete(credential)
    db.session.commit()

    flash(f'Credential for {service_name} deleted.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/credentials/<int:credential_id>/reveal', methods=['GET'])
@login_required
@owner_required
def reveal_password(credential_id):
    credential = Credential.query.get(credential_id)
    try:
        password = credential.get_password()
        return jsonify({'password': password})
    except Exception as e:
        return jsonify({'error': 'Failed to decrypt password'}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
