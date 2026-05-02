"""
Self-hosted Password Manager — Flask application.
Run: python app.py
"""

import os
import base64
import hashlib
import sqlite3
import secrets
from datetime import datetime
from functools import wraps

import bcrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, g, abort
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

DATABASE = os.path.join(os.path.dirname(__file__), "passwords.db")

# Derive a 32-byte AES key from the secret key
_AES_KEY = hashlib.sha256(app.secret_key.encode()).digest()

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER  PRIMARY KEY AUTOINCREMENT,
            username      TEXT     UNIQUE NOT NULL,
            email         TEXT     UNIQUE NOT NULL,
            password_hash TEXT     NOT NULL,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS credentials (
            id            INTEGER  PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            service_name  TEXT     NOT NULL,
            username      TEXT     NOT NULL,
            password      TEXT     NOT NULL,
            url           TEXT,
            notes         TEXT,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_creds_user ON credentials(user_id);
    """)
    db.commit()
    db.close()

# ---------------------------------------------------------------------------
# Encryption helpers
# ---------------------------------------------------------------------------

def encrypt_password(plaintext: str) -> str:
    nonce = os.urandom(12)
    aesgcm = AESGCM(_AES_KEY)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def decrypt_password(blob: str) -> str:
    raw = base64.b64decode(blob.encode())
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(_AES_KEY)
    return aesgcm.decrypt(nonce, ct, None).decode()

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def current_user_id():
    return session.get("user_id")

# ---------------------------------------------------------------------------
# CSRF helpers (lightweight — no extra dependency)
# ---------------------------------------------------------------------------

def generate_csrf():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(24)
    return session["_csrf"]


def validate_csrf():
    token = request.form.get("_csrf_token", "")
    if not secrets.compare_digest(token, session.get("_csrf", "")):
        abort(403)


app.jinja_env.globals["csrf_token"] = generate_csrf

# ---------------------------------------------------------------------------
# Routes — public
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        validate_csrf()
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        error = None
        if not all([username, email, password, confirm]):
            error = "All fields are required."
        elif password != confirm:
            error = "Passwords do not match."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."

        if error:
            flash(error, "danger")
            return render_template("register.html")

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, pw_hash)
            )
            db.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username or email already taken.", "danger")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        validate_csrf()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            session.clear()
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            generate_csrf()
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# ---------------------------------------------------------------------------
# Routes — dashboard
# ---------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    query = request.args.get("q", "").strip()
    db = get_db()

    if query:
        rows = db.execute(
            """SELECT * FROM credentials
               WHERE user_id = ?
                 AND (service_name LIKE ? OR username LIKE ? OR url LIKE ?)
               ORDER BY service_name COLLATE NOCASE""",
            (current_user_id(), f"%{query}%", f"%{query}%", f"%{query}%")
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM credentials WHERE user_id = ? ORDER BY service_name COLLATE NOCASE",
            (current_user_id(),)
        ).fetchall()

    credentials = []
    for row in rows:
        d = dict(row)
        try:
            d["password_plain"] = decrypt_password(d["password"])
        except Exception:
            d["password_plain"] = "⚠ decryption error"
        credentials.append(d)

    return render_template("dashboard.html",
                           credentials=credentials,
                           query=query,
                           username=session["username"])

# ---------------------------------------------------------------------------
# Routes — CRUD
# ---------------------------------------------------------------------------

@app.route("/credentials/new", methods=["GET", "POST"])
@login_required
def new_credential():
    if request.method == "POST":
        validate_csrf()
        service = request.form.get("service_name", "").strip()
        uname   = request.form.get("username", "").strip()
        pwd     = request.form.get("password", "")
        url     = request.form.get("url", "").strip()
        notes   = request.form.get("notes", "").strip()

        if not all([service, uname, pwd]):
            flash("Service name, username, and password are required.", "danger")
            return render_template("credential_form.html", action="new", data=request.form)

        encrypted = encrypt_password(pwd)
        db = get_db()
        db.execute(
            """INSERT INTO credentials (user_id, service_name, username, password, url, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (current_user_id(), service, uname, encrypted, url or None, notes or None)
        )
        db.commit()
        flash(f"Credential for '{service}' saved.", "success")
        return redirect(url_for("dashboard"))

    return render_template("credential_form.html", action="new", data={})


@app.route("/credentials/<int:cred_id>/edit", methods=["GET", "POST"])
@login_required
def edit_credential(cred_id):
    db = get_db()
    # Compound filter — prevents IDOR
    cred = db.execute(
        "SELECT * FROM credentials WHERE id = ? AND user_id = ?",
        (cred_id, current_user_id())
    ).fetchone()

    if cred is None:
        abort(404)

    if request.method == "POST":
        validate_csrf()
        service = request.form.get("service_name", "").strip()
        uname   = request.form.get("username", "").strip()
        pwd     = request.form.get("password", "")
        url     = request.form.get("url", "").strip()
        notes   = request.form.get("notes", "").strip()

        if not all([service, uname, pwd]):
            flash("Service name, username, and password are required.", "danger")
            return render_template("credential_form.html", action="edit",
                                   data=request.form, cred_id=cred_id)

        encrypted = encrypt_password(pwd)
        db.execute(
            """UPDATE credentials
               SET service_name=?, username=?, password=?, url=?, notes=?, updated_at=?
               WHERE id=? AND user_id=?""",
            (service, uname, encrypted, url or None, notes or None,
             datetime.utcnow(), cred_id, current_user_id())
        )
        db.commit()
        flash(f"Credential for '{service}' updated.", "success")
        return redirect(url_for("dashboard"))

    data = dict(cred)
    try:
        data["password"] = decrypt_password(data["password"])
    except Exception:
        data["password"] = ""

    return render_template("credential_form.html", action="edit", data=data, cred_id=cred_id)


@app.route("/credentials/<int:cred_id>/delete", methods=["POST"])
@login_required
def delete_credential(cred_id):
    validate_csrf()
    db = get_db()
    # Compound filter — prevents IDOR
    result = db.execute(
        "DELETE FROM credentials WHERE id = ? AND user_id = ?",
        (cred_id, current_user_id())
    )
    db.commit()
    if result.rowcount == 0:
        abort(404)
    flash("Credential deleted.", "info")
    return redirect(url_for("dashboard"))

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    print("\n  Password Manager running at http://127.0.0.1:5000\n")
    app.run(debug=False, host="127.0.0.1", port=5000)
