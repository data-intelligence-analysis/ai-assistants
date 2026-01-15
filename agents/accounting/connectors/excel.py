import pandas as pd
import requests
import io

def fetch_excel_from_url(url: str, sheet_name: str = None):
    """Fetch Excel file from a cloud URL (Dropbox, OneDrive, Google Drive direct link)"""
    r = requests.get(url)
    r.raise_for_status()

    excel_data = io.BytesIO(r.content)
    df = pd.read_excel(excel_data, sheet_name=sheet_name)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df
