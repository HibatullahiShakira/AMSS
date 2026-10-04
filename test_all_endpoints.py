# -*- coding: utf-8 -*-
"""Full sweep: test every API endpoint that the frontend calls."""
import requests, json, sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'

BASE = 'http://127.0.0.1:8000'

# 1. LOGIN
print("=" * 60)
print("1. LOGIN")
r = requests.post(f"{BASE}/auth/jwt/create/", json={
    "username": "testuser", "password": "Password123!"
})
print(f"   POST /auth/jwt/create/ => {r.status_code}")
if r.status_code != 200:
    print(f"   FAIL: {r.text}")
    sys.exit(1)
token = r.json()['access']
H = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# 2. USER ME
print("2. USER /auth/users/me/")
r = requests.get(f"{BASE}/auth/users/me/", headers=H)
print(f"   GET /auth/users/me/ => {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   user: {data.get('username')}, business: {data.get('business')}")
    if not data.get('business'):
        print("   WARNING: 'business' field missing from /users/me/ -- frontend will redirect to onboarding!")
else:
    print(f"   FAIL: {r.text[:200]}")

# 3. DASHBOARD - KPIs
print("3. DASHBOARD KPIs")
r = requests.get(f"{BASE}/finance/analytics/kpis/", headers=H)
print(f"   GET /finance/analytics/kpis/ => {r.status_code}")
if r.status_code == 200:
    try:
        data = json.loads(r.text)
        print(f"   cash={data['liquidity']['current_cash']}, margin={data['profitability']['net_margin_pct']:.1f}%")
    except Exception as e:
        print(f"   JSON PARSE FAIL: {e}")
        print(f"   Raw: {r.text[:200]}")
else:
    print(f"   FAIL: {r.text[:200]}")

# 4. DASHBOARD - PnL
print("4. DASHBOARD PnL")
r = requests.post(f"{BASE}/finance/analytics/pnl/", headers=H, json={"period": "YTD"})
print(f"   POST /finance/analytics/pnl/ => {r.status_code}")
if r.status_code == 200:
    try:
        data = json.loads(r.text)
        print(f"   revenue={data['revenue']['total']}, net_profit={data['net_profit']}")
    except Exception as e:
        print(f"   JSON PARSE FAIL: {e}")
else:
    print(f"   FAIL: {r.text[:200]}")

# 5. BILLING - Invoices list
print("5. BILLING - Invoices")
r = requests.get(f"{BASE}/billing/invoices/", headers=H)
print(f"   GET /billing/invoices/ => {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   Invoice count: {len(data)}")
else:
    print(f"   FAIL: {r.text[:200]}")

# 6. BILLING - AR Aging
print("6. BILLING - AR Aging Report")
r = requests.get(f"{BASE}/billing/ar-aging/report/", headers=H)
print(f"   GET /billing/ar-aging/report/ => {r.status_code}")
if r.status_code == 200:
    try:
        data = json.loads(r.text)
        print(f"   total_outstanding={data.get('total_outstanding')}")
        has_buckets = 'buckets' in data
        has_aging_buckets = 'aging_buckets' in data
        print(f"   Backend keys: {list(data.keys())}")
        if has_buckets and not has_aging_buckets:
            print("   ** MISMATCH: Backend returns 'buckets' (list), but frontend expects 'aging_buckets' (dict) **")
    except Exception as e:
        print(f"   JSON PARSE FAIL: {e}")
else:
    print(f"   FAIL: {r.text[:200]}")

# 7. EXPENSES - List
print("7. EXPENSES - List")
r = requests.get(f"{BASE}/finance/expenses/", headers=H)
print(f"   GET /finance/expenses/ => {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   Expense count: {len(data)}")
    if len(data) > 0:
        print(f"   First expense fields: {list(data[0].keys())}")
else:
    print(f"   FAIL: {r.text[:200]}")

# 8. EXPENSE INTELLIGENCE - Anomalies
print("8. EXPENSE INTELLIGENCE - Anomalies")
r = requests.get(f"{BASE}/finance/expense-intelligence/anomalies/", headers=H)
print(f"   GET /finance/expense-intelligence/anomalies/ => {r.status_code}")
if r.status_code == 200:
    try:
        data = json.loads(r.text)
        print(f"   anomaly_count: {data.get('anomaly_count')}")
    except Exception as e:
        print(f"   JSON PARSE FAIL: {e}")
else:
    print(f"   FAIL: {r.text[:200]}")

# 9. EXPENSE INTELLIGENCE - Breakdown
print("9. EXPENSE INTELLIGENCE - Breakdown")
r = requests.get(f"{BASE}/finance/expense-intelligence/breakdown/", headers=H)
print(f"   GET /finance/expense-intelligence/breakdown/ => {r.status_code}")
if r.status_code == 200:
    try:
        data = json.loads(r.text)
        print(f"   categories: {list(data.get('by_category', {}).keys())[:5]}")
        print(f"   total_expenses: {data.get('total_expenses')}")
    except Exception as e:
        print(f"   JSON PARSE FAIL: {e}")
else:
    print(f"   FAIL: {r.text[:200]}")

# 10. REMINDERS - Summary
print("10. REMINDERS - Summary")
r = requests.get(f"{BASE}/finance/reminders/summary/", headers=H)
print(f"   GET /finance/reminders/summary/ => {r.status_code}")
if r.status_code == 200:
    try:
        data = json.loads(r.text)
        print(f"   total: {data.get('total')}, total_upcoming_obligations: {data.get('total_upcoming_obligations')}")
    except Exception as e:
        print(f"   JSON PARSE FAIL: {e}")
else:
    print(f"   FAIL: {r.text[:200]}")

# 11. CUSTOMERS - List (used by InvoiceModal)
print("11. CUSTOMERS - List")
r = requests.get(f"{BASE}/finance/customers/", headers=H)
print(f"   GET /finance/customers/ => {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   Customer count: {len(data)}")
    if len(data) > 0:
        print(f"   First customer fields: {list(data[0].keys())}")
        has_email = 'email' in data[0]
        has_contact = 'contact_info' in data[0]
        if has_contact and not has_email:
            print("   ** MISMATCH: Model has 'contact_info' but CustomerModal sends 'email', 'phone', 'address' **")
else:
    print(f"   FAIL: {r.text[:200]}")

# 12. Test creating a customer with the fields the frontend sends
print("12. CREATE CUSTOMER (frontend payload test)")
r = requests.post(f"{BASE}/finance/customers/", headers=H, json={
    "name": "Test Customer API",
    "email": "test@example.com",
    "phone": "+2341234567890",
    "address": "123 Test Street, Lagos"
})
print(f"   POST /finance/customers/ => {r.status_code}")
if r.status_code in (200, 201):
    print(f"   Success")
else:
    print(f"   FAIL: {r.text[:300]}")

# 13. Test creating expense with frontend payload
print("13. CREATE EXPENSE (frontend payload test)")
r = requests.post(f"{BASE}/finance/expenses/", headers=H, json={
    "amount": 15000.00,
    "expense_category": "Miscellaneous",
    "description": "Test sweep expense",
    "currency": "NGN"
})
print(f"   POST /finance/expenses/ => {r.status_code}")
if r.status_code in (200, 201):
    print(f"   Success")
else:
    print(f"   FAIL: {r.text[:300]}")

print("\n" + "=" * 60)
print("SWEEP COMPLETE")
