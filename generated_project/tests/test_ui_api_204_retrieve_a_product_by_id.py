import os
import pytest

pytestmark = pytest.mark.ui

# AC1: GET /products/1 returns HTTP 200.
# AC2: The response is JSON and contains id, title, and price.
# AC3: An unknown product ID returns HTTP 404.
def test_api_204_retrieve_a_product_by_id(page):
    base_url = os.getenv("TARGET_WEB_URL")
    if not base_url:
        pytest.skip("Set TARGET_WEB_URL after reviewing selectors and test steps")
    page.goto(f"{base_url.rstrip('/')}/products/1")
    expect_text = 'Retrieve a product by ID'
    assert page.locator("body").is_visible()
    # Replace this broad assertion with a stable product selector after review.
    assert expect_text.lower() in page.locator("body").inner_text().lower()
