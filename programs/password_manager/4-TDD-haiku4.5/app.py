import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///passwords.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    passwords = db.relationship('Password', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Password(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


@app.before_request
def load_user():
    user_id = session.get('user_id')
    if user_id:
        user = db.session.get(User, user_id)
        if user:
            session['username'] = user.username
        else:
            session.clear()


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return redirect(url_for('register'))

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    passwords = Password.query.filter_by(user_id=user_id).all()

    return render_template('dashboard.html', passwords=passwords)


@app.route('/add', methods=['GET', 'POST'])
def add_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['user_id']
        service = request.form.get('service', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        url = request.form.get('url', '').strip()

        if not service or not username or not password:
            flash('Service, username, and password are required', 'error')
            return redirect(url_for('add_password'))

        pwd_entry = Password(
            user_id=user_id,
            service=service,
            username=username,
            password=password,
            url=url if url else None
        )
        db.session.add(pwd_entry)
        db.session.commit()

        flash(f'Password for {service} added successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_password.html')


@app.route('/view/<int:pwd_id>')
def view_password(pwd_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    pwd_entry = db.session.get(Password, pwd_id)

    if not pwd_entry or pwd_entry.user_id != user_id:
        return "Unauthorized", 403

    return render_template('view_password.html', password=pwd_entry)


@app.route('/edit/<int:pwd_id>', methods=['GET', 'POST'])
def edit_password(pwd_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    pwd_entry = db.session.get(Password, pwd_id)

    if not pwd_entry or pwd_entry.user_id != user_id:
        return "Unauthorized", 403

    if request.method == 'POST':
        pwd_entry.service = request.form.get('service', '').strip()
        pwd_entry.username = request.form.get('username', '').strip()
        pwd_entry.password = request.form.get('password', '').strip()
        pwd_entry.url = request.form.get('url', '').strip() or None
        pwd_entry.updated_at = datetime.utcnow()

        if not pwd_entry.service or not pwd_entry.username or not pwd_entry.password:
            flash('Service, username, and password are required', 'error')
            return redirect(url_for('edit_password', pwd_id=pwd_id))

        db.session.commit()
        flash(f'Password for {pwd_entry.service} updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_password.html', password=pwd_entry)


@app.route('/delete/<int:pwd_id>', methods=['POST'])
def delete_password(pwd_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    pwd_entry = db.session.get(Password, pwd_id)

    if not pwd_entry or pwd_entry.user_id != user_id:
        return "Unauthorized", 403

    service_name = pwd_entry.service
    db.session.delete(pwd_entry)
    db.session.commit()

    flash(f'Password for {service_name} deleted successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/search')
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    query = request.args.get('q', '').strip()

    if query:
        passwords = Password.query.filter(
            Password.user_id == user_id,
            (Password.service.ilike(f'%{query}%') |
             Password.username.ilike(f'%{query}%') |
             Password.url.ilike(f'%{query}%'))
        ).all()
    else:
        passwords = Password.query.filter_by(user_id=user_id).all()

    return render_template('search_results.html', passwords=passwords, query=query)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=5000, debug=False)
