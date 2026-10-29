import os
from google_auth_oauthlib.flow import InstalledAppFlow

# This scope matches what our live Streamlit dashboard uses to read invoices
SCOPES = ['https://googleapis.com']

def create_persistent_token():
    if not os.path.exists('credentials.json'):
        print("❌ Error: 'credentials.json' not found in this folder!")
        print("Please download it from your Google Cloud Console first.")
        return

    print("🔄 Initializing local authorization flow...")
    # Opens a temporary local server port to capture the security callback redirect
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save the long-lived token credentials to token.json
    with open('token.json', 'w') as token_file:
        token_file.write(creds.to_json())
        
    print("\n✅ Success! 'token.json' has been created successfully.")
    print("Keep this file secret. You can now delete 'generate_token.py' and 'credentials.json'.")

if __name__ == '__main__':
    create_persistent_token()
