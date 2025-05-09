import requests

BASE_URL = "https://serve-eqs0.onrender.com/"
ADMIN_PASSWORD = "my_secret_password"
TEST_UID = "test_user_1"

def generate_redemption_code():
    url = f"{BASE_URL}/generate_code"
    response = requests.post(url, json={"password": ADMIN_PASSWORD})
    if response.status_code == 200:
        code = response.json()["redemption_code"]
        print(f"[✓] Redemption code generated: {code}")
        return code
    else:
        print("[✗] Failed to generate code:", response.json())
        return None

def register_user(uid, code):
    url = f"{BASE_URL}/register_with_code"
    response = requests.post(url, json={"uid": uid, "code": code})
    if response.status_code == 200:
        data = response.json()
        print(f"[✓] User registered. Access token: {data['access_token']}")
        return data["access_token"]
    else:
        print("[✗] Registration failed:", response.json())
        return None

def get_tokens(uid):
    url = f"{BASE_URL}/get_tokens?uid={uid}"
    response = requests.get(url)
    if response.status_code == 200:
        tokens = response.json()["tokens"]
        print(f"[✓] User '{uid}' has {tokens} tokens.")
    else:
        print("[✗] Failed to get tokens:", response.json())

# === Workflow ===

print("=== Starting client test ===")
code = generate_redemption_code()
if code:
    token = register_user(TEST_UID, code)
    if token:
        get_tokens(TEST_UID)
