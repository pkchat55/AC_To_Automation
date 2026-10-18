import os
import requests

# AC1: GET /products/1 returns HTTP 200.
# AC2: The response is JSON and contains id, title, and price.
# AC3: An unknown product ID returns HTTP 404.
def test_api_204_retrieve_a_product_by_id():
    base_url = os.getenv("TARGET_API_URL", "https://dummyjson.com").rstrip("/")
    response = requests.get(f"{base_url}/products/1", timeout=15)
    assert response.status_code == 200, response.text[:500]
    assert "application/json" in response.headers.get("content-type", "")
    payload = response.json()
    assert 'id' in payload
    assert 'title' in payload
    assert 'price' in payload
