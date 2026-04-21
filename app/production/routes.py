from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import KnittingJob, DyeingJob, ProductionStage, YarnPurchase, Order
from app.production.forms import KnittingJobForm, UpdateKnittingJobForm, DyeingJobForm, UpdateDyeingJobForm, ProductionStageForm, UpdateProductionStageForm
from app.auth.routes import role_required

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
    yarns = YarnPurchase.query.filter_by(status='Received').all()
    form.yarn_purchase_id.choices = [(y.id, f"{y.yarn_type} ({y.color}) - {y.qty_kg}kg") for y in yarns]
    
    if form.validate_on_submit():
        job = KnittingJob(
            yarn_purchase_id=form.yarn_purchase_id.data,
            company_name=form.company_name.data,
            sent_qty_kg=form.sent_qty_kg.data,
        )
        yarn = YarnPurchase.query.get(form.yarn_purchase_id.data)
        yarn.status = 'Assigned'
        db.session.add(job)
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
        job.received_fabric_kg = form.received_fabric_kg.data
        job.waste_kg = form.waste_kg.data
        job.status = form.status.data
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
        job = DyeingJob(
            knitting_job_id=form.knitting_job_id.data,
            dyeing_unit_name=form.dyeing_unit_name.data,
            color_specification=form.color_specification.data,
            input_qty=form.input_qty.data
        )
        db.session.add(job)
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
        job.output_qty = form.output_qty.data
        job.status = form.status.data
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
        stage = ProductionStage(
            order_id=form.order_id.data,
            stage_name=form.stage_name.data,
            input_qty=form.input_qty.data
        )
        db.session.add(stage)
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
        stage.stage_name = form.stage_name.data
        stage.input_qty = form.input_qty.data
        stage.output_qty = form.output_qty.data
        stage.waste = form.waste.data
        stage.status = form.status.data
        db.session.commit()
        flash('Production stage updated.', 'success')
        return redirect(url_for('production.stage_list'))
    return render_template('production/form.html', form=form, title=f"Update Stage #{stage.id}", back_url=url_for('production.stage_list'))
