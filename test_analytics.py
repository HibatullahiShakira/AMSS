import requests

base_url = 'http://127.0.0.1:8000'

response = requests.post(f"{base_url}/auth/jwt/create/", json={
    "username": "testuser",
    "password": "Password123!"
})

if response.status_code == 200:
    token = response.json()['access']
    headers = {"Authorization": f"Bearer {token}"}
    
    kpis = requests.get(f"{base_url}/finance/analytics/kpis/", headers=headers)
    print("KPIs status:", kpis.status_code)
    if kpis.status_code == 500:
        print(kpis.text[:1000])
    
    pnl = requests.post(f"{base_url}/finance/analytics/pnl/", json={"period": "YTD"}, headers=headers)
    print("PnL status:", pnl.status_code)
    if pnl.status_code == 500:
        print(pnl.text[:1000])
else:
    print("Login failed:", response.status_code)
