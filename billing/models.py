"""
Billing & Collections Module — Models

Implements (from AMSS Architecture Blueprint):
- Invoice: Full lifecycle (DRAFT → SENT → PAID / OVERDUE / VOID)
- InvoiceLineItem: Individual items with quantity, unit price, tax
- Payment: Records payments against invoices (supports partial payments)
- CreditNote: Credit notes linked to invoices for adjustments/refunds
"""

from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Sum

from users.models import Business
from finance.models import Customer
from finance.models import Customer


class Product(models.Model):
    """
    Inventory items / Products for sale.
    """
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='products'
    )
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, blank=True, null=True, help_text="Stock Keeping Unit")
    description = models.TextField(blank=True, default='')
    unit_price = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))
    cost_price = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (Qty: {self.quantity_on_hand})"

class Invoice(models.Model):
    """
    Full invoice with line items, status workflow, and tax fields.
    Supports partial payments and credit notes.
    """

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SENT = 'SENT', 'Sent'
        VIEWED = 'VIEWED', 'Viewed'
        PARTIALLY_PAID = 'PARTIALLY_PAID', 'Partially Paid'
        PAID = 'PAID', 'Paid'
        OVERDUE = 'OVERDUE', 'Overdue'
        VOID = 'VOID', 'Void'

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='invoices'
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='invoices'
    )
    invoice_number = models.CharField(
        max_length=50, unique=True,
        help_text='Auto-generated invoice number (e.g. INV-001-000001)'
    )
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    currency = models.CharField(max_length=10, default='NGN')

    # Computed totals (updated on save)
    subtotal = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00')
    )
    tax_amount = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00')
    )
    total_amount = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00')
    )
    amount_paid = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00')
    )

    notes = models.TextField(blank=True, default='')
    terms = models.TextField(
        blank=True, default='Payment is due within the specified terms.'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_invoices'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date', '-created_at']

    def __str__(self):
        return f"{self.invoice_number} — {self.customer.name} ({self.status})"

    @property
    def balance_due(self):
        """Amount still owed on this invoice."""
        credits = self.credit_notes.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        return self.total_amount - self.amount_paid - credits

    def recalculate_totals(self):
        """Recalculate subtotal, tax, and total from line items."""
        items = self.line_items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.tax_amount = sum(item.tax_amount for item in items)
        self.total_amount = self.subtotal + self.tax_amount
        self.save(update_fields=['subtotal', 'tax_amount', 'total_amount'])


class InvoiceLineItem(models.Model):
    """Individual line item on an invoice."""

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='line_items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_lines'
    )
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('1.00')
    )
    unit_price = models.DecimalField(max_digits=20, decimal_places=2)
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('7.50'),
        help_text='Tax rate in % (default: 7.5% VAT)'
    )

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f"{self.description}: {self.quantity} × {self.unit_price}"

    @property
    def line_total(self):
        """Subtotal for this line (before tax)."""
        return (self.quantity * self.unit_price).quantize(Decimal('0.01'))

    @property
    def tax_amount(self):
        """Tax amount for this line."""
        return (self.line_total * self.tax_rate / Decimal('100')).quantize(Decimal('0.01'))

    @property
    def total_with_tax(self):
        """Line total including tax."""
        return self.line_total + self.tax_amount


class Payment(models.Model):
    """
    Records a payment against an invoice. Supports partial payments.
    """

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        POS = 'POS', 'POS'
        CHEQUE = 'CHEQUE', 'Cheque'
        MOBILE_MONEY = 'MOBILE_MONEY', 'Mobile Money'
        USSD = 'USSD', 'USSD'
        CARD = 'CARD', 'Card'

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='payments'
    )
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='billing_payments'
    )
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices,
        default=PaymentMethod.BANK_TRANSFER
    )
    reference = models.CharField(
        max_length=255, blank=True, default='',
        help_text='Payment reference (bank ref, receipt number)'
    )
    notes = models.TextField(blank=True, default='')
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='received_payments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment ₦{self.amount} on {self.payment_date} for {self.invoice.invoice_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update invoice amount_paid and status
        invoice = self.invoice
        total_paid = invoice.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        invoice.amount_paid = total_paid

        if total_paid >= invoice.total_amount:
            invoice.status = Invoice.Status.PAID
        elif total_paid > 0:
            invoice.status = Invoice.Status.PARTIALLY_PAID
        invoice.save(update_fields=['amount_paid', 'status'])


class CreditNote(models.Model):
    """
    Credit note linked to an invoice for adjustments or refunds.
    """
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='credit_notes'
    )
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='credit_notes'
    )
    credit_note_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    reason = models.TextField()
    issue_date = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_credit_notes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issue_date']

    def __str__(self):
        return f"CN-{self.credit_note_number} — ₦{self.amount} for {self.invoice.invoice_number}"
