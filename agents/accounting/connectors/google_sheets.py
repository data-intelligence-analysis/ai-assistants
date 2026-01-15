import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def fetch_google_sheets(sheet_name: str, worksheet: str, creds_path: str = "credentials.json"):
    """Fetch data from a Google Sheet and return as DataFrame"""
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)

    sheet = client.open(sheet_name).worksheet(worksheet)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df
