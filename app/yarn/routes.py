from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import YarnPurchase, Supplier
from app.yarn.forms import YarnPurchaseForm
from app.auth.routes import role_required

yarn = Blueprint('yarn', __name__)

@yarn.route('/inventory', methods=['GET'])
@login_required
def inventory():
    purchases = YarnPurchase.query.order_by(YarnPurchase.created_at.desc()).all()
    return render_template('yarn/inventory.html', purchases=purchases)

@yarn.route('/purchase', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager'])
def purchase():
    form = YarnPurchaseForm()
    form.supplier_id.choices = [(s.id, s.name) for s in Supplier.query.all()]
    if form.validate_on_submit():
        purchase = YarnPurchase(
            supplier_id=form.supplier_id.data,
            yarn_type=form.yarn_type.data,
            color=form.color.data,
            qty_kg=form.qty_kg.data,
            price_per_kg=form.price_per_kg.data,
            status='Received'
        )
        db.session.add(purchase)
        db.session.commit()
        flash('Yarn purchase recorded successfully!', 'success')
        return redirect(url_for('yarn.inventory'))
    return render_template('production/form.html', form=form, title='Record Yarn Purchase', back_url=url_for('yarn.inventory'))
