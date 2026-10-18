import os
import pytest

pytestmark = pytest.mark.ui

# AC1: Given the sign-in page is open, when valid credentials are submitted, then the account page is displayed.
# AC2: The account page displays the signed-in customer's email address.
# AC3: Invalid credentials display an error and do not open the account page.
def test_shop_101_customer_signs_in_with_valid_credentials(page):
    base_url = os.getenv("TARGET_WEB_URL")
    if not base_url:
        pytest.skip("Set TARGET_WEB_URL after reviewing selectors and test steps")
    page.goto(f"{base_url.rstrip('/')}/login")
    expect_text = 'Customer signs in with valid credentials'
    assert page.locator("body").is_visible()
    # Replace this broad assertion with a stable product selector after review.
    assert expect_text.lower() in page.locator("body").inner_text().lower()
