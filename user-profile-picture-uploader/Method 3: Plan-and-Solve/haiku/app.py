from pathlib import Path
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from routes.upload import upload_bp


def create_app(config=None):
    """Flask application factory with security-first configuration."""
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

    upload_folder = Path('uploads').resolve()
    upload_folder.mkdir(exist_ok=True)
    app.config['UPLOAD_FOLDER'] = str(upload_folder)

    app.config['WTF_CSRF_CHECK_DEFAULT'] = True

    if config:
        app.config.update(config)

    csrf = CSRFProtect(app)
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
    )

    limiter.limit("10/minute")(upload_bp)

    app.register_blueprint(upload_bp)

    app.logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=False, host='127.0.0.1', port=5000)
