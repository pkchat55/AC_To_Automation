from .models import Requirement


def demo_requirements() -> list[Requirement]:
    return [
        Requirement(
            source="Demo",
            key="SHOP-101",
            title="Customer signs in with valid credentials",
            description="A registered customer needs access to their account.",
            acceptance_criteria=[
                "Given the sign-in page is open, when valid credentials are submitted, then the account page is displayed.",
                "The account page displays the signed-in customer's email address.",
                "Invalid credentials display an error and do not open the account page.",
            ],
            metadata={
                "ui_path": "/login",
                "api_path": "/users/1",
                "expected_status": 200,
            },
        ),
        Requirement(
            source="Demo",
            key="API-204",
            title="Retrieve a product by ID",
            description="Consumers can retrieve an available product through the API.",
            acceptance_criteria=[
                "GET /products/1 returns HTTP 200.",
                "The response is JSON and contains id, title, and price.",
                "An unknown product ID returns HTTP 404.",
            ],
            metadata={
                "ui_path": "/products/1",
                "api_path": "/products/1",
                "expected_status": 200,
            },
        ),
    ]
