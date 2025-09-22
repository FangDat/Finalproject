import requests

# ---------------------------
# 1. Config
# ---------------------------
BASE_URL = "http://127.0.0.1:8000/"  # đổi nếu backend chạy port khác
USERNAME = "a"
PASSWORD = "D@t15112004"

# ---------------------------
# 2. Login để lấy token
# ---------------------------
login_url = f"{BASE_URL}/api/login/"
login_data = {
    "username": USERNAME,
    "password": PASSWORD
}

login_resp = requests.post(login_url, json=login_data)
if login_resp.status_code != 200:
    print("Login failed:", login_resp.status_code, login_resp.text)
    exit(1)

login_json = login_resp.json()
access_token = login_json.get("access")
if not access_token:
    print("Access token not found in login response")
    exit(1)

print("Login successful. Access token:", access_token)

# ---------------------------
# 3. Gọi API delete account
# ---------------------------
delete_url = f"{BASE_URL}/api/delete-account/"
headers = {
    "Authorization": f"Bearer {access_token}"
}
delete_data = {
    "username": USERNAME,
    "password": PASSWORD
}

delete_resp = requests.post(delete_url, json=delete_data, headers=headers)
print("\nDelete account response:")
print("Status code:", delete_resp.status_code)
try:
    print("Response body:", delete_resp.json())
except Exception:
    print("Response body (raw):", delete_resp.text)

# ---------------------------
# 4. Thử login lại sau khi xoá (nên thất bại)
# ---------------------------
login_again_resp = requests.post(login_url, json=login_data)
print("\nLogin again after delete response:")
print("Status code:", login_again_resp.status_code)
try:
    print("Response body:", login_again_resp.json())
except Exception:
    print("Response body (raw):", login_again_resp.text)

