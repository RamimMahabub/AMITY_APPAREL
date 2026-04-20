from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from datetime import datetime

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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
