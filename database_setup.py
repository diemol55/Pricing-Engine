import pandas as pd
import sqlite3
from datetime import datetime

def get_initial_markup_data():
    return pd.DataFrame([
        [0.00, 2.49, 2.586508714],
        [2.50, 4.99, 2.330134294],
        [5.00, 7.99, 2.102174088],
        [8.00, 9.99, 1.900946641],
        [10.00, 11.99, 1.7247705],
        [12.00, 14.99, 1.57196421],
        [15.00, 16.99, 1.440846316],
        [17.00, 19.99, 1.329735365],
        [20.00, 21.99, 1.236949903],
        [22.00, 24.99, 1.160808475],
        [25.00, 27.99, 1.099629626],
        [28.00, 29.99, 1.051731904],
        [30.00, 34.99, 1.015433853],
        [35.00, 39.99, 0.989054019],
        [40.00, 44.99, 0.970910948],
        [45.00, 49.99, 1.050687299],
        [50.00, 54.99, 1.052406441],
        [55.00, 59.99, 1.057554945],
        [60.00, 69.99, 1.217670698],
        [70.00, 79.99, 1.214866467],
        [80.00, 89.99, 0.985666114],
        [90.00, 99.99, 0.933296661],
        [100.00, 109.99, 0.920515342],
        [110.00, 119.99, 0.900837698],
        [120.00, 149.99, 0.872582275],
        [150.00, 169.99, 0.834067618],
        [170.00, 199.99, 0.783612273],
        [200.00, 249.99, 0.719534787],
        [250.00, 299.99, 0.701120724],
        [300.00, 499.99, 0.543787571],
        [500.00, 749.99, 0.428754933],
        [750.00, 999.99, 0.293374337],
        [1000.00, 5000.00, 0.135964327]
    ], columns=["From", "To", "RRPP Markup"])

def get_initial_category_multipliers():
    return pd.DataFrame([
        ["Speciality", 2.2],
        ["Speciality Fast", 1.5],
        ["Universal", 0.9],
        ["Diagnostic", 1.7],
        ["ATS", 1],
        ["PICO", 1.2],
        ["Local", 1],
        ["N/A", 1],
        ["Trucks", 3],
        ["Autool", 1.45]
    ], columns=["Category", "Multiplier"])

def main():
    conn = sqlite3.connect("pricing_engine.db")
    cursor = conn.cursor()

    # Create rrpp_markup_table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rrpp_markup_table (
            "From" REAL,
            "To" REAL,
            "RRPP Markup" REAL,
            "timestamp" TEXT,
            "change_type" TEXT
        )
    """)

    # Create category_multipliers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category_multipliers (
            "Category" TEXT,
            "Multiplier" REAL,
            "timestamp" TEXT,
            "change_type" TEXT
        )
    """)

    # Insert initial data into rrpp_markup_table
    markup_data = get_initial_markup_data()
    markup_data["timestamp"] = datetime.now()
    markup_data["change_type"] = "initial_load"
    markup_data.to_sql("rrpp_markup_table", conn, if_exists="replace", index=False)

    # Insert initial data into category_multipliers
    category_multipliers = get_initial_category_multipliers()
    category_multipliers["timestamp"] = datetime.now()
    category_multipliers["change_type"] = "initial_load"
    category_multipliers.to_sql("category_multipliers", conn, if_exists="replace", index=False)

    # Create priced_parts table with a timestamp column if it doesn't exist
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS priced_parts (
            "Qty" REAL,
            "Inv #" TEXT,
            "Part Number" TEXT,
            "Purchase Cost" REAL,
            "Category" TEXT,
            "Purchase Cost AUD" REAL,
            "Landed Cost AUD" REAL,
            "RRPP Markup" REAL,
            "Category Multiplier" REAL,
            "RRPP" REAL,
            "Tier 1" REAL,
            "Tier 2" REAL,
            "Tier 3" REAL,
            "Tier 4" REAL,
            "Tier 5" REAL,
            "timestamp" TEXT
        )
    """)
    conn.commit()

    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    main()
