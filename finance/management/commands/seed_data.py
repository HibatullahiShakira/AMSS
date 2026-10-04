from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from users.models import Business
from finance.models import Income, Expense, Asset, Liability, Customer
from finance.models_expense import ExpenseCategory, RecurringExpense, Reminder
from billing.models import Invoice, InvoiceLineItem, Payment

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with realistic dummy financial data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting database seed...')
        
        # Create a test user and business
        user, _ = User.objects.get_or_create(
            email='admin@amss.local',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if not user.password:
            user.set_password('admin123')
            user.save()

        business, _ = Business.objects.get_or_create(
            user=user,
            business_name='Acme Nigeria Ltd',
            defaults={
                'business_address': 'Lagos, Nigeria',
                'business_type': 'LLC',
                'business_email': 'hello@acme.com.ng',
                'industry': 'Technology',
                'annual_revenue': Decimal('50000000.00')
            }
        )
        user.business = business
        user.save()

        # Create Customers
        customer1, _ = Customer.objects.get_or_create(
            business=business, user=user, name='Dangote Group', contact_info='procurement@dangote.com'
        )
        customer2, _ = Customer.objects.get_or_create(
            business=business, user=user, name='MTN Nigeria', contact_info='vendor@mtn.com.ng'
        )

        today = timezone.now().date()

        # Seed Income (YTD)
        Income.objects.filter(business=business).delete()
        for i in range(15):
            days_ago = random.randint(1, 180)
            amount = Decimal(random.randint(500000, 5000000))
            Income.objects.create(
                business=business, user=user, amount=amount,
                source=random.choice(['Sales', 'Investment', 'Other']),
                description=f'Income record {i}',
                currency='NGN'
            )
            
        # Seed Expense Categories
        ExpenseCategory.objects.filter(business=business).delete()
        cat_rent = ExpenseCategory.objects.create(business=business, name='Rent')
        cat_salaries = ExpenseCategory.objects.create(business=business, name='Salaries')
        cat_software = ExpenseCategory.objects.create(business=business, name='Software Subscriptions')
        cat_marketing = ExpenseCategory.objects.create(business=business, name='Marketing')
        
        # Seed Expenses
        Expense.objects.filter(business=business).delete()
        for i in range(30):
            days_ago = random.randint(1, 180)
            amount = Decimal(random.randint(50000, 1000000))
            Expense.objects.create(
                business=business, user=user, amount=amount,
                expense_category=random.choice(['Rent', 'Salaries', 'Office Supplies', 'Marketing']),
                description=f'Expense record {i}',
                currency='NGN'
            )

        # Seed Billing (Invoices & Payments)
        Invoice.objects.filter(business=business).delete()
        
        # 1. Paid Invoice
        inv1 = Invoice.objects.create(
            business=business, customer=customer1, invoice_number='INV-001',
            issue_date=today - timedelta(days=45), due_date=today - timedelta(days=15),
            status='PAID', total_amount=Decimal('1075000.00'), amount_paid=Decimal('1075000.00')
        )
        InvoiceLineItem.objects.create(invoice=inv1, description='Consulting', unit_price=Decimal('1000000.00'))
        Payment.objects.create(business=business, invoice=inv1, amount=Decimal('1075000.00'), payment_date=today - timedelta(days=10))

        # 2. Overdue Invoice (31-60 days)
        inv2 = Invoice.objects.create(
            business=business, customer=customer2, invoice_number='INV-002',
            issue_date=today - timedelta(days=90), due_date=today - timedelta(days=60),
            status='SENT', total_amount=Decimal('2500000.00')
        )
        InvoiceLineItem.objects.create(invoice=inv2, description='Software Dev', unit_price=Decimal('2325581.39'))
        
        # 3. Partially Paid / Near due
        inv3 = Invoice.objects.create(
            business=business, customer=customer1, invoice_number='INV-003',
            issue_date=today - timedelta(days=20), due_date=today + timedelta(days=10),
            status='PARTIALLY_PAID', total_amount=Decimal('500000.00'), amount_paid=Decimal('200000.00')
        )
        InvoiceLineItem.objects.create(invoice=inv3, description='Maintenance', unit_price=Decimal('465116.27'))
        Payment.objects.create(business=business, invoice=inv3, amount=Decimal('200000.00'), payment_date=today - timedelta(days=2))

        # Seed Recurring Expenses (Module 6)
        RecurringExpense.objects.filter(business=business).delete()
        RecurringExpense.objects.create(
            business=business, user=user, name='Office Rent', category=cat_rent,
            amount=Decimal('1200000.00'), frequency='ANNUALLY',
            next_due_date=today + timedelta(days=15), start_date=today - timedelta(days=350)
        )
        RecurringExpense.objects.create(
            business=business, user=user, name='AWS Hosting', category=cat_software,
            amount=Decimal('85000.00'), frequency='MONTHLY',
            next_due_date=today + timedelta(days=3), start_date=today - timedelta(days=90)
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded dummy financial data!'))
