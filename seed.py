from datetime import datetime, timedelta

from sqlalchemy import text

from app import create_app, db
from app.models import (
    AuditLog,
    Buyer,
    DyeingJob,
    Employee,
    InventoryLedger,
    KnittingJob,
    Order,
    Permission,
    ProductionStage,
    SalaryPayment,
    Shipment,
    RolePermission,
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

    permissions = [
        Permission(name='inventory.manage', description='Manage yarn stock and inventory movement'),
        Permission(name='production.manage', description='Manage knitting, dyeing, and production stages'),
        Permission(name='orders.manage', description='Manage buyers, orders, and shipments'),
        Permission(name='payroll.manage', description='Manage employees and salary payments'),
        Permission(name='reports.view', description='View finance and operational reports'),
    ]
    db.session.add_all(permissions)
    db.session.flush()

    role_permissions = [
        RolePermission(role_name='Manager', permission_id=permissions[0].id),
        RolePermission(role_name='Manager', permission_id=permissions[1].id),
        RolePermission(role_name='Manager', permission_id=permissions[2].id),
        RolePermission(role_name='Manager', permission_id=permissions[3].id),
        RolePermission(role_name='Manager', permission_id=permissions[4].id),
        RolePermission(role_name='Staff', permission_id=permissions[1].id),
        RolePermission(role_name='Staff', permission_id=permissions[4].id),
    ]
    db.session.add_all(role_permissions)

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
        Supplier(
            name='Khulna Knit Source',
            contact_person='Sabbir Hossain',
            phone='01511-678901',
            email='sabbir@khulnaknit.bd',
            address='Khalishpur, Khulna',
        ),
        Supplier(
            name='Rajshahi Yarn & Dye',
            contact_person='Mim Akter',
            phone='01411-789012',
            email='mim@rajshahiyarn.bd',
            address='Kazla, Rajshahi',
        ),
    ]
    db.session.add_all(suppliers)
    db.session.flush()

    buyers = [
        Buyer(name='Aarong', country='Bangladesh', contact_info='merch@aarong.com.bd'),
        Buyer(name='Yellow by Beximco', country='Bangladesh', contact_info='sourcing@yellow.com.bd'),
        Buyer(name='H&M', country='Sweden', contact_info='orders@hm.com'),
        Buyer(name='Zara', country='Spain', contact_info='bulk@zara.com'),
        Buyer(name='LC Waikiki', country='Turkey', contact_info='bd-sourcing@lcwaikiki.com'),
        Buyer(name='Primark', country='Ireland', contact_info='dhaka.buying@primark.com'),
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
        YarnPurchase(
            supplier_id=suppliers[1].id,
            yarn_type='Poly Cotton 24s',
            color='Bottle Green',
            qty_kg=1400,
            price_per_kg=3.80,
            status='Received',
        ),
        YarnPurchase(
            supplier_id=suppliers[4].id,
            yarn_type='Viscose 40s',
            color='Heather Grey',
            qty_kg=2600,
            price_per_kg=4.25,
            status='Received',
        ),
        YarnPurchase(
            supplier_id=suppliers[5].id,
            yarn_type='Fleece 20s',
            color='Deep Maroon',
            qty_kg=1950,
            price_per_kg=4.75,
            status='Received',
        ),
    ]
    db.session.add_all(yarn_purchases)
    db.session.flush()

    inventory_ledger = [
        InventoryLedger(
            yarn_purchase_id=yarn_purchases[0].id,
            movement_type='IN',
            qty_kg=5200,
            unit_cost=3.55,
            reference_type='YarnPurchase',
            reference_id=yarn_purchases[0].id,
            note='Incoming shipment from Dhaka Cotton Mills Ltd',
            created_by_id=admin.id,
        ),
        InventoryLedger(
            yarn_purchase_id=yarn_purchases[1].id,
            movement_type='IN',
            qty_kg=2400,
            unit_cost=2.90,
            reference_type='YarnPurchase',
            reference_id=yarn_purchases[1].id,
            note='Incoming shipment from Chattogram Yarn House',
            created_by_id=manager.id,
        ),
        InventoryLedger(
            yarn_purchase_id=yarn_purchases[2].id,
            movement_type='IN',
            qty_kg=3100,
            unit_cost=3.20,
            reference_type='YarnPurchase',
            reference_id=yarn_purchases[2].id,
            note='Incoming shipment from Narayanganj Fibres Ltd',
            created_by_id=manager.id,
        ),
        InventoryLedger(
            yarn_purchase_id=yarn_purchases[0].id,
            movement_type='OUT',
            qty_kg=3000,
            unit_cost=3.55,
            reference_type='KnittingJob',
            reference_id=1,
            note='Issued to Ruposhi Knitters Ltd',
            created_by_id=manager.id,
        ),
        InventoryLedger(
            yarn_purchase_id=yarn_purchases[1].id,
            movement_type='OUT',
            qty_kg=1600,
            unit_cost=2.90,
            reference_type='KnittingJob',
            reference_id=2,
            note='Issued to Shonar Bangla Knit House',
            created_by_id=manager.id,
        ),
        InventoryLedger(
            yarn_purchase_id=yarn_purchases[4].id,
            movement_type='IN',
            qty_kg=1400,
            unit_cost=3.80,
            reference_type='YarnPurchase',
            reference_id=yarn_purchases[4].id,
            note='Incoming shipment from Chattogram for export knitwear line',
            created_by_id=admin.id,
        ),
        InventoryLedger(
            yarn_purchase_id=yarn_purchases[5].id,
            movement_type='IN',
            qty_kg=2600,
            unit_cost=4.25,
            reference_type='YarnPurchase',
            reference_id=yarn_purchases[5].id,
            note='Incoming shipment from Khulna Knit Source',
            created_by_id=manager.id,
        ),
        InventoryLedger(
            yarn_purchase_id=yarn_purchases[6].id,
            movement_type='IN',
            qty_kg=1950,
            unit_cost=4.75,
            reference_type='YarnPurchase',
            reference_id=yarn_purchases[6].id,
            note='Incoming shipment from Rajshahi Yarn & Dye',
            created_by_id=admin.id,
        ),
    ]
    db.session.add_all(inventory_ledger)

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
        KnittingJob(
            yarn_purchase_id=yarn_purchases[5].id,
            company_name='Shylet Composite Knit',
            sent_qty_kg=1450,
            received_fabric_kg=0,
            waste_kg=0,
            status='In Progress',
        ),
        KnittingJob(
            yarn_purchase_id=yarn_purchases[6].id,
            company_name='Comilla Apparel Works',
            sent_qty_kg=1100,
            received_fabric_kg=1030,
            waste_kg=70,
            status='Completed',
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
        DyeingJob(
            knitting_job_id=knitting_jobs[4].id,
            dyeing_unit_name='Sunamganj Color Lab',
            color_specification='Heather Grey',
            input_qty=1320,
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
            sale_price_per_unit=18.50,
            estimated_yarn_cost=16800,
            estimated_dyeing_cost=4200,
            estimated_labor_cost=9800,
            estimated_shipping_cost=1500,
            invoice_number='BD-INV-2026-0001',
        ),
        Order(
            buyer_id=buyers[1].id,
            product_name='Summer Polo - Local Retail Drop',
            total_qty=8500,
            deadline=days_from_now(10),
            status='Active',
            sale_price_per_unit=16.75,
            estimated_yarn_cost=11800,
            estimated_dyeing_cost=3600,
            estimated_labor_cost=7200,
            estimated_shipping_cost=1200,
            invoice_number='BD-INV-2026-0002',
        ),
        Order(
            buyer_id=buyers[2].id,
            product_name='Ladies Top - Export Batch',
            total_qty=6400,
            deadline=days_from_now(18),
            status='Completed',
            sale_price_per_unit=21.00,
            estimated_yarn_cost=8900,
            estimated_dyeing_cost=2900,
            estimated_labor_cost=6400,
            estimated_shipping_cost=1400,
            invoice_number='BD-INV-2026-0003',
        ),
        Order(
            buyer_id=buyers[3].id,
            product_name='Kids Jogger Pant - Winter Line',
            total_qty=5000,
            deadline=days_from_now(25),
            status='Shipped',
            sale_price_per_unit=19.25,
            estimated_yarn_cost=7200,
            estimated_dyeing_cost=2400,
            estimated_labor_cost=5100,
            estimated_shipping_cost=1000,
            invoice_number='BD-INV-2026-0004',
        ),
        Order(
            buyer_id=buyers[0].id,
            product_name='Prayer Cap Jersey Pack - Ramadan Line',
            total_qty=7200,
            deadline=days_from_now(5),
            status='Active',
            sale_price_per_unit=14.90,
            estimated_yarn_cost=8600,
            estimated_dyeing_cost=1800,
            estimated_labor_cost=5400,
            estimated_shipping_cost=900,
            invoice_number='BD-INV-2026-0005',
        ),
        Order(
            buyer_id=buyers[4].id,
            product_name='Women Active Tee - Dhaka Premium',
            total_qty=9100,
            deadline=days_from_now(12),
            status='Active',
            sale_price_per_unit=17.80,
            estimated_yarn_cost=12400,
            estimated_dyeing_cost=3900,
            estimated_labor_cost=8600,
            estimated_shipping_cost=1100,
            invoice_number='BD-INV-2026-0006',
        ),
        Order(
            buyer_id=buyers[5].id,
            product_name='Kids School Polo - Midyear Run',
            total_qty=5600,
            deadline=days_from_now(8),
            status='Active',
            sale_price_per_unit=15.40,
            estimated_yarn_cost=7300,
            estimated_dyeing_cost=2500,
            estimated_labor_cost=5400,
            estimated_shipping_cost=850,
            invoice_number='BD-INV-2026-0007',
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
        ProductionStage(
            order_id=orders[4].id,
            stage_name='Cutting',
            input_qty=7200,
            output_qty=7110,
            waste=90,
            status='Completed',
        ),
        ProductionStage(
            order_id=orders[4].id,
            stage_name='Sewing',
            input_qty=7110,
            output_qty=6945,
            waste=165,
            status='In Progress',
        ),
        ProductionStage(
            order_id=orders[5].id,
            stage_name='Cutting',
            input_qty=9100,
            output_qty=9010,
            waste=90,
            status='Completed',
        ),
        ProductionStage(
            order_id=orders[6].id,
            stage_name='Cutting',
            input_qty=5600,
            output_qty=5520,
            waste=80,
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
        Shipment(
            order_id=orders[4].id,
            container_no='BDU-240522-C',
            shipping_date=days_from_now(1),
            final_qty=0,
            status='Pending',
        ),
        Shipment(
            order_id=orders[5].id,
            container_no='BDU-240523-D',
            shipping_date=days_from_now(2),
            final_qty=0,
            status='Pending',
        ),
        Shipment(
            order_id=orders[6].id,
            container_no='BDU-240523-E',
            shipping_date=days_from_now(3),
            final_qty=0,
            status='Pending',
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
            paid_amount=10000,
            paid_by_id=admin.id,
            note='Advance payment',
        ),
        SalaryPayment(
            employee_id=employees[1].id,
            payment_month=current_month,
            paid_amount=9000,
            paid_by_id=manager.id,
            note='Partial payment',
        ),
        SalaryPayment(
            employee_id=employees[2].id,
            payment_month=current_month,
            paid_amount=8000,
            paid_by_id=manager.id,
            note='Partial payment',
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
        SalaryPayment(
            employee_id=employees[4].id,
            payment_month=current_month,
            paid_amount=12000,
            paid_by_id=admin.id,
            note='Partial payment',
        ),
        SalaryPayment(
            employee_id=employees[1].id,
            payment_month=prev_month,
            paid_amount=24000,
            paid_by_id=manager.id,
            note='Previous month full payment',
        ),
        SalaryPayment(
            employee_id=employees[2].id,
            payment_month=prev_month,
            paid_amount=22000,
            paid_by_id=admin.id,
            note='Previous month full payment',
        ),
    ]
    db.session.add_all(salary_payments)

    audit_logs = [
        AuditLog(
            action='seed',
            entity_type='Database',
            entity_id=1,
            note='Bangladesh-vibed demo dataset loaded',
            user_id=admin.id,
            ip_address='127.0.0.1',
        ),
        AuditLog(
            action='create',
            entity_type='Order',
            entity_id=orders[4].id,
            note='Demo Ramadan line order created',
            user_id=manager.id,
            ip_address='127.0.0.1',
        ),
        AuditLog(
            action='create',
            entity_type='Order',
            entity_id=orders[5].id,
            note='Demo Dhaka premium line order created',
            user_id=manager.id,
            ip_address='127.0.0.1',
        ),
    ]
    db.session.add_all(audit_logs)

    db.session.commit()

    print('Database seeded with Bangladesh-style demo data. Login: admin/admin123, manager/manager123, staff/staff123')
