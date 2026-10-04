"""
Billing & Collections — Business Logic

- AR aging computation (0–30, 31–60, 61–90, 90+ day buckets)
- Invoice number auto-generation
- Invoice total calculations
"""

from datetime import date
from decimal import Decimal
from django.db.models import Sum, Q, F


def generate_invoice_number(business):
    """
    Auto-generate a unique invoice number: INV-{business_pk}-{sequence}
    """
    from billing.models import Invoice

    last_invoice = Invoice.objects.filter(
        business=business
    ).order_by('-pk').first()

    next_num = (last_invoice.pk + 1) if last_invoice else 1
    return f"INV-{business.pk:03d}-{next_num:06d}"


def calculate_invoice_totals(invoice):
    """
    Recalculate an invoice's subtotal, tax_amount, and total_amount
    from its line items.
    """
    items = invoice.line_items.all()
    subtotal = sum(item.line_total for item in items)
    tax = sum(item.tax_amount for item in items)
    return {
        'subtotal': float(subtotal),
        'tax_amount': float(tax),
        'total_amount': float(subtotal + tax),
    }


def compute_ar_aging(business):
    """
    Compute Accounts Receivable aging buckets.

    Per architecture: buckets are 0–30, 31–60, 61–90, 90+ days.
    Only considers invoices that have an outstanding balance.

    Returns:
    {
        'buckets': [
            {'label': '0-30 days', 'total': ..., 'count': ..., 'invoices': [...]},
            ...
        ],
        'total_outstanding': ...,
        'total_invoices': ...,
    }
    """
    from billing.models import Invoice

    today = date.today()

    # Get all non-paid, non-void invoices
    outstanding_invoices = Invoice.objects.filter(
        business=business
    ).exclude(
        status__in=[Invoice.Status.PAID, Invoice.Status.VOID, Invoice.Status.DRAFT]
    )

    buckets = {
        '0-30': {'label': '0–30 days', 'total': Decimal('0'), 'count': 0, 'invoices': []},
        '31-60': {'label': '31–60 days', 'total': Decimal('0'), 'count': 0, 'invoices': []},
        '61-90': {'label': '61–90 days', 'total': Decimal('0'), 'count': 0, 'invoices': []},
        '90+': {'label': '90+ days', 'total': Decimal('0'), 'count': 0, 'invoices': []},
    }

    for invoice in outstanding_invoices:
        balance = invoice.balance_due
        if balance <= 0:
            continue

        days_overdue = (today - invoice.due_date).days

        if days_overdue <= 30:
            bucket_key = '0-30'
        elif days_overdue <= 60:
            bucket_key = '31-60'
        elif days_overdue <= 90:
            bucket_key = '61-90'
        else:
            bucket_key = '90+'

        buckets[bucket_key]['total'] += balance
        buckets[bucket_key]['count'] += 1
        buckets[bucket_key]['invoices'].append({
            'invoice_number': invoice.invoice_number,
            'customer': invoice.customer.name,
            'total_amount': float(invoice.total_amount),
            'balance_due': float(balance),
            'due_date': str(invoice.due_date),
            'days_overdue': max(days_overdue, 0),
        })

    total_outstanding = sum(b['total'] for b in buckets.values())
    total_count = sum(b['count'] for b in buckets.values())

    return {
        'buckets': [
            {
                'label': b['label'],
                'total': float(b['total']),
                'count': b['count'],
                'percentage': round(float(b['total'] / total_outstanding * 100), 1)
                if total_outstanding > 0 else 0,
                'invoices': b['invoices'],
            }
            for b in buckets.values()
        ],
        'total_outstanding': float(total_outstanding),
        'total_invoices': total_count,
        'as_of_date': str(today),
    }


def get_collection_alerts(business):
    """
    Generate collection alert recommendations for overdue invoices.
    """
    from billing.models import Invoice

    today = date.today()
    alerts = []

    overdue = Invoice.objects.filter(
        business=business,
        due_date__lt=today
    ).exclude(
        status__in=[Invoice.Status.PAID, Invoice.Status.VOID, Invoice.Status.DRAFT]
    ).order_by('due_date')

    for inv in overdue:
        balance = inv.balance_due
        if balance <= 0:
            continue

        days_overdue = (today - inv.due_date).days

        if days_overdue > 90:
            severity = 'CRITICAL'
            action = 'Escalate to legal/collections. Consider bad debt provision.'
        elif days_overdue > 60:
            severity = 'HIGH'
            action = 'Send formal demand letter. Call customer directly.'
        elif days_overdue > 30:
            severity = 'MEDIUM'
            action = 'Send second reminder. Offer payment plan.'
        else:
            severity = 'LOW'
            action = 'Send friendly payment reminder.'

        alerts.append({
            'invoice_number': inv.invoice_number,
            'customer': inv.customer.name,
            'balance_due': float(balance),
            'days_overdue': days_overdue,
            'severity': severity,
            'recommended_action': action,
        })

    return alerts
