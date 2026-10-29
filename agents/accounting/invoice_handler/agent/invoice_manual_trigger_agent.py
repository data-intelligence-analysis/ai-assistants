###Local Script Listens Siri Voice Commands Request

#Add AI to synthesize the commands
import os
import subprocess
import time
import webbrowser
from flask import Flask, request, jsonify
from google import genai
# Add these Google Auth libraries to your orchestrator imports
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

app = Flask(name)
PORT = 8501
CONTAINER_NAME = "live_accounting_dashboard"
SCOPES = ['https://googleapis.com']

# Initialize Gemini Client (Ensure GEMINI_API_KEY is exported in your workstation shell)
client = genai.Client()

def refresh_token_if_expired():
    """
    Checks your existing token.json. If it is expired, it silently 
    renews it in the background without opening a browser.
    """
    if not os.path.exists('token.json'):
        raise FileNotFoundError("Initial token.json missing! Run generate_token.py once manually.")

    # Load existing credentials
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If the token is dead but we have a refresh token, renew it silently
    if creds and creds.expired and creds.refresh_token:
        print("Token expired. Refreshing authorization keys silently in background...")
        creds.refresh(Request())
        
        # Save the freshly updated token back to the file so it stays valid
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
        print("Token successfully updated.")
        
    return creds

def analyze_financial_intent(user_speech):
    """
    Evaluates speech via AI. Strictly allows only financial/accounting requests.
    Returns True if allowed, False otherwise.
    """
    prompt = f"""
    Analyze this voice command: "{user_speech}"
    Determine if this query is explicitly related to corporate financials, accounting, bills, business expenses, or invoice data.
    
    Respond with exactly one word:
    - ALLOWED: If it matches accounting/financial commands.
    - DENIED: If it is about marketing leads, sales metrics, CRM data, or anything else.
    
    Reply with nothing else but the classification word.
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        classification = response.text.strip().upper()
        return "ALLOWED" in classification
    except Exception as e:
        print(f"Guardrail engine error: {e}")
        return False

@app.route('/trigger-dashboard', methods=['POST'])
def trigger_dashboard():
    data = request.get_json(silent=True) or {}
    user_command = data.get('command', '')
    
    print(f"Evaluating raw speech entry: '{user_command}'")
    
    # Financial Intent Guardrail Check
    is_financial = analyze_financial_intent(user_command)
    
    if not is_financial:
        print("Command blocked: Out of financial/accounting scope.")
        return jsonify({
            "status": "rejected", 
            "message": "Access Denied. This engine is locked to strictly financial and accounting protocols."
        }), 403

    print("Command accepted. Initializing live workspace environment...")
    
    # Teardown any running dashboard instances
    subprocess.run(f"docker rm -f {CONTAINER_NAME}", shell=True, capture_output=True)
    
    # Read your pre-authenticated local token file to inject straight into the ephemeral container environment variables
    # This completely bypasses the need for GitHub Actions or cloud tables
    try:
        with open('token.json', 'r') as f:
            gmail_token_string = f.read()
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "Workstation is missing a valid pre-authorized token.json credential file."}), 500

    # Run container, mapping the live data token as an environment setting
    cmd = (
        f"docker run -d --name {CONTAINER_NAME} "
        f"-p {PORT}:8501 "
        f"-e GOOGLE_TOKEN_JSON='{gmail_token_string}' "
        f"live-accounting-image"
    )
    
    subprocess.run(cmd, shell=True, check=True)
    time.sleep(2.5)
    webbrowser.open(f"http://localhost:{PORT}")
    
    return jsonify({"status": "success", "message": "Live analytics session generated successfully."})

if __name__ == '__main__':
    print("Pre-compiling live application dependencies...")
    subprocess.run("docker build -t live-accounting-image .", shell=True)
    app.run(host='0.0.0.0', port=5001)

#Directly from google sheets
'''import os
import subprocess
import time
import webbrowser
from flask import Flask, jsonify

app = Flask(__name__)

PORT = 8501
CONTAINER_NAME = "ephemeral_streamlit_dashboard"
SHEET_EXPORT_LINK = "https://google.com"

@app.route('/trigger-dashboard', methods=['POST', 'GET'])
def trigger_dashboard():
    # Teardown any existing active runtime container first
    subprocess.run(f"docker rm -f {CONTAINER_NAME}", shell=True, capture_output=True)
    
    # Run the isolated environment on command
    cmd = (
        f"docker run -d --name {CONTAINER_NAME} "
        f"-p {PORT}:8501 "
        f"-e SHEET_CSV_URL=\"{SHEET_EXPORT_LINK}\" "
        f"streamlit-dashboard-image"
    )
    
    subprocess.run(cmd, shell=True, check=True)
    
    # Allow container service boot buffer window
    time.sleep(2)
    
    # Direct system command to trigger dashboard automatically inside local web browser
    webbrowser.open(f"http://localhost:{PORT}")
    
    return jsonify({"status": "success", "message": "Ephemeral Streamlit dashboard initiated successfully."})

if __name__ == '__main__':
    # Build container system configuration context once upon initial execution wrapper boot
    print("Preparing local Docker image context framework...")
    subprocess.run("docker build -t streamlit-dashboard-image .", shell=True)
    app.run(host='0.0.0.0', port=5001)'''
