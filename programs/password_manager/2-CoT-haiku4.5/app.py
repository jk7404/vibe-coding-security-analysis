from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User
from dotenv import load_dotenv

load_dotenv()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        from routes.auth import auth_bp
        from routes.vault import vault_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(vault_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='127.0.0.1', port=5000)
