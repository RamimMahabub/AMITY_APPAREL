from app import create_app, db
from app.models import User, Buyer, Supplier, YarnPurchase, KnittingJob, DyeingJob, Order
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    # Only for dev: drop and recreate
    db.drop_all()
    db.create_all()

    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@amityapparel.com', role='Admin')
        admin.set_password('admin123')
        db.session.add(admin)
        
        manager = User(username='manager', email='manager@amityapparel.com', role='Manager')
        manager.set_password('manager123')
        db.session.add(manager)

        staff = User(username='staff', email='staff@amityapparel.com', role='Staff')
        staff.set_password('staff123')
        db.session.add(staff)

    # Seed Suppliers
    s1 = Supplier(name='Global Yarns Ltd', contact_person='John Doe', phone='123-456', address='Dhaka')
    s2 = Supplier(name='Premium Threads Inc', contact_person='Jane Smith', phone='987-654', address='Chattogram')
    db.session.add_all([s1, s2])
    db.session.commit()

    # Seed Buyers
    b1 = Buyer(name='H&M', country='Sweden', contact_info='contact@hm.com')
    b2 = Buyer(name='Zara', country='Spain', contact_info='hello@zara.com')
    db.session.add_all([b1, b2])
    db.session.commit()

    # Seed Yarn
    y1 = YarnPurchase(supplier_id=s1.id, yarn_type='Cotton 30s', color='Raw White', qty_kg=5000, price_per_kg=3.5, status='Received')
    y2 = YarnPurchase(supplier_id=s2.id, yarn_type='Polyester 20d', color='Black', qty_kg=2000, price_per_kg=2.8, status='Received')
    db.session.add_all([y1, y2])
    db.session.commit()

    # Seed Orders
    o1 = Order(buyer_id=b1.id, product_name='Basic T-Shirt', total_qty=10000, deadline=datetime.utcnow() + timedelta(days=3))
    o2 = Order(buyer_id=b2.id, product_name='Summer Polo', total_qty=5000, deadline=datetime.utcnow() + timedelta(days=10))
    db.session.add_all([o1, o2])
    db.session.commit()

    print("Database seeded successfully with dummy data! Login with admin / admin123")
