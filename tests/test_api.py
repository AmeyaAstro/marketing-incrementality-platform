"""
Tests for the Marketing Incrementality FastAPI application.

These tests verify:

- health-check endpoint
- single-customer scoring
- campaign batch optimization
- request validation
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
# Create test client
# ---------------------------------------------------------

client = TestClient(app)


# ---------------------------------------------------------
# Shared single-customer example
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
# Shared batch example
# ---------------------------------------------------------

EXAMPLE_CAMPAIGN = {
    "customers": [
        {
            "recency": 3,
            "history": 250.0,
            "mens": 1,
            "womens": 0,
            "zip_code": "Urban",
            "newbie": 0,
            "channel": "Web",
        },
        {
            "recency": 6,
            "history": 120.0,
            "mens": 0,
            "womens": 1,
            "zip_code": "Suburban",
            "newbie": 1,
            "channel": "Phone",
        },
        {
            "recency": 2,
            "history": 500.0,
            "mens": 1,
            "womens": 1,
            "zip_code": "Rural",
            "newbie": 0,
            "channel": "Multichannel",
        },
    ],
    "max_emails": 2,
    "email_cost": 0.01,
    "gross_margin": 0.40,
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
# single-customer scoring endpoint should work
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
# returned single-customer recommendations must be valid
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
# invalid single-customer request should be rejected
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


# ---------------------------------------------------------
# Test 5:
# campaign optimization endpoint should work
# ---------------------------------------------------------

def test_optimize_campaign_endpoint():

    response = client.post(
        "/optimize-campaign",
        json=EXAMPLE_CAMPAIGN,
    )

    assert response.status_code == 200

    body = response.json()

    assert "summary" in body
    assert "recommendations" in body

    assert len(
        body["recommendations"]
    ) == 3


# ---------------------------------------------------------
# Test 6:
# campaign optimizer must respect max_emails
# ---------------------------------------------------------

def test_campaign_optimizer_respects_limit():

    response = client.post(
        "/optimize-campaign",
        json=EXAMPLE_CAMPAIGN,
    )

    assert response.status_code == 200

    body = response.json()

    summary = body["summary"]

    assert (
        summary["emails_selected"]
        <=
        EXAMPLE_CAMPAIGN["max_emails"]
    )


# ---------------------------------------------------------
# Test 7:
# campaign summary should include profit information
# ---------------------------------------------------------

def test_campaign_summary_contains_profit():

    response = client.post(
        "/optimize-campaign",
        json=EXAMPLE_CAMPAIGN,
    )

    assert response.status_code == 200

    summary = response.json()[
        "summary"
    ]

    assert (
        "baseline_expected_profit"
        in summary
    )

    assert (
        "optimized_expected_profit"
        in summary
    )

    assert (
        "incremental_expected_profit"
        in summary
    )