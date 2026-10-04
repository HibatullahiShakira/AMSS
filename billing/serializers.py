"""
Billing & Collections — Serializers
"""

from rest_framework import serializers
from .models import Invoice, InvoiceLineItem, Payment, CreditNote, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'description', 'unit_price', 'cost_price',
            'quantity_on_hand', 'reorder_level', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    total_with_tax = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceLineItem
        fields = [
            'id', 'product', 'description', 'quantity', 'unit_price', 'tax_rate',
            'line_total', 'tax_amount', 'total_with_tax'
        ]
        read_only_fields = ['id']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'amount', 'payment_date', 'payment_method',
            'reference', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CreditNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditNote
        fields = [
            'id', 'invoice', 'credit_note_number', 'amount', 'reason',
            'issue_date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class InvoiceSerializer(serializers.ModelSerializer):
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    credit_notes = CreditNoteSerializer(many=True, read_only=True)
    balance_due = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'customer', 'customer_name',
            'issue_date', 'due_date', 'status', 'currency',
            'subtotal', 'tax_amount', 'total_amount', 'amount_paid',
            'balance_due', 'notes', 'terms',
            'line_items', 'payments', 'credit_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'subtotal', 'tax_amount',
            'total_amount', 'amount_paid', 'created_at', 'updated_at'
        ]


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating invoices (without nested data)."""
    class Meta:
        model = Invoice
        fields = [
            'customer', 'issue_date', 'due_date', 'currency', 'notes', 'terms'
        ]
