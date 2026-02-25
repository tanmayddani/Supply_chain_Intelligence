# Safe transform for your current sheets

import pandas as pd
from load_excel import load_excel
from load_api import load_api

def transform_data():
    orders_df, returns_df, people_df = load_excel()
    api_df = load_api()

    # Standardize column names
    orders_df.columns = [c.strip().lower().replace(" ", "_") for c in orders_df.columns]
    returns_df.columns = [c.strip().lower().replace(" ", "_") for c in returns_df.columns]
    people_df.columns = [c.strip().lower().replace(" ", "_") for c in people_df.columns]
    api_df.columns = [c.strip().lower().replace(" ", "_") for c in api_df.columns]

    # Compute lead time
    orders_df['order_date'] = pd.to_datetime(orders_df['order_date'])
    orders_df['ship_date'] = pd.to_datetime(orders_df['ship_date'])
    orders_df['lead_time_days'] = (orders_df['ship_date'] - orders_df['order_date']).dt.days

    full_df = orders_df.copy()

    # Merge Returns safely
    if 'order_id' in full_df.columns and 'order_id' in returns_df.columns:
        full_df = full_df.merge(returns_df[['order_id', 'returned']], on='order_id', how='left')

    # Merge API data if possible
    if 'product_name' in full_df.columns and 'title' in api_df.columns:
        full_df = full_df.merge(api_df, left_on='product_name', right_on='title', how='left')

    # Save processed data
    full_df.to_csv('data/processed_data.csv', index=False)
    print("Processed data saved: data/processed_data.csv")

    return full_df

if __name__ == "__main__":
    transform_data()