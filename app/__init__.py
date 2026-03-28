from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register blueprints (these modules will be created next)
    from app.auth.routes import auth as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.yarn.routes import yarn as yarn_bp
    app.register_blueprint(yarn_bp, url_prefix='/yarn')

    from app.production.routes import production as prod_bp
    app.register_blueprint(prod_bp, url_prefix='/production')

    from app.orders.routes import orders as orders_bp
    app.register_blueprint(orders_bp, url_prefix='/orders')

    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.dashboard'))

    return app
