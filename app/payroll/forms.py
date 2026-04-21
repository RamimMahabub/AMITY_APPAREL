from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, DecimalField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class EmployeeForm(FlaskForm):
    employee_code = StringField('Employee Code', validators=[DataRequired(), Length(max=32)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=128)])
    designation = StringField('Designation', validators=[DataRequired(), Length(max=64)])
    department = StringField('Department', validators=[DataRequired(), Length(max=64)])
    monthly_salary = DecimalField('Monthly Salary', validators=[DataRequired(), NumberRange(min=0.01)])
    join_date = DateField('Join Date', validators=[DataRequired()], format='%Y-%m-%d')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Employee')
