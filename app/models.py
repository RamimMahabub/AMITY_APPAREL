from datetime import date, datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Staff')  # Admin, Manager, Staff
    recorded_salary_payments = db.relationship('SalaryPayment', backref='paid_by', lazy=True)
    reset_tokens = db.relationship('PasswordResetToken', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, *roles):
        return self.role in roles

    def has_permission(self, permission_name):
        if self.role == 'Admin':
            return True
        return (
            db.session.query(RolePermission.id)
            .join(Permission, RolePermission.permission_id == Permission.id)
            .filter(RolePermission.role_name == self.role, Permission.name == permission_name)
            .first()
            is not None
        )

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    contact_person = db.Column(db.String(64))
    phone = db.Column(db.String(32))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    yarn_purchases = db.relationship('YarnPurchase', backref='supplier', lazy=True)

class YarnPurchase(db.Model):
    __tablename__ = 'yarn_purchases'
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    yarn_type = db.Column(db.String(64), nullable=False)
    color = db.Column(db.String(64), nullable=False)
    qty_kg = db.Column(db.Numeric(10, 2), nullable=False)
    price_per_kg = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='Received')  # Received, Assigned
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    knitting_jobs = db.relationship('KnittingJob', backref='yarn_purchase', lazy=True)
    ledger_entries = db.relationship('InventoryLedger', backref='yarn_purchase', lazy=True, cascade='all, delete-orphan')

class KnittingJob(db.Model):
    __tablename__ = 'knitting_jobs'
    id = db.Column(db.Integer, primary_key=True)
    yarn_purchase_id = db.Column(db.Integer, db.ForeignKey('yarn_purchases.id'), nullable=False)
    company_name = db.Column(db.String(128), nullable=False)
    sent_qty_kg = db.Column(db.Numeric(10, 2), nullable=False)
    received_fabric_kg = db.Column(db.Numeric(10, 2), default=0.0)
    waste_kg = db.Column(db.Numeric(10, 2), default=0.0)
    status = db.Column(db.String(20), default='In Progress')  # In Progress, Completed
    dyeing_jobs = db.relationship('DyeingJob', backref='knitting_job', lazy=True)

class DyeingJob(db.Model):
    __tablename__ = 'dyeing_jobs'
    id = db.Column(db.Integer, primary_key=True)
    knitting_job_id = db.Column(db.Integer, db.ForeignKey('knitting_jobs.id'), nullable=False)
    dyeing_unit_name = db.Column(db.String(128), nullable=False)
    color_specification = db.Column(db.String(64), nullable=False)
    input_qty = db.Column(db.Numeric(10, 2), nullable=False)
    output_qty = db.Column(db.Numeric(10, 2), default=0.0)
    status = db.Column(db.String(20), default='In Progress')  # In Progress, Completed

class Buyer(db.Model):
    __tablename__ = 'buyers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    country = db.Column(db.String(64))
    contact_info = db.Column(db.String(128))
    orders = db.relationship('Order', backref='buyer', lazy=True)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('buyers.id'), nullable=False)
    product_name = db.Column(db.String(128), nullable=False)
    design_image = db.Column(db.String(256))  # file_path
    total_qty = db.Column(db.Integer, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Active')  # Active, Completed, Shipped
    sale_price_per_unit = db.Column(db.Numeric(12, 2), nullable=False, default=15)
    estimated_yarn_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    estimated_dyeing_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    estimated_labor_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    estimated_shipping_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    invoice_number = db.Column(db.String(64), unique=True, index=True)
    invoice_generated_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    production_stages = db.relationship('ProductionStage', backref='order', lazy=True)
    shipments = db.relationship('Shipment', backref='order', lazy=True)

class ProductionStage(db.Model):
    __tablename__ = 'production_stages'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    stage_name = db.Column(db.String(64), nullable=False)  # Cutting, Sewing, Finishing, Packing
    input_qty = db.Column(db.Integer, nullable=False, default=0)
    output_qty = db.Column(db.Integer, nullable=False, default=0)
    waste = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), default='In Progress')  # In Progress, Completed

class Shipment(db.Model):
    __tablename__ = 'shipments'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    container_no = db.Column(db.String(64), nullable=False)
    shipping_date = db.Column(db.DateTime)
    final_qty = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Shipped
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(128), nullable=False)
    designation = db.Column(db.String(64), nullable=False)
    department = db.Column(db.String(64), nullable=False)
    monthly_salary = db.Column(db.Numeric(12, 2), nullable=False)
    join_date = db.Column(db.Date, nullable=False, default=date.today)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    salary_payments = db.relationship('SalaryPayment', backref='employee', lazy=True, cascade='all, delete-orphan')


class SalaryPayment(db.Model):
    __tablename__ = 'salary_payments'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    payment_month = db.Column(db.Date, nullable=False, index=True)  # Store first day of the month.
    paid_amount = db.Column(db.Numeric(12, 2), nullable=False)
    paid_on = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    note = db.Column(db.String(255))
    paid_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    expense_date = db.Column(db.Date, nullable=False, index=True, default=date.today)
    category = db.Column(db.String(64), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.relationship('User', backref='expenses', lazy=True)


class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))


class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(20), nullable=False, index=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False, index=True)
    permission = db.relationship('Permission', backref='role_permissions', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('role_name', 'permission_id', name='uq_role_permission'),
    )


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token_hash = db.Column(db.String(255), nullable=False, unique=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class InventoryLedger(db.Model):
    __tablename__ = 'inventory_ledger'
    id = db.Column(db.Integer, primary_key=True)
    yarn_purchase_id = db.Column(db.Integer, db.ForeignKey('yarn_purchases.id'), nullable=False, index=True)
    movement_type = db.Column(db.String(16), nullable=False, default='IN')  # IN, OUT, ADJUSTMENT
    qty_kg = db.Column(db.Numeric(10, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2))
    reference_type = db.Column(db.String(64))
    reference_id = db.Column(db.Integer)
    note = db.Column(db.String(255))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.relationship('User', backref='inventory_ledger_entries', lazy=True)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(32), nullable=False, index=True)
    entity_type = db.Column(db.String(64), nullable=False, index=True)
    entity_id = db.Column(db.Integer, index=True)
    before_data = db.Column(db.Text)
    after_data = db.Column(db.Text)
    note = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    ip_address = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship('User', backref='audit_logs', lazy=True)
