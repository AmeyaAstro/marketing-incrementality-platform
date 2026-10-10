"""
FastAPI application for the Marketing Incrementality Platform.

This API exposes the production decision engine over HTTP.

Current endpoints:

GET /
    Simple health check.

POST /score-customer
    Score one customer and return:
    - conversion probabilities
    - uplift estimates
    - expected spend
    - expected profit
    - recommended action for conversion
    - recommended action for revenue
    - recommended action for profit
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.decision_engine import (
    load_artifacts,
    score_customer,
)


# ---------------------------------------------------------
# Create FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="Marketing Incrementality API",
    description=(
        "API for personalized marketing treatment recommendations "
        "using causal uplift models."
    ),
    version="0.2.0",
)


# ---------------------------------------------------------
# Load trained artifacts once when the API starts
# ---------------------------------------------------------

artifacts = load_artifacts()


# ---------------------------------------------------------
# Define the expected customer input
# ---------------------------------------------------------
#
# The business assumptions below are optional.
#
# If the user does not provide them, the API uses:
#
# email_cost = $0.01
# gross_margin = 40%
#
# gross_margin should be written as a decimal:
#
# 0.40 = 40%
# 0.25 = 25%
# 0.60 = 60%

class CustomerInput(BaseModel):

    # -------------------------
    # Customer features
    # -------------------------

    recency: int

    history: float

    mens: int

    womens: int

    zip_code: str

    newbie: int

    channel: str

    purchase_preference: str


    # -------------------------
    # Business assumptions
    # -------------------------

    email_cost: float = Field(
        default=0.01,
        ge=0.0,
        description="Cost of sending one marketing email.",
    )

    gross_margin: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        description=(
            "Gross margin as a decimal. "
            "Example: 0.40 means 40%."
        ),
    )


# ---------------------------------------------------------
# Health-check endpoint
# ---------------------------------------------------------

@app.get("/")
def root():
    """
    Simple endpoint used to confirm the API is running.
    """

    return {
        "status": "ok",
        "message": "Marketing Incrementality API is running",
    }


# ---------------------------------------------------------
# Customer scoring endpoint
# ---------------------------------------------------------

@app.post("/score-customer")
def score_customer_endpoint(
    customer: CustomerInput
):
    """
    Score one customer under all three campaign actions.

    The API uses both customer features and business assumptions
    to produce conversion, revenue, and profit recommendations.
    """

    # -----------------------------------------------------
    # Separate customer features from business assumptions
    # -----------------------------------------------------
    #
    # The machine-learning models were trained only on the
    # customer features.
    #
    # email_cost and gross_margin are business assumptions,
    # so they must NOT be passed into the scikit-learn model.

    customer_data = {
        "recency": customer.recency,
        "history": customer.history,
        "mens": customer.mens,
        "womens": customer.womens,
        "zip_code": customer.zip_code,
        "newbie": customer.newbie,
        "channel": customer.channel,
        "purchase_preference": customer.purchase_preference,
    }


    # -----------------------------------------------------
    # Use the production decision engine
    # -----------------------------------------------------

    result = score_customer(
        customer_data,
        artifacts,
        email_cost=customer.email_cost,
        gross_margin=customer.gross_margin,
    )

    return result