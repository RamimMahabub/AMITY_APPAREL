from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, IntegerField, DateField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional

class BuyerForm(FlaskForm):
    name = StringField('Buyer Name', validators=[DataRequired()])
    country = StringField('Country')
    contact_info = StringField('Contact Info')
    submit = SubmitField('Add Buyer')

class OrderForm(FlaskForm):
    buyer_id = SelectField('Buyer', coerce=int, validators=[DataRequired()])
    product_name = StringField('Product Name', validators=[DataRequired()])
    total_qty = IntegerField('Total Quantity (pcs)', validators=[DataRequired()])
    deadline = DateField('Deadline', format='%Y-%m-%d', validators=[DataRequired()])
    design_image = FileField('Design Reference Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Create Order')

class ShipmentForm(FlaskForm):
    order_id = SelectField('Order', coerce=int, validators=[DataRequired()])
    container_no = StringField('Container Number', validators=[DataRequired()])
    final_qty = IntegerField('Final Quantity', validators=[DataRequired()])
    shipping_date = DateField('Shipping Date', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Create Shipment')


class UpdateShipmentForm(FlaskForm):
    order_id = SelectField('Order', coerce=int, validators=[DataRequired()])
    container_no = StringField('Container Number', validators=[DataRequired()])
    final_qty = IntegerField('Final Quantity', validators=[DataRequired()])
    shipping_date = DateField('Shipping Date', format='%Y-%m-%d', validators=[Optional()])
    status = SelectField('Status', choices=[('Pending', 'Pending'), ('Shipped', 'Shipped')], validators=[DataRequired()])
    submit = SubmitField('Update Shipment')
