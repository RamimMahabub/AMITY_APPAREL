from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class KnittingJobForm(FlaskForm):
    yarn_purchase_id = SelectField('Yarn Batch', coerce=int, validators=[DataRequired()])
    company_name = StringField('Knitting Company', validators=[DataRequired()])
    sent_qty_kg = DecimalField('Sent Yarn Qty (kg)', validators=[DataRequired(), NumberRange(min=0.1)])
    submit = SubmitField('Create Knitting Job')

class UpdateKnittingJobForm(FlaskForm):
    received_fabric_kg = DecimalField('Received Fabric Qty (kg)', validators=[DataRequired(), NumberRange(min=0)])
    waste_kg = DecimalField('Waste (kg)', validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField('Status', choices=[('In Progress', 'In Progress'), ('Completed', 'Completed')], validators=[DataRequired()])
    submit = SubmitField('Update Job')

class DyeingJobForm(FlaskForm):
    knitting_job_id = SelectField('Knitting Batch (Fabric)', coerce=int, validators=[DataRequired()])
    dyeing_unit_name = StringField('Dyeing Unit Name', validators=[DataRequired()])
    color_specification = StringField('Color Specification', validators=[DataRequired()])
    input_qty = DecimalField('Input Fabric (kg)', validators=[DataRequired(), NumberRange(min=0.1)])
    submit = SubmitField('Create Dyeing Job')

class UpdateDyeingJobForm(FlaskForm):
    output_qty = DecimalField('Output Dyed Fabric (kg)', validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField('Status', choices=[('In Progress', 'In Progress'), ('Completed', 'Completed')], validators=[DataRequired()])
    submit = SubmitField('Update Job')

class ProductionStageForm(FlaskForm):
    order_id = SelectField('Order', coerce=int, validators=[DataRequired()])
    stage_name = SelectField('Stage Name', choices=[('Cutting', 'Cutting'), ('Sewing', 'Sewing'), ('Finishing', 'Finishing'), ('Packing', 'Packing')], validators=[DataRequired()])
    input_qty = IntegerField('Input Quantity (pcs)', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Start Stage')

class UpdateProductionStageForm(FlaskForm):
    output_qty = IntegerField('Output Quantity (pcs)', validators=[DataRequired(), NumberRange(min=0)])
    waste = IntegerField('Waste (pcs)', validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField('Status', choices=[('In Progress', 'In Progress'), ('Completed', 'Completed')], validators=[DataRequired()])
    submit = SubmitField('Update Stage')
