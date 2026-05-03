import base64
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func, or_
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import Email, EqualTo, InputRequired, Length, Optional


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SECRETS_ENV_PATH = os.path.join(BASE_DIR, ".secrets.env")

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login"
csrf = CSRFProtect()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_probably_base64_urlsafe(value: str) -> bool:
    try:
        base64.urlsafe_b64decode(value.encode("utf-8"))
        return True
    except Exception:
        return False


def ensure_secrets_file() -> None:
    if os.path.exists(SECRETS_ENV_PATH):
        return

    app_secret = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8")
    vault_master = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8")

    with open(SECRETS_ENV_PATH, "w", encoding="utf-8") as f:
        f.write("# Auto-generated secrets for local development.\n")
        f.write("# Do NOT commit this file.\n")
        f.write(f"APP_SECRET_KEY={app_secret}\n")
        f.write(f"VAULT_MASTER_KEY={vault_master}\n")
        f.write("SESSION_COOKIE_SECURE=0\n")


def load_config_from_env(app: Flask) -> None:
    ensure_secrets_file()
    load_dotenv(SECRETS_ENV_PATH, override=False)

    app_secret = os.environ.get("APP_SECRET_KEY", "").strip()
    vault_master_key = os.environ.get("VAULT_MASTER_KEY", "").strip()

    if not app_secret or len(app_secret) < 32:
        raise RuntimeError("Missing/weak APP_SECRET_KEY. Set it in .secrets.env.")
    if not vault_master_key or not _is_probably_base64_urlsafe(vault_master_key):
        raise RuntimeError("Missing/invalid VAULT_MASTER_KEY (urlsafe base64). Set it in .secrets.env.")

    samesite = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax").strip()
    if samesite not in ("Lax", "Strict", "None"):
        samesite = "Lax"

    app.config.update(
        SECRET_KEY=app_secret,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            f"sqlite:///{os.path.join(BASE_DIR, 'vault.db')}",
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=64 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE=samesite,
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0") == "1",
        WTF_CSRF_TIME_LIMIT=3600,
        VAULT_MASTER_KEY=vault_master_key,
    )


def contains_control_chars(value: str) -> bool:
    for ch in value:
        code = ord(ch)
        if code < 32 or code == 127:
            return True
    return False


def normalize_simple_text(value: str) -> str:
    value = (value or "").strip()
    return value


def validate_url_http_https(value: str) -> str:
    value = normalize_simple_text(value)
    if not value:
        return ""
    if len(value) > 2048:
        raise ValueError("URL too long.")
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL scheme must be http or https.")
    if not parsed.netloc:
        raise ValueError("URL must include a hostname.")
    return value


def derive_user_fernet(master_key_b64: str, user_id: int) -> Fernet:
    master_key = base64.urlsafe_b64decode(master_key_b64.encode("utf-8"))
    salt = user_id.to_bytes(8, "big", signed=False)
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b"vault-user-key-v1",
    )
    derived = hkdf.derive(master_key)
    fernet_key = base64.urlsafe_b64encode(derived)
    return Fernet(fernet_key)


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email(), Length(max=254)])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=12, max=256)])
    confirm = PasswordField(
        "Confirm Password",
        validators=[InputRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email(), Length(max=254)])
    password = PasswordField("Password", validators=[InputRequired(), Length(max=256)])
    submit = SubmitField("Log In")


class CredentialForm(FlaskForm):
    service_name = StringField("Service Name", validators=[InputRequired(), Length(min=1, max=100)])
    account_username = StringField("Username", validators=[InputRequired(), Length(min=1, max=150)])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=1, max=1024)])
    url = StringField("URL (optional)", validators=[Optional(), Length(max=2048)])
    submit = SubmitField("Save")


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class Credential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    service_name = db.Column(db.String(100), nullable=False)
    account_username = db.Column(db.String(150), nullable=False)
    password_enc = db.Column(db.LargeBinary, nullable=False)
    url = db.Column(db.String(2048), nullable=False, default="")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (db.Index("ix_cred_user_service", "user_id", "service_name"),)


class LoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), nullable=False, index=True)
    ip = db.Column(db.String(64), nullable=False, index=True)
    window_start = db.Column(db.DateTime(timezone=True), nullable=False)
    count = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime(timezone=True), nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


@login_manager.user_loader
def load_user(user_id: str):
    try:
        uid = int(user_id)
    except ValueError:
        return None
    return db.session.get(User, uid)


def record_login_failure(email: str, ip: str) -> None:
    now = utcnow()
    window = timedelta(minutes=10)
    max_attempts = 5
    lockout = timedelta(minutes=10)

    attempt = (
        LoginAttempt.query.filter_by(email=email, ip=ip)
        .order_by(LoginAttempt.updated_at.desc())
        .first()
    )
    if attempt is None or attempt.window_start < now - window:
        attempt = LoginAttempt(email=email, ip=ip, window_start=now, count=0, locked_until=None)
        db.session.add(attempt)

    attempt.count += 1
    if attempt.count >= max_attempts:
        attempt.locked_until = now + lockout
    db.session.commit()


def is_login_locked(email: str, ip: str) -> bool:
    now = utcnow()
    attempt = (
        LoginAttempt.query.filter_by(email=email, ip=ip)
        .order_by(LoginAttempt.updated_at.desc())
        .first()
    )
    if not attempt or not attempt.locked_until:
        return False
    return attempt.locked_until > now


def clear_login_failures(email: str, ip: str) -> None:
    LoginAttempt.query.filter_by(email=email, ip=ip).delete()
    db.session.commit()


def create_app() -> Flask:
    app = Flask(__name__)
    load_config_from_env(app)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @app.after_request
    def set_security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "img-src 'self' data:; "
            "style-src 'self'; "
            "script-src 'self'"
        )
        if current_user.is_authenticated:
            resp.headers["Cache-Control"] = "no-store"
            resp.headers["Pragma"] = "no-cache"
        return resp

    with app.app_context():
        db.create_all()

    @app.get("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("vault"))
        return redirect(url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("vault"))
        form = RegisterForm()
        if form.validate_on_submit():
            email = normalize_simple_text(form.email.data).lower()
            if contains_control_chars(email):
                abort(400)
            if User.query.filter(func.lower(User.email) == email).first():
                flash("That email is already registered.", "error")
                return render_template("register.html", form=form)
            password_hash = generate_password_hash(form.password.data, method="scrypt")
            user = User(email=email, password_hash=password_hash)
            db.session.add(user)
            db.session.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        return render_template("register.html", form=form)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("vault"))
        form = LoginForm()
        if form.validate_on_submit():
            email = normalize_simple_text(form.email.data).lower()
            if contains_control_chars(email):
                abort(400)
            ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()

            if is_login_locked(email, ip):
                flash("Too many failed attempts. Try again later.", "error")
                return render_template("login.html", form=form), 429

            user = User.query.filter(func.lower(User.email) == email).first()
            if not user or not check_password_hash(user.password_hash, form.password.data):
                record_login_failure(email, ip)
                time.sleep(0.4)
                flash("Invalid email or password.", "error")
                return render_template("login.html", form=form), 401

            clear_login_failures(email, ip)
            login_user(user, fresh=True)
            flash("Logged in.", "success")
            return redirect(url_for("vault"))
        return render_template("login.html", form=form)

    @app.post("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Logged out.", "success")
        return redirect(url_for("login"))

    @app.get("/vault")
    @login_required
    def vault():
        q = normalize_simple_text(request.args.get("q", ""))
        if len(q) > 100:
            abort(400)
        query = Credential.query.filter_by(user_id=current_user.id)
        if q:
            like = f"%{q}%"
            query = query.filter(
                or_(
                    Credential.service_name.ilike(like),
                    Credential.account_username.ilike(like),
                    Credential.url.ilike(like),
                )
            )
        creds = query.order_by(Credential.updated_at.desc()).all()
        return render_template("vault.html", creds=creds, q=q)

    def _get_owned_credential_or_404(cred_id: int) -> Credential:
        cred = Credential.query.filter_by(id=cred_id, user_id=current_user.id).first()
        if not cred:
            abort(404)
        return cred

    @app.route("/vault/new", methods=["GET", "POST"])
    @login_required
    def cred_new():
        form = CredentialForm()
        if form.validate_on_submit():
            service_name = normalize_simple_text(form.service_name.data)
            account_username = normalize_simple_text(form.account_username.data)
            url = normalize_simple_text(form.url.data)

            if contains_control_chars(service_name) or contains_control_chars(account_username) or contains_control_chars(url):
                abort(400)
            try:
                url = validate_url_http_https(url) if url else ""
            except ValueError as e:
                flash(str(e), "error")
                return render_template("cred_form.html", form=form, mode="new")

            fernet = derive_user_fernet(app.config["VAULT_MASTER_KEY"], current_user.id)
            password_enc = fernet.encrypt(form.password.data.encode("utf-8"))

            cred = Credential(
                user_id=current_user.id,
                service_name=service_name,
                account_username=account_username,
                password_enc=password_enc,
                url=url,
            )
            db.session.add(cred)
            db.session.commit()
            flash("Saved.", "success")
            return redirect(url_for("vault"))
        return render_template("cred_form.html", form=form, mode="new")

    @app.route("/vault/<int:cred_id>/edit", methods=["GET", "POST"])
    @login_required
    def cred_edit(cred_id: int):
        cred = _get_owned_credential_or_404(cred_id)
        form = CredentialForm()
        if request.method == "GET":
            form.service_name.data = cred.service_name
            form.account_username.data = cred.account_username
            form.url.data = cred.url
        if form.validate_on_submit():
            service_name = normalize_simple_text(form.service_name.data)
            account_username = normalize_simple_text(form.account_username.data)
            url = normalize_simple_text(form.url.data)
            if contains_control_chars(service_name) or contains_control_chars(account_username) or contains_control_chars(url):
                abort(400)
            try:
                url = validate_url_http_https(url) if url else ""
            except ValueError as e:
                flash(str(e), "error")
                return render_template("cred_form.html", form=form, mode="edit", cred=cred)

            fernet = derive_user_fernet(app.config["VAULT_MASTER_KEY"], current_user.id)
            cred.service_name = service_name
            cred.account_username = account_username
            cred.url = url
            cred.password_enc = fernet.encrypt(form.password.data.encode("utf-8"))
            db.session.commit()
            flash("Updated.", "success")
            return redirect(url_for("vault"))
        return render_template("cred_form.html", form=form, mode="edit", cred=cred)

    class _DeleteForm(FlaskForm):
        submit = SubmitField("Delete")

    @app.post("/vault/<int:cred_id>/delete")
    @login_required
    def cred_delete(cred_id: int):
        form = _DeleteForm()
        if not form.validate_on_submit():
            abort(400)
        cred = _get_owned_credential_or_404(cred_id)
        db.session.delete(cred)
        db.session.commit()
        flash("Deleted.", "success")
        return redirect(url_for("vault"))

    @app.route("/vault/<int:cred_id>/reveal", methods=["GET", "POST"])
    @login_required
    def cred_reveal(cred_id: int):
        cred = _get_owned_credential_or_404(cred_id)
        form = _DeleteForm()
        if request.method == "POST" and form.validate_on_submit():
            return redirect(url_for("vault"))
        fernet = derive_user_fernet(app.config["VAULT_MASTER_KEY"], current_user.id)
        try:
            password_plain = fernet.decrypt(cred.password_enc).decode("utf-8")
        except InvalidToken:
            password_plain = "[Decryption failed]"
        return render_template("reveal.html", cred=cred, password_plain=password_plain, form=form)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
