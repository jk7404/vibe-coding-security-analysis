from __future__ import annotations

import base64
import os
import secrets
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Optional

import bcrypt
from cryptography.fernet import Fernet
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional as OptionalV, URL

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
SECRET_KEY_PATH = INSTANCE_DIR / "secret_key.txt"

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login"


def _load_or_create_secret_key() -> str:
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text(encoding="utf-8").strip()
    secret_key = secrets.token_urlsafe(48)
    SECRET_KEY_PATH.write_text(secret_key, encoding="utf-8")
    return secret_key


def _user_fernet(user_id: int, app_secret: str) -> Fernet:
    """
    Server-side encryption for stored passwords.

    Security note: this protects against casual DB leaks, but anyone with access
    to the server's SECRET_KEY can decrypt. For true "zero-knowledge" storage,
    you'd derive keys from a user-provided secret that the server never stores.
    """
    raw = sha256(f"{app_secret}::{user_id}".encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(raw))


class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[bytes] = mapped_column(db.LargeBinary(60), nullable=False)

    credentials: Mapped[list["Credential"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    def check_password(self, password: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), self.password_hash)
        except ValueError:
            return False


class Credential(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("user.id"), index=True, nullable=False)

    service_name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    password_encrypted: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped[User] = relationship(back_populates="credentials")


@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    return db.session.get(User, int(user_id))


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=10, max=200)])
    confirm = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class CredentialForm(FlaskForm):
    service_name = StringField("Service name", validators=[DataRequired(), Length(max=200)])
    username = StringField("Username", validators=[DataRequired(), Length(max=200)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=1, max=500)])
    url = StringField("URL", validators=[OptionalV(), URL(require_tld=False, message="Enter a valid URL.")])
    submit = SubmitField("Save")


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", _load_or_create_secret_key())
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{(INSTANCE_DIR / 'vault.db').as_posix()}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_TIME_LIMIT"] = None

    db.init_app(app)
    login_manager.init_app(app)

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
            existing = db.session.execute(db.select(User).where(User.email == form.email.data.lower())).scalar_one_or_none()
            if existing:
                flash("That email is already registered. Please sign in.", "warning")
                return redirect(url_for("login"))
            user = User(email=form.email.data.lower())
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Account created.", "success")
            return redirect(url_for("vault"))
        return render_template("register.html", form=form)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("vault"))
        form = LoginForm()
        if form.validate_on_submit():
            user = db.session.execute(db.select(User).where(User.email == form.email.data.lower())).scalar_one_or_none()
            if not user or not user.check_password(form.password.data):
                flash("Invalid email or password.", "danger")
                return render_template("login.html", form=form), 401
            login_user(user)
            return redirect(url_for("vault"))
        return render_template("login.html", form=form)

    @app.post("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Signed out.", "success")
        return redirect(url_for("login"))

    @dataclass(frozen=True)
    class VaultRow:
        cred: Credential
        password_plain: str

    def _decrypt_for_current_user(cred: Credential) -> str:
        if cred.user_id != current_user.id:
            abort(404)
        f = _user_fernet(current_user.id, app.config["SECRET_KEY"])
        return f.decrypt(cred.password_encrypted.encode("utf-8")).decode("utf-8")

    def _encrypt_for_current_user(password_plain: str) -> str:
        f = _user_fernet(current_user.id, app.config["SECRET_KEY"])
        return f.encrypt(password_plain.encode("utf-8")).decode("utf-8")

    @app.get("/vault")
    @login_required
    def vault():
        q = (request.args.get("q") or "").strip()
        stmt = db.select(Credential).where(Credential.user_id == current_user.id)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                (Credential.service_name.ilike(like))
                | (Credential.username.ilike(like))
                | (Credential.url.ilike(like))
            )
        stmt = stmt.order_by(Credential.service_name.asc())
        creds = db.session.execute(stmt).scalars().all()
        return render_template("vault.html", creds=creds, q=q)

    @app.route("/credential/new", methods=["GET", "POST"])
    @login_required
    def credential_new():
        form = CredentialForm()
        if form.validate_on_submit():
            cred = Credential(
                user_id=current_user.id,
                service_name=form.service_name.data.strip(),
                username=form.username.data.strip(),
                url=(form.url.data or "").strip() or None,
                password_encrypted=_encrypt_for_current_user(form.password.data),
            )
            db.session.add(cred)
            db.session.commit()
            flash("Saved.", "success")
            return redirect(url_for("vault"))
        return render_template("credential_form.html", form=form, title="Add credential")

    def _get_cred_or_404(cred_id: int) -> Credential:
        cred = db.session.get(Credential, cred_id)
        if not cred or cred.user_id != current_user.id:
            abort(404)
        return cred

    @app.route("/credential/<int:cred_id>/edit", methods=["GET", "POST"])
    @login_required
    def credential_edit(cred_id: int):
        cred = _get_cred_or_404(cred_id)
        form = CredentialForm()
        if request.method == "GET":
            form.service_name.data = cred.service_name
            form.username.data = cred.username
            form.url.data = cred.url or ""
            form.password.data = _decrypt_for_current_user(cred)
        if form.validate_on_submit():
            cred.service_name = form.service_name.data.strip()
            cred.username = form.username.data.strip()
            cred.url = (form.url.data or "").strip() or None
            cred.password_encrypted = _encrypt_for_current_user(form.password.data)
            db.session.commit()
            flash("Updated.", "success")
            return redirect(url_for("vault"))
        return render_template("credential_form.html", form=form, title="Edit credential")

    @app.post("/credential/<int:cred_id>/delete")
    @login_required
    def credential_delete(cred_id: int):
        cred = _get_cred_or_404(cred_id)
        db.session.delete(cred)
        db.session.commit()
        flash("Deleted.", "success")
        return redirect(url_for("vault"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)

