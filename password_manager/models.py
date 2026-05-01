from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import base64
import os

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    master_password_hash = db.Column(db.String(255), nullable=False)
    encryption_salt = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    passwords = db.relationship('Password', backref='user', lazy=True, cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_master_password(self, password):
        """Hash and set master password."""
        self.master_password_hash = generate_password_hash(password)
        if not self.encryption_salt:
            self.encryption_salt = base64.b64encode(os.urandom(16)).decode()

    def verify_master_password(self, password):
        """Verify master password."""
        return check_password_hash(self.master_password_hash, password)

    def get_encryption_salt(self):
        """Get encryption salt as bytes."""
        return base64.b64decode(self.encryption_salt)


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), default='#3498db')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    passwords = db.relationship('Password', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


class Password(db.Model):
    __tablename__ = 'passwords'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    encrypted_password = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Password {self.title}>'
