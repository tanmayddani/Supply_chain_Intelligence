# scripts/load_raw_mysql.py
import pandas as pd
from sqlalchemy import create_engine
from load_excel import load_excel
from load_api import load_api

def load_raw_data_to_mysql():
    """
    Load all raw data (Excel + API) into MySQL database.
    - Excel sheets: Orders, Returns, People
    - API: Fake Store Products
    Handles dictionary columns in API (e.g., rating) for MySQL compatibility.
    """

    # MySQL connection details
    user = 'root'
    password = '369369'  # <-- replace with your MySQL password
    host = 'localhost'
    port = 3306
    database = 'supply_chain_db'  # <-- replace if your DB name is different

    # Create SQLAlchemy engine
    engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')

    # 1️⃣ Load Excel sheets
    orders_df, returns_df, people_df = load_excel()

    # Optional: clean column names
    orders_df.columns = [c.strip().lower().replace(" ", "_") for c in orders_df.columns]
    returns_df.columns = [c.strip().lower().replace(" ", "_") for c in returns_df.columns]
    people_df.columns = [c.strip().lower().replace(" ", "_") for c in people_df.columns]

    # 2️⃣ Load API data
    api_df = load_api()

    # Flatten 'rating' column if exists (dict -> separate columns)
    if 'rating' in api_df.columns:
        api_df['rating_rate'] = api_df['rating'].apply(lambda x: x.get('rate') if isinstance(x, dict) else None)
        api_df['rating_count'] = api_df['rating'].apply(lambda x: x.get('count') if isinstance(x, dict) else None)
        api_df = api_df.drop(columns=['rating'])

    # 3️⃣ Load each dataframe to MySQL
    orders_df.to_sql('orders_raw', con=engine, if_exists='replace', index=False)
    returns_df.to_sql('returns_raw', con=engine, if_exists='replace', index=False)
    people_df.to_sql('people_raw', con=engine, if_exists='replace', index=False)
    api_df.to_sql('api_products_raw', con=engine, if_exists='replace', index=False)

    print("✅ All raw data loaded into MySQL successfully!")

# Run script directly
if __name__ == "__main__":
    load_raw_data_to_mysql()