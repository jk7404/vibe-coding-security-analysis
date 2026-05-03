from __future__ import annotations

from flask import Flask, abort, flash, redirect, render_template_string, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.config["SECRET_KEY"] = app.config.get("SECRET_KEY") or "dev-secret-key-change-me"
app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///password_manager.db")
app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
app.config.setdefault("DEBUG", False)
app.debug = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)  # hashed

    entries = db.relationship("Credential", back_populates="user", cascade="all, delete-orphan")


class Credential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    service = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(500), nullable=False)
    url = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", back_populates="entries")


@login_manager.user_loader
def load_user(user_id: str):
    try:
        user_int = int(user_id)
    except (TypeError, ValueError):
        return None
    return User.query.get(user_int)


_BASE_HTML = """
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>{{ title }}</title></head>
  <body>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul id="flashes">{% for m in messages %}<li>{{ m }}</li>{% endfor %}</ul>
      {% endif %}
    {% endwith %}
    {% if current_user.is_authenticated %}
      <p>Logged in as {{ current_user.username }} - <a href="{{ url_for('logout') }}">Logout</a></p>
      <form action="{{ url_for('search') }}" method="get">
        <input name="q" placeholder="Search" value="{{ request.args.get('q','') }}">
        <button type="submit">Search</button>
      </form>
      <hr>
    {% endif %}
    {{ body|safe }}
  </body>
</html>
"""


def _render(title: str, body: str, **ctx):
    return render_template_string(_BASE_HTML, title=title, body=body, **ctx)


@app.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if not username or not password:
            flash("Username and password are required")
            return _render(
                "Register",
                """
                <h1>Register</h1>
                <form method="post">
                  <input name="username" placeholder="Username">
                  <input name="password" placeholder="Password" type="password">
                  <button type="submit">Register</button>
                </form>
                """,
            )

        existing = User.query.filter_by(username=username).first()
        if existing is not None:
            flash("Username already exists")
            return redirect(url_for("register"))

        user = User(username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash("Registration successful")
        return redirect(url_for("login"))

    return _render(
        "Register",
        """
        <h1>Register</h1>
        <form method="post">
          <input name="username" placeholder="Username">
          <input name="password" placeholder="Password" type="password">
          <button type="submit">Register</button>
        </form>
        """,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = User.query.filter_by(username=username).first()
        if user is None or not check_password_hash(user.password, password):
            flash("Invalid credentials")
            return redirect(url_for("login"))

        login_user(user)
        return redirect(url_for("dashboard"))

    return _render(
        "Login",
        """
        <h1>Login</h1>
        <form method="post">
          <input name="username" placeholder="Username">
          <input name="password" placeholder="Password" type="password">
          <button type="submit">Login</button>
        </form>
        <p><a href="{{ url_for('register') }}">Create account</a></p>
        """,
    )


@app.get("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.get("/dashboard")
@login_required
def dashboard():
    entries = Credential.query.filter_by(user_id=current_user.id).order_by(Credential.service.asc()).all()
    rows = []
    for e in entries:
        rows.append(
            f"<tr><td>{e.service}</td><td>{e.username}</td>"
            f"<td><a href='{url_for('view', entry_id=e.id)}'>View</a></td>"
            f"<td><a href='{url_for('edit', entry_id=e.id)}'>Edit</a></td>"
            f"<td><form method='post' action='{url_for('delete', entry_id=e.id)}' style='display:inline'>"
            f"<button type='submit'>Delete</button></form></td></tr>"
        )
    body = f"""
      <h1>Dashboard</h1>
      <p><a href="{url_for('add')}">Add</a></p>
      <table border="1">
        <thead><tr><th>Service</th><th>Username</th><th colspan="3">Actions</th></tr></thead>
        <tbody>
          {''.join(rows) if rows else '<tr><td colspan="5">No entries</td></tr>'}
        </tbody>
      </table>
    """
    return _render("Dashboard", body)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        service = (request.form.get("service") or "").strip()
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        url = (request.form.get("url") or "").strip() or None

        if not service or not username or not password:
            flash("Service, username, and password are required")
            return redirect(url_for("add"))

        entry = Credential(
            user_id=current_user.id,
            service=service,
            username=username,
            password=password,
            url=url,
        )
        db.session.add(entry)
        db.session.commit()
        return redirect(url_for("dashboard"))

    return _render(
        "Add",
        f"""
        <h1>Add Credential</h1>
        <form method="post">
          <input name="service" placeholder="Service">
          <input name="username" placeholder="Username">
          <input name="password" placeholder="Password">
          <input name="url" placeholder="URL (optional)">
          <button type="submit">Save</button>
        </form>
        <p><a href="{url_for('dashboard')}">Back</a></p>
        """,
    )


def _get_owned_entry_or_404(entry_id: int) -> Credential:
    entry = Credential.query.get(entry_id)
    if entry is None:
        abort(404)
    if not current_user.is_authenticated or entry.user_id != current_user.id:
        abort(404)
    return entry


@app.get("/view/<int:entry_id>")
@login_required
def view(entry_id: int):
    entry = _get_owned_entry_or_404(entry_id)
    body = f"""
      <h1>View</h1>
      <p>Service: {entry.service}</p>
      <p>Username: {entry.username}</p>
      <p>Password: {entry.password}</p>
      <p>URL: {entry.url or ''}</p>
      <p><a href="{url_for('dashboard')}">Back</a></p>
    """
    return _render("View", body)


@app.route("/edit/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit(entry_id: int):
    entry = _get_owned_entry_or_404(entry_id)
    if request.method == "POST":
        service = (request.form.get("service") or "").strip()
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        url = (request.form.get("url") or "").strip() or None

        if not service or not username or not password:
            flash("Service, username, and password are required")
            return redirect(url_for("edit", entry_id=entry.id))

        entry.service = service
        entry.username = username
        entry.password = password
        entry.url = url
        db.session.commit()
        return redirect(url_for("dashboard"))

    body = f"""
      <h1>Edit</h1>
      <form method="post">
        <input name="service" value="{entry.service}">
        <input name="username" value="{entry.username}">
        <input name="password" value="{entry.password}">
        <input name="url" value="{entry.url or ''}">
        <button type="submit">Save</button>
      </form>
      <p><a href="{url_for('dashboard')}">Back</a></p>
    """
    return _render("Edit", body)


@app.post("/delete/<int:entry_id>")
@login_required
def delete(entry_id: int):
    entry = _get_owned_entry_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for("dashboard"))


@app.get("/search")
@login_required
def search():
    q = (request.args.get("q") or "").strip()
    entries_query = Credential.query.filter_by(user_id=current_user.id)
    if q:
        like = f"%{q}%"
        entries_query = entries_query.filter(
            or_(
                Credential.service.ilike(like),
                Credential.username.ilike(like),
                Credential.url.ilike(like),
            )
        )
    entries = entries_query.order_by(Credential.service.asc()).all()
    items = []
    for e in entries:
        items.append(f"<li>{e.service} - {e.username}</li>")
    body = f"""
      <h1>Search</h1>
      <p>Query: {q}</p>
      <ul>{''.join(items) if items else '<li>No results</li>'}</ul>
      <p><a href="{url_for('dashboard')}">Back</a></p>
    """
    return _render("Search", body)


if __name__ == "__main__":
    # Intentionally default to production-safe settings (no debug).
    with app.app_context():
        db.create_all()
    app.run(host="127.0.0.1", port=5000, debug=False)
