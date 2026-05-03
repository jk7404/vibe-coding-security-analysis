from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp, Optional, ValidationError, URL
from models import User
from urllib.parse import urlparse
import re


class RegistrationForm(FlaskForm):
    """Registration form with secure input validation."""
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(min=3, max=20, message='Username must be 3-20 characters'),
            Regexp('^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
        ]
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(message='Invalid email format')
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8, message='Password must be at least 8 characters'),
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match')
        ]
    )
    submit = SubmitField('Register')

    def validate_username(self, field):
        """Check if username already exists."""
        user = User.query.filter_by(username=field.data.lower()).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')

    def validate_email(self, field):
        """Check if email already exists."""
        user = User.query.filter_by(email=field.data.lower()).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')

    def validate_password(self, field):
        """Validate password strength."""
        password = field.data
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[0-9]', password):
            raise ValidationError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Password must contain at least one special character (!@#$%^&*)')


class LoginForm(FlaskForm):
    """Login form with input validation."""
    username = StringField(
        'Username',
        validators=[DataRequired()]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    submit = SubmitField('Login')


class CredentialForm(FlaskForm):
    """Form for adding/editing stored credentials."""
    service_name = StringField(
        'Service Name',
        validators=[
            DataRequired(),
            Length(min=1, max=255, message='Service name must not exceed 255 characters')
        ]
    )
    username = StringField(
        'Username/Email',
        validators=[
            DataRequired(),
            Length(min=1, max=255, message='Username must not exceed 255 characters')
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=1, max=255, message='Password must not exceed 255 characters')
        ]
    )
    url = StringField(
        'URL (Optional)',
        validators=[
            Optional(),
            Length(max=500, message='URL must not exceed 500 characters')
        ]
    )
    submit = SubmitField('Save Credential')

    def validate_url(self, field):
        """Validate URL format and scheme if provided."""
        if field.data and field.data.strip():
            try:
                parsed = urlparse(field.data)
                if parsed.scheme and parsed.scheme not in ['http', 'https']:
                    raise ValidationError('Only HTTP and HTTPS URLs are allowed')
                if not parsed.scheme and field.data.strip():
                    if not (field.data.startswith('http://') or field.data.startswith('https://')):
                        if '.' in field.data:
                            raise ValidationError('Invalid URL format. Use http://example.com or https://example.com')
            except Exception:
                raise ValidationError('Invalid URL format')


class SearchForm(FlaskForm):
    """Search form for finding credentials."""
    search_query = StringField(
        'Search',
        validators=[
            Length(max=255, message='Search query must not exceed 255 characters')
        ]
    )
    submit = SubmitField('Search')
