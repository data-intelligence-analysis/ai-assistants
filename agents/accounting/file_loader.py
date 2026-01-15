import pandas as pd
import requests
from io import BytesIO
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
import yaml
import glob


def load_config(config_path: str = "config.yaml"):
    """
    Load YAML configuration file into a Python dictionary.
    """
    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}


def load_from_sheets(spreadsheet_key, worksheet_name='Transactions', creds_path='secrets/credentials.json'):
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_key)
    ws = sh.worksheet(worksheet_name)
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    return df.dropna(subset=['date','description','amount','account','category'])

def load_google_sheets(creds_file="service_account.json"):
    """
    Load multiple Google Sheets defined in config.yaml
    Returns concatenated DataFrame
    """
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    client = gspread.authorize(creds)
    config = load_config()
    frames = []
    for entry in config.get("google_sheets", []):
        sheet_url = entry["sheet_url"]
        name = entry.get("name", "Sheet")
        sh = client.open_by_url(sheet_url)
        ws = sh.sheet1  # Default first sheet, could extend to match gid if needed
        df = pd.DataFrame(ws.get_all_records())
        df["Source"] = f"GoogleSheet:{name}"
        frames.append(df)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_excel_files():
    """
    Load Excel files from URLs with sheet name
    """
    config = load_config()
    frames = []
    for entry in config.get("excel_files", []):
        url = entry["file_url"]
        sheet_name = entry.get("sheet_name", 0)
        name = entry.get("name", "ExcelFile")

        try:
            response = requests.get(url)
            response.raise_for_status()
            df = pd.read_excel(BytesIO(response.content), sheet_name=sheet_name)
            df["Source"] = f"Excel:{name}"
            frames.append(df)
        except Exception as e:
            print(f"❌ Error loading Excel {name} from {url}: {e}")

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def load_csv_files():
    config = load_config()
    csv_glob = config['datasource_csv']['csv_glob']
    return pd.concat([pd.read_csv(f) for f in glob.glob(csv_glob)], ignore_index=True)