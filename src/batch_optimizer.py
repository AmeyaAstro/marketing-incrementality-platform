"""
Batch scoring and budget-constrained campaign optimization.

This module takes many customers, scores each customer under
all three possible actions, and decides who should receive an
email when the company cannot contact everyone.

The optimization objective is incremental expected profit.
"""

import pandas as pd
from decimal import Decimal
from src.decision_engine import score_customer


# ---------------------------------------------------------
# Required customer columns
# ---------------------------------------------------------

REQUIRED_COLUMNS = {
    "recency",
    "history",
    "mens",
    "womens",
    "zip_code",
    "newbie",
    "channel",
}


# ---------------------------------------------------------
# Derive purchase preference
# ---------------------------------------------------------

def derive_purchase_preference(
    mens,
    womens,
):
    """
    Derive the purchase-preference feature used by the models.

    The original model supports:

    - Mens Only
    - Womens Only
    - Both

    Customers with neither purchase category are outside
    the model's training support.
    """

    if mens == 1 and womens == 1:
        return "Both"

    if mens == 1:
        return "Mens Only"

    if womens == 1:
        return "Womens Only"

    return None


# ---------------------------------------------------------
# Validate batch input
# ---------------------------------------------------------

def validate_customer_batch(
    customers_df,
):
    """
    Validate the incoming customer DataFrame.
    """

    missing_columns = (
        REQUIRED_COLUMNS
        -
        set(customers_df.columns)
    )

    if missing_columns:

        missing_text = ", ".join(
            sorted(missing_columns)
        )

        raise ValueError(
            f"Missing required columns: {missing_text}"
        )

    if customers_df.empty:

        raise ValueError(
            "Customer batch cannot be empty."
        )


# ---------------------------------------------------------
# Score many customers
# ---------------------------------------------------------

def score_customer_batch(
    customers_df,
    artifacts,
    email_cost=0.01,
    gross_margin=0.40,
):
    """
    Score every customer under all campaign actions.

    Returns
    -------
    pandas.DataFrame
        One row per valid customer containing:

        - predicted conversion probabilities
        - expected revenue
        - expected profit
        - best email treatment
        - incremental expected profit
    """

    validate_customer_batch(
        customers_df
    )

    results = []


    # -----------------------------------------------------
    # Score customers one at a time
    # -----------------------------------------------------

    for row_number, (_, row) in enumerate(
        customers_df.iterrows(),
        start=1,
    ):

        purchase_preference = (
            derive_purchase_preference(
                row["mens"],
                row["womens"],
            )
        )


        # -------------------------------------------------
        # Reject unsupported customer profiles
        # -------------------------------------------------

        if purchase_preference is None:

            raise ValueError(
                "Customer at batch row "
                f"{row_number} has neither men's nor "
                "women's historical purchases. "
                "This profile is outside the model's "
                "training data."
            )


        # -------------------------------------------------
        # Build model input
        # -------------------------------------------------

        customer_data = {
            "recency": row["recency"],
            "history": row["history"],
            "mens": row["mens"],
            "womens": row["womens"],
            "zip_code": row["zip_code"],
            "newbie": row["newbie"],
            "channel": row["channel"],
            "purchase_preference":
                purchase_preference,
        }


        # -------------------------------------------------
        # Score customer using our existing production
        # decision engine
        # -------------------------------------------------

        score = score_customer(
            customer_data,
            artifacts,
            email_cost=email_cost,
            gross_margin=gross_margin,
        )


        # -------------------------------------------------
        # Extract profit estimates
        # -------------------------------------------------

        no_email_profit = (
            score["expected_profit"][
                "No E-Mail"
            ]
        )

        mens_email_profit = (
            score["expected_profit"][
                "Mens E-Mail"
            ]
        )

        womens_email_profit = (
            score["expected_profit"][
                "Womens E-Mail"
            ]
        )


        # -------------------------------------------------
        # Find the better EMAIL option
        # -------------------------------------------------
        #
        # Notice that this compares only:
        #
        # Mens E-Mail
        # Womens E-Mail
        #
        # We later compare the best email against No E-Mail.

        if mens_email_profit >= womens_email_profit:

            best_email_action = "Mens E-Mail"

            best_email_profit = (
                mens_email_profit
            )

        else:

            best_email_action = "Womens E-Mail"

            best_email_profit = (
                womens_email_profit
            )


        # -------------------------------------------------
        # Incremental profit from contacting this customer
        # -------------------------------------------------
        #
        # Incremental Profit =
        #
        # best expected email profit
        # -
        # expected profit if we send no email

        incremental_profit = (
            best_email_profit
            -
            no_email_profit
        )


        # -------------------------------------------------
        # Store one flattened result row
        # -------------------------------------------------

        result_row = {
            "batch_row": row_number,

            "recency": row["recency"],
            "history": row["history"],
            "mens": row["mens"],
            "womens": row["womens"],
            "zip_code": row["zip_code"],
            "newbie": row["newbie"],
            "channel": row["channel"],
            "purchase_preference":
                purchase_preference,

            "prob_no_email":
                score["conversion_probability"][
                    "No E-Mail"
                ],

            "prob_mens_email":
                score["conversion_probability"][
                    "Mens E-Mail"
                ],

            "prob_womens_email":
                score["conversion_probability"][
                    "Womens E-Mail"
                ],

            "expected_profit_no_email":
                no_email_profit,

            "expected_profit_mens_email":
                mens_email_profit,

            "expected_profit_womens_email":
                womens_email_profit,

            "best_email_action":
                best_email_action,

            "best_email_profit":
                best_email_profit,

            "incremental_profit":
                incremental_profit,
        }

        results.append(
            result_row
        )


    return pd.DataFrame(
        results
    )


# ---------------------------------------------------------
# Optimize a limited email budget
# ---------------------------------------------------------

def optimize_email_budget(
    scored_customers,
    max_emails,
):
    """
    Select customers for email contact when the business
    has a maximum number of emails it can send.

    Customers are ranked by predicted incremental profit.

    Only customers with positive incremental expected profit
    are eligible to receive an email.
    """

    if max_emails < 0:

        raise ValueError(
            "max_emails must be zero or greater."
        )


    required_columns = {
        "best_email_action",
        "incremental_profit",
        "expected_profit_no_email",
        "best_email_profit",
    }

    missing_columns = (
        required_columns
        -
        set(scored_customers.columns)
    )

    if missing_columns:

        raise ValueError(
            "Input DataFrame has not been "
            "scored correctly."
        )


    # -----------------------------------------------------
    # Rank customers by incremental profit
    # -----------------------------------------------------

    optimized = (
        scored_customers
        .copy()
        .sort_values(
            "incremental_profit",
            ascending=False,
        )
        .reset_index(drop=True)
    )


    # -----------------------------------------------------
    # Determine who is eligible for an email
    # -----------------------------------------------------
    #
    # Sending an email makes economic sense only when
    # incremental expected profit is positive.

    positive_profit_mask = (
        optimized["incremental_profit"]
        >
        0
    )

    positive_indexes = optimized.index[
        positive_profit_mask
    ]


    # -----------------------------------------------------
    # Respect the campaign capacity
    # -----------------------------------------------------

    selected_indexes = positive_indexes[
        :max_emails
    ]


    # Default everyone to No E-Mail.

    optimized[
        "final_recommended_action"
    ] = "No E-Mail"

    optimized[
        "selected_for_campaign"
    ] = False


    # Assign the best email only to selected customers.

    optimized.loc[
        selected_indexes,
        "final_recommended_action",
    ] = optimized.loc[
        selected_indexes,
        "best_email_action",
    ]

    optimized.loc[
        selected_indexes,
        "selected_for_campaign",
    ] = True


    # -----------------------------------------------------
    # Profit under the final optimized policy
    # -----------------------------------------------------

    optimized[
        "optimized_expected_profit"
    ] = optimized[
        "expected_profit_no_email"
    ]

    optimized.loc[
        selected_indexes,
        "optimized_expected_profit",
    ] = optimized.loc[
        selected_indexes,
        "best_email_profit",
    ]


    # -----------------------------------------------------
    # Calculate campaign summary
    # -----------------------------------------------------

    baseline_profit = optimized[
        "expected_profit_no_email"
    ].sum()

    optimized_profit = optimized[
        "optimized_expected_profit"
    ].sum()

    incremental_campaign_profit = (
        optimized_profit
        -
        baseline_profit
    )

    selected_count = int(
        optimized[
            "selected_for_campaign"
        ].sum()
    )


    summary = {
        "total_customers": int(
            len(optimized)
        ),

        "max_emails": int(
            max_emails
        ),

        "emails_selected": selected_count,

        "baseline_expected_profit": float(
            baseline_profit
        ),

        "optimized_expected_profit": float(
            optimized_profit
        ),

        "incremental_expected_profit": float(
            incremental_campaign_profit
        ),
    }


    return {
        "recommendations": optimized,
        "summary": summary,
    }

# ---------------------------------------------------------
# Optimize using a dollar campaign budget
# ---------------------------------------------------------

def optimize_campaign_budget(
    scored_customers,
    campaign_budget,
    email_cost,
):
    """
    Optimize a campaign using a total dollar budget.

    Parameters
    ----------
    scored_customers : pandas.DataFrame
        Output produced by score_customer_batch().

    campaign_budget : float
        Maximum total dollars available for email sends.

    email_cost : float
        Cost of sending one email.

    Returns
    -------
    dict
        Contains customer-level recommendations and an
        expanded campaign summary.
    """

    # -----------------------------------------------------
    # Validate business inputs
    # -----------------------------------------------------

    if campaign_budget < 0:

        raise ValueError(
            "campaign_budget must be zero or greater."
        )

    if email_cost < 0:

        raise ValueError(
            "email_cost must be zero or greater."
        )


    # -----------------------------------------------------
    # Convert dollar budget into campaign capacity
    # -----------------------------------------------------
    #
    # Example:
    #
    # budget = $10
    # cost = $0.05
    #
    # affordable emails = 200

    if email_cost == 0:

        # If sending an email costs nothing, budget does not
        # restrict the number of customers we can contact.

        max_affordable_emails = len(
            scored_customers
        )

    else:

        max_affordable_emails = int(
        Decimal(str(campaign_budget))
        /
        Decimal(str(email_cost))
    )


    # -----------------------------------------------------
    # Reuse our existing optimizer
    # -----------------------------------------------------
    #
    # This avoids duplicating ranking logic.

    result = optimize_email_budget(
        scored_customers,
        max_emails=max_affordable_emails,
    )


    recommendations = result[
        "recommendations"
    ]

    summary = result[
        "summary"
    ]


    # -----------------------------------------------------
    # Calculate actual campaign spending
    # -----------------------------------------------------

    emails_selected = summary[
        "emails_selected"
    ]

    campaign_spend = (
        emails_selected
        *
        email_cost
    )

    budget_remaining = (
        campaign_budget
        -
        campaign_spend
    )


    # -----------------------------------------------------
    # Add budget-specific metrics
    # -----------------------------------------------------

    summary[
        "campaign_budget"
    ] = float(
        campaign_budget
    )

    summary[
        "email_cost"
    ] = float(
        email_cost
    )

    summary[
        "max_affordable_emails"
    ] = int(
        max_affordable_emails
    )

    summary[
        "campaign_spend"
    ] = float(
        campaign_spend
    )

    summary[
        "budget_remaining"
    ] = float(
        budget_remaining
    )


    return {
        "recommendations": recommendations,
        "summary": summary,
    }