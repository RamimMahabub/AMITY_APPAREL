from datetime import datetime, timedelta

from sqlalchemy import text

from app import create_app, db
from app.models import (
    Buyer,
    DyeingJob,
    Employee,
    KnittingJob,
    Order,
    ProductionStage,
    SalaryPayment,
    Shipment,
    Supplier,
    User,
    YarnPurchase,
)

app = create_app()


def days_from_now(days):
    return datetime.utcnow() + timedelta(days=days)


def month_start(dt: datetime):
    return dt.date().replace(day=1)


with app.app_context():
    # Reset schema for demo seeding.
    if db.engine.dialect.name == 'mysql':
        db.session.execute(text('SET FOREIGN_KEY_CHECKS=0'))
    db.drop_all()
    db.create_all()
    if db.engine.dialect.name == 'mysql':
        db.session.execute(text('SET FOREIGN_KEY_CHECKS=1'))
    db.session.commit()

    admin = User(username='admin', email='admin@amityapparel.com', role='Admin')
    admin.set_password('admin123')
    manager = User(username='manager', email='manager@amityapparel.com', role='Manager')
    manager.set_password('manager123')
    staff = User(username='staff', email='staff@amityapparel.com', role='Staff')
    staff.set_password('staff123')
    db.session.add_all([admin, manager, staff])
    db.session.flush()

    # Bangladesh-style supplier network.
    suppliers = [
        Supplier(
            name='Dhaka Cotton Mills Ltd',
            contact_person='Rahim Uddin',
            phone='01711-234567',
            email='rahim@dhakacotton.bd',
            address='Gazipur, Dhaka',
        ),
        Supplier(
            name='Chattogram Yarn House',
            contact_person='Farzana Akter',
            phone='01811-345678',
            email='farzana@ctgyarn.bd',
            address='CEPZ, Chattogram',
        ),
        Supplier(
            name='Narayanganj Fibres Ltd',
            contact_person='Alamgir Hossain',
            phone='01911-456789',
            email='alamgir@narayanganjfibres.bd',
            address='Fatullah, Narayanganj',
        ),
        Supplier(
            name='Mymensingh Threads & Co',
            contact_person='Nusrat Jahan',
            phone='01611-567890',
            email='nusrat@mymensinghthreads.bd',
            address='Bhaluka, Mymensingh',
        ),
    ]
    db.session.add_all(suppliers)
    db.session.flush()

    buyers = [
        Buyer(name='Aarong', country='Bangladesh', contact_info='merch@aarong.com.bd'),
        Buyer(name='Yellow by Beximco', country='Bangladesh', contact_info='sourcing@yellow.com.bd'),
        Buyer(name='H&M', country='Sweden', contact_info='orders@hm.com'),
        Buyer(name='Zara', country='Spain', contact_info='bulk@zara.com'),
    ]
    db.session.add_all(buyers)
    db.session.flush()

    yarn_purchases = [
        YarnPurchase(
            supplier_id=suppliers[0].id,
            yarn_type='Cotton 30s Combed',
            color='Raw White',
            qty_kg=5200,
            price_per_kg=3.55,
            status='Received',
        ),
        YarnPurchase(
            supplier_id=suppliers[1].id,
            yarn_type='Polyester 20D',
            color='Jet Black',
            qty_kg=2400,
            price_per_kg=2.90,
            status='Received',
        ),
        YarnPurchase(
            supplier_id=suppliers[2].id,
            yarn_type='Melange 24s',
            color='Grey Melange',
            qty_kg=3100,
            price_per_kg=3.20,
            status='Received',
        ),
        YarnPurchase(
            supplier_id=suppliers[3].id,
            yarn_type='Cotton Spandex 40s',
            color='Navy Blue',
            qty_kg=1800,
            price_per_kg=4.10,
            status='Assigned',
        ),
    ]
    db.session.add_all(yarn_purchases)
    db.session.flush()

    knitting_jobs = [
        KnittingJob(
            yarn_purchase_id=yarn_purchases[0].id,
            company_name='Ruposhi Knitters Ltd',
            sent_qty_kg=3000,
            received_fabric_kg=2780,
            waste_kg=220,
            status='Completed',
        ),
        KnittingJob(
            yarn_purchase_id=yarn_purchases[1].id,
            company_name='Shonar Bangla Knit House',
            sent_qty_kg=1600,
            received_fabric_kg=1405,
            waste_kg=195,
            status='Completed',
        ),
        KnittingJob(
            yarn_purchase_id=yarn_purchases[3].id,
            company_name='Desh View Knit Factory',
            sent_qty_kg=900,
            received_fabric_kg=0,
            waste_kg=0,
            status='In Progress',
        ),
    ]
    db.session.add_all(knitting_jobs)
    db.session.flush()

    dyeing_jobs = [
        DyeingJob(
            knitting_job_id=knitting_jobs[0].id,
            dyeing_unit_name='Apon Dyeing & Finishing',
            color_specification='Royal Blue',
            input_qty=2600,
            output_qty=2525,
            status='Completed',
        ),
        DyeingJob(
            knitting_job_id=knitting_jobs[1].id,
            dyeing_unit_name='Mukti Dye House',
            color_specification='Deep Black',
            input_qty=1350,
            output_qty=0,
            status='In Progress',
        ),
    ]
    db.session.add_all(dyeing_jobs)
    db.session.flush()

    orders = [
        Order(
            buyer_id=buyers[0].id,
            product_name='Panjabi Cotton Tee - Eid Batch',
            total_qty=12000,
            deadline=days_from_now(3),
            status='Active',
        ),
        Order(
            buyer_id=buyers[1].id,
            product_name='Summer Polo - Local Retail Drop',
            total_qty=8500,
            deadline=days_from_now(10),
            status='Active',
        ),
        Order(
            buyer_id=buyers[2].id,
            product_name='Ladies Top - Export Batch',
            total_qty=6400,
            deadline=days_from_now(18),
            status='Completed',
        ),
        Order(
            buyer_id=buyers[3].id,
            product_name='Kids Jogger Pant - Winter Line',
            total_qty=5000,
            deadline=days_from_now(25),
            status='Shipped',
        ),
    ]
    db.session.add_all(orders)
    db.session.flush()

    production_stages = [
        ProductionStage(
            order_id=orders[0].id,
            stage_name='Cutting',
            input_qty=12000,
            output_qty=11890,
            waste=110,
            status='Completed',
        ),
        ProductionStage(
            order_id=orders[0].id,
            stage_name='Sewing',
            input_qty=11890,
            output_qty=11240,
            waste=650,
            status='In Progress',
        ),
        ProductionStage(
            order_id=orders[1].id,
            stage_name='Cutting',
            input_qty=8500,
            output_qty=8400,
            waste=100,
            status='Completed',
        ),
        ProductionStage(
            order_id=orders[2].id,
            stage_name='Packing',
            input_qty=6400,
            output_qty=6360,
            waste=40,
            status='Completed',
        ),
        ProductionStage(
            order_id=orders[3].id,
            stage_name='Packing',
            input_qty=5000,
            output_qty=4985,
            waste=15,
            status='Completed',
        ),
    ]
    db.session.add_all(production_stages)

    shipments = [
        Shipment(
            order_id=orders[3].id,
            container_no='BDU-240521-A',
            shipping_date=days_from_now(-2),
            final_qty=4985,
            status='Shipped',
        ),
        Shipment(
            order_id=orders[2].id,
            container_no='BDU-240521-B',
            shipping_date=days_from_now(-1),
            final_qty=6360,
            status='Shipped',
        ),
    ]
    db.session.add_all(shipments)

    employees = [
        Employee(
            employee_code='EMP-001',
            full_name='Md. Sohel Rana',
            designation='Line Supervisor',
            department='Sewing',
            monthly_salary=28500,
            join_date=datetime(2022, 6, 5).date(),
            is_active=True,
        ),
        Employee(
            employee_code='EMP-002',
            full_name='Shirin Akter',
            designation='Quality Inspector',
            department='Finishing',
            monthly_salary=24000,
            join_date=datetime(2023, 1, 12).date(),
            is_active=True,
        ),
        Employee(
            employee_code='EMP-003',
            full_name='Abdul Karim',
            designation='Cutting Operator',
            department='Cutting',
            monthly_salary=22000,
            join_date=datetime(2021, 11, 20).date(),
            is_active=True,
        ),
        Employee(
            employee_code='EMP-004',
            full_name='Nigar Sultana',
            designation='Helper',
            department='Packing',
            monthly_salary=18000,
            join_date=datetime(2024, 2, 3).date(),
            is_active=True,
        ),
        Employee(
            employee_code='EMP-005',
            full_name='Jahangir Alam',
            designation='Machine Mechanic',
            department='Maintenance',
            monthly_salary=30000,
            join_date=datetime(2020, 9, 1).date(),
            is_active=True,
        ),
    ]
    db.session.add_all(employees)
    db.session.flush()

    current_month = month_start(datetime.utcnow())
    prev_month = (datetime.utcnow().replace(day=1) - timedelta(days=1)).date().replace(day=1)

    salary_payments = [
        SalaryPayment(
            employee_id=employees[0].id,
            payment_month=current_month,
            paid_amount=20000,
            paid_by_id=admin.id,
            note='Advance + mid-month',
        ),
        SalaryPayment(
            employee_id=employees[1].id,
            payment_month=current_month,
            paid_amount=24000,
            paid_by_id=manager.id,
            note='Full month paid',
        ),
        SalaryPayment(
            employee_id=employees[2].id,
            payment_month=current_month,
            paid_amount=12000,
            paid_by_id=manager.id,
            note='Partial paid',
        ),
        SalaryPayment(
            employee_id=employees[0].id,
            payment_month=prev_month,
            paid_amount=28500,
            paid_by_id=admin.id,
            note='Previous month full payment',
        ),
        SalaryPayment(
            employee_id=employees[3].id,
            payment_month=prev_month,
            paid_amount=18000,
            paid_by_id=manager.id,
            note='Previous month full payment',
        ),
    ]
    db.session.add_all(salary_payments)

    db.session.commit()

    print('Database seeded with Bangladesh-style demo data. Login: admin/admin123, manager/manager123, staff/staff123')
