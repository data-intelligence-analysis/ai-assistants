import pandas as pd
import yaml
import glob
import os
import argparse, os, glob, yaml
import pandas as pd
from dateutil import parser as dateparser
from categorizer import Categorizer
from statements import income_statement, balance_sheet, income_statement_grouped, balance_sheet_grouped
from pdf_render import income_statement_pdf, balance_sheet_pdf, income_statement_pdf_grouped, balance_sheet_pdf_grouped
from file_loader import load_google_sheets, load_excel_files
from plaid_loader import load_plaid_transactions
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / 'output'
OUTPUT_DIR.mkdir(exist_ok=True)

# Load configuration
# cfg = yaml.safe_load(open('config.yaml'))

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
    return yaml.safe_load(f)
# Load CSV transactions
def load_csvs(globpat):
    files = glob.glob(globpat)
    # if not files:
    #     return pd.DataFrame(columns=['date','description','amount','account','category'])
    # df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    # df['date'] = pd.to_datetime(df['date'], errors='coerce')
    # df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    # return df.dropna(subset=['date','amount'])
    frames = []
    for fp in files:
        df = pd.read_csv(fp)
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=['date','description','amount','account','category'])
    df = pd.concat(frames, ignore_index=True)
    # normalize columns
    cols = {c.lower(): c for c in df.columns}
    

    def get(col):
        for k in cols:
            if k == col:
                return cols[k]
        return None
    # create normalized columns
    def pick(name, default=None):
        col = get(name)
        if col and col in df:
            return df[col]
        return default
        out = pd.DataFrame({
            'date': pd.to_datetime(pick('date'), errors='coerce'),
            'description': pick('description', ''),
            'amount': pd.to_numeric(pick('amount'), errors='coerce'),
            'account': pick('account', ''),
            'category': pick('category', ''),
        })
        out = out.dropna(subset=['date','amount'])
        return out

def categorize(df, config, rules_path):
    cat = Categorizer(rules_path)
    # map categories into account types
    mapping = config.get('account_mapping', {})
    def map_type(cat_name):
        for typ, cats in mapping.items():
        if cat_name in (cats or []):
            return typ
        return None
    cats, types = [], []
    for _, row in df.iterrows():
        base = str(row.get('category') or '')
        desc = str(row.get('description') or '')
        detected, _ = cat.classify(desc, fallback=base if base else None)
        ctype = map_type(detected) if detected else None
        cats.append(detected or 'Uncategorized')
        types.append(ctype or 'expense' if (row['amount']<0) else 'revenue')
    df = df.copy()
    df['category'] = cats
    df['category_type'] = types
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default='config.yaml')
    ap.add_argument('--period', default='monthly', choices=['monthly','quarterly','annual'])
    ap.add_argument('--start', default=None, help='YYYY-MM-DD')
    ap.add_argument('--end', default=None, help='YYYY-MM-DD')
    ap.add_argument('--outdir', default='output')
    args = ap.parse_args()
    cfg = load_config(args.config)
    os.makedirs(args.outdir, exist_ok=True)

    # Load transactions
    ds = cfg.get('datasource_csv', {})
    if ds.get('type') == 'csv':
        df = load_csvs(ds.get('csv_glob', 'data/transactions/*.csv'))
    else:
        # sheets support (optional; requires credentials), kept minimal here
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name('secrets/credentials.json', scope)
            client = gspread.authorize(creds)
            sh = client.open_by_key(ds['spreadsheet_key'])
            ws = sh.worksheet(ds.get('worksheet_name','Transactions'))
            records = ws.get_all_records()
            import pandas as pd
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            df = df.dropna(subset=['date','amount'])
        except Exception as e:
            raise SystemExit(f"Sheets error: {e}\\nSwitch datasource.type to 'csv' in config.yaml or provide credentials.")

    # Filter by date
    if args.start:
        df = df[df['date'] >= pd.Timestamp(args.start)]
    if args.end:
        df = df[df['date'] <= pd.Timestamp(args.end)]

    # Categorize
    # df = categorize(df, cfg, 'rules.yaml') old way
    df = categorize(df, cfg.get('rules', {}), 'config.yaml') #config.yaml

    # Build Income Statement
    is_df = income_statement_grouped(df, period=args.period)
    # Build Balance Sheet as-of end date (or today)
    as_of = args.end or pd.Timestamp.today().strftime('%Y-%m-%d')
    bs = balance_sheet_grouped(cfg.get('opening_balances', {}), df, as_of_date=as_of)

    company = cfg.get('company', {}).get('name', 'Company')
    currency = cfg.get('company', {}).get('currency', 'USD')

    # PDF outputs
    is_path = os.path.join(args.outdir, f"Income_Statement_{args.period}_{args.start or 'start'}_{args.end or 'end'}.pdf")
    bs_path = os.path.join(args.outdir, f"Balance_Sheet_{as_of}.pdf")
    income_statement_pdf_grouped(is_path, company, f"{args.period} {args.start or ''} to {args.end or ''}".strip(), is_df, currency)
    balance_sheet_pdf_grouped(bs_path, company, bs, currency)

    # Also save CSV summaries
    is_df.to_csv(os.path.join(args.outdir, f"Income_Statement_{args.period}.csv"), index=False)
    bs_df.to_csv(os.path.join(args.outdir, f"Balance_Sheet_{as_of}.csv"), index=False)

    print("Generated:")
    print(is_path)
    print(bs_path)

def load_all_transactions(cfg):
    frames = []
    # CSVs
    csv_df = load_csvs(cfg['datasource_csv']['csv_glob']) 
    if not csv_df.empty: frames.append(csv_df)

    # Plaid
    plaid_df = load_plaid_transactions(cfg)
    if not plaid_df.empty: frames.append(plaid_df)

    # Google Sheets
    gsheet_df = load_google_sheets(cfg)
    if not gsheet_df.empty: frames.append(gsheet_df)

    # Excel files
    excel_df = load_excel_files(cfg)
    if not excel_df.empty: frames.append(excel_df)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    df = load_csvs(cfg['datasource_csv']['csv_glob'])

    # Categorize
    cat = Categorizer('rules.yaml')
    df['category'] = [cat.classify(r['description'], fallback=r.get('category','Uncategorized'))[0] for _,r in df.iterrows()]

    # Generate PDFs
    is_df = income_statement(df)
    bs = balance_sheet(cfg.get('opening_balances',{}), df, as_of_date='2025-03-31')

    income_statement_pdf(OUTPUT_DIR / 'Income_Statement_monthly_2025-01-01_2025-03-31.pdf', cfg['company']['name'], 'Jan-Mar 2025', is_df, cfg['company']['currency'])
    balance_sheet_pdf(OUTPUT_DIR / 'Balance_Sheet_2025-03-31.pdf', cfg['company']['name'], bs, cfg['company']['currency'])

if __name__ == 'main':
    main()

