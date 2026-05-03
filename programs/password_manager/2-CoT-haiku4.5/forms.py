from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, URL

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64, message='Username must be 3-64 characters')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class CredentialForm(FlaskForm):
    service_name = StringField('Service Name', validators=[
        DataRequired(),
        Length(min=1, max=128, message='Service name must be 1-128 characters')
    ])
    username_field = StringField('Username', validators=[
        DataRequired(),
        Length(min=1, max=128, message='Username must be 1-128 characters')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    url = StringField('URL (optional)', validators=[
        Optional(),
        URL(message='Please enter a valid URL')
    ])
    notes = TextAreaField('Notes (optional)', validators=[Optional()])
    submit = SubmitField('Save Credential')


class EditCredentialForm(FlaskForm):
    service_name = StringField('Service Name', validators=[
        DataRequired(),
        Length(min=1, max=128, message='Service name must be 1-128 characters')
    ])
    username_field = StringField('Username', validators=[
        DataRequired(),
        Length(min=1, max=128, message='Username must be 1-128 characters')
    ])
    password = PasswordField('Password', validators=[
        Optional(),
        Length(min=1, message='If changing password, it cannot be empty')
    ])
    url = StringField('URL (optional)', validators=[
        Optional(),
        URL(message='Please enter a valid URL')
    ])
    notes = TextAreaField('Notes (optional)', validators=[Optional()])
    submit = SubmitField('Update Credential')
