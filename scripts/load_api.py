# scripts/load_api.py

import requests
import pandas as pd

def load_api(api_url="https://fakestoreapi.com/products"):
    """
    Load products from Fake Store API
    Returns:
        api_df (DataFrame)
    """
    response = requests.get(api_url)
    api_data = response.json()
    api_df = pd.DataFrame(api_data)
    return api_df