# Gemini Workspace

This file is used by the Gemini CLI to store information about the project and its context. It is not intended to be version-controlled.

## Project Overview

This project is a standalone pricing engine built with Streamlit, Pandas, and SQLite. It allows users to upload purchase data, calculate landed costs, recommended retail prices (RRPP), and tiered pricing, while also managing RRPP markup tables and category multipliers.

## Technologies Used

-   **Frontend:** Streamlit
-   **Data Manipulation:** Pandas
-   **Database:** SQLite

## Project Structure

-   `Welcome.py`: The main Streamlit application entry point, serving as the welcome page.
-   `pages/`: Directory containing the individual pages of the application:
    -   `1_Upload_and_Validate.py`: Handles file uploads, data validation, and interactive category editing.
    -   `2_Calculate_and_Export.py`: Performs pricing calculations and allows saving/exporting of results.
    -   `3_Configure_Pricing_Rules.py`: Manages RRPP markup tables, category multipliers, and price increase functionality.
-   `calculations.py`: Contains the core pricing logic, including functions for calculating landed cost, RRPP, and tiered pricing.
-   `database_setup.py`: A utility script for initializing and setting up the SQLite database schema, including baseline RRPP markup and category multipliers.
-   `pricing_engine.db`: The SQLite database file used for storing RRPP markup tables, category multipliers, and historical priced parts data.
-   `requirements.txt`: Lists the Python dependencies required to run the project.
-   `pyproject.toml`: Project metadata and dependencies.

## Standards and Conventions

-   **Modular Design:** The application is structured as a multi-page Streamlit app, with each page having a specific purpose.
-   **Data Persistence:** Data is stored in a local SQLite database, with a dedicated script for schema setup.
-   **Change Tracking:** Changes to the RRPP markup table and category multipliers are timestamped and flagged by type (`individual_change`, `reset`, `price_increase`).
-   **User Input Validation:** The application validates uploaded data and provides a user-friendly way to correct errors.
-   **Session State Management:** Streamlit's session state is used to maintain data and state across different pages of the application. The session is cleared whenever a new file is uploaded to ensure a clean state. The default currency is set to "USD".
