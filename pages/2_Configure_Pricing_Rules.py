import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from database_setup import get_initial_markup_data, get_initial_category_multipliers

st.set_page_config(page_title="Configure Pricing Rules", layout="wide")

st.title("Configure Pricing Rules")

conn = sqlite3.connect("pricing_engine.db")

rrpp_tab, category_tab, increase_tab = st.tabs(["RRPP Markup", "Category Multipliers", "Price Increase"])

with rrpp_tab:
    st.subheader("🛠️ RRPP Markup Table")
    markup_data = pd.read_sql("SELECT * FROM rrpp_markup_table", conn)
    if 'original_markup_data' not in st.session_state:
        st.session_state.original_markup_data = markup_data.copy()

    edited_markup = st.data_editor(markup_data, use_container_width=True, num_rows="dynamic", disabled=["From", "To", "timestamp", "change_type"])
    if st.button("Save RRPP Markup Table"):
        diff_mask = edited_markup['RRPP Markup'] != st.session_state.original_markup_data['RRPP Markup']
        changed_indices = diff_mask[diff_mask].index

        if not changed_indices.empty:
            for index in changed_indices:
                edited_markup.loc[index, "timestamp"] = datetime.now()
                edited_markup.loc[index, "change_type"] = "individual_change"
            
            edited_markup.to_sql("rrpp_markup_table", conn, if_exists="replace", index=False)
            st.success(f"{len(changed_indices)} row(s) saved in RRPP Markup Table.")
            st.session_state.original_markup_data = edited_markup.copy()
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

with category_tab:
    st.subheader("🛠️ Category Multipliers")
    category_multipliers_df = pd.read_sql("SELECT * FROM category_multipliers", conn)
    if 'original_category_multipliers_df' not in st.session_state:
        st.session_state.original_category_multipliers_df = category_multipliers_df.copy()

    edited_category_multipliers = st.data_editor(category_multipliers_df, use_container_width=True, num_rows="dynamic", disabled=["Category", "timestamp", "change_type"])
    if st.button("Save Category Multipliers"):
        diff_mask = edited_category_multipliers['Multiplier'] != st.session_state.original_category_multipliers_df['Multiplier']
        changed_indices = diff_mask[diff_mask].index

        if not changed_indices.empty:
            for index in changed_indices:
                edited_category_multipliers.loc[index, "timestamp"] = datetime.now()
                edited_category_multipliers.loc[index, "change_type"] = "individual_change"
            
            edited_category_multipliers.to_sql("category_multipliers", conn, if_exists="replace", index=False)
            st.success(f"{len(changed_indices)} row(s) saved in Category Multipliers.")
            st.session_state.original_category_multipliers_df = edited_category_multipliers.copy()
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

with increase_tab:
    st.subheader("📈 Apply Price Increase")
    increase_percentage = st.number_input("Percentage Increase (e.g., 5 for 5%)", min_value=0.0, value=0.0, step=0.1)
    increase_target = st.radio("Apply to:", ("RRPP Markup", "Category Multipliers"))

    if increase_target == "Category Multipliers":
        valid_categories = pd.read_sql("SELECT Category FROM category_multipliers", conn)["Category"].tolist()
        all_categories = ["All Categories"] + valid_categories
        selected_category_for_increase = st.selectbox("Select Category", options=all_categories)

    if st.button("Apply Increase"):
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
        st.rerun()
