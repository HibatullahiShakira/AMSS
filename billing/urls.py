"""
Billing & Collections — URLs
"""

from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet, PaymentViewSet, CreditNoteViewSet, ARAgingViewSet, ProductViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'credit-notes', CreditNoteViewSet, basename='creditnote')
router.register(r'ar-aging', ARAgingViewSet, basename='ar-aging')

urlpatterns = router.urls
