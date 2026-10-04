"""
Billing & Collections — Views

Endpoints:
- /billing/invoices/         — Full invoice CRUD + send, void, aging
- /billing/payments/         — Record and list payments
- /billing/credit-notes/     — Issue credit notes
- /billing/ar-aging/         — AR aging report
- /billing/collections/      — Collection alerts
"""

from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.models import TokenUser

from users.models import User
from finance.permissions import IsOwnerOrAdmin
from .models import Invoice, InvoiceLineItem, Payment, CreditNote, Product
from .serializers import (
    InvoiceSerializer, InvoiceCreateSerializer,
    InvoiceLineItemSerializer, PaymentSerializer, CreditNoteSerializer, ProductSerializer
)
from .helpers import generate_invoice_number, compute_ar_aging, get_collection_alerts


class BillingBusinessMixin:
    """Mixin that provides business-scoped querysets for billing views."""

    def get_business(self):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)
        return getattr(user, 'business', None)

    def get_queryset(self):
        business = self.get_business()
        if business is None:
            return self.queryset.none()
        return self.queryset.filter(business=business)


class ProductViewSet(BillingBusinessMixin, viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsOwnerOrAdmin]

    def perform_create(self, serializer):
        business = self.get_business()
        serializer.save(business=business)


class InvoiceViewSet(BillingBusinessMixin, viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer
        return InvoiceSerializer

    def perform_create(self, serializer):
        business = self.get_business()
        if not business:
            raise Exception("No business found.")
        invoice_number = generate_invoice_number(business)
        serializer.save(
            business=business,
            invoice_number=invoice_number,
            created_by=self.request.user if not isinstance(self.request.user, TokenUser) else None
        )

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_line_item(self, request, pk=None):
        """Add a line item to an invoice."""
        invoice = self.get_object()
        if invoice.status != Invoice.Status.DRAFT:
            return JsonResponse(
                {'error': 'Can only add items to draft invoices.'},
                status=400
            )

        serializer = InvoiceLineItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(invoice=invoice)
        invoice.recalculate_totals()

        return JsonResponse(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=['post'], url_path='send')
    def send_invoice(self, request, pk=None):
        """Mark an invoice as sent."""
        invoice = self.get_object()
        if invoice.status != Invoice.Status.DRAFT:
            return JsonResponse(
                {'error': 'Only draft invoices can be sent.'},
                status=400
            )

        invoice.status = Invoice.Status.SENT
        invoice.save(update_fields=['status'])
        
        from finance.helpers_accounting import create_journal_entry_from_invoice
        create_journal_entry_from_invoice(invoice)
        
        return JsonResponse({'message': f'Invoice {invoice.invoice_number} sent.', 'status': 'SENT'})

    @action(detail=True, methods=['post'], url_path='void')
    def void_invoice(self, request, pk=None):
        """Void an invoice."""
        invoice = self.get_object()
        if invoice.status == Invoice.Status.PAID:
            return JsonResponse(
                {'error': 'Cannot void a paid invoice. Issue a credit note instead.'},
                status=400
            )

        invoice.status = Invoice.Status.VOID
        invoice.save(update_fields=['status'])
        return JsonResponse({'message': f'Invoice {invoice.invoice_number} voided.', 'status': 'VOID'})

    @action(detail=True, methods=['post'], url_path='record-payment')
    def record_payment(self, request, pk=None):
        """Record a payment against this invoice."""
        invoice = self.get_object()
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        business = self.get_business()
        serializer.save(
            invoice=invoice,
            business=business,
            received_by=self.request.user if not isinstance(self.request.user, TokenUser) else None
        )

        return JsonResponse({
            'message': 'Payment recorded.',
            'amount_paid': float(invoice.amount_paid),
            'balance_due': float(invoice.balance_due),
            'status': invoice.status,
        })

    @action(detail=False, methods=['post'], url_path='pos-checkout')
    def pos_checkout(self, request):
        from django.db import transaction
        from datetime import datetime
        
        business = self.get_business()
        if not business:
            return JsonResponse({'error': 'No business found'}, status=400)
            
        data = request.data
        items = data.get('items', [])
        amount_paid = float(data.get('amount_paid', 0))
        payment_method = data.get('payment_method', 'CASH')
        
        if not items:
            return JsonResponse({'error': 'No items provided'}, status=400)
            
        with transaction.atomic():
            # 1. Create Invoice
            invoice = Invoice.objects.create(
                business=business,
                invoice_number=generate_invoice_number(business),
                issue_date=datetime.now().date(),
                due_date=datetime.now().date(),
                status=Invoice.Status.DRAFT,
                created_by=self.request.user if not isinstance(self.request.user, TokenUser) else None,
                currency='NGN'
            )
            
            # 2. Add Line Items
            for item in items:
                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    product_id=item.get('product_id'),
                    description=item.get('description', 'POS Item'),
                    quantity=item.get('quantity', 1),
                    unit_price=item.get('unit_price', 0),
                    tax_rate=item.get('tax_rate', 7.5)
                )
            
            invoice.recalculate_totals()
            
            from finance.helpers_accounting import create_journal_entry_from_invoice
            create_journal_entry_from_invoice(invoice)
            
            # 3. Create Payment if amount > 0
            if amount_paid > 0:
                Payment.objects.create(
                    invoice=invoice,
                    business=business,
                    amount=amount_paid,
                    payment_date=datetime.now().date(),
                    payment_method=payment_method,
                    received_by=self.request.user if not isinstance(self.request.user, TokenUser) else None
                )
                
            return JsonResponse({
                'message': 'POS Checkout successful',
                'invoice_id': invoice.id,
                'total_amount': float(invoice.total_amount),
                'amount_paid': float(invoice.amount_paid),
                'status': invoice.status
            })


class PaymentViewSet(BillingBusinessMixin, viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsOwnerOrAdmin]

    def perform_create(self, serializer):
        business = self.get_business()
        serializer.save(
            business=business,
            received_by=self.request.user if not isinstance(self.request.user, TokenUser) else None
        )


class CreditNoteViewSet(BillingBusinessMixin, viewsets.ModelViewSet):
    queryset = CreditNote.objects.all()
    serializer_class = CreditNoteSerializer
    permission_classes = [IsOwnerOrAdmin]

    def perform_create(self, serializer):
        business = self.get_business()
        serializer.save(
            business=business,
            created_by=self.request.user if not isinstance(self.request.user, TokenUser) else None
        )


class ARAgingViewSet(viewsets.ViewSet):
    """Accounts Receivable aging report."""
    permission_classes = [IsOwnerOrAdmin]

    @action(detail=False, methods=['get'], url_path='report')
    def aging_report(self, request):
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)
        business = getattr(user, 'business', None)
        if not business:
            return JsonResponse({'error': 'No business found.'}, status=400)

        aging = compute_ar_aging(business)
        return JsonResponse(aging)

    @action(detail=False, methods=['get'], url_path='alerts')
    def collection_alerts(self, request):
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)
        business = getattr(user, 'business', None)
        if not business:
            return JsonResponse({'error': 'No business found.'}, status=400)

        alerts = get_collection_alerts(business)
        return JsonResponse({
            'alert_count': len(alerts),
            'alerts': alerts
        })
