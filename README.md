# Pricing Engine

This project is a standalone pricing engine built with Streamlit, Pandas, and SQLite.

## Features

- **File Upload:** Upload purchase files in Excel format (.xlsx, .xls).
- **Currency Conversion:** Convert purchase costs from different currencies to AUD.
- **Landed Cost Calculation:** Calculate the landed cost for each item, including freight costs.
- **RRPP Calculation:**  Calculate the Recommended Retail Price (RRPP) based on a customizable markup table.
- **Tiered Pricing:** Generate up to 5 tiers of pricing based on the RRPP.
- **Editable RRPP Markup Table:** View and edit the RRPP markup table directly in the application.
- **Data Persistence:** Save the priced parts and the RRPP markup table to a local SQLite database.
- **Export to CSV:** Export the priced parts to a CSV file.

## Project Structure

- `app.py`: The main Streamlit application file. It contains the UI, pricing logic, and database interactions.
- `local_pricing.db`: The SQLite database file used for storing RRPP markup tables and priced parts.
- `requirements.txt`: A list of the Python dependencies for the project.
- `pyproject.toml`: Project metadata and dependencies.

## Getting Started

### Prerequisites

- Python 3.8+

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    ```
2.  **Navigate to the project directory:**
    ```bash
    cd pricing-engine
    ```
3.  **Install the Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the Streamlit application:**
    ```bash
    streamlit run app.py
    ```
    The application will open in your web browser, typically at `http://localhost:8501`.

## How to Use

1.  **Upload a purchase file:** Click on the "Upload purchase file (Excel)" button and select your Excel file. The file should contain columns for `Purchase Cost` and `Qty`.
2.  **Set the input parameters:**
    - **Currency:** Select the currency of the purchase costs.
    - **Exchange Rate:** Enter the exchange rate to convert the purchase costs to AUD (if the currency is not AUD).
    - **Total Freight Cost:** Enter the total freight cost in AUD.
    - **Freight Mode:** Select "Auto" to distribute the freight cost automatically based on the purchase cost of each item, or "Manual" if you have a different method for calculating freight.
3.  **Edit the RRPP Markup Table (Optional):** Check the "Edit RRPP Markup Table" box to view and edit the markup table.
4.  **Calculate the price:** Click on the "Calculate Price" button to perform the pricing calculations.
5.  **View the results:** The priced parts will be displayed in a table.
6.  **Save the data:** The priced parts and the RRPP markup table will be automatically saved to the `local_pricing.db` database.
7.  **Export to CSV:** You can download the priced parts as a CSV file.

## Database

The application uses a local SQLite database (`local_pricing.db`) to store the following tables:

- `rrpp_markup_table`: Stores the RRPP markup table.
- `priced_parts`: Stores the priced parts data.

The database file will be created in the project root directory when the application is run for the first time.