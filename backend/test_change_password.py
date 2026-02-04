import requests

# ---------------------------
# 1. Config
# ---------------------------
BASE_URL = "localhost:8000/"  # đổi nếu backend chạy trên port khác
USERNAME = "a"
PASSWORD = "D@t15112005"

# Mật khẩu mới để test
NEW_PASSWORD = "D@t15112004"
CONFIRM_PASSWORD = "D@t15112004"

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
# 3. Gọi API change password
# ---------------------------
change_pw_url = f"{BASE_URL}/api/change-password/"
headers = {
    "Authorization": f"Bearer {access_token}"
}
change_pw_data = {
    "current_password": PASSWORD,
    "new_password": NEW_PASSWORD,
    "confirm_password": CONFIRM_PASSWORD
}

change_resp = requests.post(
    change_pw_url, json=change_pw_data, headers=headers)
print("\nChange password response:")
print("Status code:", change_resp.status_code)
print("Response body:", change_resp.json())

# ---------------------------
# 4. Kiểm tra login lại với mật khẩu mới
# ---------------------------
login_new_data = {
    "username": USERNAME,
    "password": NEW_PASSWORD
}
login_new_resp = requests.post(login_url, json=login_new_data)
print("\nLogin with new password response:")
print("Status code:", login_new_resp.status_code)
print("Response body:", login_new_resp.json())
