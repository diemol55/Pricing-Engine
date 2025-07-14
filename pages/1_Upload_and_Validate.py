import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Upload and Validate", layout="wide")

st.title("Upload and Validate Data")

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

if uploaded_file:
    if 'df' not in st.session_state or st.session_state.uploaded_file_name != uploaded_file.name:
        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)
        st.session_state.df.columns = st.session_state.df.columns.str.strip()
        # Clean and convert data types
        for col in st.session_state.df.columns:
            if st.session_state.df[col].dtype == 'object':
                st.session_state.df[col] = st.session_state.df[col].str.strip()
        
        st.session_state.df['Purchase Cost'] = st.session_state.df['Purchase Cost'].replace({'[^0-9.]': ''}, regex=True).astype(float)
        st.session_state.df['Qty'] = pd.to_numeric(st.session_state.df['Qty'], errors='coerce').fillna(0).astype(int)

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
    st.dataframe(st.session_state.df)
