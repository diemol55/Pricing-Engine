import streamlit as st

st.set_page_config(page_title="Welcome", layout="wide")

st.title("Welcome to the Pricing Engine")

st.markdown("""
This application is a tool to help you calculate and manage pricing for your products.

**To get started, please navigate to the pages in the sidebar:**

- **1. Upload and Validate:** Upload your purchase data and correct any mismatched categories.
- **2. Configure Pricing Rules:** Manage your RRPP markup table, category multipliers, and apply price increases.
- **3. Calculate and Export:** Calculate the final pricing and export the results.
""")
