import requests

base_url = 'http://127.0.0.1:8000'

# 1. Login
response = requests.post(f"{base_url}/auth/jwt/create/", json={
    "username": "testuser",
    "password": "Password123!"
})
print("Login Status:", response.status_code)
if response.status_code == 200:
    token = response.json().get('access')
    
    # 2. Get Me
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = requests.get(f"{base_url}/auth/users/me/", headers=headers)
    print("Me Status:", me_resp.status_code)
    print("Me Data:", me_resp.json())
else:
    print("Login failed:", response.text)
