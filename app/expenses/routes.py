from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.auth.routes import role_required
from app.expenses.forms import ExpenseForm
from app.models import Expense
from app.services import log_audit

expenses = Blueprint('expenses', __name__)


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


@expenses.route('/', methods=['GET'])
@login_required
@role_required(['Admin', 'Manager'])
def expense_list():
    month_start = _resolve_month(request.args.get('month'))
    if month_start.month == 12:
        month_end = date(month_start.year + 1, 1, 1)
    else:
        month_end = date(month_start.year, month_start.month + 1, 1)

    rows = (
        Expense.query
        .filter(Expense.expense_date >= month_start, Expense.expense_date < month_end)
        .order_by(Expense.expense_date.desc(), Expense.id.desc())
        .all()
    )
    total_expense = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(Expense.expense_date >= month_start, Expense.expense_date < month_end)
        .scalar()
        or 0
    )

    form = ExpenseForm()
    if not form.expense_date.data:
        form.expense_date.data = date.today()

    return render_template(
        'expenses/expense_list.html',
        month_start=month_start,
        expenses=rows,
        total_expense=float(total_expense),
        form=form,
    )


@expenses.route('/new', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Manager'])
def expense_new():
    form = ExpenseForm()
    if form.validate_on_submit():
        item = Expense(
            expense_date=form.expense_date.data,
            category=form.category.data,
            amount=form.amount.data,
            description=(form.description.data or '').strip() or None,
            created_by_id=current_user.id,
        )
        db.session.add(item)
        db.session.flush()
        log_audit(
            'create',
            'Expense',
            item.id,
            user=current_user,
            after_data={
                'expense_date': item.expense_date.isoformat(),
                'category': item.category,
                'amount': float(item.amount),
                'description': item.description,
            },
            note='Expense entry created',
        )
        db.session.commit()
        flash('Expense added successfully.', 'success')
        return redirect(url_for('expenses.expense_list', month=item.expense_date.strftime('%Y-%m')))

    if request.method == 'GET' and not form.expense_date.data:
        form.expense_date.data = date.today()

    return render_template(
        'expenses/expense_list.html',
        form=form,
        expenses=[],
        month_start=_resolve_month(request.args.get('month')),
        total_expense=0.0,
    )
