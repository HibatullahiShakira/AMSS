import os
import django
from django.test.client import Client

def run_tests():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AMS.settings')
    django.setup()

    # The router does not have an api/ prefix unless specified in AMS/urls.py
    # Let's check AMS/urls.py to see where finance is mounted.
    # Usually it's mounted at api/ or directly at /
    
    from django.urls import reverse
    
    client = Client()
    print("Testing Endpoints...")
    
    # We will test if the routes resolve and don't 500. 
    # Without authentication they might return 401 or 403, which is fine and proves the views exist and are protected.
    endpoints = [
        '/finance/assets/',
        '/finance/incomes/',
        '/finance/expenses/',
        '/finance/accounts/',
        '/finance/cash_flow/strategies/',
    ]
    
    for ep in endpoints:
        resp = client.get(ep)
        print(f"GET {ep} -> Status: {resp.status_code}")

if __name__ == '__main__':
    run_tests()
