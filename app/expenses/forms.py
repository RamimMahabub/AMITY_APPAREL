from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class ExpenseForm(FlaskForm):
    expense_date = DateField('Expense Date', validators=[DataRequired()], format='%Y-%m-%d')
    category = SelectField(
        'Category',
        choices=[
            ('Rent', 'Rent'),
            ('Utility', 'Utility'),
            ('Transport', 'Transport'),
            ('Maintenance', 'Maintenance'),
            ('Office', 'Office'),
            ('Other', 'Other'),
        ],
        validators=[DataRequired()],
    )
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    description = StringField('Description', validators=[Length(max=255)])
    submit = SubmitField('Add Expense')
