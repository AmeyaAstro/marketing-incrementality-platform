"""
Streamlit dashboard for the Marketing Incrementality Platform.

This frontend sends customer information to the FastAPI backend
and displays personalized marketing recommendations.
"""

import httpx
import streamlit as st


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="Marketing Incrementality Platform",
    page_icon="📈",
    layout="wide",
)


# ---------------------------------------------------------
# API configuration
# ---------------------------------------------------------

API_URL = "http://127.0.0.1:8000"


# ---------------------------------------------------------
# Dashboard title
# ---------------------------------------------------------

st.title("📈 Personalized Marketing Incrementality Platform")

st.write(
    """
    Estimate how different email campaigns may change a customer's
    probability of purchasing and expected revenue.

    The system compares three possible actions:

    - No E-Mail
    - Men's E-Mail
    - Women's E-Mail
    """
)

st.divider()


# ---------------------------------------------------------
# Customer input section
# ---------------------------------------------------------

st.subheader("Customer Profile")


col1, col2 = st.columns(2)


# ---------------------------------------------------------
# Left-side inputs
# ---------------------------------------------------------

with col1:

    recency = st.number_input(
        "Recency (months)",
        min_value=0,
        value=3,
        step=1,
        help="How recently the customer purchased.",
    )

    history = st.number_input(
        "Historical Spend ($)",
        min_value=0.0,
        value=250.0,
        step=10.0,
        help="Customer's historical spending amount.",
    )

    mens = st.selectbox(
        "Previously Purchased Men's Products?",
        options=[0, 1],
        format_func=lambda x: "Yes" if x == 1 else "No",
    )

    womens = st.selectbox(
        "Previously Purchased Women's Products?",
        options=[0, 1],
        format_func=lambda x: "Yes" if x == 1 else "No",
    )


# ---------------------------------------------------------
# Right-side inputs
# ---------------------------------------------------------

with col2:

    zip_code = st.selectbox(
        "Customer Location",
        options=[
            "Urban",
            "Suburban",
            "Rural",
        ],
    )

    newbie = st.selectbox(
        "New Customer?",
        options=[0, 1],
        format_func=lambda x: "Yes" if x == 1 else "No",
    )

    channel = st.selectbox(
        "Shopping Channel",
        options=[
            "Web",
            "Phone",
            "Multichannel",
        ],
    )


# ---------------------------------------------------------
# Automatically derive purchase preference
# ---------------------------------------------------------
#
# The ML model was trained with this feature.
#
# Instead of asking the user to manually enter it,
# we calculate it from the men's/women's purchase indicators.

if mens == 1 and womens == 1:
    purchase_preference = "Both"

elif mens == 1:
    purchase_preference = "Mens Only"

elif womens == 1:
    purchase_preference = "Womens Only"

else:
    purchase_preference = "Neither"


st.caption(
    f"Derived purchase preference: **{purchase_preference}**"
)


# ---------------------------------------------------------
# Validate purchase-history combination
# ---------------------------------------------------------
#
# The training dataset does not contain customers with
# neither men's nor women's historical purchases.
#
# Therefore, scoring this combination would require the
# model to extrapolate beyond its training data.

valid_purchase_history = not (
    mens == 0 and womens == 0
)

if not valid_purchase_history:
    st.warning(
        """
        This customer profile is outside the model's training data.
        The original experiment does not contain customers with
        neither men's nor women's historical purchases.
        Select at least one previous product category before scoring.
        """
    )


st.divider()


# ---------------------------------------------------------
# Score customer
# ---------------------------------------------------------

if st.button(
    "Generate Marketing Recommendation",
    type="primary",
    use_container_width=True,
    disabled=not valid_purchase_history,
):

    customer_data = {
        "recency": recency,
        "history": history,
        "mens": mens,
        "womens": womens,
        "zip_code": zip_code,
        "newbie": newbie,
        "channel": channel,
        "purchase_preference": purchase_preference,
    }

    try:

        # Send customer information to our FastAPI backend.

        response = httpx.post(
            f"{API_URL}/score-customer",
            json=customer_data,
            timeout=10.0,
        )

        response.raise_for_status()

        result = response.json()


        # -------------------------------------------------
        # Main recommendation
        # -------------------------------------------------

        st.success(
            "Customer scored successfully."
        )

        recommendation_col1, recommendation_col2 = st.columns(2)

        with recommendation_col1:

            st.metric(
                "Best Action for Conversion",
                result["recommended_for_conversion"],
            )

        with recommendation_col2:

            st.metric(
                "Best Action for Revenue",
                result["recommended_for_revenue"],
            )


        # -------------------------------------------------
        # Conversion probabilities
        # -------------------------------------------------

        st.subheader("Predicted Conversion Probability")

        probabilities = result["conversion_probability"]

        prob_col1, prob_col2, prob_col3 = st.columns(3)

        with prob_col1:
            st.metric(
                "No E-Mail",
                f"{probabilities['No E-Mail']:.2%}",
            )

        with prob_col2:
            st.metric(
                "Men's E-Mail",
                f"{probabilities['Mens E-Mail']:.2%}",
            )

        with prob_col3:
            st.metric(
                "Women's E-Mail",
                f"{probabilities['Womens E-Mail']:.2%}",
            )


        # -------------------------------------------------
        # Causal uplift
        # -------------------------------------------------

        st.subheader("Estimated Conversion Uplift")

        uplift = result["uplift"]

        uplift_col1, uplift_col2 = st.columns(2)

        with uplift_col1:
            st.metric(
                "Men's E-Mail vs No E-Mail",
                f"{uplift['Mens E-Mail']:.2%}",
            )

        with uplift_col2:
            st.metric(
                "Women's E-Mail vs No E-Mail",
                f"{uplift['Womens E-Mail']:.2%}",
            )


        # -------------------------------------------------
        # Expected revenue
        # -------------------------------------------------

        st.subheader("Predicted Expected Spend per Customer")

        spend = result["expected_spend"]

        spend_col1, spend_col2, spend_col3 = st.columns(3)

        with spend_col1:
            st.metric(
                "No E-Mail",
                f"${spend['No E-Mail']:.2f}",
            )

        with spend_col2:
            st.metric(
                "Men's E-Mail",
                f"${spend['Mens E-Mail']:.2f}",
            )

        with spend_col3:
            st.metric(
                "Women's E-Mail",
                f"${spend['Womens E-Mail']:.2f}",
            )


        # -------------------------------------------------
        # Important interpretation note
        # -------------------------------------------------

        st.info(
            """
            **Interpretation:** These are model-based estimates.
            Individual uplift is not directly observable ground truth.
            The platform should be used as a decision-support system,
            especially for ranking or budget-constrained targeting.
            """
        )


    except httpx.RequestError:

        st.error(
            """
            Could not connect to the FastAPI backend.

            Make sure the API is running with:

            `python -m uvicorn api.main:app --reload`
            """
        )

    except httpx.HTTPStatusError as error:

        st.error(
            f"API returned an error: {error.response.status_code}"
        )
