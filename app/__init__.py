import os

from flask import Flask, redirect, render_template, url_for
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
    database_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if isinstance(database_uri, str) and database_uri.startswith('mysql'):
        app.config.setdefault(
            'SQLALCHEMY_ENGINE_OPTIONS',
            {
                'pool_pre_ping': True,
                'pool_recycle': 280,
                'connect_args': {'connect_timeout': 5},
            },
        )
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

    from app.payroll.routes import payroll as payroll_bp
    app.register_blueprint(payroll_bp, url_prefix='/payroll')

    from app.expenses.routes import expenses as expenses_bp
    app.register_blueprint(expenses_bp, url_prefix='/expenses')

    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('auth.dashboard'))
        return render_template('home.html')

    return app
