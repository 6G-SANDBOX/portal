from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from logging.handlers import RotatingFileHandler
from config import Config
import os
import logging


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'authentication.login'
login.login_message = 'Please log in to access this page.'
bootstrap = Bootstrap()
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.authentication import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/authentication')

    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/5genesis.log', maxBytes=1024000,
                                           backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('5Genesis startup')

    return app


from app import models
