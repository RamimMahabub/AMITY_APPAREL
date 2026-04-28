from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app import db
from app.models import InventoryLedger, Supplier, YarnPurchase
from app.yarn.forms import YarnPurchaseForm
from app.auth.routes import role_required
from decimal import Decimal, InvalidOperation
from app.services import get_low_stock_purchases, get_total_yarn_stock, log_audit, record_inventory_in

yarn = Blueprint('yarn', __name__)

@yarn.route('/inventory', methods=['GET'])
@login_required
def inventory():
    purchases = YarnPurchase.query.order_by(YarnPurchase.created_at.desc()).all()
    low_stock_alerts = get_low_stock_purchases()
    total_yarn_stock = get_total_yarn_stock()
    return render_template('yarn/inventory.html', purchases=purchases, low_stock_alerts=low_stock_alerts, total_yarn_stock=total_yarn_stock)


@yarn.route('/supplier/create', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def create_supplier():
    name = (request.form.get('name') or '').strip()
    if not name:
        return jsonify({'ok': False, 'message': 'Supplier name is required.'}), 400

    contact_person = (request.form.get('contact_person') or '').strip()
    phone = (request.form.get('phone') or '').strip()
    email = (request.form.get('email') or '').strip()
    address = (request.form.get('address') or '').strip()

    supplier = Supplier.query.filter_by(name=name).first()
    if supplier is None:
        supplier = Supplier(
            name=name,
            contact_person=contact_person or None,
            phone=phone or None,
            email=email or None,
            address=address or None,
        )
        db.session.add(supplier)
    else:
        if contact_person:
            supplier.contact_person = contact_person
        if phone:
            supplier.phone = phone
        if email:
            supplier.email = email
        if address:
            supplier.address = address

    db.session.commit()
    return jsonify({'ok': True, 'id': supplier.id, 'name': supplier.name})


@yarn.route('/companies', methods=['GET'])
@login_required
@role_required(['Admin', 'Manager'])
def supplier_list():
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()
    return render_template('yarn/supplier_list.html', suppliers=suppliers)

@yarn.route('/purchase', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager'])
def purchase():
    form = YarnPurchaseForm()
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()
    form.supplier_id.choices = [(0, '-- Select Existing Supplier --')] + [(s.id, s.name) for s in suppliers]
    form.status.data = 'Received'
    if form.validate_on_submit():
        new_supplier_name = (form.new_supplier_name.data or '').strip()
        supplier_id = form.supplier_id.data
        contact_person = (form.supplier_contact_person.data or '').strip()
        phone = (form.supplier_phone.data or '').strip()
        email = (form.supplier_email.data or '').strip()
        address = (form.supplier_address.data or '').strip()

        if new_supplier_name:
            supplier = Supplier.query.filter_by(name=new_supplier_name).first()
            if supplier is None:
                supplier = Supplier(
                    name=new_supplier_name,
                    contact_person=contact_person or None,
                    phone=phone or None,
                    email=email or None,
                    address=address or None,
                )
                db.session.add(supplier)
                db.session.flush()
            else:
                # Keep existing values, but accept overrides when user provides new info.
                if contact_person:
                    supplier.contact_person = contact_person
                if phone:
                    supplier.phone = phone
                if email:
                    supplier.email = email
                if address:
                    supplier.address = address
            supplier_id = supplier.id

        if not supplier_id:
            flash('Please select an existing supplier or enter a new supplier name.', 'danger')
            return render_template('yarn/purchase.html', form=form, title='Record Yarn Purchase', back_url=url_for('yarn.inventory'))

        items = [
            {
                'yarn_type': form.yarn_type.data.strip(),
                'color': form.color.data.strip(),
                'qty_kg': form.qty_kg.data,
                'price_per_kg': form.price_per_kg.data,
            }
        ]

        extra_types = [v.strip() for v in request.form.getlist('extra_yarn_type[]')]
        extra_colors = [v.strip() for v in request.form.getlist('extra_color[]')]
        extra_qtys = [v.strip() for v in request.form.getlist('extra_qty_kg[]')]
        extra_prices = [v.strip() for v in request.form.getlist('extra_price_per_kg[]')]

        extra_count = max(len(extra_types), len(extra_colors), len(extra_qtys), len(extra_prices))
        for idx in range(extra_count):
            yarn_type = extra_types[idx] if idx < len(extra_types) else ''
            color = extra_colors[idx] if idx < len(extra_colors) else ''
            qty_raw = extra_qtys[idx] if idx < len(extra_qtys) else ''
            price_raw = extra_prices[idx] if idx < len(extra_prices) else ''

            if not any([yarn_type, color, qty_raw, price_raw]):
                continue

            if not all([yarn_type, color, qty_raw, price_raw]):
                flash(f'Yarn item #{idx + 2} is incomplete. Fill all fields or remove that row.', 'danger')
                return render_template('yarn/purchase.html', form=form, title='Record Yarn Purchase', back_url=url_for('yarn.inventory'))

            try:
                qty_kg = Decimal(qty_raw)
                price_per_kg = Decimal(price_raw)
            except InvalidOperation:
                flash(f'Yarn item #{idx + 2} has invalid quantity or price.', 'danger')
                return render_template('yarn/purchase.html', form=form, title='Record Yarn Purchase', back_url=url_for('yarn.inventory'))

            if qty_kg <= 0 or price_per_kg <= 0:
                flash(f'Yarn item #{idx + 2} must have quantity and price greater than 0.', 'danger')
                return render_template('yarn/purchase.html', form=form, title='Record Yarn Purchase', back_url=url_for('yarn.inventory'))

            items.append(
                {
                    'yarn_type': yarn_type,
                    'color': color,
                    'qty_kg': qty_kg,
                    'price_per_kg': price_per_kg,
                }
            )

        for item in items:
            purchase = YarnPurchase(
                supplier_id=supplier_id,
                yarn_type=item['yarn_type'],
                color=item['color'],
                qty_kg=item['qty_kg'],
                price_per_kg=item['price_per_kg'],
                status='Received',
            )
            db.session.add(purchase)
            db.session.flush()
            db.session.add(record_inventory_in(purchase, user=current_user, note='Yarn purchase received into stock'))
            log_audit(
                'create',
                'YarnPurchase',
                purchase.id,
                user=current_user,
                after_data={'qty_kg': float(item['qty_kg']), 'price_per_kg': float(item['price_per_kg'])},
                note='Yarn purchase recorded',
            )

        db.session.commit()
        flash(f'{len(items)} yarn item(s) recorded successfully!', 'success')
        return redirect(url_for('yarn.inventory'))
    return render_template('yarn/purchase.html', form=form, title='Record Yarn Purchase', back_url=url_for('yarn.inventory'))


@yarn.route('/receipt/<int:purchase_id>', methods=['GET'])
@login_required
def receipt(purchase_id):
    purchase = YarnPurchase.query.get_or_404(purchase_id)
    return render_template('yarn/receipt.html', purchase=purchase)


@yarn.route('/purchase/<int:purchase_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager'])
def edit_purchase(purchase_id):
    purchase = YarnPurchase.query.get_or_404(purchase_id)
    form = YarnPurchaseForm(obj=purchase)
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()
    form.supplier_id.choices = [(0, '-- Select Existing Supplier --')] + [(s.id, s.name) for s in suppliers]
    form.status.choices = [('Received', 'Received'), ('Assigned', 'Assigned')]
    form.supplier_id.data = purchase.supplier_id
    form.status.data = purchase.status

    if form.validate_on_submit():
        original_data = {
            'supplier_id': purchase.supplier_id,
            'yarn_type': purchase.yarn_type,
            'color': purchase.color,
            'qty_kg': float(purchase.qty_kg),
            'price_per_kg': float(purchase.price_per_kg),
            'status': purchase.status,
        }
        initial_inventory = InventoryLedger.query.filter_by(
            yarn_purchase_id=purchase.id,
            movement_type='IN',
            reference_type='YarnPurchase',
            reference_id=purchase.id,
        ).first()
        has_outgoing = InventoryLedger.query.filter_by(yarn_purchase_id=purchase.id, movement_type='OUT').first() is not None
        new_supplier_name = (form.new_supplier_name.data or '').strip()
        supplier_id = form.supplier_id.data
        contact_person = (form.supplier_contact_person.data or '').strip()
        phone = (form.supplier_phone.data or '').strip()
        email = (form.supplier_email.data or '').strip()
        address = (form.supplier_address.data or '').strip()

        if new_supplier_name:
            supplier = Supplier.query.filter_by(name=new_supplier_name).first()
            if supplier is None:
                supplier = Supplier(
                    name=new_supplier_name,
                    contact_person=contact_person or None,
                    phone=phone or None,
                    email=email or None,
                    address=address or None,
                )
                db.session.add(supplier)
                db.session.flush()
            else:
                if contact_person:
                    supplier.contact_person = contact_person
                if phone:
                    supplier.phone = phone
                if email:
                    supplier.email = email
                if address:
                    supplier.address = address
            supplier_id = supplier.id

        if not supplier_id:
            flash('Please select an existing supplier or enter a new supplier name.', 'danger')
            return render_template('yarn/edit_purchase.html', form=form, purchase=purchase, back_url=url_for('yarn.inventory'))

        if has_outgoing and form.qty_kg.data != purchase.qty_kg:
            flash('Quantity cannot be changed after yarn has been allocated to production.', 'danger')
            return render_template('yarn/edit_purchase.html', form=form, purchase=purchase, back_url=url_for('yarn.inventory'))

        purchase.supplier_id = supplier_id
        purchase.yarn_type = form.yarn_type.data.strip()
        purchase.color = form.color.data.strip()
        purchase.qty_kg = form.qty_kg.data
        purchase.price_per_kg = form.price_per_kg.data
        purchase.status = form.status.data or purchase.status

        if initial_inventory is not None and not has_outgoing:
            initial_inventory.qty_kg = purchase.qty_kg
            initial_inventory.unit_cost = purchase.price_per_kg

        log_audit(
            'update',
            'YarnPurchase',
            purchase.id,
            user=current_user,
            before_data=original_data,
            after_data={
                'supplier_id': purchase.supplier_id,
                'yarn_type': purchase.yarn_type,
                'color': purchase.color,
                'qty_kg': float(purchase.qty_kg),
                'price_per_kg': float(purchase.price_per_kg),
                'status': purchase.status,
            },
            note='Yarn purchase updated',
        )

        db.session.commit()
        flash('Yarn purchase updated successfully!', 'success')
        return redirect(url_for('yarn.inventory'))

    return render_template('yarn/edit_purchase.html', form=form, purchase=purchase, back_url=url_for('yarn.inventory'))
