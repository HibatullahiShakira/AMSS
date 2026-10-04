import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AMS.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Business
from finance.models import Customer, Expense, Income, Asset
from billing.models import Invoice, InvoiceLineItem, Payment

User = get_user_model()

def run():
    print("Starting database seed...")

    # 1. Create User
    email = "testuser@amss.ng"
    password = "Password123!"
    
    user = User.objects.filter(username="testuser").first()
    if user:
        print(f"User {email} already exists. Reusing.")
        user.email = email
        user.set_password(password)
        user.save()
    else:
        user = User.objects.create_user(
            username="testuser",
            email=email,
            password=password,
            first_name="Chinedu",
            last_name="Okafor"
        )
        print(f"Created User: {email} / {password}")

    # 2. Create Business
    b_name = "Lagos Tech Innovations Ltd"
    business = Business.objects.filter(business_name=b_name).first()
    if not business:
        business = Business.objects.create(
            user=user,
            business_name=b_name,
            business_address="14 Victoria Island, Lagos, Nigeria",
            business_type="LLC",
            preferred_currency="NGN",
            industry="Software Development",
            business_email="contact@lagostech.ng"
        )
        user.business = business
        user.save()
        print(f"Created Business: {b_name}")

    # 3. Create Customers
    customer_data = [
        {"name": "Dangote Group", "contact_info": "procurement@dangote.com, +2348000000001"},
        {"name": "MTN Nigeria", "contact_info": "vendor@mtn.ng, +2348000000002"},
        {"name": "Zenith Bank Plc", "contact_info": "finance@zenithbank.com, +2348000000003"},
        {"name": "Jumia Nigeria", "contact_info": "accounts@jumia.com.ng, +2348000000004"},
        {"name": "Flutterwave", "contact_info": "billing@flutterwavego.com, +2348000000005"}
    ]
    
    customers = []
    for c_data in customer_data:
        cust, created = Customer.objects.get_or_create(
            name=c_data["name"],
            defaults={"contact_info": c_data["contact_info"], "business": business, "user": user}
        )
        customers.append(cust)
    print(f"Created {len(customers)} Customers.")

    # Dates calculation (last 24 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2 * 365)
    
    def random_date(start, end):
        return start + timedelta(days=random.randint(0, int((end - start).days)))

    # 4. Generate Expenses & Income (Past 24 months)
    categories = ['Rent', 'Utilities', 'Salaries', 'Office Supplies', 'Travel', 'Marketing', 'Maintenance', 'Miscellaneous']
    
    expenses_created = 0
    incomes_created = 0
    
    for i in range(120): # 120 expenses over 2 years
        dt = random_date(start_date, end_date)
        cat = random.choice(categories)
        amount = Decimal(random.randint(50000, 1500000))
        
        # Diesel/Generator is expensive in Nigeria
        if cat == 'Utilities':
            desc = f"Monthly Diesel Supply (500 Liters) #{i}"
            amount = Decimal(random.randint(400000, 700000))
        elif cat == 'Salaries':
            desc = f"Monthly Staff Payroll #{i}"
            amount = Decimal(random.randint(1500000, 3000000))
        else:
            desc = f"{cat} expenses for {dt.strftime('%B %Y')} #{i}"
            
        exp = Expense.objects.create(
            amount=amount,
            expense_category=cat,
            description=desc,
            currency="NGN",
            business=business,
            user=user
        )
        # Fix auto_now_add
        Expense.objects.filter(pk=exp.pk).update(date=dt)
        expenses_created += 1

    for i in range(60): # 60 income records over 2 years
        dt = random_date(start_date, end_date)
        amount = Decimal(random.randint(2000000, 8000000))
        inc = Income.objects.create(
            amount=amount,
            source='Sales',
            description=f"Software Consulting Services - {dt.strftime('%B')} #{i}",
            currency="NGN",
            business=business,
            user=user
        )
        Income.objects.filter(pk=inc.pk).update(date=dt)
        incomes_created += 1
        
    print(f"Created {expenses_created} Expenses and {incomes_created} Incomes.")

    # 5. Generate Invoices
    services = ["API Integration", "Web App Development", "Cloud Migration", "Cybersecurity Audit", "Monthly Retainer"]
    statuses = ['PAID', 'PAID', 'PAID', 'SENT', 'OVERDUE', 'DRAFT']
    
    invoices_created = 0
    for i in range(40):
        c = random.choice(customers)
        issue = random_date(start_date, end_date)
        due = issue + timedelta(days=30)
        status = random.choice(statuses)
        
        # Override overdue if due is in future
        if due > end_date and status == 'OVERDUE':
            status = 'SENT'
        # Override sent if past due by a lot
        if due < (end_date - timedelta(days=10)) and status == 'SENT':
            status = 'OVERDUE'
            
        inv = Invoice.objects.create(
            business=business,
            customer=c,
            invoice_number=f"INV-{issue.strftime('%Y%m')}-{i:04d}",
            issue_date=issue.date(),
            due_date=due.date(),
            currency="NGN",
            status=status,
            notes="Thank you for your business."
        )
        
        # Line Items
        num_items = random.randint(1, 4)
        for _ in range(num_items):
            InvoiceLineItem.objects.create(
                invoice=inv,
                description=random.choice(services),
                quantity=random.randint(1, 5),
                unit_price=Decimal(random.randint(500000, 2000000)),
                tax_rate=Decimal("7.50")
            )
        
        # If paid, add a payment
        if status == 'PAID':
            inv.refresh_from_db() # calculate totals
            Payment.objects.create(
                invoice=inv,
                business=business,
                amount=inv.total_amount,
                payment_date=issue.date(),
                payment_method='BANK_TRANSFER',
                reference=f"TRX-{random.randint(10000, 99999)}"
            )
            
        invoices_created += 1
        
    print(f"Created {invoices_created} Invoices.")
    
    print("\n--- SEED COMPLETE ---")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print("---------------------\n")

if __name__ == '__main__':
    run()
