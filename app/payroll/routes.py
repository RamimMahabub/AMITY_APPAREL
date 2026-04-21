from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.auth.routes import role_required
from app.models import Employee, SalaryPayment
from app.payroll.forms import EmployeeForm

payroll = Blueprint('payroll', __name__)


def _resolve_month(month_str: str | None):
    today = date.today()
    if not month_str:
        return date(today.year, today.month, 1)

    try:
        year_str, month_num_str = month_str.split('-', 1)
        year = int(year_str)
        month_num = int(month_num_str)
        if month_num < 1 or month_num > 12:
            raise ValueError('Invalid month')
        return date(year, month_num, 1)
    except Exception:
        return date(today.year, today.month, 1)


@payroll.route('/')
@login_required
@role_required(['Admin', 'Manager'])
def index():
    return redirect(url_for('payroll.employee_list'))


@payroll.route('/employees', methods=['GET'])
@login_required
@role_required(['Admin', 'Manager'])
def employee_list():
    month_start = _resolve_month(request.args.get('month'))
    employees = Employee.query.order_by(Employee.full_name.asc()).all()

    paid_rows = (
        db.session.query(
            SalaryPayment.employee_id,
            func.coalesce(func.sum(SalaryPayment.paid_amount), 0),
        )
        .filter(SalaryPayment.payment_month == month_start)
        .group_by(SalaryPayment.employee_id)
        .all()
    )
    paid_map = {employee_id: float(total_paid) for employee_id, total_paid in paid_rows}

    payroll_rows = []
    total_salary = 0.0
    total_paid = 0.0
    total_due = 0.0
    for employee in employees:
        salary = float(employee.monthly_salary or 0)
        paid = paid_map.get(employee.id, 0.0)
        due = max(salary - paid, 0.0)
        payroll_rows.append({'employee': employee, 'salary': salary, 'paid': paid, 'due': due})
        total_salary += salary
        total_paid += paid
        total_due += due

    recent_payments = (
        SalaryPayment.query.join(Employee)
        .filter(SalaryPayment.payment_month == month_start)
        .order_by(SalaryPayment.paid_on.desc())
        .limit(20)
        .all()
    )

    return render_template(
        'payroll/employee_list.html',
        month_start=month_start,
        payroll_rows=payroll_rows,
        total_salary=total_salary,
        total_paid=total_paid,
        total_due=total_due,
        recent_payments=recent_payments,
    )


@payroll.route('/employees/new', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager'])
def employee_new():
    form = EmployeeForm()
    if form.validate_on_submit():
        existing = Employee.query.filter_by(employee_code=form.employee_code.data.strip()).first()
        if existing:
            flash('Employee code already exists.', 'danger')
            return render_template('payroll/employee_form.html', form=form)

        employee = Employee(
            employee_code=form.employee_code.data.strip(),
            full_name=form.full_name.data.strip(),
            designation=form.designation.data.strip(),
            department=form.department.data.strip(),
            monthly_salary=form.monthly_salary.data,
            join_date=form.join_date.data,
            is_active=bool(form.is_active.data),
        )
        db.session.add(employee)
        db.session.commit()
        flash('Employee created successfully.', 'success')
        return redirect(url_for('payroll.employee_list'))

    return render_template('payroll/employee_form.html', form=form)


@payroll.route('/pay-multiple', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def pay_multiple():
    month_start = _resolve_month(request.form.get('month'))
    selected_ids = request.form.getlist('selected_employee_ids')

    if not selected_ids:
        flash('Select at least one employee to pay.', 'danger')
        return redirect(url_for('payroll.employee_list', month=month_start.strftime('%Y-%m')))

    employee_ids = [int(emp_id) for emp_id in selected_ids]
    employees = Employee.query.filter(Employee.id.in_(employee_ids)).all()
    employee_map = {employee.id: employee for employee in employees}

    paid_rows = (
        db.session.query(
            SalaryPayment.employee_id,
            func.coalesce(func.sum(SalaryPayment.paid_amount), 0),
        )
        .filter(SalaryPayment.payment_month == month_start, SalaryPayment.employee_id.in_(employee_ids))
        .group_by(SalaryPayment.employee_id)
        .all()
    )
    paid_map = {employee_id: float(total_paid) for employee_id, total_paid in paid_rows}

    created_count = 0
    total_paid_now = 0.0

    for emp_id in employee_ids:
        employee = employee_map.get(emp_id)
        if not employee:
            continue

        already_paid = paid_map.get(emp_id, 0.0)
        due = max(float(employee.monthly_salary or 0) - already_paid, 0.0)
        if due <= 0:
            continue

        amount_key = f'amount_{emp_id}'
        try:
            pay_amount = float(request.form.get(amount_key, '0') or 0)
        except ValueError:
            flash(f'Invalid amount for {employee.full_name}.', 'danger')
            return redirect(url_for('payroll.employee_list', month=month_start.strftime('%Y-%m')))

        if pay_amount <= 0:
            flash(f'Payment amount for {employee.full_name} must be greater than 0.', 'danger')
            return redirect(url_for('payroll.employee_list', month=month_start.strftime('%Y-%m')))

        if pay_amount > due:
            flash(f'Payment for {employee.full_name} exceeds due amount.', 'danger')
            return redirect(url_for('payroll.employee_list', month=month_start.strftime('%Y-%m')))

        payment = SalaryPayment(
            employee_id=emp_id,
            payment_month=month_start,
            paid_amount=pay_amount,
            paid_on=datetime.utcnow(),
            note='Bulk salary payment',
            paid_by_id=current_user.id,
        )
        db.session.add(payment)
        created_count += 1
        total_paid_now += pay_amount

    if created_count == 0:
        flash('No payable due found for selected employees.', 'info')
    else:
        db.session.commit()
        flash(f'Paid salary for {created_count} employee(s). Total paid: {total_paid_now:,.2f}', 'success')

    return redirect(url_for('payroll.employee_list', month=month_start.strftime('%Y-%m')))
