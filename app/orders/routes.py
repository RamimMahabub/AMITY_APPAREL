import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import current_user, login_required
from app import db
from app.models import Buyer, Order, Shipment
from app.orders.forms import BuyerForm, OrderForm, ShipmentForm, UpdateShipmentForm
from app.auth.routes import role_required
from sqlalchemy import func
from app.services import calculate_order_financials, calculate_shipment_progress, log_audit

orders = Blueprint('orders', __name__)


def _sync_order_shipment_status(order: Order):
    shipped_total = db.session.query(func.coalesce(func.sum(Shipment.final_qty), 0)).filter(Shipment.order_id == order.id).scalar() or 0
    if shipped_total >= order.total_qty:
        order.status = 'Shipped'
    elif order.production_stages and all(stage.status == 'Completed' for stage in order.production_stages):
        order.status = 'Completed'
    else:
        order.status = 'Active'

@orders.route('/buyers', methods=['GET'])
@login_required
def buyer_list():
    buyers = Buyer.query.all()
    return render_template('orders/buyer_list.html', buyers=buyers)

@orders.route('/buyers/new', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager'])
def buyer_new():
    form = BuyerForm()
    if form.validate_on_submit():
        buyer = Buyer(
            name=form.name.data,
            country=form.country.data,
            contact_info=form.contact_info.data
        )
        db.session.add(buyer)
        db.session.commit()
        flash('Buyer added successfully.', 'success')
        return redirect(url_for('orders.buyer_list'))
    return render_template('production/form.html', form=form, title="New Buyer", back_url=url_for('orders.buyer_list'))

@orders.route('/list', methods=['GET'])
@login_required
def order_list():
    orders_data = Order.query.order_by(Order.deadline.asc()).all()
    progress_data = {}
    finance_data = {}
    for o in orders_data:
        progress_data[o.id] = float(calculate_shipment_progress(o))
        finance_data[o.id] = calculate_order_financials(o)
    from datetime import datetime
    return render_template('orders/order_list.html', orders=orders_data, progress_data=progress_data, finance_data=finance_data, current_time=datetime.utcnow())

@orders.route('/new', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager'])
def order_new():
    form = OrderForm()
    form.buyer_id.choices = [(b.id, b.name) for b in Buyer.query.all()]
    if form.validate_on_submit():
        filename = None
        if form.design_image.data:
            f = form.design_image.data
            filename = secure_filename(f.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            f.save(upload_path)
            
        order = Order(
            buyer_id=form.buyer_id.data,
            product_name=form.product_name.data,
            total_qty=form.total_qty.data,
            deadline=form.deadline.data,
            design_image=filename
        )
        db.session.add(order)
        db.session.flush()
        log_audit('create', 'Order', order.id, user=current_user, after_data={'buyer_id': order.buyer_id, 'product_name': order.product_name, 'total_qty': order.total_qty, 'deadline': order.deadline.isoformat() if order.deadline else None}, note='Order created')
        db.session.commit()
        flash('Order created.', 'success')
        return redirect(url_for('orders.order_list'))
    return render_template('production/form.html', form=form, title="New Order", back_url=url_for('orders.order_list'), has_file=True)

@orders.route('/shipments', methods=['GET'])
@login_required
def shipment_list():
    shipments = Shipment.query.order_by(Shipment.id.desc()).all()
    progress_data = {}
    for shipment in shipments:
        progress_data[shipment.id] = float(calculate_shipment_progress(shipment.order))
    return render_template('orders/shipment_list.html', shipments=shipments, progress_data=progress_data)

@orders.route('/shipments/new', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager'])
def shipment_new():
    form = ShipmentForm()
    active_orders = Order.query.filter(Order.status != 'Shipped').all()
    form.order_id.choices = [(o.id, f"Order #{o.id} - {o.product_name} (Qty: {o.total_qty})") for o in active_orders]
    
    if form.validate_on_submit():
        order = Order.query.get_or_404(form.order_id.data)
        shipped_val = db.session.query(func.sum(Shipment.final_qty)).filter(Shipment.order_id == order.id).scalar()
        prev_shipped = int(shipped_val) if shipped_val else 0
        remaining_qty = max(order.total_qty - prev_shipped, 0)
        if form.final_qty.data > remaining_qty:
            flash(f'Shipment quantity exceeds the remaining order balance of {remaining_qty} pcs.', 'danger')
            return render_template('production/form.html', form=form, title="New Shipment", back_url=url_for('orders.shipment_list'))

        shipment = Shipment(
            order_id=form.order_id.data,
            container_no=form.container_no.data,
            final_qty=form.final_qty.data,
            shipping_date=form.shipping_date.data,
            status='Shipped'
        )
        
        db.session.add(shipment)
        db.session.flush()
        _sync_order_shipment_status(order)

        log_audit('create', 'Shipment', shipment.id, user=current_user, after_data={'order_id': order.id, 'container_no': shipment.container_no, 'final_qty': shipment.final_qty, 'status': shipment.status}, note='Shipment recorded')
        db.session.commit()
        flash('Shipment recorded.', 'success')
        return redirect(url_for('orders.shipment_list'))
    return render_template('production/form.html', form=form, title="New Shipment", back_url=url_for('orders.shipment_list'))


@orders.route('/shipments/<int:shipment_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager'])
def shipment_edit(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)
    form = UpdateShipmentForm(obj=shipment)
    active_orders = Order.query.filter(Order.status != 'Shipped').all()
    current_order = Order.query.get(shipment.order_id)
    order_choices = [(o.id, f"Order #{o.id} - {o.product_name} (Qty: {o.total_qty})") for o in active_orders]
    if current_order and all(choice_id != current_order.id for choice_id, _ in order_choices):
        order_choices.insert(0, (current_order.id, f"Order #{current_order.id} - {current_order.product_name} (Qty: {current_order.total_qty})"))
    form.order_id.choices = order_choices
    form.order_id.data = shipment.order_id
    form.status.data = shipment.status

    if form.validate_on_submit():
        previous_order = Order.query.get_or_404(shipment.order_id)
        order = Order.query.get_or_404(form.order_id.data)
        other_shipped = (
            db.session.query(func.coalesce(func.sum(Shipment.final_qty), 0))
            .filter(Shipment.order_id == order.id, Shipment.id != shipment.id)
            .scalar()
            or 0
        )
        if form.final_qty.data + other_shipped > order.total_qty:
            flash(f'Shipment quantity exceeds the remaining order balance of {order.total_qty - other_shipped} pcs.', 'danger')
            return render_template('production/form.html', form=form, title=f'Update Shipment #{shipment.id}', back_url=url_for('orders.shipment_list'))

        before_data = {
            'order_id': shipment.order_id,
            'container_no': shipment.container_no,
            'final_qty': shipment.final_qty,
            'shipping_date': shipment.shipping_date.isoformat() if shipment.shipping_date else None,
            'status': shipment.status,
        }
        shipment.order_id = form.order_id.data
        shipment.container_no = form.container_no.data
        shipment.final_qty = form.final_qty.data
        shipment.shipping_date = form.shipping_date.data
        shipment.status = form.status.data
        _sync_order_shipment_status(order)
        if previous_order.id != order.id:
            _sync_order_shipment_status(previous_order)
        log_audit('update', 'Shipment', shipment.id, user=current_user, before_data=before_data, after_data={'order_id': shipment.order_id, 'container_no': shipment.container_no, 'final_qty': shipment.final_qty, 'shipping_date': shipment.shipping_date.isoformat() if shipment.shipping_date else None, 'status': shipment.status}, note='Shipment updated')
        db.session.commit()
        flash('Shipment updated successfully.', 'success')
        return redirect(url_for('orders.shipment_list'))

    return render_template('production/form.html', form=form, title=f'Update Shipment #{shipment.id}', back_url=url_for('orders.shipment_list'))
