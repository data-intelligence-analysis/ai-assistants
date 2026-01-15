"""
ETL Agent for Accounting Reports
Runs daily via GitHub Actions
Decides if monthly, quarterly, or annual reports should be generated.
- Generates monthly reports on the 1st of each month
- Generates quarterly reports on the 1st of January, April, July, October
- Generates annual reports on January 1st
Saves reports as PDFs and can also send them via Telegram/Google Sheets/Excel
"""


import os
import datetime as dt
from pathlib import Path
# from agent import *
from send_reports import send_telegram_reports, send_whatsapp_reports
from statements import income_statement, balance_sheet
from pdf_render import income_statement_pdf, balance_sheet_pdf
from categorizer import Categorizer
from plaid_loader import load_plaid_transactions
from file_loader import load_google_sheets, load_excel_files, load_csv_files
from connectors.google_sheets import fetch_google_sheets
from connectors.excel import fetch_excel_from_url

# OUTPUT_DIR = Path(__file__).parent / 'output'

# def main():
#     # Run agent logic
#     # agent.py already generates PDFs
#     # Here we just call agent.py as module
#     import subprocess
#     subprocess.run(['python','agent.py'])
    
#     # Send PDFs via Telegram
#     pdfs = list(OUTPUT_DIR.glob('*.pdf'))
#     if pdfs:
#         send_reports([str(p) for p in pdfs])
#         print(f"Sent {len(pdfs)} reports to Telegram")

# if __name__=='__main__':
#     main()


# OUTPUT_DIR = "accounting_agent/output"
OUTPUT_DIR = Path(__file__).parent / 'output'

def is_last_day_of_month(date):
    next_day = date + dt.timedelta(days=1)
    return next_day.month != date.month

def is_last_day_of_quarter(date):
    return is_last_day_of_month(date) and date.month in [3, 6, 9, 12]

def is_last_day_of_year(date):
    return is_last_day_of_month(date) and date.month == 12

def run_etl():
    today = dt.date.today()

    # --- Load Data ---
    print("Loading data from sources...")
    transactions = []
    transactions += load_google_sheets()
    transactions += load_excel_files()

    if not transactions:
        print("No transactions found. Exiting.")
        return

    # --- Always generate daily statement ---
    print("Generating daily income statement...")
    inc_stmt = income_statement(transactions, freq="daily")
    bal_sheet = balance_sheet(transactions)

    inc_pdf = os.path.join(OUTPUT_DIR, f"Income_Statement_daily_{today}.pdf")
    bal_pdf = os.path.join(OUTPUT_DIR, f"Balance_Sheet_daily_{today}.pdf")
    income_statement_pdf(inc_stmt, inc_pdf)
    balance_sheet_pdf(bal_sheet, bal_pdf)

    send_telegram_reports(inc_pdf)
    send_telegram_reports(bal_pdf)

    # --- Conditional monthly/quarterly/annual ---
    if is_last_day_of_month(today):
        print("Generating monthly report...")
        inc_stmt = income_statement(transactions, freq="monthly")
        bal_sheet = balance_sheet(transactions)

        inc_pdf = os.path.join(OUTPUT_DIR, f"Income_Statement_monthly_{today}.pdf")
        bal_pdf = os.path.join(OUTPUT_DIR, f"Balance_Sheet_monthly_{today}.pdf")
        income_statement_pdf(inc_stmt, inc_pdf)
        balance_sheet_pdf(bal_sheet, bal_pdf)
        send_telegram_reports(inc_pdf)
        send_telegram_reports(bal_pdf)

    if is_last_day_of_quarter(today):
        print("Generating quarterly report...")
        inc_stmt = income_statement(transactions, freq="quarterly")
        bal_sheet = balance_sheet(transactions)

        inc_pdf = os.path.join(OUTPUT_DIR, f"Income_Statement_quarterly_{today}.pdf")
        bal_pdf = os.path.join(OUTPUT_DIR, f"Balance_Sheet_quarterly_{today}.pdf")
        income_statement_pdf(inc_stmt, inc_pdf)
        balance_sheet_pdf(bal_sheet, bal_pdf)
        send_telegram_reports(inc_pdf)
        send_telegram_reports(bal_pdf)

    if is_last_day_of_year(today):
        print("Generating annual report...")
        inc_stmt = income_statement(transactions, freq="annual")
        bal_sheet = balance_sheet(transactions)

        inc_pdf = os.path.join(OUTPUT_DIR, f"Income_Statement_annual_{today}.pdf")
        bal_pdf = os.path.join(OUTPUT_DIR, f"Balance_Sheet_annual_{today}.pdf")
        income_statement_pdf(inc_stmt, inc_pdf)
        balance_sheet_pdf(bal_sheet, bal_pdf)
        send_telegram_reports(inc_pdf)
        send_telegram_reports(bal_pdf)

def run_reports():
    today = dt.date.today()

    # Load transactions from multiple sources
    transactions = []
    transactions.extend(load_plaid_transactions())
    transactions.extend(load_google_sheets())
    transactions.extend(load_excel_files())
    transactions = Categorizer.classify(transactions)

    # Always generate a daily snapshot (optional)
    daily_income = income_statement(transactions, period="daily")
    daily_balance = balance_sheet(transactions)
    income_statement_pdf(daily_income, OUTPUT_DIR, f"Income_Statement_daily_{today}.pdf")
    balance_sheet_pdf(daily_balance, OUTPUT_DIR, f"Balance_Sheet_daily_{today}.pdf")

    # Monthly report: run on 1st of each month
    if today.day == 1:
        month_start = today.replace(day=1)
        prev_month_end = month_start - dt.timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        monthly_income = income_statement(transactions, start_date=prev_month_start, end_date=prev_month_end, period="monthly")
        monthly_balance = balance_sheet(transactions, date=prev_month_end)

        income_pdf = income_statement_pdf(monthly_income, OUTPUT_DIR, f"Income_Statement_monthly_{prev_month_start}_{prev_month_end}.pdf")
        balance_pdf = balance_sheet_pdf(monthly_balance, OUTPUT_DIR, f"Balance_Sheet_{prev_month_end}.pdf")

        send_telegram_reports(income_pdf)
        send_telegram_reports(balance_pdf)

    # Quarterly report: run on Jan 1, Apr 1, Jul 1, Oct 1
    if today.month in [1, 4, 7, 10] and today.day == 1:
        quarter_start_month = {1: 10, 4: 1, 7: 4, 10: 7}[today.month]
        year = today.year if today.month != 1 else today.year - 1
        quarter_start = dt.date(year, quarter_start_month, 1)
        quarter_end = today - dt.timedelta(days=1)

        quarterly_income = income_statement(transactions, start_date=quarter_start, end_date=quarter_end, period="quarterly")
        quarterly_balance = balance_sheet(transactions, date=quarter_end)

        income_pdf = income_statement_pdf(quarterly_income, OUTPUT_DIR, f"Income_Statement_quarterly_{quarter_start}_{quarter_end}.pdf")
        balance_pdf = balance_sheet_pdf(quarterly_balance, OUTPUT_DIR, f"Balance_Sheet_{quarter_end}.pdf")

        send_telegram_reports(income_pdf)
        send_telegram_reports(balance_pdf)

    # Annual report: run on Jan 1
    if today.month == 1 and today.day == 1:
        last_year = today.year - 1
        year_start = dt.date(last_year, 1, 1)
        year_end = dt.date(last_year, 12, 31)

        annual_income = income_statement(transactions, start_date=year_start, end_date=year_end, period="annual")
        annual_balance = balance_sheet(transactions, date=year_end)

        income_pdf = income_statement_pdf(annual_income, OUTPUT_DIR, f"Income_Statement_annual_{last_year}.pdf")
        balance_pdf = balance_sheet_pdf(annual_balance, OUTPUT_DIR, f"Balance_Sheet_{last_year}.pdf")

        send_telegram_reports(income_pdf)
        send_telegram_reports(balance_pdf)

def run_local_transactions():
    transactions = []
    transactions.extend(load_csv_files())
    transactions = Categorizer.classify(transactions)
    inc_stmt = income_statement(transactions)
    bal_sheet = balance_sheet(transactions)
    income_statement_pdf(inc_stmt, OUTPUT_DIR, f"Income_Statement_daily_{today}.pdf")
    balance_sheet_pdf(bal_sheet, OUTPUT_DIR, f"Balance_Sheet_daily_{today}.pdf")
    send_telegram_reports(inc_pdf)
    send_telegram_reports(bal_pdf)
    # send_whatsapp_reports(inc_pdf)
    # send_whatsapp_reports(bal_pdf)


def main():
    # Example: choose source
    source = "sheets"  # or "excel" or "csv"

    if source == "sheets":
        df = fetch_google_sheets(sheet_name="Accounting Data", worksheet="2025")
    elif source == "excel":
        url = "https://www.dropbox.com/s/example/myfile.xlsx?dl=1"
        df = fetch_excel_from_url(url, sheet_name="Transactions")
    else:
        df = pd.read_csv("sample_data.csv", parse_dates=["date"])

    # classify + generate reports
    df = classify_transactions(df)
    inc = income_statement(df)
    bal = balance_sheet({"assets": {}, "liabilities": {}, "equity": {}}, df, df["date"].max())

    generate_income_pdf(inc, "income_statement.pdf")
    generate_balance_pdf(bal, "balance_sheet.pdf")
    send_telegram_reports("Reports generated & sent!")

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # run_etl()
    # run_reports() ##all reports
    run_local_transactions()


