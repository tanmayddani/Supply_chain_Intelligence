🏭 Supply Chain Data System

A Supply Chain Data Integration System that integrates structured sales data and simulated product metadata into a dimensional data warehouse in Google BigQuery, with a real-time analytics dashboard built in Streamlit.

The system applies Python-based transformations, models data into a star schema, and exposes business insights through interactive visualizations.

📐 Architecture
Raw Data (CSV + API)
        ↓
Python ETL (Transformation & Surrogate Keys)
        ↓
Star Schema in BigQuery
        ↓
Analytical Views
        ↓
Streamlit Dashboard

🗂 Data Model
Fact Table
fact_orders – Stores transactional sales/order data
Dimension Tables
dim_product – Product metadata
dim_customer – Customer information
dim_people – people dimension

🚀 Run Locally
1️⃣ Clone & Setup
git clone <repo-url>
cd supply_chain_data_system
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

2️⃣ Run ETL Steps Individually
py scripts/load_api.py
py scripts/transform.py
py scripts/load_raw_sql.py

3️⃣ Set Google Cloud Credentials (Windows PowerShell)
$env:GOOGLE_APPLICATION_CREDENTIALS="path_to_service_account.json"

4️⃣ Run Complete ETL Pipeline
py scripts/etl.py

this loads data into BigQuery tables:

fact_orders
dim_customers
dim_people

5️⃣ Launch Streamlit Dashboard
py -m streamlit run dashboards\app.py

Dashboard provides:
📈 Revenue & order trends
🏆 Top customers & segments
🥧 Product category & sub-category distribution
📊 KPIs: Total Orders, Avg Order Value, Customer Count
🔎 Filters for date range, category, and customer segment

The system enables monitoring of vendor performance, order efficiency, and inventory health.
It converts raw data into structured insights, helping improve operational efficiency and data-driven decisionmaking.
The pipeline can be automated using schedulers for daily batch processing and extended with real-time data
streaming or demand forecasting models.
