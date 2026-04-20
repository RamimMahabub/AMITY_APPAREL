from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlsplit
from app import db
from app.models import User, Order, YarnPurchase, Shipment
from app.auth.forms import LoginForm
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func

auth = Blueprint('auth', __name__)

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

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('auth.dashboard')
        return redirect(next_page)
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@auth.route('/dashboard')
@login_required
def dashboard():
    total_active_orders = Order.query.filter_by(status='Active').count()
    total_yarn_stock_val = db.session.query(func.sum(YarnPurchase.qty_kg)).filter(YarnPurchase.status == 'Received').scalar()
    total_yarn_stock = float(total_yarn_stock_val) if total_yarn_stock_val else 0.0
    
    # Revenue estimate ($15 per item logic for demo)
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    monthly_orders = Order.query.filter(Order.deadline >= month_start).all()
    monthly_revenue = sum([o.total_qty * 15 for o in monthly_orders])
    
    # Urgent orders
    urgent_deadline = datetime.utcnow() + timedelta(days=2)
    urgent_orders = Order.query.filter(Order.status == 'Active', Order.deadline <= urgent_deadline).all()

    order_counts = {
        'Active': Order.query.filter_by(status='Active').count(),
        'Completed': Order.query.filter_by(status='Completed').count(),
        'Shipped': Order.query.filter_by(status='Shipped').count()
    }
    
    return render_template('dashboard.html', 
        total_active_orders=total_active_orders,
        total_yarn_stock=total_yarn_stock,
        monthly_revenue=monthly_revenue,
        urgent_orders=urgent_orders,
        order_counts=order_counts
    )
