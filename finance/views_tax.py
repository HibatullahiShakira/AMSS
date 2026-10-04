"""
Nigerian Tax Engine — Views

Endpoints:
- /finance/tax-config/           — Manage business tax configuration (VAT, TIN, CIT rate)
- /finance/tax-transactions/     — List tax line items
- /finance/tax-returns/          — Manage, generate, file tax returns
- /finance/tax-deadlines/        — View upcoming FIRS deadlines
- /finance/tax-calculator/       — Utility for quick tax calculations
"""

from datetime import date
from django.http import JsonResponse
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response

from .views import BusinessOwnerViewSet
from .models_tax import TaxConfiguration, TaxTransaction, TaxReturn, TaxFilingDeadline
from .serializers_tax import (
    TaxConfigurationSerializer,
    TaxTransactionSerializer,
    TaxReturnSerializer,
    TaxFilingDeadlineSerializer,
)
from .helpers_tax import (
    calculate_vat,
    calculate_wht,
    compute_cit_liability,
    generate_vat_return,
    get_filing_deadlines,
)
from .permissions import IsOwnerOrAdmin


class TaxConfigurationView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update the tax configuration for the current business.
    This is a Singleton view per business.
    """
    serializer_class = TaxConfigurationSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_object(self):
        from users.models import User
        from rest_framework_simplejwt.models import TokenUser
        
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)
            
        business = getattr(user, 'business', None)
        if not business:
            raise Exception("No business found.")
            
        config, created = TaxConfiguration.objects.get_or_create(business=business)
        return config


class TaxTransactionViewSet(BusinessOwnerViewSet):
    queryset = TaxTransaction.objects.all()
    serializer_class = TaxTransactionSerializer
    permission_classes = [IsOwnerOrAdmin]


class TaxReturnViewSet(BusinessOwnerViewSet):
    queryset = TaxReturn.objects.all()
    serializer_class = TaxReturnSerializer
    permission_classes = [IsOwnerOrAdmin]

    @action(detail=False, methods=['post'], url_path='generate-vat')
    def generate_vat(self, request):
        """Generate a VAT return for a specific month and year."""
        month = int(request.data.get('month', date.today().month))
        year = int(request.data.get('year', date.today().year))
        
        business = self.get_business()
        if not business:
            return JsonResponse({'error': 'No business found.'}, status=400)

        data = generate_vat_return(business, month, year)
        
        # Save draft return
        start_date = data['start_date']
        end_date = data['end_date']
        
        tax_return, created = TaxReturn.objects.update_or_create(
            business=business,
            tax_type='VAT',
            period_start=start_date,
            period_end=end_date,
            defaults={
                'total_liability': data['total_vat_liability'],
                'report_data_json': data,
            }
        )
        
        serializer = self.get_serializer(tax_return)
        return JsonResponse(serializer.data)


class TaxFilingDeadlineViewSet(BusinessOwnerViewSet):
    queryset = TaxFilingDeadline.objects.all()
    serializer_class = TaxFilingDeadlineSerializer
    permission_classes = [IsOwnerOrAdmin]

    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming(self, request):
        """List upcoming tax deadlines."""
        business = self.get_business()
        if not business:
            return JsonResponse({'error': 'No business found.'}, status=400)

        deadlines = get_filing_deadlines(business)
        return JsonResponse({'deadlines': deadlines})


class TaxCalculatorViewSet(viewsets.ViewSet):
    """Utility endpoint for calculating taxes on the fly."""
    permission_classes = [IsOwnerOrAdmin]
    
    @action(detail=False, methods=['post'], url_path='calculate')
    def calculate(self, request):
        amount = request.data.get('amount', 0)
        tax_type = request.data.get('tax_type', 'VAT')
        
        if tax_type == 'VAT':
            rate = request.data.get('rate', '7.5')
            result = calculate_vat(amount, rate)
            return JsonResponse({'tax_amount': float(result), 'rate': rate})
            
        elif tax_type == 'WHT':
            service_type = request.data.get('service_type', 'CONTRACT')
            result = calculate_wht(amount, service_type)
            return JsonResponse({'tax_amount': float(result), 'service_type': service_type})
            
        return JsonResponse({'error': 'Unsupported tax type'}, status=400)
