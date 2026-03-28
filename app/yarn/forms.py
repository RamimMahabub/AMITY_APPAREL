from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class YarnPurchaseForm(FlaskForm):
    supplier_id = SelectField('Supplier', coerce=int, validators=[DataRequired()])
    yarn_type = StringField('Yarn Type', validators=[DataRequired()])
    color = StringField('Color', validators=[DataRequired()])
    qty_kg = DecimalField('Quantity (kg)', validators=[DataRequired(), NumberRange(min=0.1)])
    price_per_kg = DecimalField('Price per kg ($)', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Record Purchase')
