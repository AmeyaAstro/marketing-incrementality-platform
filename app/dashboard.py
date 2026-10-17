"""
Streamlit dashboard for the Marketing Incrementality Platform.

The dashboard supports two workflows:

1. Single Customer Recommendation
2. Batch Campaign Optimizer

Batch campaign optimization supports:

- Maximum-email capacity constraints
- Dollar-budget constraints

The frontend communicates with the FastAPI backend.
"""

import io

import httpx
import pandas as pd
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
    Use causal uplift models to compare different email actions,
    estimate expected revenue and profit, and optimize campaign
    targeting under limited marketing capacity or budget.
    """
)

st.divider()


# ---------------------------------------------------------
# Dashboard mode
# ---------------------------------------------------------

mode = st.radio(
    "Choose workflow",
    options=[
        "Single Customer Recommendation",
        "Batch Campaign Optimizer",
    ],
    horizontal=True,
)


# =========================================================
# SINGLE CUSTOMER MODE
# =========================================================

if mode == "Single Customer Recommendation":

    st.header("Single Customer Recommendation")

    st.write(
        """
        Score one customer under:

        - No E-Mail
        - Men's E-Mail
        - Women's E-Mail
        """
    )

    st.divider()


    # -----------------------------------------------------
    # Customer profile
    # -----------------------------------------------------

    st.subheader("Customer Profile")

    col1, col2 = st.columns(2)


    with col1:

        recency = st.number_input(
            "Recency (months)",
            min_value=0,
            value=3,
            step=1,
        )

        history = st.number_input(
            "Historical Spend ($)",
            min_value=0.0,
            value=250.0,
            step=10.0,
        )

        mens = st.selectbox(
            "Previously Purchased Men's Products?",
            options=[0, 1],
            format_func=lambda x: (
                "Yes" if x == 1 else "No"
            ),
        )

        womens = st.selectbox(
            "Previously Purchased Women's Products?",
            options=[0, 1],
            format_func=lambda x: (
                "Yes" if x == 1 else "No"
            ),
        )


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
            format_func=lambda x: (
                "Yes" if x == 1 else "No"
            ),
        )

        channel = st.selectbox(
            "Shopping Channel",
            options=[
                "Web",
                "Phone",
                "Multichannel",
            ],
        )


    # -----------------------------------------------------
    # Derive purchase preference
    # -----------------------------------------------------

    if mens == 1 and womens == 1:

        purchase_preference = "Both"

    elif mens == 1:

        purchase_preference = "Mens Only"

    elif womens == 1:

        purchase_preference = "Womens Only"

    else:

        purchase_preference = "Neither"


    st.caption(
        f"Derived purchase preference: "
        f"**{purchase_preference}**"
    )


    # -----------------------------------------------------
    # Validate customer support
    # -----------------------------------------------------

    valid_purchase_history = not (
        mens == 0 and womens == 0
    )

    if not valid_purchase_history:

        st.warning(
            """
            This customer profile is outside the model's
            training data.

            Select at least one historical product category.
            """
        )


    st.divider()


    # -----------------------------------------------------
    # Business assumptions
    # -----------------------------------------------------

    st.subheader("Business Assumptions")

    business_col1, business_col2 = st.columns(2)


    with business_col1:

        email_cost = st.number_input(
            "Email Cost per Customer ($)",
            min_value=0.0,
            value=0.01,
            step=0.01,
            format="%.2f",
        )


    with business_col2:

        gross_margin_percent = st.number_input(
            "Gross Margin (%)",
            min_value=0.0,
            max_value=100.0,
            value=40.0,
            step=1.0,
        )


    gross_margin = (
        gross_margin_percent / 100.0
    )


    st.divider()


    # -----------------------------------------------------
    # Score customer
    # -----------------------------------------------------

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
            "purchase_preference":
                purchase_preference,
            "email_cost": email_cost,
            "gross_margin": gross_margin,
        }


        try:

            response = httpx.post(
                f"{API_URL}/score-customer",
                json=customer_data,
                timeout=10.0,
            )

            response.raise_for_status()

            result = response.json()


            # ---------------------------------------------
            # Main recommendations
            # ---------------------------------------------

            st.success(
                "Customer scored successfully."
            )

            st.subheader("Recommended Actions")

            recommendation_col1, \
                recommendation_col2, \
                recommendation_col3 = st.columns(3)


            with recommendation_col1:

                st.metric(
                    "Best Action for Conversion",
                    result[
                        "recommended_for_conversion"
                    ],
                )


            with recommendation_col2:

                st.metric(
                    "Best Action for Revenue",
                    result[
                        "recommended_for_revenue"
                    ],
                )


            with recommendation_col3:

                st.metric(
                    "Best Action for Profit",
                    result[
                        "recommended_for_profit"
                    ],
                )


            st.divider()


            # ---------------------------------------------
            # Conversion probabilities
            # ---------------------------------------------

            st.subheader(
                "Predicted Conversion Probability"
            )

            probabilities = result[
                "conversion_probability"
            ]

            prob_col1, prob_col2, prob_col3 = (
                st.columns(3)
            )


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


            # ---------------------------------------------
            # Uplift
            # ---------------------------------------------

            st.subheader(
                "Estimated Conversion Uplift"
            )

            uplift = result["uplift"]

            uplift_col1, uplift_col2 = (
                st.columns(2)
            )


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


            # ---------------------------------------------
            # Expected spend
            # ---------------------------------------------

            st.subheader(
                "Predicted Expected Spend per Customer"
            )

            spend = result["expected_spend"]

            spend_col1, spend_col2, spend_col3 = (
                st.columns(3)
            )


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


            # ---------------------------------------------
            # Expected profit
            # ---------------------------------------------

            st.subheader(
                "Predicted Expected Profit per Customer"
            )

            profit = result["expected_profit"]

            profit_col1, profit_col2, profit_col3 = (
                st.columns(3)
            )


            with profit_col1:

                st.metric(
                    "No E-Mail",
                    f"${profit['No E-Mail']:.2f}",
                )


            with profit_col2:

                st.metric(
                    "Men's E-Mail",
                    f"${profit['Mens E-Mail']:.2f}",
                )


            with profit_col3:

                st.metric(
                    "Women's E-Mail",
                    f"${profit['Womens E-Mail']:.2f}",
                )


            # ---------------------------------------------
            # Interpretation
            # ---------------------------------------------

            st.info(
                """
                Individual uplift values are model-based
                estimates, not directly observed causal
                outcomes.

                Use this system as decision support rather
                than as certainty about an individual
                customer.
                """
            )


        except httpx.RequestError:

            st.error(
                """
                Could not connect to the FastAPI backend.

                Start it with:

                `python -m uvicorn api.main:app --reload`
                """
            )


        except httpx.HTTPStatusError as error:

            st.error(
                "API returned an error: "
                f"{error.response.status_code}"
            )


# =========================================================
# BATCH CAMPAIGN MODE
# =========================================================

else:

    st.header("Batch Campaign Optimizer")

    st.write(
        """
        Upload a CSV containing many customers.

        The platform will:

        1. Score each customer under every campaign action.
        2. Estimate incremental expected profit.
        3. Rank customers by expected economic benefit.
        4. Select the best customers under either a campaign
           capacity limit or a dollar budget.
        """
    )

    st.divider()


    # -----------------------------------------------------
    # Expected input format
    # -----------------------------------------------------

    st.subheader("CSV Format")

    st.write(
        """
        Your CSV must contain these columns:
        """
    )

    required_columns_display = pd.DataFrame(
        {
            "column": [
                "recency",
                "history",
                "mens",
                "womens",
                "zip_code",
                "newbie",
                "channel",
            ],
            "example": [
                3,
                250.0,
                1,
                0,
                "Urban",
                0,
                "Web",
            ],
        }
    )

    st.dataframe(
        required_columns_display,
        use_container_width=True,
        hide_index=True,
    )


    # -----------------------------------------------------
    # Provide example CSV
    # -----------------------------------------------------

    example_df = pd.DataFrame(
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


    example_csv = (
        example_df
        .to_csv(index=False)
        .encode("utf-8")
    )


    st.download_button(
        "Download Example CSV",
        data=example_csv,
        file_name="example_customers.csv",
        mime="text/csv",
    )


    st.divider()


    # -----------------------------------------------------
    # Upload customer CSV
    # -----------------------------------------------------

    uploaded_file = st.file_uploader(
        "Upload Customer CSV",
        type=["csv"],
    )


    if uploaded_file is not None:

        try:

            customers_df = pd.read_csv(
                uploaded_file
            )

        except Exception as error:

            st.error(
                f"Could not read CSV: {error}"
            )

            st.stop()


        st.success(
            f"Loaded {len(customers_df):,} customers."
        )


        st.subheader("Uploaded Customer Preview")

        st.dataframe(
            customers_df.head(20),
            use_container_width=True,
        )


        st.divider()


        # -------------------------------------------------
        # Optimization constraint
        # -------------------------------------------------

        st.subheader("Optimization Constraint")

        optimization_mode = st.radio(
            "How should campaign size be limited?",
            options=[
                "Maximum Emails",
                "Dollar Budget",
            ],
            horizontal=True,
        )


        st.caption(
            """
            **Maximum Emails** limits the number of customers
            contacted.

            **Dollar Budget** limits total campaign spending
            based on the cost per email.
            """
        )


        st.divider()


        # -------------------------------------------------
        # Campaign settings
        # -------------------------------------------------

        st.subheader("Campaign Settings")


        # Shared business assumptions.

        settings_col1, settings_col2 = st.columns(2)


        with settings_col1:

            batch_email_cost = st.number_input(
                "Email Cost per Customer ($)",
                min_value=0.0,
                value=0.01,
                step=0.01,
                format="%.2f",
                key="batch_email_cost",
            )


        with settings_col2:

            batch_margin_percent = st.number_input(
                "Gross Margin (%)",
                min_value=0.0,
                max_value=100.0,
                value=40.0,
                step=1.0,
                key="batch_margin",
            )


        batch_gross_margin = (
            batch_margin_percent / 100.0
        )


        # -------------------------------------------------
        # Capacity-specific setting
        # -------------------------------------------------

        if optimization_mode == "Maximum Emails":

            max_emails = st.number_input(
                "Maximum Emails",
                min_value=0,
                max_value=int(
                    len(customers_df)
                ),
                value=min(
                    100,
                    len(customers_df),
                ),
                step=1,
            )


        # -------------------------------------------------
        # Dollar-budget-specific setting
        # -------------------------------------------------

        else:

            campaign_budget = st.number_input(
                "Total Campaign Budget ($)",
                min_value=0.0,
                value=10.00,
                step=1.00,
                format="%.2f",
                help=(
                    "Maximum total amount the business "
                    "is willing to spend on email sends."
                ),
            )


            # Show implied affordable capacity immediately.

            if batch_email_cost > 0:

                affordable_preview = int(
                    campaign_budget
                    //
                    batch_email_cost
                )

                affordable_preview = min(
                    affordable_preview,
                    len(customers_df),
                )

                st.caption(
                    "At the current email cost, this budget "
                    f"can fund up to **{affordable_preview:,} "
                    "emails** in this uploaded customer batch."
                )

            else:

                st.caption(
                    """
                    Email cost is $0.00, so the dollar budget
                    does not limit campaign capacity.
                    """
                )


        st.divider()


        # -------------------------------------------------
        # Run optimization
        # -------------------------------------------------

        if st.button(
            "Optimize Campaign",
            type="primary",
            use_container_width=True,
        ):

            required_columns = {
                "recency",
                "history",
                "mens",
                "womens",
                "zip_code",
                "newbie",
                "channel",
            }


            missing_columns = (
                required_columns
                -
                set(customers_df.columns)
            )


            if missing_columns:

                st.error(
                    "Missing required columns: "
                    +
                    ", ".join(
                        sorted(
                            missing_columns
                        )
                    )
                )

                st.stop()


            # ---------------------------------------------
            # Convert customer rows into JSON
            # ---------------------------------------------

            customer_records = (
                customers_df[
                    [
                        "recency",
                        "history",
                        "mens",
                        "womens",
                        "zip_code",
                        "newbie",
                        "channel",
                    ]
                ]
                .to_dict(
                    orient="records"
                )
            )


            # ---------------------------------------------
            # Build API request based on constraint mode
            # ---------------------------------------------

            if optimization_mode == "Maximum Emails":

                campaign_request = {
                    "customers":
                        customer_records,

                    "max_emails":
                        int(max_emails),

                    "email_cost":
                        float(
                            batch_email_cost
                        ),

                    "gross_margin":
                        float(
                            batch_gross_margin
                        ),
                }

                endpoint = (
                    f"{API_URL}/optimize-campaign"
                )


            else:

                campaign_request = {
                    "customers":
                        customer_records,

                    "campaign_budget":
                        float(
                            campaign_budget
                        ),

                    "email_cost":
                        float(
                            batch_email_cost
                        ),

                    "gross_margin":
                        float(
                            batch_gross_margin
                        ),
                }

                endpoint = (
                    f"{API_URL}/optimize-campaign-budget"
                )


            try:

                with st.spinner(
                    "Scoring customers and "
                    "optimizing campaign..."
                ):

                    response = httpx.post(
                        endpoint,
                        json=campaign_request,
                        timeout=60.0,
                    )


                response.raise_for_status()

                result = response.json()

                summary = result["summary"]

                recommendations_df = (
                    pd.DataFrame(
                        result[
                            "recommendations"
                        ]
                    )
                )


                # -----------------------------------------
                # Campaign summary
                # -----------------------------------------

                st.success(
                    "Campaign optimization complete."
                )

                st.subheader(
                    "Campaign Summary"
                )


                # -----------------------------------------
                # Basic campaign metrics
                # -----------------------------------------

                summary_col1, \
                    summary_col2, \
                    summary_col3 = st.columns(3)


                with summary_col1:

                    st.metric(
                        "Total Customers",
                        summary[
                            "total_customers"
                        ],
                    )


                with summary_col2:

                    st.metric(
                        "Emails Selected",
                        summary[
                            "emails_selected"
                        ],
                    )


                with summary_col3:

                    if (
                        optimization_mode
                        ==
                        "Maximum Emails"
                    ):

                        st.metric(
                            "Campaign Capacity",
                            summary[
                                "max_emails"
                            ],
                        )

                    else:

                        st.metric(
                            "Max Affordable Emails",
                            summary[
                                "max_affordable_emails"
                            ],
                        )


                # -----------------------------------------
                # Profit metrics
                # -----------------------------------------

                profit_col1, \
                    profit_col2, \
                    profit_col3 = st.columns(3)


                with profit_col1:

                    st.metric(
                        "Baseline Expected Profit",
                        "$"
                        f"{summary['baseline_expected_profit']:.2f}",
                    )


                with profit_col2:

                    st.metric(
                        "Optimized Expected Profit",
                        "$"
                        f"{summary['optimized_expected_profit']:.2f}",
                    )


                with profit_col3:

                    st.metric(
                        "Incremental Expected Profit",
                        "$"
                        f"{summary['incremental_expected_profit']:.2f}",
                    )


                # -----------------------------------------
                # Budget-specific metrics
                # -----------------------------------------

                if optimization_mode == "Dollar Budget":

                    st.subheader(
                        "Budget Utilization"
                    )

                    budget_col1, \
                        budget_col2, \
                        budget_col3 = st.columns(3)


                    with budget_col1:

                        st.metric(
                            "Campaign Budget",
                            "$"
                            f"{summary['campaign_budget']:.2f}",
                        )


                    with budget_col2:

                        st.metric(
                            "Campaign Spend",
                            "$"
                            f"{summary['campaign_spend']:.2f}",
                        )


                    with budget_col3:

                        st.metric(
                            "Budget Remaining",
                            "$"
                            f"{summary['budget_remaining']:.2f}",
                        )


                    # -------------------------------------
                    # Budget utilization percentage
                    # -------------------------------------

                    if summary["campaign_budget"] > 0:

                        budget_utilization = (
                            summary["campaign_spend"]
                            /
                            summary["campaign_budget"]
                        )

                        st.progress(
                            min(
                                budget_utilization,
                                1.0,
                            )
                        )

                        st.caption(
                            "Budget utilization: "
                            f"{budget_utilization:.1%}"
                        )

                    elif summary["campaign_spend"] == 0:

                        st.caption(
                            "Budget utilization: 0.0%"
                        )


                st.divider()


                # -----------------------------------------
                # Selected customers only
                # -----------------------------------------

                st.subheader(
                    "Customers Selected for Campaign"
                )


                selected_df = (
                    recommendations_df[
                        recommendations_df[
                            "selected_for_campaign"
                        ]
                    ]
                    .copy()
                )


                if selected_df.empty:

                    st.warning(
                        """
                        No customers had positive enough
                        expected profit to justify sending
                        an email under the current business
                        assumptions.
                        """
                    )

                else:

                    selected_display_columns = [
                        "batch_row",
                        "purchase_preference",
                        "best_email_action",
                        "incremental_profit",
                        "final_recommended_action",
                    ]


                    st.dataframe(
                        selected_df[
                            selected_display_columns
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )


                st.divider()


                # -----------------------------------------
                # Full recommendation table
                # -----------------------------------------

                st.subheader(
                    "Full Customer Recommendations"
                )


                st.dataframe(
                    recommendations_df,
                    use_container_width=True,
                    hide_index=True,
                )


                # -----------------------------------------
                # Download optimized results
                # -----------------------------------------

                output_buffer = io.StringIO()

                recommendations_df.to_csv(
                    output_buffer,
                    index=False,
                )


                st.download_button(
                    "Download Optimized Campaign CSV",
                    data=output_buffer.getvalue(),
                    file_name=(
                        "optimized_campaign.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                )


                # -----------------------------------------
                # Interpretation
                # -----------------------------------------

                if optimization_mode == "Dollar Budget":

                    st.info(
                        """
                        The optimizer converts the available
                        dollar budget into an affordable email
                        capacity using the selected per-email
                        cost.

                        It then ranks customers by
                        **incremental expected profit** and
                        selects the strongest profitable
                        customers first.

                        A campaign may leave some budget unused
                        when additional emails are predicted to
                        reduce expected profit.
                        """
                    )

                else:

                    st.info(
                        """
                        The optimizer ranks customers by
                        **incremental expected profit**.

                        Customers with negative incremental
                        expected profit are not contacted even
                        if unused campaign capacity remains.

                        These values are model-based decision
                        estimates and should be validated in
                        future randomized campaigns.
                        """
                    )


            except httpx.RequestError:

                st.error(
                    """
                    Could not connect to the FastAPI backend.

                    Start it with:

                    `python -m uvicorn api.main:app --reload`
                    """
                )


            except httpx.HTTPStatusError as error:

                st.error(
                    "API returned an error: "
                    f"{error.response.status_code}"
                )

                try:

                    st.json(
                        error.response.json()
                    )

                except Exception:

                    pass