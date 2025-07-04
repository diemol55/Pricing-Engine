import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Pricing Tool", layout="wide")
st.title("📦 Ozwide Pricing Calculator")

# File Upload
uploaded_file = st.file_uploader("Upload purchase file (Excel)", type=[".xlsx", ".xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()  # Remove whitespace from headers

    st.subheader("File Preview")
    st.dataframe(df.head(20))

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

    show_rrpp_editor = st.checkbox("Edit RRPP Markup Table", value=False)

    conn = sqlite3.connect("local_pricing.db")
    try:
        markup_data = pd.read_sql("SELECT * FROM rrpp_markup_table", conn)
    except:
        markup_data = pd.DataFrame([
            [0.00, 2.49, 2.586508714], [2.50, 4.99, 2.330134294], [5.00, 7.99, 2.102174088],
            [8.00, 9.99, 1.900946641], [10.00, 11.99, 1.7247705], [12.00, 14.99, 1.57196421],
            [15.00, 16.99, 1.440846316], [17.00, 19.99, 1.329735365], [20.00, 21.99, 1.236949903],
            [22.00, 24.99, 1.160808475], [25.00, 27.99, 1.099629626], [28.00, 29.99, 1.051731904],
            [30.00, 34.99, 1.015433853], [35.00, 39.99, 0.989054019], [40.00, 44.99, 0.970910948],
            [45.00, 49.99, 1.050687299], [50.00, 54.99, 1.052406441], [55.00, 59.99, 1.057554945],
            [60.00, 69.99, 1.217670698], [70.00, 79.99, 1.214866467], [80.00, 89.99, 0.985666114],
            [90.00, 99.99, 0.933296661], [100.00, 109.99, 0.920515342], [110.00, 119.99, 0.900837698],
            [120.00, 149.99, 0.872582275], [150.00, 169.99, 0.834067618], [170.00, 199.99, 0.783612273],
            [200.00, 249.99, 0.719534787], [250.00, 299.99, 0.701120724], [300.00, 499.99, 0.543787571],
            [500.00, 749.99, 0.428754933], [750.00, 999.99, 0.293374337], [1000.00, 5000.00, 0.135964327]
        ], columns=["From", "To", "RRPP Markup"])

    if show_rrpp_editor:
        st.subheader("🛠️ RRPP Markup Table")
        edited_markup = st.data_editor(markup_data, use_container_width=True, num_rows="dynamic")
        edited_markup.to_sql("rrpp_markup_table", conn, if_exists="replace", index=False)
    else:
        edited_markup = markup_data

    category_multipliers = {
        "Speciality": 2.2,
        "Speciality Fast": 1.5,
        "Universal": 0.9,
        "Diagnostic": 1.7,
        "ATS": 1,
        "PICO": 1.2,
        "Local": 1,
        "N/A": 1,
        "Trucks": 3,
        "Autool": 1.45
    }

    if st.button("Calculate Price"):
        try:
            df['Purchase Cost'] = df['Purchase Cost'].replace('[\$,]', '', regex=True).astype(float)
            df['Qty'] = df['Qty'].astype(float)

            total_purchase = (df['Qty'] * df['Purchase Cost']).sum()
            df['Purchase Cost AUD'] = df['Purchase Cost'] / exchange_rate if currency != "AUD" else df['Purchase Cost']

            df['Landed Cost AUD'] = df.apply(lambda row: row['Purchase Cost AUD'] + (((row['Qty'] * row['Purchase Cost']) / total_purchase) * freight_cost) / row['Qty'], axis=1)

            def lookup_rrpp_markup(cost):
                row = edited_markup[(edited_markup['From'] <= cost) & (cost <= edited_markup['To'])]
                return float(row['RRPP Markup'].iloc[0]) if not row.empty else 1.0

            df['RRPP Markup'] = df['Landed Cost AUD'].apply(lookup_rrpp_markup)
            df['Category Multiplier'] = df['Category'].map(category_multipliers).fillna(1.0)
            df['RRPP'] = (df['Landed Cost AUD'] * ((df['RRPP Markup'] * df['Category Multiplier'])+1)).round(0)

            df['Tier 1'] = df.apply(lambda row: round(row['RRPP'] * 0.95 if row['Category'] in ['Speciality Fast', 'Universal', 'Local'] else row['RRPP'] * 0.9), axis=1)
            df['Tier 2'] = df.apply(lambda row: round(row['RRPP'] * 1.37) if ((-row['RRPP'] + (row['Tier 1'] * 0.95)) / row['RRPP']) > 0.37 else round(row['Tier 1'] * 0.95), axis=1)
            df['Tier 3'] = df.apply(lambda row: round(row['RRPP'] * 1.35) if ((-row['RRPP'] + (row['Tier 2'] * 0.9)) / row['RRPP']) > 0.35 else round(row['Tier 2'] * 0.9), axis=1)
            df['Tier 4'] = df.apply(lambda row: round(row['RRPP'] * 1.3) if ((-row['RRPP'] + (row['Tier 3'] * 0.85)) / row['RRPP']) > 0.3 else round(row['Tier 3'] * 0.85), axis=1)
            df['Tier 5'] = df.apply(lambda row: round(row['RRPP'] * 1.25) if ((-row['RRPP'] + (row['Tier 4'] * 0.95)) / row['RRPP']) > 0.25 else round(row['Tier 4'] * 0.95), axis=1)

            st.success("Landed Cost, RRPP, and Tiers calculated successfully.")
            st.dataframe(df)

            df.to_sql("priced_parts", conn, if_exists="replace", index=False)
            conn.close()
            st.success("Data saved to local_pricing.db (tables: priced_parts, rrpp_markup_table)")

        except Exception as e:
            st.error(f"An error occurred: {e}")
