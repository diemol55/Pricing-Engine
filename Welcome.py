import streamlit as st

st.set_page_config(page_title="Welcome", layout="wide", page_icon="favicon.png")

# Initialize session state variables for input parameters if they don't exist
if 'currency' not in st.session_state:
    st.session_state.currency = "USD"
if 'exchange_rate' not in st.session_state:
    st.session_state.exchange_rate = 1.0
if 'freight_cost' not in st.session_state:
    st.session_state.freight_cost = 0.0
if 'freight_mode' not in st.session_state:
    st.session_state.freight_mode = "Auto"

st.title("Welcome to the Pricing Engine")

st.markdown("""
This application is a tool to help you calculate and manage pricing for your products.

**To get started, please navigate to the pages in the sidebar:**

- **1. Upload and Validate:** Upload your purchase data and correct any mismatched categories.
- **2. Calculate and Export:** Calculate the final pricing and export the results.
- **3. Configure Pricing Rules:** Manage your RRPP markup table, category multipliers, and apply price increases.
""")