"""
Tests for batch customer scoring and
budget-constrained campaign optimization.
"""
from src.batch_optimizer import (  # noqa: E402
    derive_purchase_preference,
    optimize_campaign_budget,
    optimize_email_budget,
    score_customer_batch,
)
import sys
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Allow imports from project root
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


from src.batch_optimizer import (  # noqa: E402
    derive_purchase_preference,
    optimize_email_budget,
    score_customer_batch,
)
from src.decision_engine import load_artifacts  # noqa: E402


# ---------------------------------------------------------
# Shared test batch
# ---------------------------------------------------------

TEST_CUSTOMERS = pd.DataFrame(
    [
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
    ]
)


# ---------------------------------------------------------
# Test 1:
# purchase preference derivation
# ---------------------------------------------------------

def test_derive_purchase_preference():

    assert (
        derive_purchase_preference(1, 0)
        ==
        "Mens Only"
    )

    assert (
        derive_purchase_preference(0, 1)
        ==
        "Womens Only"
    )

    assert (
        derive_purchase_preference(1, 1)
        ==
        "Both"
    )

    assert (
        derive_purchase_preference(0, 0)
        is None
    )


# ---------------------------------------------------------
# Test 2:
# batch scoring should return one row per customer
# ---------------------------------------------------------

def test_score_customer_batch():

    artifacts = load_artifacts()

    scored = score_customer_batch(
        TEST_CUSTOMERS,
        artifacts,
        email_cost=0.01,
        gross_margin=0.40,
    )

    assert len(scored) == 3

    assert "best_email_action" in scored.columns
    assert "incremental_profit" in scored.columns

    assert (
        scored["incremental_profit"]
        .notna()
        .all()
    )


# ---------------------------------------------------------
# Test 3:
# optimizer must respect the email limit
# ---------------------------------------------------------

def test_optimize_email_budget_respects_limit():

    artifacts = load_artifacts()

    scored = score_customer_batch(
        TEST_CUSTOMERS,
        artifacts,
    )

    result = optimize_email_budget(
        scored,
        max_emails=1,
    )

    recommendations = result[
        "recommendations"
    ]

    summary = result[
        "summary"
    ]

    assert (
        summary["emails_selected"]
        <=
        1
    )

    assert (
        recommendations[
            "selected_for_campaign"
        ].sum()
        <=
        1
    )


# ---------------------------------------------------------
# Test 4:
# selected customers must have positive incremental profit
# ---------------------------------------------------------

def test_selected_customers_have_positive_profit():

    artifacts = load_artifacts()

    scored = score_customer_batch(
        TEST_CUSTOMERS,
        artifacts,
    )

    result = optimize_email_budget(
        scored,
        max_emails=3,
    )

    selected = result[
        "recommendations"
    ]

    selected = selected[
        selected["selected_for_campaign"]
    ]

    if not selected.empty:

        assert (
            selected["incremental_profit"]
            >
            0
        ).all()


# ---------------------------------------------------------
# Test 5:
# invalid unsupported customer should be rejected
# ---------------------------------------------------------

def test_invalid_purchase_history_is_rejected():

    artifacts = load_artifacts()

    invalid_batch = pd.DataFrame(
        [
            {
                "recency": 3,
                "history": 50.0,
                "mens": 0,
                "womens": 0,
                "zip_code": "Urban",
                "newbie": 1,
                "channel": "Web",
            }
        ]
    )

    try:

        score_customer_batch(
            invalid_batch,
            artifacts,
        )

    except ValueError as error:

        assert (
            "outside the model's training data"
            in str(error)
        )

    else:

        raise AssertionError(
            "Expected ValueError was not raised."
        )

# ---------------------------------------------------------
# Test 6:
# dollar budget should limit campaign spending
# ---------------------------------------------------------

def test_campaign_budget_respects_dollar_limit():

    artifacts = load_artifacts()

    scored = score_customer_batch(
        TEST_CUSTOMERS,
        artifacts,
        email_cost=0.50,
        gross_margin=0.40,
    )

    result = optimize_campaign_budget(
        scored,
        campaign_budget=1.00,
        email_cost=0.50,
    )

    summary = result[
        "summary"
    ]

    assert (
        summary["campaign_spend"]
        <=
        summary["campaign_budget"]
    )

    assert (
        summary["max_affordable_emails"]
        ==
        2
    )


# ---------------------------------------------------------
# Test 7:
# zero-dollar budget should select no paid emails
# ---------------------------------------------------------

def test_zero_campaign_budget():

    artifacts = load_artifacts()

    scored = score_customer_batch(
        TEST_CUSTOMERS,
        artifacts,
        email_cost=0.50,
        gross_margin=0.40,
    )

    result = optimize_campaign_budget(
        scored,
        campaign_budget=0.0,
        email_cost=0.50,
    )

    summary = result[
        "summary"
    ]

    assert (
        summary["emails_selected"]
        ==
        0
    )

    assert (
        summary["campaign_spend"]
        ==
        0.0
    )


# ---------------------------------------------------------
# Test 8:
# free email should not be restricted by dollar budget
# ---------------------------------------------------------

def test_zero_email_cost():

    artifacts = load_artifacts()

    scored = score_customer_batch(
        TEST_CUSTOMERS,
        artifacts,
        email_cost=0.0,
        gross_margin=0.40,
    )

    result = optimize_campaign_budget(
        scored,
        campaign_budget=0.0,
        email_cost=0.0,
    )

    summary = result[
        "summary"
    ]

    assert (
        summary["max_affordable_emails"]
        ==
        len(TEST_CUSTOMERS)
    )

    assert (
        summary["campaign_spend"]
        ==
        0.0
    )