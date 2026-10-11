"""
FastAPI application for the Marketing Incrementality Platform.

This API exposes:

GET /
    Health check.

POST /score-customer
    Score one customer.

POST /optimize-campaign
    Score many customers and optimize who should receive
    an email under a campaign capacity limit.
"""

from typing import List

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.batch_optimizer import (
    optimize_email_budget,
    score_customer_batch,
)
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
        "and budget-constrained campaign optimization."
    ),
    version="0.3.0",
)


# ---------------------------------------------------------
# Load trained artifacts once when API starts
# ---------------------------------------------------------

artifacts = load_artifacts()


# ---------------------------------------------------------
# Single-customer input model
# ---------------------------------------------------------

class CustomerInput(BaseModel):

    recency: int
    history: float
    mens: int
    womens: int
    zip_code: str
    newbie: int
    channel: str
    purchase_preference: str

    email_cost: float = Field(
        default=0.01,
        ge=0.0,
        description="Cost of sending one email.",
    )

    gross_margin: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        description="Gross margin as a decimal.",
    )


# ---------------------------------------------------------
# Batch customer model
# ---------------------------------------------------------
#
# Notice that purchase_preference is NOT required here.
#
# The batch optimizer derives it automatically from:
#
# mens
# womens

class BatchCustomerInput(BaseModel):

    recency: int
    history: float
    mens: int
    womens: int
    zip_code: str
    newbie: int
    channel: str


# ---------------------------------------------------------
# Campaign optimization request
# ---------------------------------------------------------

class CampaignOptimizationInput(BaseModel):

    customers: List[BatchCustomerInput]

    max_emails: int = Field(
        ge=0,
        description=(
            "Maximum number of customers who can "
            "receive an email."
        ),
    )

    email_cost: float = Field(
        default=0.01,
        ge=0.0,
        description="Cost of sending one email.",
    )

    gross_margin: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        description="Gross margin as a decimal.",
    )


# ---------------------------------------------------------
# Health-check endpoint
# ---------------------------------------------------------

@app.get("/")
def root():
    """
    Confirm that the API is running.
    """

    return {
        "status": "ok",
        "message": "Marketing Incrementality API is running",
    }


# ---------------------------------------------------------
# Single-customer scoring endpoint
# ---------------------------------------------------------

@app.post("/score-customer")
def score_customer_endpoint(
    customer: CustomerInput
):
    """
    Score one customer under all campaign actions.
    """

    customer_data = {
        "recency": customer.recency,
        "history": customer.history,
        "mens": customer.mens,
        "womens": customer.womens,
        "zip_code": customer.zip_code,
        "newbie": customer.newbie,
        "channel": customer.channel,
        "purchase_preference":
            customer.purchase_preference,
    }

    result = score_customer(
        customer_data,
        artifacts,
        email_cost=customer.email_cost,
        gross_margin=customer.gross_margin,
    )

    return result


# ---------------------------------------------------------
# Campaign optimization endpoint
# ---------------------------------------------------------

@app.post("/optimize-campaign")
def optimize_campaign_endpoint(
    campaign: CampaignOptimizationInput
):
    """
    Score a batch of customers and select who should
    receive an email under a maximum campaign size.

    Customers are ranked by incremental expected profit.
    """

    # -----------------------------------------------------
    # Convert validated Pydantic customers into dictionaries
    # -----------------------------------------------------

    customer_records = [
        customer.model_dump()
        for customer in campaign.customers
    ]


    # -----------------------------------------------------
    # Convert list of dictionaries into DataFrame
    # -----------------------------------------------------

    import pandas as pd

    customers_df = pd.DataFrame(
        customer_records
    )


    # -----------------------------------------------------
    # Score every customer
    # -----------------------------------------------------

    scored_customers = score_customer_batch(
        customers_df,
        artifacts,
        email_cost=campaign.email_cost,
        gross_margin=campaign.gross_margin,
    )


    # -----------------------------------------------------
    # Apply campaign capacity constraint
    # -----------------------------------------------------

    optimization_result = optimize_email_budget(
        scored_customers,
        max_emails=campaign.max_emails,
    )


    recommendations_df = optimization_result[
        "recommendations"
    ]

    summary = optimization_result[
        "summary"
    ]


    # -----------------------------------------------------
    # Convert DataFrame into JSON-safe records
    # -----------------------------------------------------

    recommendations = (
        recommendations_df
        .to_dict(
            orient="records"
        )
    )


    return {
        "summary": summary,
        "recommendations": recommendations,
    }