"""
Tests for the marketing decision engine.

These tests make sure the production scoring logic
continues to work when we modify the project later.
"""

import sys
from pathlib import Path


# ---------------------------------------------------------
# Allow tests to import code from src/
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


from src.decision_engine import (  # noqa: E402
    load_artifacts,
    score_customer,
)


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
# saved artifacts should load successfully
# ---------------------------------------------------------

def test_load_artifacts():

    artifacts = load_artifacts()

    assert "control_model" in artifacts
    assert "mens_model" in artifacts
    assert "womens_model" in artifacts
    assert "purchase_values" in artifacts


# ---------------------------------------------------------
# Test 2:
# scoring one customer should return all required outputs
# ---------------------------------------------------------

def test_score_customer_structure():

    artifacts = load_artifacts()

    result = score_customer(
        EXAMPLE_CUSTOMER,
        artifacts
    )

    assert "conversion_probability" in result
    assert "uplift" in result
    assert "expected_spend" in result
    assert "recommended_for_conversion" in result
    assert "recommended_for_revenue" in result


# ---------------------------------------------------------
# Test 3:
# probabilities must be valid probabilities
# ---------------------------------------------------------

def test_probabilities_are_valid():

    artifacts = load_artifacts()

    result = score_customer(
        EXAMPLE_CUSTOMER,
        artifacts
    )

    probabilities = result[
        "conversion_probability"
    ].values()

    for probability in probabilities:

        assert 0 <= probability <= 1


# ---------------------------------------------------------
# Test 4:
# recommendation must be one of our valid actions
# ---------------------------------------------------------

def test_recommendation_is_valid():

    artifacts = load_artifacts()

    result = score_customer(
        EXAMPLE_CUSTOMER,
        artifacts
    )

    valid_actions = {
        "No E-Mail",
        "Mens E-Mail",
        "Womens E-Mail",
    }

    assert (
        result["recommended_for_conversion"]
        in valid_actions
    )

    assert (
        result["recommended_for_revenue"]
        in valid_actions
    )