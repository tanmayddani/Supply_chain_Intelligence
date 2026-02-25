# scripts/etl.py
import pandas as pd
from google.cloud import bigquery
from google.cloud.bigquery import SchemaField
import os

# -----------------------------
# Helpers
# -----------------------------
def normalize_columns(df):
    """Strip spaces, lowercase, replace spaces with underscores."""
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    return df

def convert_datetime_columns(df):
    """Convert datetime64 columns to Python datetime for BigQuery."""
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].apply(lambda x: x.to_pydatetime() if pd.notnull(x) else None)
    return df

def get_schema_from_df(df):
    """Infer BigQuery schema from dataframe."""
    schema = []
    for col, dtype in zip(df.columns, df.dtypes):
        if 'int' in str(dtype):
            schema.append(SchemaField(col, "INTEGER"))
        elif 'float' in str(dtype):
            schema.append(SchemaField(col, "FLOAT"))
        elif 'datetime' in str(dtype):
            schema.append(SchemaField(col, "TIMESTAMP"))
        else:
            schema.append(SchemaField(col, "STRING"))
    return schema

# -----------------------------
# Load to BigQuery
# -----------------------------
def load_to_bigquery(fact_orders, dim_product, dim_customer, dim_people, dim_api_product):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\tanma\OneDrive\Desktop\SupplyChainProject\service-account.json"
    project_id = "supplychainproject-488405"
    dataset_id = f"{project_id}.supply_chain"
    client = bigquery.Client(project=project_id)

    # Create dataset if not exists
    try:
        client.get_dataset(dataset_id)
        print(f"✅ Dataset exists: {dataset_id}")
    except:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        client.create_dataset(dataset)
        print(f"✅ Dataset created: {dataset_id}")

    # Dictionary of tables to load
    tables = {
        "fact_orders": fact_orders,
        "dim_product": dim_product,
        "dim_customer": dim_customer,
        "dim_people": dim_people,
        "dim_api_product": dim_api_product
    }

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")

    for table_name, df in tables.items():
        if df is None or df.empty:
            print(f"⚠️ Skipping empty table: {table_name}")
            continue

        df = convert_datetime_columns(df)
        schema = get_schema_from_df(df)
        job_config.schema = schema

        client.load_table_from_dataframe(df, f"{dataset_id}.{table_name}", job_config=job_config).result()
        print(f"✅ {table_name} loaded into BigQuery")

# -----------------------------
# ETL Function
# -----------------------------
def etl_mysql_to_bigquery():
    processed_file = "data/processed_data.csv"
    df = pd.read_csv(processed_file, parse_dates=True)
    df = normalize_columns(df)

    # Build dimension tables based on existing columns
    dim_product = df[['product_id','product_name','category','sub-category']].drop_duplicates() if set(['product_id','product_name','category','sub-category']).issubset(df.columns) else pd.DataFrame()
    dim_customer = df[['customer_id','customer_name','segment','city','state','country']].drop_duplicates() if set(['customer_id','customer_name','segment','city','state','country']).issubset(df.columns) else pd.DataFrame()
    dim_people = df[['customer_name']].drop_duplicates() if 'customer_name' in df.columns else pd.DataFrame()
    dim_api_product = pd.DataFrame()  # empty placeholder, load separately if needed

    fact_orders = df.copy()

    load_to_bigquery(fact_orders, dim_product, dim_customer, dim_people, dim_api_product)

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    if not os.path.exists("data/processed_data.csv"):
        print("⚠️ Processed file not found. Run transform.py first.")
    else:
        etl_mysql_to_bigquery()