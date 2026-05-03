from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from datetime import timedelta
import os
from models import db, User, Credential
from forms import RegistrationForm, LoginForm, CredentialForm, SearchForm


def create_app():
    """Application factory with security configuration."""
    app = Flask(__name__)

    # Security Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///password_manager.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Session Security Configuration
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

    # WTForms Configuration (CSRF Protection)
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = None

    # Database Initialization
    db.init_app(app)

    # Rate Limiting Configuration
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )

    # Create database tables
    with app.app_context():
        db.create_all()

    # ==================== Authentication Decorator ====================
    def login_required(f):
        """Decorator to require user login."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    # ==================== Routes ====================

    @app.route('/')
    def index():
        """Home page - redirect to dashboard if logged in."""
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    @limiter.limit("3 per minute")
    def register():
        """User registration with rate limiting."""
        if 'user_id' in session:
            return redirect(url_for('dashboard'))

        form = RegistrationForm()
        if form.validate_on_submit():
            # Create new user with hashed password
            user = User(
                username=form.username.data.lower(),
                email=form.email.data.lower()
            )
            user.set_password(form.password.data)

            try:
                db.session.add(user)
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred during registration. Please try again.', 'error')
                return redirect(url_for('register'))

        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    @limiter.limit("5 per minute")
    def login():
        """User login with rate limiting and timing-safe password check."""
        if 'user_id' in session:
            return redirect(url_for('dashboard'))

        form = LoginForm()
        if form.validate_on_submit():
            # Generic error message to prevent user enumeration
            user = User.query.filter_by(username=form.username.data.lower()).first()

            if user and user.check_password(form.password.data):
                session['user_id'] = user.id
                session['username'] = user.username
                session.permanent = True
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'error')

        return render_template('login.html', form=form)

    @app.route('/logout')
    def logout():
        """User logout with session cleanup."""
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Dashboard with credential list and search."""
        user_id = session['user_id']
        search_form = SearchForm()
        search_query = request.args.get('search_query', '').strip()

        if search_query:
            # Parameterized search query - no SQL injection possible
            credentials = Credential.query.filter(
                Credential.user_id == user_id,
                Credential.service_name.ilike(f'%{search_query}%')
            ).all()
        else:
            # Get all credentials for current user only
            credentials = Credential.query.filter_by(user_id=user_id).all()

        return render_template(
            'dashboard.html',
            credentials=credentials,
            search_form=search_form,
            search_query=search_query
        )

    @app.route('/credential/add', methods=['GET', 'POST'])
    @login_required
    def add_credential():
        """Add new credential with input validation."""
        user_id = session['user_id']
        form = CredentialForm()

        if form.validate_on_submit():
            credential = Credential(
                user_id=user_id,
                service_name=form.service_name.data,
                username=form.username.data,
                password=form.password.data,
                url=form.url.data if form.url.data else None
            )

            try:
                db.session.add(credential)
                db.session.commit()
                flash(f'Credential for {form.service_name.data} saved successfully!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                db.session.rollback()
                flash('Error saving credential. Please try again.', 'error')

        return render_template('credential_form.html', form=form, action='Add')

    @app.route('/credential/<int:credential_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_credential(credential_id):
        """Edit existing credential with authorization check."""
        user_id = session['user_id']

        # Authorization check - ensure credential belongs to current user
        credential = Credential.query.get(credential_id)
        if not credential or credential.user_id != user_id:
            flash('You do not have permission to access this credential.', 'error')
            return redirect(url_for('dashboard'))

        form = CredentialForm()

        if form.validate_on_submit():
            credential.service_name = form.service_name.data
            credential.username = form.username.data
            credential.password = form.password.data
            credential.url = form.url.data if form.url.data else None

            try:
                db.session.commit()
                flash(f'Credential for {form.service_name.data} updated successfully!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                db.session.rollback()
                flash('Error updating credential. Please try again.', 'error')

        elif request.method == 'GET':
            form.service_name.data = credential.service_name
            form.username.data = credential.username
            form.password.data = credential.password
            form.url.data = credential.url

        return render_template('credential_form.html', form=form, action='Edit', credential_id=credential_id)

    @app.route('/credential/<int:credential_id>/delete', methods=['POST'])
    @login_required
    def delete_credential(credential_id):
        """Delete credential with authorization check and CSRF token."""
        user_id = session['user_id']

        # Authorization check - ensure credential belongs to current user
        credential = Credential.query.get(credential_id)
        if not credential or credential.user_id != user_id:
            flash('You do not have permission to delete this credential.', 'error')
            return redirect(url_for('dashboard'))

        service_name = credential.service_name

        try:
            db.session.delete(credential)
            db.session.commit()
            flash(f'Credential for {service_name} deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting credential. Please try again.', 'error')

        return redirect(url_for('dashboard'))

    # ==================== Error Handlers ====================

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return render_template('error.html', error_code=404, error_message='Page not found.'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 errors."""
        return render_template('error.html', error_code=403, error_message='Access denied.'), 403

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        db.session.rollback()
        return render_template('error.html', error_code=500, error_message='An internal error occurred.'), 500

    return app


if __name__ == '__main__':
    app = create_app()
    # Development server - set SECRET_KEY for production
    app.run(debug=False, host='127.0.0.1', port=5000)
