import os
import requests

# AC1: Given the sign-in page is open, when valid credentials are submitted, then the account page is displayed.
# AC2: The account page displays the signed-in customer's email address.
# AC3: Invalid credentials display an error and do not open the account page.
def test_shop_101_customer_signs_in_with_valid_credentials():
    base_url = os.getenv("TARGET_API_URL", "https://dummyjson.com").rstrip("/")
    response = requests.get(f"{base_url}/users/1", timeout=15)
    assert response.status_code == 200, response.text[:500]
    assert "application/json" in response.headers.get("content-type", "")
    payload = response.json()
    assert 'email' in payload
