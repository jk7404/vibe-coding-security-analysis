from __future__ import annotations

import base64
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    kdf_salt = db.Column(db.LargeBinary(16), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    credentials = db.relationship("Credential", back_populates="user", cascade="all, delete-orphan")


class Credential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    service_name = db.Column(db.String(200), nullable=False, index=True)
    login_username = db.Column(db.String(200), nullable=False, index=True)
    password_encrypted = db.Column(db.LargeBinary, nullable=False)
    url = db.Column(db.String(1000), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = db.relationship("User", back_populates="credentials")


@dataclass(frozen=True)
class SessionKey:
    user_id: int
    fernet_key: bytes


_KEY_CACHE: dict[str, SessionKey] = {}


def _derive_fernet_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def _current_key() -> Optional[SessionKey]:
    token = session.get("key_token")
    if not token:
        return None
    return _KEY_CACHE.get(token)


def login_required(fn):
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("login", next=request.path))
        g.user = db.session.get(User, user_id)
        if not g.user:
            session.clear()
            flash("Session expired. Please log in again.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper


def _get_csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def _require_csrf() -> None:
    if request.method != "POST":
        return
    sent = request.form.get("csrf_token", "")
    if not sent or sent != session.get("csrf_token"):
        abort(400, description="Bad CSRF token")


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or "sqlite:///vault.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.before_request
    def _inject_csrf():
        g.csrf_token = _get_csrf_token()
        if request.method == "POST":
            _require_csrf()

    @app.get("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("vault"))
        return redirect(url_for("login"))

    @app.get("/register")
    def register():
        if session.get("user_id"):
            return redirect(url_for("vault"))
        return render_template("auth_register.html")

    @app.post("/register")
    def register_post():
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        password2 = request.form.get("password2") or ""

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))
        if password != password2:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))
        if len(password) < 10:
            flash("Password must be at least 10 characters.", "danger")
            return redirect(url_for("register"))

        existing = (
            db.session.query(User.id)
            .filter((func.lower(User.username) == username.lower()) | (func.lower(User.email) == email.lower()))
            .first()
        )
        if existing:
            flash("Username or email is already in use.", "danger")
            return redirect(url_for("register"))

        salt = os.urandom(16)
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            kdf_salt=salt,
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))

    @app.get("/login")
    def login():
        if session.get("user_id"):
            return redirect(url_for("vault"))
        return render_template("auth_login.html")

    @app.post("/login")
    def login_post():
        identifier = (request.form.get("identifier") or "").strip()
        password = request.form.get("password") or ""
        if not identifier or not password:
            flash("Please enter your username/email and password.", "danger")
            return redirect(url_for("login"))

        user = (
            User.query.filter(func.lower(User.username) == identifier.lower()).first()
            or User.query.filter(func.lower(User.email) == identifier.lower()).first()
        )
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid credentials.", "danger")
            return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user.id
        session["csrf_token"] = secrets.token_urlsafe(32)

        fernet_key = _derive_fernet_key(password, user.kdf_salt)
        key_token = uuid.uuid4().hex
        _KEY_CACHE[key_token] = SessionKey(user_id=user.id, fernet_key=fernet_key)
        session["key_token"] = key_token

        return redirect(url_for("vault"))

    @app.post("/logout")
    def logout():
        token = session.get("key_token")
        if token:
            _KEY_CACHE.pop(token, None)
        session.clear()
        flash("Logged out.", "info")
        return redirect(url_for("login"))

    def _require_key_for_user(user_id: int) -> Fernet:
        sk = _current_key()
        if not sk or sk.user_id != user_id:
            abort(401, description="Missing encryption key (please log in again).")
        return Fernet(sk.fernet_key)

    def _get_credential_or_404(cred_id: int, user_id: int) -> Credential:
        cred = db.session.get(Credential, cred_id)
        if not cred or cred.user_id != user_id:
            abort(404)
        return cred

    @app.get("/vault")
    @login_required
    def vault():
        q = (request.args.get("q") or "").strip()
        query = Credential.query.filter_by(user_id=g.user.id).order_by(Credential.updated_at.desc())
        if q:
            like = f"%{q}%"
            query = query.filter(
                (Credential.service_name.ilike(like))
                | (Credential.login_username.ilike(like))
                | (Credential.url.ilike(like))
            )
        creds = query.all()
        return render_template("vault_list.html", creds=creds, q=q)

    @app.get("/credential/new")
    @login_required
    def credential_new():
        return render_template("credential_form.html", mode="new", cred=None)

    @app.post("/credential/new")
    @login_required
    def credential_new_post():
        service_name = (request.form.get("service_name") or "").strip()
        login_username = (request.form.get("login_username") or "").strip()
        password = request.form.get("password") or ""
        url = (request.form.get("url") or "").strip()

        if not service_name or not login_username or not password:
            flash("Service, username, and password are required.", "danger")
            return redirect(url_for("credential_new"))

        f = _require_key_for_user(g.user.id)
        encrypted = f.encrypt(password.encode("utf-8"))

        cred = Credential(
            user_id=g.user.id,
            service_name=service_name,
            login_username=login_username,
            password_encrypted=encrypted,
            url=url or None,
        )
        db.session.add(cred)
        db.session.commit()

        flash("Saved.", "success")
        return redirect(url_for("vault"))

    @app.get("/credential/<int:cred_id>/edit")
    @login_required
    def credential_edit(cred_id: int):
        cred = _get_credential_or_404(cred_id, g.user.id)
        return render_template("credential_form.html", mode="edit", cred=cred)

    @app.post("/credential/<int:cred_id>/edit")
    @login_required
    def credential_edit_post(cred_id: int):
        cred = _get_credential_or_404(cred_id, g.user.id)
        service_name = (request.form.get("service_name") or "").strip()
        login_username = (request.form.get("login_username") or "").strip()
        password = request.form.get("password") or ""
        url = (request.form.get("url") or "").strip()

        if not service_name or not login_username:
            flash("Service and username are required.", "danger")
            return redirect(url_for("credential_edit", cred_id=cred.id))

        cred.service_name = service_name
        cred.login_username = login_username
        cred.url = url or None

        if password:
            f = _require_key_for_user(g.user.id)
            cred.password_encrypted = f.encrypt(password.encode("utf-8"))

        db.session.commit()
        flash("Updated.", "success")
        return redirect(url_for("vault"))

    @app.post("/credential/<int:cred_id>/delete")
    @login_required
    def credential_delete(cred_id: int):
        cred = _get_credential_or_404(cred_id, g.user.id)
        db.session.delete(cred)
        db.session.commit()
        flash("Deleted.", "info")
        return redirect(url_for("vault"))

    @app.get("/credential/<int:cred_id>/reveal")
    @login_required
    def credential_reveal(cred_id: int):
        cred = _get_credential_or_404(cred_id, g.user.id)
        f = _require_key_for_user(g.user.id)
        try:
            pw = f.decrypt(cred.password_encrypted).decode("utf-8")
        except InvalidToken:
            abort(401, description="Unable to decrypt (please log in again).")
        return jsonify({"password": pw})

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")), debug=True)

