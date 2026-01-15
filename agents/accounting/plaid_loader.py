# Plaid loader template
import os
try:
    from plaid import Client
except:
    Client = None

def load_plaid_transactions(access_token: str, start_date: str, end_date: str):
    if Client is None:
        raise RuntimeError('plaid-python not installed')
    client_id = os.environ.get('PLAID_CLIENT_ID')
    secret = os.environ.get('PLAID_SECRET')
    env = os.environ.get('PLAID_ENV','sandbox')
    client = Client(client_id=client_id, secret=secret, environment=env)
    resp = client.Transactions.get(access_token, start_date=start_date, end_date=end_date)
    out = []
    for t in resp.get('transactions',[]):
        out.append({
            'date': t.get('date'),
            'description': t.get('name'),
            'amount': t.get('amount'),
            'account': t.get('account_id')
        })
    return out
