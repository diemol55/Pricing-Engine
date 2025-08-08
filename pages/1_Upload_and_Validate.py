import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Upload and Validate", layout="wide", page_icon="favicon.png")

st.title("Upload and Validate Data")

# Connect to the database and get valid categories once
conn = sqlite3.connect("pricing_engine.db")
category_multipliers_df = pd.read_sql("SELECT * FROM category_multipliers", conn)
valid_categories = category_multipliers_df["Category"].tolist()

# File Upload
uploaded_file = st.file_uploader("Upload purchase file (Excel or CSV)", type=[".xlsx", ".xls", ".csv"])

# Download template
@st.cache_data
def get_template_df():
    return pd.DataFrame({
        "Qty": [1, 2],
        "Inv #": ["INV001", "INV002"],
        "Part Number": ["PN001", "PN002"],
        "Purchase Cost": [100, 200],
        "Category": ["Speciality", "Universal"]
    })

st.download_button(
    label="Download CSV Template",
    data=get_template_df().to_csv(index=False),
    file_name="template.csv",
    mime="text/csv",
)

# Process file if it exists
if uploaded_file:
    if st.session_state.get('uploaded_file_name') != uploaded_file.name:
        st.session_state.clear()
        st.session_state.currency = "USD"
        st.session_state.exchange_rate = 1.0
        st.session_state.freight_cost = 0.0
        st.session_state.freight_mode = "Auto"

        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)
        
        st.session_state.df.columns = st.session_state.df.columns.str.strip()
        for col in st.session_state.df.columns:
            if st.session_state.df[col].dtype == 'object':
                st.session_state.df[col] = st.session_state.df[col].str.strip()
        
        st.session_state.df['Purchase Cost'] = st.session_state.df['Purchase Cost'].replace({'[^0-9.]': ''}, regex=True).astype(float)
        st.session_state.df['Qty'] = pd.to_numeric(st.session_state.df['Qty'], errors='coerce').fillna(0).astype(int)

        default_category = valid_categories[0] if valid_categories else ""
        if 'Category' not in st.session_state.df.columns:
            st.session_state.df['Category'] = default_category
        
        st.session_state.df['Category'] = st.session_state.df['Category'].fillna(default_category).astype(str)
        st.session_state.df['Category'] = st.session_state.df['Category'].replace("", default_category)

        st.session_state.uploaded_file_name = uploaded_file.name
        st.rerun()

# Display and validation logic if df exists in state
if 'df' in st.session_state:
    st.subheader("Edit Data and Categories")
    st.info("Edit the categories below and click 'Apply Changes' to save them to the current session.")

    edited_df = st.data_editor(
        st.session_state.df,
        column_config={
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=valid_categories,
                required=True,
            )
        },
        use_container_width=True,
        key="data_editor"
    )

    if st.button("Apply Changes"):
        st.session_state.df = edited_df
        st.success("Changes have been applied successfully!")
        st.rerun()

    mismatched_categories = st.session_state.df[~st.session_state.df["Category"].isin(valid_categories)]
    if not mismatched_categories.empty:
        st.warning("Some rows still have invalid categories. Please correct them before proceeding.")