import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required
from app import db
from app.models import Buyer, Order, Shipment
from app.orders.forms import BuyerForm, OrderForm, ShipmentForm
from app.auth.routes import role_required
from sqlalchemy import func

orders = Blueprint('orders', __name__)

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
    for o in orders_data:
        shipped_val = db.session.query(func.sum(Shipment.final_qty)).filter(Shipment.order_id == o.id).scalar()
        shipped_qty = int(shipped_val) if shipped_val else 0
        progress_data[o.id] = min(round((shipped_qty / o.total_qty * 100), 2), 100) if o.total_qty > 0 else 0
    from datetime import datetime
    return render_template('orders/order_list.html', orders=orders_data, progress_data=progress_data, current_time=datetime.utcnow())

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
        db.session.commit()
        flash('Order created.', 'success')
        return redirect(url_for('orders.order_list'))
    return render_template('production/form.html', form=form, title="New Order", back_url=url_for('orders.order_list'), has_file=True)

@orders.route('/shipments', methods=['GET'])
@login_required
def shipment_list():
    shipments = Shipment.query.all()
    return render_template('orders/shipment_list.html', shipments=shipments)

@orders.route('/shipments/new', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager'])
def shipment_new():
    form = ShipmentForm()
    active_orders = Order.query.filter(Order.status != 'Shipped').all()
    form.order_id.choices = [(o.id, f"Order #{o.id} - {o.product_name} (Qty: {o.total_qty})") for o in active_orders]
    
    if form.validate_on_submit():
        shipment = Shipment(
            order_id=form.order_id.data,
            container_no=form.container_no.data,
            final_qty=form.final_qty.data,
            shipping_date=form.shipping_date.data,
            status='Shipped'
        )
        
        order = Order.query.get(form.order_id.data)
        shipped_val = db.session.query(func.sum(Shipment.final_qty)).filter(Shipment.order_id == order.id).scalar()
        prev_shipped = int(shipped_val) if shipped_val else 0
        if prev_shipped + form.final_qty.data >= order.total_qty:
            order.status = 'Shipped'
        
        db.session.add(shipment)
        db.session.commit()
        flash('Shipment recorded.', 'success')
        return redirect(url_for('orders.shipment_list'))
    return render_template('production/form.html', form=form, title="New Shipment", back_url=url_for('orders.shipment_list'))
