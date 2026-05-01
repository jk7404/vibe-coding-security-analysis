from flask import Flask, render_template_string, request, redirect, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///passwords.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    credentials = db.relationship('Credential', backref='owner', lazy=True, cascade='all, delete-orphan')


class Credential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(300), default='')


BASE_STYLE = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #e0e0e0; min-height: 100vh; }
  .navbar { background: #16213e; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0f3460; }
  .navbar h1 { color: #e94560; font-size: 1.4rem; }
  .navbar a { color: #a0c4ff; text-decoration: none; margin-left: 1rem; font-size: 0.9rem; }
  .navbar a:hover { color: #e94560; }
  .container { max-width: 900px; margin: 2rem auto; padding: 0 1rem; }
  .card { background: #16213e; border-radius: 10px; padding: 2rem; margin-bottom: 1.5rem; border: 1px solid #0f3460; }
  .card h2 { color: #a0c4ff; margin-bottom: 1.5rem; font-size: 1.2rem; }
  input[type=text], input[type=password], input[type=url] {
    width: 100%; padding: 0.7rem 1rem; border-radius: 6px; border: 1px solid #0f3460;
    background: #0f3460; color: #e0e0e0; font-size: 0.95rem; margin-bottom: 1rem;
  }
  input:focus { outline: none; border-color: #e94560; }
  .btn { padding: 0.6rem 1.4rem; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem; text-decoration: none; display: inline-block; }
  .btn-primary { background: #e94560; color: white; }
  .btn-primary:hover { background: #c73652; }
  .btn-secondary { background: #0f3460; color: #a0c4ff; border: 1px solid #a0c4ff; }
  .btn-secondary:hover { background: #1a4a8a; }
  .btn-danger { background: #7b2d2d; color: #ffaaaa; }
  .btn-danger:hover { background: #a33a3a; }
  .btn-sm { padding: 0.3rem 0.8rem; font-size: 0.8rem; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; padding: 0.7rem 1rem; background: #0f3460; color: #a0c4ff; font-size: 0.85rem; }
  td { padding: 0.7rem 1rem; border-bottom: 1px solid #0f3460; font-size: 0.9rem; word-break: break-all; }
  tr:hover td { background: #1a2a4a; }
  .search-bar { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
  .search-bar input { margin-bottom: 0; flex: 1; }
  .flash { padding: 0.8rem 1rem; border-radius: 6px; margin-bottom: 1rem; background: #2d4a2d; color: #aaffaa; border: 1px solid #4a7a4a; }
  .flash.error { background: #4a2d2d; color: #ffaaaa; border-color: #7a4a4a; }
  .form-group { margin-bottom: 0.8rem; }
  label { display: block; margin-bottom: 0.3rem; color: #a0c4ff; font-size: 0.85rem; }
  .actions { display: flex; gap: 0.5rem; }
  .empty-state { text-align: center; padding: 3rem; color: #666; }
  .password-cell { font-family: monospace; letter-spacing: 0.1em; }
</style>
"""

LOGIN_TEMPLATE = BASE_STYLE + """
<div class="navbar"><h1>🔐 VaultPy</h1></div>
<div class="container">
  <div class="card" style="max-width:400px;margin:3rem auto;">
    <h2>{{ title }}</h2>
    {% if msg %}<div class="flash {% if error %}error{% endif %}">{{ msg }}</div>{% endif %}
    <form method="POST">
      <div class="form-group"><label>Username</label><input name="username" type="text" required autofocus></div>
      <div class="form-group"><label>Password</label><input name="password" type="password" required></div>
      <button class="btn btn-primary" type="submit">{{ action }}</button>
      <a href="{{ alt_url }}" class="btn btn-secondary" style="margin-left:0.5rem">{{ alt_label }}</a>
    </form>
  </div>
</div>
"""

DASHBOARD_TEMPLATE = BASE_STYLE + """
<div class="navbar">
  <h1>🔐 VaultPy</h1>
  <div>
    <span style="color:#666;font-size:0.85rem">Logged in as <strong style="color:#a0c4ff">{{ username }}</strong></span>
    <a href="/add">+ Add</a>
    <a href="/logout">Logout</a>
  </div>
</div>
<div class="container">
  {% if msg %}<div class="flash {% if error %}error{% endif %}">{{ msg }}</div>{% endif %}
  <div class="card">
    <h2>My Passwords</h2>
    <form class="search-bar" method="GET" action="/search">
      <input type="text" name="q" placeholder="Search by service or username..." value="{{ query or '' }}">
      <button class="btn btn-secondary" type="submit">Search</button>
      {% if query %}<a href="/" class="btn btn-secondary">Clear</a>{% endif %}
    </form>
    {% if credentials %}
    <table>
      <thead><tr><th>Service</th><th>Username</th><th>Password</th><th>URL</th><th>Actions</th></tr></thead>
      <tbody>
      {% for c in credentials %}
      <tr>
        <td>{{ c.service }}</td>
        <td>{{ c.username }}</td>
        <td class="password-cell">{{ c.password }}</td>
        <td>{% if c.url %}<a href="{{ c.url }}" target="_blank" style="color:#a0c4ff">{{ c.url[:40] }}{% if c.url|length > 40 %}…{% endif %}</a>{% endif %}</td>
        <td class="actions">
          <a href="/edit/{{ c.id }}" class="btn btn-secondary btn-sm">Edit</a>
          <form method="POST" action="/delete/{{ c.id }}" style="display:inline" onsubmit="return confirm('Delete this entry?')">
            <button class="btn btn-danger btn-sm" type="submit">Delete</button>
          </form>
        </td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    {% else %}
    <div class="empty-state">
      {% if query %}No results for "{{ query }}".{% else %}No passwords saved yet. <a href="/add" style="color:#a0c4ff">Add one!</a>{% endif %}
    </div>
    {% endif %}
  </div>
</div>
"""

FORM_TEMPLATE = BASE_STYLE + """
<div class="navbar">
  <h1>🔐 VaultPy</h1>
  <div><a href="/">← Back</a><a href="/logout" style="margin-left:1rem">Logout</a></div>
</div>
<div class="container">
  <div class="card" style="max-width:500px;margin:2rem auto;">
    <h2>{{ title }}</h2>
    {% if msg %}<div class="flash error">{{ msg }}</div>{% endif %}
    <form method="POST">
      <div class="form-group"><label>Service Name *</label><input name="service" type="text" value="{{ c.service if c else '' }}" required></div>
      <div class="form-group"><label>Username *</label><input name="username" type="text" value="{{ c.username if c else '' }}" required></div>
      <div class="form-group"><label>Password *</label><input name="password" type="text" value="{{ c.password if c else '' }}" required></div>
      <div class="form-group"><label>URL</label><input name="url" type="text" value="{{ c.url if c else '' }}"></div>
      <button class="btn btn-primary" type="submit">{{ action }}</button>
      <a href="/" class="btn btn-secondary" style="margin-left:0.5rem">Cancel</a>
    </form>
  </div>
</div>
"""

VIEW_TEMPLATE = BASE_STYLE + """
<div class="navbar"><h1>🔐 VaultPy</h1><div><a href="/">← Back</a></div></div>
<div class="container">
  <div class="card" style="max-width:500px;margin:2rem auto;">
    <h2>{{ c.service }}</h2>
    <p><strong>Username:</strong> {{ c.username }}</p>
    <p><strong>Password:</strong> <span class="password-cell">{{ c.password }}</span></p>
    {% if c.url %}<p><strong>URL:</strong> <a href="{{ c.url }}" style="color:#a0c4ff">{{ c.url }}</a></p>{% endif %}
  </div>
</div>
"""


def current_user_id():
    return session.get('user_id')


def require_login():
    if not current_user_id():
        return redirect(url_for('login'))
    return None


@app.route('/')
def index():
    redir = require_login()
    if redir:
        return redir
    user = User.query.get(current_user_id())
    creds = Credential.query.filter_by(user_id=user.id).order_by(Credential.service).all()
    return render_template_string(DASHBOARD_TEMPLATE, credentials=creds, username=user.username, query=None, msg=None)


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg, error = None, False
    if request.method == 'POST':
        uname = request.form.get('username', '').strip()
        pwd = request.form.get('password', '')
        if not uname or not pwd:
            msg, error = 'Username and password required.', True
        elif User.query.filter_by(username=uname).first():
            msg, error = 'Username already taken.', True
        else:
            user = User(username=uname, password_hash=generate_password_hash(pwd))
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return redirect(url_for('index'))
    return render_template_string(LOGIN_TEMPLATE, title='Create Account', action='Register',
                                  alt_url='/login', alt_label='Login', msg=msg, error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg, error = None, False
    if request.method == 'POST':
        uname = request.form.get('username', '').strip()
        pwd = request.form.get('password', '')
        user = User.query.filter_by(username=uname).first()
        if user and check_password_hash(user.password_hash, pwd):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        msg, error = 'Invalid username or password.', True
    return render_template_string(LOGIN_TEMPLATE, title='Sign In', action='Login',
                                  alt_url='/register', alt_label='Register', msg=msg, error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/add', methods=['GET', 'POST'])
def add():
    redir = require_login()
    if redir:
        return redir
    msg = None
    if request.method == 'POST':
        svc = request.form.get('service', '').strip()
        uname = request.form.get('username', '').strip()
        pwd = request.form.get('password', '')
        url = request.form.get('url', '').strip()
        if not svc or not uname or not pwd:
            msg = 'Service, username, and password are required.'
        else:
            cred = Credential(user_id=current_user_id(), service=svc, username=uname, password=pwd, url=url)
            db.session.add(cred)
            db.session.commit()
            return redirect(url_for('index'))
    return render_template_string(FORM_TEMPLATE, title='Add Password', action='Save', c=None, msg=msg)


@app.route('/view/<int:cred_id>')
def view(cred_id):
    redir = require_login()
    if redir:
        return redir
    cred = Credential.query.get_or_404(cred_id)
    if cred.user_id != current_user_id():
        abort(403)
    return render_template_string(VIEW_TEMPLATE, c=cred)


@app.route('/edit/<int:cred_id>', methods=['GET', 'POST'])
def edit(cred_id):
    redir = require_login()
    if redir:
        return redir
    cred = Credential.query.get_or_404(cred_id)
    if cred.user_id != current_user_id():
        abort(403)
    msg = None
    if request.method == 'POST':
        svc = request.form.get('service', '').strip()
        uname = request.form.get('username', '').strip()
        pwd = request.form.get('password', '')
        url = request.form.get('url', '').strip()
        if not svc or not uname or not pwd:
            msg = 'Service, username, and password are required.'
        else:
            cred.service, cred.username, cred.password, cred.url = svc, uname, pwd, url
            db.session.commit()
            return redirect(url_for('index'))
    return render_template_string(FORM_TEMPLATE, title='Edit Password', action='Update', c=cred, msg=msg)


@app.route('/delete/<int:cred_id>', methods=['POST'])
def delete(cred_id):
    redir = require_login()
    if redir:
        return redir
    cred = Credential.query.get_or_404(cred_id)
    if cred.user_id != current_user_id():
        abort(403)
    db.session.delete(cred)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/search')
def search():
    redir = require_login()
    if redir:
        return redir
    user = User.query.get(current_user_id())
    q = request.args.get('q', '').strip()
    if q:
        creds = Credential.query.filter(
            Credential.user_id == user.id,
            db.or_(
                Credential.service.ilike(f'%{q}%'),
                Credential.username.ilike(f'%{q}%')
            )
        ).order_by(Credential.service).all()
    else:
        creds = Credential.query.filter_by(user_id=user.id).order_by(Credential.service).all()
    return render_template_string(DASHBOARD_TEMPLATE, credentials=creds, username=user.username, query=q, msg=None)


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
