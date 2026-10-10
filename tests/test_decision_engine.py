"""
Tests for the Marketing Incrementality decision engine.

These tests verify that:
- saved artifacts load correctly
- customer scoring returns the expected structure
- probabilities are valid
- recommendations are valid
- profit outputs are included
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
# saved artifacts should load correctly
# ---------------------------------------------------------

def test_load_artifacts():

    artifacts = load_artifacts()

    expected_keys = {
        "control_model",
        "mens_model",
        "womens_model",
        "purchase_values",
    }

    assert expected_keys.issubset(
        artifacts.keys()
    )


# ---------------------------------------------------------
# Test 2:
# score_customer should return the expected structure
# ---------------------------------------------------------

def test_score_customer_structure():

    artifacts = load_artifacts()

    result = score_customer(
        EXAMPLE_CUSTOMER,
        artifacts,
    )

    assert "conversion_probability" in result
    assert "uplift" in result
    assert "expected_spend" in result
    assert "expected_profit" in result

    assert "recommended_for_conversion" in result
    assert "recommended_for_revenue" in result
    assert "recommended_for_profit" in result


# ---------------------------------------------------------
# Test 3:
# predicted probabilities must be valid probabilities
# ---------------------------------------------------------

def test_probabilities_are_valid():

    artifacts = load_artifacts()

    result = score_customer(
        EXAMPLE_CUSTOMER,
        artifacts,
    )

    probabilities = result[
        "conversion_probability"
    ]

    for probability in probabilities.values():

        assert 0.0 <= probability <= 1.0


# ---------------------------------------------------------
# Test 4:
# all recommendations must be valid campaign actions
# ---------------------------------------------------------

def test_recommendation_is_valid():

    artifacts = load_artifacts()

    result = score_customer(
        EXAMPLE_CUSTOMER,
        artifacts,
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

    assert (
        result["recommended_for_profit"]
        in valid_actions
    )