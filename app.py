import streamlit as st
import pandas as pd
import sqlite3
from calculations import calculate_landed_cost, calculate_rrpp, calculate_tiered_pricing
from database_setup import get_initial_markup_data, get_initial_category_multipliers
from datetime import datetime

st.set_page_config(page_title="Pricing Tool", layout="wide")
st.title("📦 Ozwide Pricing Calculator")

# File Upload
uploaded_file = st.file_uploader("Upload purchase file (Excel or CSV)", type=[".xlsx", ".xls", ".csv"])

# Download template
@st.cache_data
def get_template_df():
    return pd.DataFrame({
        "QtyPart": [1, 2],
        "Inv #": ["INV001", "INV002"],
        "Purchase Cost": [100, 200],
        "Category": ["Speciality", "Universal"]
    })

st.download_button(
    label="Download CSV Template",
    data=get_template_df().to_csv(index=False),
    file_name="template.csv",
    mime="text/csv",
)

if uploaded_file:
    if 'df' not in st.session_state or st.session_state.uploaded_file_name != uploaded_file.name:
        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)
        st.session_state.df.columns = st.session_state.df.columns.str.strip()  # Remove whitespace from headers
        st.session_state.df.rename(columns={
            "QtyPart": "Qty",
            "#Purchase": "Purchase Cost",
            "CostCategory": "Category"
        }, inplace=True)
        st.session_state.uploaded_file_name = uploaded_file.name

    conn = sqlite3.connect("pricing_engine.db")
    category_multipliers_df = pd.read_sql("SELECT * FROM category_multipliers", conn)
    valid_categories = category_multipliers_df["Category"].tolist()
    mismatched_categories = st.session_state.df[~st.session_state.df["Category"].isin(valid_categories)]

    if not mismatched_categories.empty:
        st.subheader("Mismatched Categories")
        st.warning("The following rows have categories that are not in the database. Please correct them.")
        edited_rows = st.data_editor(
            mismatched_categories,
            column_config={
                "Category": st.column_config.SelectboxColumn(
                    "Category",
                    options=valid_categories,
                    required=True,
                )
            },
            use_container_width=True,
        )

        if st.button("Apply Changes"):
            for index, row in edited_rows.iterrows():
                st.session_state.df.loc[index, "Category"] = row["Category"]
            st.success("Changes applied.")
            st.rerun()

    st.subheader("File Preview")
    st.dataframe(st.session_state.df.head(20))

    st.subheader("Input Parameters")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        currency = st.selectbox("Currency", options=["AUD", "USD"], index=0)
    with col2:
        exchange_rate = st.number_input("Exchange Rate (if not AUD)", min_value=0.0, value=1.0, step=0.01)
    with col3:
        freight_cost = st.number_input("Total Freight Cost (AUD)", min_value=0.0, value=0.0, step=1.0)
    with col4:
        freight_mode = st.selectbox("Freight Mode", options=["Auto", "Manual"], index=0)

    if freight_mode == "Manual":
        st.warning("Manual freight mode selected. Please ensure freight rate is added as a percentage elsewhere.")

    st.subheader("Markup and Multipliers")
    show_rrpp_editor = st.checkbox("Edit RRPP Markup Table", value=False)
    show_category_editor = st.checkbox("Edit Category Multipliers", value=False)

    st.subheader("📈 Apply Price Increase")
    increase_percentage = st.number_input("Percentage Increase (e.g., 5 for 5%)", min_value=0.0, value=0.0, step=0.1)
    increase_target = st.radio("Apply to:", ("RRPP Markup", "Category Multipliers"))

    if increase_target == "Category Multipliers":
        all_categories = ["All Categories"] + valid_categories
        selected_category_for_increase = st.selectbox("Select Category", options=all_categories)

    if st.button("Apply Increase"):
        conn = sqlite3.connect("pricing_engine.db")
        if increase_target == "RRPP Markup":
            current_markup = pd.read_sql("SELECT * FROM rrpp_markup_table", conn)
            current_markup["RRPP Markup"] = current_markup["RRPP Markup"] * (1 + increase_percentage / 100)
            current_markup["timestamp"] = datetime.now()
            current_markup["change_type"] = "price_increase"
            current_markup.to_sql("rrpp_markup_table", conn, if_exists="replace", index=False)
            st.success(f"RRPP Markup increased by {increase_percentage}%")
        else: # Category Multipliers
            current_multipliers = pd.read_sql("SELECT * FROM category_multipliers", conn)
            if selected_category_for_increase == "All Categories":
                current_multipliers["Multiplier"] = current_multipliers["Multiplier"] * (1 + increase_percentage / 100)
                st.success(f"All Category Multipliers increased by {increase_percentage}%")
            else:
                current_multipliers.loc[current_multipliers["Category"] == selected_category_for_increase, "Multiplier"] *= (1 + increase_percentage / 100)
                st.success(f"Category '{selected_category_for_increase}' Multiplier increased by {increase_percentage}%")
            current_multipliers["timestamp"] = datetime.now()
            current_multipliers["change_type"] = "price_increase"
            current_multipliers.to_sql("category_multipliers", conn, if_exists="replace", index=False)
        conn.close()
        st.rerun()

    markup_data = pd.read_sql("SELECT * FROM rrpp_markup_table", conn)

    if 'original_markup_data' not in st.session_state:
        st.session_state.original_markup_data = markup_data.copy()

    if show_rrpp_editor:
        st.subheader("🛠️ RRPP Markup Table")
        if 'original_markup_data' not in st.session_state:
            st.session_state.original_markup_data = markup_data.copy()

        edited_markup = st.data_editor(markup_data, use_container_width=True, num_rows="dynamic", disabled=["From", "To", "timestamp", "change_type"])
        if st.button("Save RRPP Markup Table"):
            # Find indices where the 'RRPP Markup' value has actually changed
            diff_mask = edited_markup['RRPP Markup'] != st.session_state.original_markup_data['RRPP Markup']
            changed_indices = diff_mask[diff_mask].index

            if not changed_indices.empty:
                # Update only the changed rows
                for index in changed_indices:
                    edited_markup.loc[index, "timestamp"] = datetime.now()
                    edited_markup.loc[index, "change_type"] = "individual_change"
                
                # Save the entire updated dataframe
                edited_markup.to_sql("rrpp_markup_table", conn, if_exists="replace", index=False)
                st.success(f"{len(changed_indices)} row(s) saved in RRPP Markup Table.")
                st.session_state.original_markup_data = edited_markup.copy() # Update the original state
                st.rerun()
            else:
                st.warning("No changes to save.")

        if st.button("Reset RRPP Markup Table"):
            markup_data = get_initial_markup_data()
            markup_data["timestamp"] = datetime.now()
            markup_data["change_type"] = "reset"
            markup_data.to_sql("rrpp_markup_table", conn, if_exists="replace", index=False)
            st.success("RRPP Markup Table reset to default.")
            st.rerun()
    else:
        edited_markup = markup_data

    if 'original_category_multipliers_df' not in st.session_state:
        st.session_state.original_category_multipliers_df = category_multipliers_df.copy()

    if show_category_editor:
        st.subheader("🛠️ Category Multipliers")
        if 'original_category_multipliers_df' not in st.session_state:
            st.session_state.original_category_multipliers_df = category_multipliers_df.copy()

        edited_category_multipliers = st.data_editor(category_multipliers_df, use_container_width=True, num_rows="dynamic", disabled=["Category", "timestamp", "change_type"])
        if st.button("Save Category Multipliers"):
            # Find indices where the 'Multiplier' value has actually changed
            diff_mask = edited_category_multipliers['Multiplier'] != st.session_state.original_category_multipliers_df['Multiplier']
            changed_indices = diff_mask[diff_mask].index

            if not changed_indices.empty:
                # Update only the changed rows
                for index in changed_indices:
                    edited_category_multipliers.loc[index, "timestamp"] = datetime.now()
                    edited_category_multipliers.loc[index, "change_type"] = "individual_change"
                
                # Save the entire updated dataframe
                edited_category_multipliers.to_sql("category_multipliers", conn, if_exists="replace", index=False)
                st.success(f"{len(changed_indices)} row(s) saved in Category Multipliers.")
                st.session_state.original_category_multipliers_df = edited_category_multipliers.copy() # Update the original state
                st.rerun()
            else:
                st.warning("No changes to save.")

        if st.button("Reset Category Multipliers"):
            category_multipliers_df = get_initial_category_multipliers()
            category_multipliers_df["timestamp"] = datetime.now()
            category_multipliers_df["change_type"] = "reset"
            category_multipliers_df.to_sql("category_multipliers", conn, if_exists="replace", index=False)
            st.success("Category Multipliers reset to default.")
            st.rerun()
    else:
        edited_category_multipliers = category_multipliers_df

    category_multipliers = pd.Series(edited_category_multipliers.Multiplier.values,index=edited_category_multipliers.Category).to_dict()

    def perform_calculations(df_to_calculate):
        df_calculated = df_to_calculate.copy()
        df_calculated['Purchase Cost'] = df_calculated['Purchase Cost'].replace('[\$,]', '', regex=True).astype(float)
        df_calculated['Qty'] = df_calculated['Qty'].astype(float)

        total_purchase = (df_calculated['Qty'] * df_calculated['Purchase Cost']).sum()

        df_calculated = calculate_landed_cost(df_calculated, total_purchase, freight_cost, currency, exchange_rate)
        df_calculated = calculate_rrpp(df_calculated, edited_markup, category_multipliers)
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
        if st.button("Save Pricing Calculations"):
            try:
                if 'calculated_df' in st.session_state:
                    st.session_state.calculated_df["timestamp"] = datetime.now()
                    st.session_state.calculated_df.to_sql("priced_parts", conn, if_exists="append", index=False)
                    conn.close()
                    
                    # Store data for download in session state
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
        if st.button("Reset Calculations"):
            st.session_state.clear()
            st.rerun()

    if 'download_csv_data' in st.session_state and st.session_state.download_csv_data:
        st.download_button(
            label="Click here to download",
            data=st.session_state.download_csv_data,
            file_name=st.session_state.download_file_name,
            mime=st.session_state.download_mime_type,
            key="final_download_button"
        )
        # Clear download data after button is displayed
        del st.session_state.download_csv_data
        del st.session_state.download_file_name
        del st.session_state.download_mime_type