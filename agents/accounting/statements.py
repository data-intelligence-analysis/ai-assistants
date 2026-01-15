import pandas as pd
from dateutil.relativedelta import relativedelta

def to_period(df, period='monthly'):
    if period == 'monthly':
        return df.groupby([df['date'].dt.to_period('M')])
    if period == 'quarterly':
        # pandas period 'Q' honors quarter; use 'Q-DEC' default
        return df.groupby([df['date'].dt.to_period('Q')])
    if period == 'annual':
        return df.groupby([df['date'].dt.to_period('Y')])
    raise ValueError("period must be monthly|quarterly|annual")

def income_statement_grouped(transactions: pd.DataFrame, period='monthly'):
    # Expect columns: date, amount, category_type in {'revenue','cogs','expense'}
    df = transactions.copy()
    df = df[df['category_type'].isin(['revenue','cogs','expense'])]
    grouped = to_period(df, period)
    rows = []
    for per, g in grouped:
        rev = g[g['category_type']=='revenue']['amount'].sum()
        cogs = g[g['category_type']=='cogs']['amount'].sum()
        exp = g[g['category_type']=='expense']['amount'].sum()
        gross_profit = rev + cogs # cogs should be negative
        operating_income = gross_profit + exp # expenses negative
        net_income = operating_income # if no other income/expense
        rows.append({
            'period': str(per),
            'Revenue': round(rev,2),
            'COGS': round(cogs,2),
            'Gross Profit': round(gross_profit,2),
            'Operating Expenses': round(exp,2),
            'Net Income': round(net_income,2),
        })
    return pd.DataFrame(rows)
def balance_sheet_grouped(opening_balances: dict, transactions: pd.DataFrame, as_of_date):
    # opening_balances: dict with assets/liabilities/equity dicts
    # transactions: may include movements affecting assets/liabilities/equity accounts
    # For simplicity, we compute retained earnings from net income YTD.
    df = transactions.copy()
    df = df[df['date'] <= pd.Timestamp(as_of_date)]
    # Sum by category_type
    rev = df[df['category_type']=='revenue']['amount'].sum()
    cogs = df[df['category_type']=='cogs']['amount'].sum()
    exp = df[df['category_type']=='expense']['amount'].sum()
    net_income = rev + cogs + exp
    # Start with opening balances
    assets = opening_balances.get('assets', {}).copy()
    liabilities = opening_balances.get('liabilities', {}).copy()
    equity = opening_balances.get('equity', {}).copy()

    # Apply any explicit asset/liability transactions if provided via 'account' column
    # If a row has account that belongs to assets/liabilities, add amount to that account.
    for _, row in df.iterrows():
        acct = row.get('account') or ''
        amt = float(row.get('amount') or 0)
        if acct in assets:
            assets[acct] = round(assets.get(acct,0)+amt,2)
        elif acct in liabilities:
            liabilities[acct] = round(liabilities.get(acct,0)+amt,2)
        # equity accounts typically aren't directly hit except owner draws/contribs

    # Update retained earnings
    equity['RetainedEarnings'] = round(equity.get('RetainedEarnings', 0) + net_income, 2)

    # Totals
    total_assets = round(sum(assets.values()),2)
    total_liabilities = round(sum(liabilities.values()),2)
    total_equity = round(sum(equity.values()),2)
    return {
        'as_of': str(pd.Timestamp(as_of_date).date()),
        'assets': assets,
        'liabilities': liabilities,
        'equity': equity,
        'totals': {
            'Assets': total_assets,
            'Liabilities + Equity': round(total_liabilities + total_equity, 2)
        },
        'net_income_ytd': round(net_income,2),
    }

def income_statement(df: pd.DataFrame, period='monthly'):
    # Group by month
    df['period'] = to_period(df, period)
    revenue = df[df['amount'] > 0].groupby('period')['amount'].sum().rename('Revenue')
    expenses = df[df['amount'] < 0].groupby('period')['amount'].sum().abs().rename('Expenses')
    net = (revenue - expenses).rename('Net Income')
    return pd.concat([revenue, expenses, net], axis=1).fillna(0)

def balance_sheet(opening_balances: dict, df: pd.DataFrame, as_of_date):
    assets = opening_balances.get('assets',{}).copy()
    liabilities = opening_balances.get('liabilities',{}).copy()
    equity = opening_balances.get('equity',{}).copy()
    totals = {
        'Assets': sum(assets.values()),
        'Liabilities + Equity': sum(liabilities.values()) + sum(equity.values())
    }
    return {'as_of': as_of_date, 'totals': totals}
