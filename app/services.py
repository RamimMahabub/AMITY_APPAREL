from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func

from app import db
from app.models import AuditLog, Expense, InventoryLedger, Order, SalaryPayment, Shipment, YarnPurchase


ZERO = Decimal('0')
DEFAULT_LOW_STOCK_THRESHOLD = Decimal('500')
DEFAULT_SALE_PRICE = Decimal('15')


def to_decimal(value: Any) -> Decimal:
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def serialize_model(instance) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for column in instance.__table__.columns:
        value = getattr(instance, column.name)
        if isinstance(value, datetime):
            data[column.name] = value.isoformat()
        elif isinstance(value, Decimal):
            data[column.name] = float(value)
        else:
            data[column.name] = value
    return data


def _serialize_audit_payload(payload):
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload
    return json.dumps(payload, default=str, ensure_ascii=False, sort_keys=True)


def log_audit(action: str, entity_type: str, entity_id: int | None = None, *, user=None, before_data=None, after_data=None, note: str | None = None, ip_address: str | None = None) -> AuditLog:
    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_data=_serialize_audit_payload(before_data),
        after_data=_serialize_audit_payload(after_data),
        note=note,
        user_id=getattr(user, 'id', None),
        ip_address=ip_address,
    )
    db.session.add(entry)
    return entry


def get_purchase_available_qty(purchase: YarnPurchase) -> Decimal:
    ledger_rows = InventoryLedger.query.filter_by(yarn_purchase_id=purchase.id).all()
    if not ledger_rows:
        return to_decimal(purchase.qty_kg)

    balance = ZERO
    for ledger_row in ledger_rows:
        quantity = to_decimal(ledger_row.qty_kg)
        if ledger_row.movement_type == 'OUT':
            balance -= quantity
        else:
            balance += quantity
    return balance


def get_total_yarn_stock() -> Decimal:
    ledger_rows = InventoryLedger.query.all()
    if ledger_rows:
        total = ZERO
        for ledger_row in ledger_rows:
            quantity = to_decimal(ledger_row.qty_kg)
            total += quantity if ledger_row.movement_type != 'OUT' else -quantity
        return total
    purchased = db.session.query(func.coalesce(func.sum(YarnPurchase.qty_kg), 0)).scalar() or 0
    return to_decimal(purchased)


def get_low_stock_purchases(threshold: Decimal = DEFAULT_LOW_STOCK_THRESHOLD):
    purchases = YarnPurchase.query.order_by(YarnPurchase.created_at.desc()).all()
    low_stock = []
    for purchase in purchases:
        available = get_purchase_available_qty(purchase)
        if available <= threshold:
            low_stock.append({'purchase': purchase, 'available_qty': available})
    return low_stock


def record_inventory_in(purchase: YarnPurchase, *, user=None, note: str | None = None) -> InventoryLedger:
    return InventoryLedger(
        yarn_purchase_id=purchase.id,
        movement_type='IN',
        qty_kg=to_decimal(purchase.qty_kg),
        unit_cost=to_decimal(purchase.price_per_kg),
        reference_type='YarnPurchase',
        reference_id=purchase.id,
        note=note or 'Yarn received into stock',
        created_by_id=getattr(user, 'id', None),
    )


def record_inventory_out(purchase: YarnPurchase, qty_kg, *, reference_type: str, reference_id: int | None = None, user=None, note: str | None = None) -> InventoryLedger:
    qty = to_decimal(qty_kg)
    available = get_purchase_available_qty(purchase)
    if qty <= 0:
        raise ValueError('Quantity must be greater than zero.')
    if qty > available:
        raise ValueError(f'Insufficient yarn stock. Available: {available:.2f} kg')
    return InventoryLedger(
        yarn_purchase_id=purchase.id,
        movement_type='OUT',
        qty_kg=qty,
        unit_cost=to_decimal(purchase.price_per_kg),
        reference_type=reference_type,
        reference_id=reference_id,
        note=note or 'Yarn allocated from stock',
        created_by_id=getattr(user, 'id', None),
    )


def calculate_waste_percentage(input_qty, waste_qty) -> Decimal:
    input_decimal = to_decimal(input_qty)
    waste_decimal = to_decimal(waste_qty)
    if input_decimal <= 0:
        return ZERO
    return (waste_decimal / input_decimal * Decimal('100')).quantize(Decimal('0.01'))


def calculate_shipment_progress(order: Order) -> Decimal:
    shipped_qty = db.session.query(func.coalesce(func.sum(Shipment.final_qty), 0)).filter(Shipment.order_id == order.id).scalar() or 0
    total_qty = to_decimal(order.total_qty)
    if total_qty <= 0:
        return ZERO
    return min((to_decimal(shipped_qty) / total_qty * Decimal('100')).quantize(Decimal('0.01')), Decimal('100.00'))


def calculate_order_financials(order: Order) -> dict[str, Decimal]:
    revenue_per_unit = to_decimal(order.sale_price_per_unit) or DEFAULT_SALE_PRICE
    revenue = to_decimal(order.total_qty) * revenue_per_unit
    total_cost = (
        to_decimal(order.estimated_yarn_cost)
        + to_decimal(order.estimated_dyeing_cost)
        + to_decimal(order.estimated_labor_cost)
        + to_decimal(order.estimated_shipping_cost)
    )
    profit = revenue - total_cost
    return {
        'revenue': revenue.quantize(Decimal('0.01')),
        'total_cost': total_cost.quantize(Decimal('0.01')),
        'profit': profit.quantize(Decimal('0.01')),
    }


def calculate_dashboard_metrics(month_start: datetime, urgent_deadline: datetime) -> dict[str, Any]:
    active_orders = Order.query.filter_by(status='Active').order_by(Order.deadline.asc()).all()
    delayed_orders = [order for order in active_orders if order.deadline < datetime.utcnow()]
    urgent_orders = [order for order in active_orders if order.deadline <= urgent_deadline]
    shipped_orders = Order.query.filter_by(status='Shipped').count()
    completed_orders = Order.query.filter_by(status='Completed').count()
    total_orders = Order.query.count()
    total_yarn_stock = get_total_yarn_stock()
    low_stock_alerts = get_low_stock_purchases()

    current_month_payroll = (
        db.session.query(func.coalesce(func.sum(SalaryPayment.paid_amount), 0))
        .filter(SalaryPayment.payment_month == month_start.date())
        .scalar()
        or 0
    )

    monthly_revenue = sum((calculate_order_financials(order)['revenue'] for order in active_orders), ZERO)
    monthly_cost = sum((calculate_order_financials(order)['total_cost'] for order in active_orders), ZERO)
    month_start_date = month_start.date()
    if month_start_date.month == 12:
        month_end_date = month_start_date.replace(year=month_start_date.year + 1, month=1, day=1)
    else:
        month_end_date = month_start_date.replace(month=month_start_date.month + 1, day=1)
    monthly_expenses = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(Expense.expense_date >= month_start_date, Expense.expense_date < month_end_date)
        .scalar()
        or 0
    )
    monthly_cost += to_decimal(monthly_expenses)
    estimated_profit = monthly_revenue - monthly_cost

    total_shipments = db.session.query(func.count(Shipment.id)).scalar() or 0
    shipped_count = db.session.query(func.count(Shipment.id)).filter(Shipment.status == 'Shipped').scalar() or 0
    shipment_progress = Decimal('0') if total_shipments == 0 else (to_decimal(shipped_count) / to_decimal(total_shipments) * Decimal('100')).quantize(Decimal('0.01'))

    production_efficiency = Decimal('0')
    if active_orders:
        delivered_ratio = sum((calculate_shipment_progress(order) for order in active_orders), ZERO) / to_decimal(len(active_orders))
        production_efficiency = delivered_ratio.quantize(Decimal('0.01'))

    return {
        'active_orders': active_orders,
        'delayed_orders': delayed_orders,
        'urgent_orders': urgent_orders,
        'low_stock_alerts': low_stock_alerts,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'shipped_orders': shipped_orders,
        'total_yarn_stock': total_yarn_stock.quantize(Decimal('0.01')),
        'current_month_payroll': to_decimal(current_month_payroll).quantize(Decimal('0.01')),
        'monthly_revenue': monthly_revenue.quantize(Decimal('0.01')),
        'monthly_cost': monthly_cost.quantize(Decimal('0.01')),
        'estimated_profit': estimated_profit.quantize(Decimal('0.01')),
        'shipment_progress': shipment_progress,
        'production_efficiency': production_efficiency,
        'order_status_counts': {
            'Active': len(active_orders),
            'Completed': completed_orders,
            'Shipped': shipped_orders,
        },
    }
