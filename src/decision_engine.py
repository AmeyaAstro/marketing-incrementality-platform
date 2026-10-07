"""
Decision engine for the Marketing Incrementality Platform.

This module:

1. Loads the trained treatment models.
2. Scores a customer under:
   - No E-Mail
   - Mens E-Mail
   - Womens E-Mail
3. Estimates treatment uplift.
4. Estimates expected spend.
5. Recommends the best campaign action for:
   - conversion
   - revenue
"""

from pathlib import Path

import joblib
import pandas as pd


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------
#
# __file__ points to:
#
# marketing-incrementality-platform/src/decision_engine.py
#
# .parent gives:
# marketing-incrementality-platform/src
#
# .parent.parent gives:
# marketing-incrementality-platform
#
# This is safer than relying on the terminal's
# current working directory.

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"


# ---------------------------------------------------------
# Saved artifact paths
# ---------------------------------------------------------

CONTROL_MODEL_PATH = (
    ARTIFACTS_DIR / "control_conversion_model.joblib"
)

MENS_MODEL_PATH = (
    ARTIFACTS_DIR / "mens_conversion_model.joblib"
)

WOMENS_MODEL_PATH = (
    ARTIFACTS_DIR / "womens_conversion_model.joblib"
)

PURCHASE_VALUES_PATH = (
    ARTIFACTS_DIR / "purchase_value_summary.csv"
)


# ---------------------------------------------------------
# Load saved artifacts
# ---------------------------------------------------------

def load_artifacts():
    """
    Load the three trained treatment models and the
    training-only purchase-value summary.

    Returns
    -------
    dict
        Dictionary containing the models and purchase values.
    """

    control_model = joblib.load(
        CONTROL_MODEL_PATH
    )

    mens_model = joblib.load(
        MENS_MODEL_PATH
    )

    womens_model = joblib.load(
        WOMENS_MODEL_PATH
    )

    purchase_values = pd.read_csv(
        PURCHASE_VALUES_PATH
    )

    return {
        "control_model": control_model,
        "mens_model": mens_model,
        "womens_model": womens_model,
        "purchase_values": purchase_values,
    }


# ---------------------------------------------------------
# Score one customer
# ---------------------------------------------------------

def score_customer(customer_data, artifacts):
    """
    Score one customer under all three possible campaign actions.

    Parameters
    ----------
    customer_data : dict
        Customer features using the same columns used
        during model training.

    artifacts : dict
        Dictionary returned by load_artifacts().

    Returns
    -------
    dict
        Predicted conversion probabilities,
        uplift estimates,
        expected spend values,
        and recommended actions.
    """

    # -----------------------------------------------------
    # Convert the customer dictionary into a 1-row DataFrame
    # -----------------------------------------------------
    #
    # scikit-learn expects tabular data with column names.
    #
    # Example:
    #
    # {
    #     "recency": 3,
    #     "history": 250.0,
    #     ...
    # }
    #
    # becomes a one-row table.

    customer_df = pd.DataFrame(
        [customer_data]
    )


    # -----------------------------------------------------
    # Get trained models
    # -----------------------------------------------------

    control_model = artifacts["control_model"]

    mens_model = artifacts["mens_model"]

    womens_model = artifacts["womens_model"]


    # -----------------------------------------------------
    # Predict conversion probability under each action
    # -----------------------------------------------------
    #
    # [:, 1] would mean:
    # probability of class 1 = conversion.
    #
    # Because we only have one row, we use [0, 1].

    prob_no_email = control_model.predict_proba(
        customer_df
    )[0, 1]

    prob_mens_email = mens_model.predict_proba(
        customer_df
    )[0, 1]

    prob_womens_email = womens_model.predict_proba(
        customer_df
    )[0, 1]


    # -----------------------------------------------------
    # Estimate uplift relative to No E-Mail
    # -----------------------------------------------------
    #
    # Men's uplift =
    # probability with Men's Email
    # -
    # probability with No Email

    mens_uplift = (
        prob_mens_email
        -
        prob_no_email
    )

    womens_uplift = (
        prob_womens_email
        -
        prob_no_email
    )


    # -----------------------------------------------------
    # Load average purchase amounts
    # -----------------------------------------------------
    #
    # These values were calculated using the training data.
    #
    # They tell us:
    #
    # "If somebody converts under this treatment,
    # how much did converters spend on average?"

    purchase_values = artifacts[
        "purchase_values"
    ]

    avg_purchase_no_email = purchase_values.loc[
        purchase_values["treatment"]
        ==
        "No E-Mail",
        "avg_purchase_amount_given_purchase"
    ].iloc[0]

    avg_purchase_mens = purchase_values.loc[
        purchase_values["treatment"]
        ==
        "Mens E-Mail",
        "avg_purchase_amount_given_purchase"
    ].iloc[0]

    avg_purchase_womens = purchase_values.loc[
        purchase_values["treatment"]
        ==
        "Womens E-Mail",
        "avg_purchase_amount_given_purchase"
    ].iloc[0]


    # -----------------------------------------------------
    # Estimate expected spend under each treatment
    # -----------------------------------------------------
    #
    # Expected Spend =
    #
    # probability of conversion
    # ×
    # average purchase amount if conversion occurs

    expected_spend_no_email = (
        prob_no_email
        *
        avg_purchase_no_email
    )

    expected_spend_mens_email = (
        prob_mens_email
        *
        avg_purchase_mens
    )

    expected_spend_womens_email = (
        prob_womens_email
        *
        avg_purchase_womens
    )


    # -----------------------------------------------------
    # Choose the best action for conversion
    # -----------------------------------------------------

    conversion_values = {
        "No E-Mail": prob_no_email,
        "Mens E-Mail": prob_mens_email,
        "Womens E-Mail": prob_womens_email,
    }

    recommended_for_conversion = max(
        conversion_values,
        key=conversion_values.get
    )


    # -----------------------------------------------------
    # Choose the best action for expected revenue
    # -----------------------------------------------------

    revenue_values = {
        "No E-Mail": expected_spend_no_email,
        "Mens E-Mail": expected_spend_mens_email,
        "Womens E-Mail": expected_spend_womens_email,
    }

    recommended_for_revenue = max(
        revenue_values,
        key=revenue_values.get
    )


    # -----------------------------------------------------
    # Return a clean result dictionary
    # -----------------------------------------------------

    return {
        "conversion_probability": {
            "No E-Mail": float(
                prob_no_email
            ),
            "Mens E-Mail": float(
                prob_mens_email
            ),
            "Womens E-Mail": float(
                prob_womens_email
            ),
        },

        "uplift": {
            "Mens E-Mail": float(
                mens_uplift
            ),
            "Womens E-Mail": float(
                womens_uplift
            ),
        },

        "expected_spend": {
            "No E-Mail": float(
                expected_spend_no_email
            ),
            "Mens E-Mail": float(
                expected_spend_mens_email
            ),
            "Womens E-Mail": float(
                expected_spend_womens_email
            ),
        },

        "recommended_for_conversion":
            recommended_for_conversion,

        "recommended_for_revenue":
            recommended_for_revenue,
    }


# ---------------------------------------------------------
# Simple test when this file is run directly
# ---------------------------------------------------------

if __name__ == "__main__":

    # Load the saved models and purchase-value summary.
    artifacts = load_artifacts()

    print(
        "Artifacts loaded successfully."
    )


    # -----------------------------------------------------
    # Example customer
    # -----------------------------------------------------
    #
    # This is just a fake test customer used to verify
    # that the production decision engine works end-to-end.

    example_customer = {
        "recency": 3,
        "history": 250.0,
        "mens": 1,
        "womens": 0,
        "zip_code": "Urban",
        "newbie": 0,
        "channel": "Web",
        "purchase_preference": "Mens Only",
    }


    # Score the customer.
    result = score_customer(
        example_customer,
        artifacts
    )


    # Show the recommendation.
    print(
        "\nCustomer recommendation:"
    )

    print(result)