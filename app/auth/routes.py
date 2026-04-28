from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Order, YarnPurchase, Shipment
from app.auth.forms import LoginForm
from app.services import calculate_dashboard_metrics

auth = Blueprint('auth', __name__)

LOGIN_RATE_LIMIT_WINDOW_SECONDS = 5 * 60
LOGIN_RATE_LIMIT_ATTEMPTS = 5


def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_permission(permission_name):
                flash('You do not have permission to access this resource.', 'danger')
                return redirect(url_for('auth.dashboard'))
            return f(*args, **kwargs)

        return decorated_function

    return decorator

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('You do not have permission to access.', 'danger')
                return redirect(url_for('auth.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def _login_attempts() -> list[float]:
    attempts = session.get('login_attempts', [])
    cutoff = datetime.utcnow().timestamp() - LOGIN_RATE_LIMIT_WINDOW_SECONDS
    attempts = [attempt for attempt in attempts if attempt >= cutoff]
    session['login_attempts'] = attempts
    return attempts


def _register_login_failure():
    attempts = _login_attempts()
    attempts.append(datetime.utcnow().timestamp())
    session['login_attempts'] = attempts


def _clear_login_attempts():
    session.pop('login_attempts', None)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    if request.method == 'GET':
        _clear_login_attempts()
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            _register_login_failure()
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        _clear_login_attempts()
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('auth.dashboard')
        return redirect(next_page)
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    _clear_login_attempts()
    return redirect(url_for('index'))

@auth.route('/dashboard')
@login_required
def dashboard():
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    urgent_deadline = datetime.utcnow() + timedelta(days=2)
    metrics = calculate_dashboard_metrics(month_start, urgent_deadline)

    chart_counts = metrics['order_status_counts']
    return render_template('dashboard.html', 
        total_active_orders=len(metrics['active_orders']),
        total_yarn_stock=float(metrics['total_yarn_stock']),
        monthly_revenue=float(metrics['monthly_revenue']),
        monthly_cost=float(metrics['monthly_cost']),
        estimated_profit=float(metrics['estimated_profit']),
        urgent_orders=metrics['urgent_orders'],
        delayed_orders=metrics['delayed_orders'],
        low_stock_alerts=metrics['low_stock_alerts'],
        current_month_payroll=float(metrics['current_month_payroll']),
        shipment_progress=float(metrics['shipment_progress']),
        production_efficiency=float(metrics['production_efficiency']),
        order_counts=chart_counts,
        total_orders=metrics['total_orders'],
        completed_orders=metrics['completed_orders'],
        shipped_orders=metrics['shipped_orders'],
        active_orders=metrics['active_orders'],
    )
