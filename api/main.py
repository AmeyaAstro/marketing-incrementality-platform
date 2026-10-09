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
    - recommended action for conversion
    - recommended action for revenue
"""

from fastapi import FastAPI
from pydantic import BaseModel

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
    version="0.1.0",
)


# ---------------------------------------------------------
# Load trained artifacts once when the API starts
# ---------------------------------------------------------
#
# We do NOT want to reload the models every time someone
# sends a request.
#
# They are loaded once here and reused.

artifacts = load_artifacts()


# ---------------------------------------------------------
# Define the expected customer input
# ---------------------------------------------------------
#
# Pydantic automatically validates incoming JSON.
#
# Example:
#
# {
#   "recency": 3,
#   "history": 250.0,
#   "mens": 1,
#   "womens": 0,
#   "zip_code": "Urban",
#   "newbie": 0,
#   "channel": "Web",
#   "purchase_preference": "Mens Only"
# }

class CustomerInput(BaseModel):
    recency: int
    history: float
    mens: int
    womens: int
    zip_code: str
    newbie: int
    channel: str
    purchase_preference: str


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
    """

    # Convert validated Pydantic input into a normal dictionary.
    customer_data = customer.model_dump()

    # Use the production decision engine.
    result = score_customer(
        customer_data,
        artifacts
    )

    return result