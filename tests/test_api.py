"""
Tests for the Marketing Incrementality FastAPI application.

These tests make sure the HTTP API correctly exposes
the production decision engine.
"""

import sys
from pathlib import Path


# ---------------------------------------------------------
# Allow tests to import code from the project root
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


from fastapi.testclient import TestClient  # noqa: E402
from api.main import app  # noqa: E402


# ---------------------------------------------------------
# Create a test client
# ---------------------------------------------------------

client = TestClient(app)


# ---------------------------------------------------------
# Shared example customer
# ---------------------------------------------------------

EXAMPLE_CUSTOMER = {
    "recency": 3,
    "history": 250.0,
    "mens": 1,
    "womens": 0,
    "zip_code": "Urban",
    "newbie": 0,
    "channel": "Web",
    "purchase_preference": "Mens Only",
}


# ---------------------------------------------------------
# Test 1:
# health-check endpoint should work
# ---------------------------------------------------------

def test_root_endpoint():

    response = client.get("/")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"


# ---------------------------------------------------------
# Test 2:
# scoring endpoint should return a valid response
# ---------------------------------------------------------

def test_score_customer_endpoint():

    response = client.post(
        "/score-customer",
        json=EXAMPLE_CUSTOMER,
    )

    assert response.status_code == 200

    body = response.json()

    assert "conversion_probability" in body
    assert "uplift" in body
    assert "expected_spend" in body
    assert "expected_profit" in body

    assert "recommended_for_conversion" in body
    assert "recommended_for_revenue" in body
    assert "recommended_for_profit" in body


# ---------------------------------------------------------
# Test 3:
# returned recommendations must be valid actions
# ---------------------------------------------------------

def test_api_recommendations_are_valid():

    response = client.post(
        "/score-customer",
        json=EXAMPLE_CUSTOMER,
    )

    assert response.status_code == 200

    body = response.json()

    valid_actions = {
        "No E-Mail",
        "Mens E-Mail",
        "Womens E-Mail",
    }

    assert (
        body["recommended_for_conversion"]
        in valid_actions
    )

    assert (
        body["recommended_for_revenue"]
        in valid_actions
    )

    assert (
        body["recommended_for_profit"]
        in valid_actions
    )


# ---------------------------------------------------------
# Test 4:
# invalid requests should be rejected automatically
# ---------------------------------------------------------

def test_invalid_customer_request():

    invalid_customer = {
        "recency": 3
    }

    response = client.post(
        "/score-customer",
        json=invalid_customer,
    )

    assert response.status_code == 422