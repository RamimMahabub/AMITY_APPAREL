from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from app import db
from app.models import DyeingJob, InventoryLedger, KnittingJob, Order, ProductionStage, YarnPurchase
from app.production.forms import KnittingJobForm, UpdateKnittingJobForm, DyeingJobForm, UpdateDyeingJobForm, ProductionStageForm, UpdateProductionStageForm
from app.auth.routes import role_required
from app.services import calculate_waste_percentage, get_purchase_available_qty, log_audit, record_inventory_out

production = Blueprint('production', __name__)

@production.route('/knitting', methods=['GET'])
@login_required
def knitting_list():
    jobs = KnittingJob.query.order_by(KnittingJob.id.desc()).all()
    return render_template('production/knitting_list.html', jobs=jobs)

@production.route('/knitting/new', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager'])
def knitting_new():
    form = KnittingJobForm()
    yarns = YarnPurchase.query.filter(YarnPurchase.status.in_(['Received', 'Assigned'])).all()
    form.yarn_purchase_id.choices = [
        (yarn.id, f"{yarn.yarn_type} ({yarn.color}) - {float(get_purchase_available_qty(yarn)):.2f}kg available")
        for yarn in yarns
        if get_purchase_available_qty(yarn) > 0
    ]
    
    if form.validate_on_submit():
        yarn = YarnPurchase.query.get_or_404(form.yarn_purchase_id.data)
        available_qty = get_purchase_available_qty(yarn)
        if form.sent_qty_kg.data > available_qty:
            flash(f'Insufficient yarn stock. Only {available_qty:.2f} kg is available.', 'danger')
            return render_template('production/form.html', form=form, title="New Knitting Job", back_url=url_for('production.knitting_list'))

        job = KnittingJob(
            yarn_purchase_id=form.yarn_purchase_id.data,
            company_name=form.company_name.data,
            sent_qty_kg=form.sent_qty_kg.data,
        )
        db.session.add(job)
        db.session.flush()
        db.session.add(record_inventory_out(yarn, form.sent_qty_kg.data, reference_type='KnittingJob', reference_id=job.id, user=current_user, note='Yarn issued to knitting job'))
        yarn.status = 'Assigned'
        log_audit('create', 'KnittingJob', job.id, user=current_user, after_data={'yarn_purchase_id': yarn.id, 'sent_qty_kg': float(form.sent_qty_kg.data), 'company_name': form.company_name.data}, note='Knitting job created')
        db.session.commit()
        flash('Knitting job created.', 'success')
        return redirect(url_for('production.knitting_list'))
    return render_template('production/form.html', form=form, title="New Knitting Job", back_url=url_for('production.knitting_list'))

@production.route('/knitting/<int:job_id>/update', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager', 'Staff'])
def knitting_update(job_id):
    job = KnittingJob.query.get_or_404(job_id)
    form = UpdateKnittingJobForm(obj=job)
    if form.validate_on_submit():
        before_data = {
            'received_fabric_kg': float(job.received_fabric_kg or 0),
            'waste_kg': float(job.waste_kg or 0),
            'status': job.status,
        }
        job.received_fabric_kg = form.received_fabric_kg.data
        job.waste_kg = form.waste_kg.data
        job.status = form.status.data
        log_audit('update', 'KnittingJob', job.id, user=current_user, before_data=before_data, after_data={'received_fabric_kg': float(job.received_fabric_kg), 'waste_kg': float(job.waste_kg), 'status': job.status, 'waste_percentage': float(calculate_waste_percentage(job.sent_qty_kg, job.waste_kg))}, note='Knitting job updated')
        db.session.commit()
        flash('Knitting job updated.', 'success')
        return redirect(url_for('production.knitting_list'))
    return render_template('production/form.html', form=form, title=f"Update Knitting Batch #{job.id}", back_url=url_for('production.knitting_list'))

@production.route('/dyeing', methods=['GET'])
@login_required
def dyeing_list():
    jobs = DyeingJob.query.order_by(DyeingJob.id.desc()).all()
    return render_template('production/dyeing_list.html', jobs=jobs)

@production.route('/dyeing/new', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager'])
def dyeing_new():
    form = DyeingJobForm()
    completed_knitting = KnittingJob.query.filter_by(status='Completed').all()
    form.knitting_job_id.choices = [(k.id, f"Batch {k.id} - {k.received_fabric_kg}kg") for k in completed_knitting]
    
    if form.validate_on_submit():
        knitting_job = KnittingJob.query.get_or_404(form.knitting_job_id.data)
        if knitting_job.status != 'Completed':
            flash('Only completed knitting batches can be sent to dyeing.', 'danger')
            return render_template('production/form.html', form=form, title="New Dyeing Job", back_url=url_for('production.dyeing_list'))

        job = DyeingJob(
            knitting_job_id=form.knitting_job_id.data,
            dyeing_unit_name=form.dyeing_unit_name.data,
            color_specification=form.color_specification.data,
            input_qty=form.input_qty.data
        )
        db.session.add(job)
        db.session.flush()
        log_audit('create', 'DyeingJob', job.id, user=current_user, after_data={'knitting_job_id': job.knitting_job_id, 'input_qty': float(job.input_qty), 'color_specification': job.color_specification}, note='Dyeing job created')
        db.session.commit()
        flash('Dyeing job created.', 'success')
        return redirect(url_for('production.dyeing_list'))
    return render_template('production/form.html', form=form, title="New Dyeing Job", back_url=url_for('production.dyeing_list'))

@production.route('/dyeing/<int:job_id>/update', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager', 'Staff'])
def dyeing_update(job_id):
    job = DyeingJob.query.get_or_404(job_id)
    form = UpdateDyeingJobForm(obj=job)
    if form.validate_on_submit():
        before_data = {'output_qty': float(job.output_qty or 0), 'status': job.status}
        job.output_qty = form.output_qty.data
        job.status = form.status.data
        log_audit('update', 'DyeingJob', job.id, user=current_user, before_data=before_data, after_data={'output_qty': float(job.output_qty), 'status': job.status}, note='Dyeing job updated')
        db.session.commit()
        flash('Dyeing job updated.', 'success')
        return redirect(url_for('production.dyeing_list'))
    return render_template('production/form.html', form=form, title=f"Update Dyeing Batch #{job.id}", back_url=url_for('production.dyeing_list'))

@production.route('/stages', methods=['GET'])
@login_required
def stage_list():
    stages = ProductionStage.query.order_by(ProductionStage.id.desc()).all()
    return render_template('production/stage_list.html', stages=stages)

@production.route('/stages/new', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager'])
def stage_new():
    form = ProductionStageForm()
    orders = Order.query.filter_by(status='Active').all()
    form.order_id.choices = [(o.id, f"Order #{o.id} - {o.product_name}") for o in orders]
    
    if form.validate_on_submit():
        order = Order.query.get_or_404(form.order_id.data)
        stage = ProductionStage(
            order_id=form.order_id.data,
            stage_name=form.stage_name.data,
            input_qty=form.input_qty.data
        )
        db.session.add(stage)
        db.session.flush()
        log_audit('create', 'ProductionStage', stage.id, user=current_user, after_data={'order_id': order.id, 'stage_name': stage.stage_name, 'input_qty': stage.input_qty}, note='Production stage started')
        db.session.commit()
        flash('Production stage started.', 'success')
        return redirect(url_for('production.stage_list'))
    return render_template('production/form.html', form=form, title="New Production Stage", back_url=url_for('production.stage_list'))

@production.route('/stages/<int:stage_id>/update', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager', 'Staff'])
def stage_update(stage_id):
    stage = ProductionStage.query.get_or_404(stage_id)
    form = UpdateProductionStageForm(obj=stage)
    if form.validate_on_submit():
        before_data = {'stage_name': stage.stage_name, 'input_qty': stage.input_qty, 'output_qty': stage.output_qty, 'waste': stage.waste, 'status': stage.status}
        stage.stage_name = form.stage_name.data
        stage.input_qty = form.input_qty.data
        stage.output_qty = form.output_qty.data
        stage.waste = form.waste.data
        stage.status = form.status.data
        if stage.status == 'Completed' and all(existing_stage.status == 'Completed' for existing_stage in stage.order.production_stages):
            stage.order.status = 'Completed'
        log_audit('update', 'ProductionStage', stage.id, user=current_user, before_data=before_data, after_data={'stage_name': stage.stage_name, 'input_qty': stage.input_qty, 'output_qty': stage.output_qty, 'waste': stage.waste, 'status': stage.status}, note='Production stage updated')
        db.session.commit()
        flash('Production stage updated.', 'success')
        return redirect(url_for('production.stage_list'))
    return render_template('production/form.html', form=form, title=f"Update Stage #{stage.id}", back_url=url_for('production.stage_list'))
