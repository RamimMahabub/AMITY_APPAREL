from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional, Length

class YarnPurchaseForm(FlaskForm):
    supplier_id = SelectField('Supplier', coerce=int, validators=[Optional()])
    new_supplier_name = StringField('Or Add New Supplier', validators=[Optional(), Length(max=128)])
    supplier_contact_person = StringField('Contact Person', validators=[Optional(), Length(max=64)])
    supplier_phone = StringField('Phone Number', validators=[Optional(), Length(max=32)])
    supplier_email = StringField('Email', validators=[Optional(), Length(max=120)])
    supplier_address = StringField('Address', validators=[Optional(), Length(max=255)])
    status = SelectField('Status', choices=[('Received', 'Received'), ('Assigned', 'Assigned')], validators=[Optional()])
    yarn_type = StringField('Yarn Type', validators=[DataRequired()])
    color = StringField('Color', validators=[DataRequired()])
    qty_kg = DecimalField('Quantity (kg)', validators=[DataRequired(), NumberRange(min=0.1)])
    price_per_kg = DecimalField('Price per kg ($)', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Record Purchase')
