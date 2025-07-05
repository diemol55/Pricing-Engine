# Pricing Engine

This project is a standalone pricing engine built with Streamlit, Pandas, and SQLite. It allows users to upload purchase data, calculate landed costs, recommended retail prices (RRPP), and tiered pricing, while also managing RRPP markup tables and category multipliers.

## Features

-   **Flexible File Upload:** Supports both Excel (.xlsx, .xls) and CSV (.csv) file formats for purchase data.
-   **Downloadable Template:** Provides a CSV template with the correct column layout (`QtyPart`, `NumberInv`, `#Purchase`, `CostCategory`) for easy data preparation.
-   **Intelligent Data Handling:** Automatically renames uploaded columns to internal application standards (`Qty`, `Part Number`, `Purchase Cost`, `Category`).
-   **Category Mismatch Correction:** Identifies and allows interactive correction of mismatched categories in uploaded files using a dropdown selection of valid categories.
-   **Dynamic Input Parameters:** Users can specify currency, exchange rate, total freight cost, and freight mode.
-   **Customizable RRPP Markup Table:** View, edit, save, and reset the RRPP markup table directly within the application. Changes are timestamped and flagged by type (`individual_change`, `reset`, `price_increase`).
-   **Editable Category Multipliers:** View, edit, save, and reset category-specific multipliers. Changes are timestamped and flagged by type (`individual_change`, `reset`, `price_increase`).
-   **Percentage-Based Price Increase:** Apply a percentage increase to either the global RRPP markup table or to specific (or all) category multipliers.
-   **Comprehensive Pricing Calculation:** Calculates landed cost, RRPP, and up to five tiers of pricing.
-   **Data Persistence:** Stores RRPP markup tables, category multipliers, and calculated priced parts in a local SQLite database (`pricing_engine.db`).
-   **Save and Download:** A single button to save calculated pricing data to the database (with a timestamp) and trigger a CSV download of the results (excluding internal calculation columns).
-   **Application Reset:** A dedicated button to clear the application's session state and reload it to its initial configuration.

## Project Structure

-   `Welcome.py`: The main Streamlit application entry point, serving as the welcome page.
-   `pages/`: Directory containing the individual pages of the application:
    -   `1_Upload_and_Validate.py`: Handles file uploads, data validation, and category mismatch correction.
    -   `2_Configure_Pricing_Rules.py`: Manages RRPP markup tables, category multipliers, and price increase functionality.
    -   `3_Calculate_and_Export.py`: Performs pricing calculations and allows saving/exporting of results.
-   `calculations.py`: Contains the core pricing logic, including functions for calculating landed cost, RRPP, and tiered pricing.
-   `database_setup.py`: A utility script for initializing and setting up the SQLite database schema, including baseline RRPP markup and category multipliers.
-   `pricing_engine.db`: The SQLite database file used for storing RRPP markup tables, category multipliers, and historical priced parts data.
-   `requirements.txt`: Lists the Python dependencies required to run the project.
-   `pyproject.toml`: Project metadata and dependencies.

## Getting Started

### Prerequisites

-   Python 3.8+

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
4.  **Initialize the database:**
    ```bash
    python database_setup.py
    ```
    This will create `pricing_engine.db` and populate it with initial RRPP markup and category multiplier data.

5.  **Run the Streamlit application:**
    ```bash
    streamlit run Welcome.py
    ```
    The application will open in your web browser, typically at `http://localhost:8501`.

## How to Use

1.  **Navigate:** Use the sidebar to navigate between the different sections of the application.
2.  **Upload a purchase file (Upload and Validate page):** Click on the "Upload purchase file (Excel or CSV)" button and select your data file. You can download a CSV template for the expected format.
3.  **Correct Mismatched Categories (Upload and Validate page - if prompted):** If your uploaded file contains categories not present in the system, a section will appear allowing you to correct them using a dropdown menu. Click "Apply Changes" after making corrections.
4.  **Set Input Parameters (Calculate and Export page):** Adjust the currency, exchange rate, total freight cost, and freight mode as needed.
5.  **Manage Markup and Multipliers (Configure Pricing Rules page - Optional):** Use the tabs to expand and edit the RRPP Markup Table or Category Multipliers. Remember to click "Save" after making changes or "Reset" to revert to defaults.
6.  **Apply Price Increase (Configure Pricing Rules page - Optional):** In the "Apply Price Increase" section, enter a percentage and choose whether to apply it to the RRPP Markup table (globally) or to specific (or all) Category Multipliers. Click "Apply Increase" to implement the change.
7.  **Calculate Pricing (Calculate and Export page):** Click the "Calculate Pricing" button to see the calculated landed costs, RRPP, and tiered pricing. This will display the results without saving them.
8.  **Save and Download (Calculate and Export page):** After calculating, click the "Save and Download" button to save the current calculated pricing data to the database (with a timestamp) and download a CSV file of the results. The application will then reload.
9.  **Reset App (Calculate and Export page):** If you wish to clear all session data and restart the application from its initial state, click the "Reset App" button.

## Database Schema

The `pricing_engine.db` database contains the following key tables:

-   `rrpp_markup_table`: Stores the RRPP markup data (`From`, `To`, `RRPP Markup`, `timestamp`, `change_type`).
-   `category_multipliers`: Stores the category multipliers (`Category`, `Multiplier`, `timestamp`, `change_type`).
-   `priced_parts`: Stores historical pricing calculation results, including all input and calculated columns, along with a `timestamp` for each entry.
