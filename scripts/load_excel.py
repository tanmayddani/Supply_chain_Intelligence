# scripts/load_excel.py

import pandas as pd

def load_excel(file_path='data/global_superstore.xlsx'):
    """
    Load the Excel sheets: Orders, Returns, People
    Returns:
        orders_df, returns_df, people_df
    """
    # Load all sheets
    all_sheets = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')

    # Debug: show available sheets
    print("Available sheets in Excel:", list(all_sheets.keys()))

    # Load individual sheets using correct names
    orders_df = all_sheets['Orders']
    returns_df = all_sheets['Returns']
    people_df = all_sheets['People']

    return orders_df, returns_df, people_df