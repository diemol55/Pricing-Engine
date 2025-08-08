import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from calculations import calculate_landed_cost, calculate_rrpp, calculate_tiered_pricing

st.set_page_config(page_title="Calculate and Export", layout="wide")

st.title("Calculate and Export")

if 'df' not in st.session_state:
    st.warning("Please upload a file on the 'Upload and Validate' page first.")
else:
    st.subheader("Input Parameters")

    # Callback functions to update session state immediately
    def update_currency():
        st.session_state.currency = st.session_state.currency_input_widget

    def update_exchange_rate():
        st.session_state.exchange_rate = st.session_state.exchange_rate_input_widget

    def update_freight_cost():
        st.session_state.freight_cost = st.session_state.freight_cost_input_widget

    def update_freight_mode():
        st.session_state.freight_mode = st.session_state.freight_mode_input_widget

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.selectbox(
            "Currency",
            options=["USD","AUD"],
            key="currency_input_widget", # Use a distinct key for the widget
            index=0, # Set default to USD
            on_change=update_currency
        )
    with col2:
        st.number_input(
            "Exchange Rate (if not AUD)",
            min_value=0.0,
            value=st.session_state.exchange_rate,
            step=0.01,
            key="exchange_rate_input_widget", # Use a distinct key for the widget
            on_change=update_exchange_rate
        )
    with col3:
        st.number_input(
            "Total Freight Cost (AUD)",
            min_value=0.0,
            value=st.session_state.freight_cost,
            step=1.0,
            key="freight_cost_input_widget", # Use a distinct key for the widget
            on_change=update_freight_cost
        )
    with col4:
        st.selectbox(
            "Freight Mode",
            options=["Auto", "Manual"],
            key="freight_mode_input_widget", # Use a distinct key for the widget
            index=["Auto", "Manual"].index(st.session_state.freight_mode),
            on_change=update_freight_mode
        )

    # Assign the session state values to local variables for use in calculations
    currency = st.session_state.currency
    exchange_rate = st.session_state.exchange_rate
    freight_cost = st.session_state.freight_cost
    freight_mode = st.session_state.freight_mode

    if freight_mode == "Manual":
        st.warning("Manual freight mode selected. Please ensure freight rate is added as a percentage elsewhere.")

    conn = sqlite3.connect("pricing_engine.db")
    markup_data = pd.read_sql("SELECT * FROM rrpp_markup_table", conn)
    category_multipliers_df = pd.read_sql("SELECT * FROM category_multipliers", conn)
    category_multipliers = pd.Series(category_multipliers_df.Multiplier.values,index=category_multipliers_df.Category).to_dict()

    def perform_calculations(df_to_calculate):
        df_calculated = df_to_calculate.copy()
        df_calculated['Purchase Cost'] = df_calculated['Purchase Cost'].replace('[\$,]', '', regex=True).astype(float)
        df_calculated['Qty'] = df_calculated['Qty'].astype(float)

        total_purchase = (df_calculated['Qty'] * df_calculated['Purchase Cost']).sum()

        df_calculated = calculate_landed_cost(df_calculated, total_purchase, freight_cost, currency, exchange_rate)
        df_calculated = calculate_rrpp(df_calculated, markup_data, category_multipliers)
        df_calculated = calculate_tiered_pricing(df_calculated)

        st.success("Landed Cost, RRPP, and Tiers calculated successfully.")
        st.dataframe(df_calculated)
        return df_calculated

    col_calc1, col_calc2, col_calc3 = st.columns(3)
    with col_calc1:
        if st.button("Calculate Pricing"):
            try:
                st.session_state.calculated_df = perform_calculations(st.session_state.df)
            except Exception as e:
                st.error(f"An error occurred during recalculation: {e}")

    with col_calc2:
        if st.button("Save and Download"):
            try:
                if 'calculated_df' in st.session_state:
                    st.session_state.calculated_df["timestamp"] = datetime.now()
                    st.session_state.calculated_df.to_sql("priced_parts", conn, if_exists="append", index=False)
                    conn.close()
                    
                    st.session_state.download_csv_data = st.session_state.calculated_df.drop(columns=["timestamp", "RRPP Markup", "Category Multiplier"], errors='ignore').to_csv(index=False)
                    st.session_state.download_file_name = "priced_parts.csv"
                    st.session_state.download_mime_type = "text/csv"

                    st.success("Pricing data saved. Initiating download and restarting...")
                    st.rerun()
                else:
                    st.warning("Please calculate pricing first before saving and downloading.")
            except Exception as e:
                st.error(f"An error occurred during saving and downloading: {e}")

    with col_calc3:
        if st.button("Reset App"):
            st.session_state.clear()
            st.session_state.currency = "USD"
            st.session_state.exchange_rate = 1.0
            st.session_state.freight_cost = 0.0
            st.session_state.freight_mode = "Auto"
            st.rerun()

    if 'download_csv_data' in st.session_state and st.session_state.download_csv_data:
        st.download_button(
            label="Click here to download",
            data=st.session_state.download_csv_data,
            file_name=st.session_state.download_file_name,
            mime=st.session_state.download_mime_type,
            key="final_download_button"
        )
        del st.session_state.download_csv_data
        del st.session_state.download_file_name
        del st.session_state.download_mime_type