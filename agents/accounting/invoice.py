import os
import re
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://googleapis.com',
    'https://googleapis.com',
    'https://googleapis.com'
]

# ID of your target Google Sheet and specific application email search string
SPREADSHEET_ID = os.environ.get('GOOGLE_SPREADSHEET_ID', 'YOUR_SPREADSHEET_ID_HERE')
APP_EMAIL_FILTER = 'from:no-reply@specificapp.com subject:"Invoice"'

def get_google_services():
    creds = None
    # Token structure managed securely via GitHub secrets or environment mapping
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Fallback to local creation context if secrets aren't present
            client_config = {
                "installed": {
                    "client_id": os.environ.get("GCP_CLIENT_ID"),
                    "project_id": os.environ.get("GCP_PROJECT_ID"),
                    "auth_uri": "https://google.com",
                    "token_uri": "https://googleapis.com",
                    "client_secret": os.environ.get("GCP_CLIENT_SECRET"),
                    "redirect_uris": ["http://localhost"]
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    gmail_service = build('gmail', 'v1', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    return gmail_service, sheets_service

def parse_invoice_body(body_text):
    """
    Custom parsing logic based on your specific application text layout.
    Modify regex targets to fit your specific receipt formatting.
    """
    invoice_id = "UNKNOWN"
    amount = "0.00"
    date = "UNKNOWN"

    inv_match = re.search(r'Invoice\s*#?\s*([A-Z0-9\-]+)', body_text, re.IGNORECASE)
    amt_match = re.search(r'\$\s*([0-9]+\.[0-9]{2})', body_text)
    date_match = re.search(r'(?:Date|Billing Period):\s*([A-Za-z0-9\s,]+)', body_text)

    if inv_match: invoice_id = inv_match.group(1)
    if amt_match: amount = amt_match.group(1)
    if date_match: date = date_match.group(1).strip()

    return [date, invoice_id, amount]

def process_invoices():
    gmail, sheets = get_google_services()
    
    # Query messages
    response = gmail.users().messages().list(userId='me', q=APP_EMAIL_FILTER).execute()
    messages = response.get('messages', [])
    
    if not messages:
        print("No matching new invoices found.")
        return

    extracted_rows = []
    for msg in messages:
        msg_data = gmail.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        payload = msg_data.get('payload', {})
        body = ""

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        else:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        parsed_data = parse_invoice_body(body)
        extracted_rows.append(parsed_data)

    # Append rows to Google Sheet
    body = {'values': extracted_rows}
    result = sheets.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1!A:C',
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()
    print(f"Successfully appended {len(extracted_rows)} invoices to Google Sheet.")

if __name__ == '__main__':
    process_invoices()
