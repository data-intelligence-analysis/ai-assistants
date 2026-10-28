'''import os
import subprocess
import time
import webbrowser
from flask import Flask, request, jsonify
# Using the standard modern google-genai library
from google import genai
from google.genai import types

app = Flask(__name__)

PORT = 8501
CONTAINER_NAME = "ephemeral_streamlit_dashboard"
SHEET_EXPORT_LINK = "https://google.com"

# Initialize Gemini Client (Ensure GEMINI_API_KEY is set in your local environment)
client = genai.Client()

def classify_voice_intent(user_speech):
    """Uses AI to determine what dashboard or action the user wants."""
    prompt = f"""
    You are an AI routing assistant for a local dashboard framework.
    Analyze the following user voice command and classify it into one of these strict categories:
    - INVOICES (for expenses, spending, bills, invoice receipts, layout data costs)
    - SALES (for revenue, pipeline, deals, sales targets)
    - LEADS (for marketing, signups, new clients, conversions)
    - UNKNOWN (if it doesn't match anything useful)

    User voice command: "{user_speech}"
    
    Respond with ONLY the category name. Do not include extra text.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip().upper()
    except Exception as e:
        print(f"AI Classification failed, defaulting to INVOICES. Error: {e}")
        return "INVOICES"

@app.route('/trigger-dashboard', methods=['POST'])
def trigger_dashboard():
    data = request.get_json(silent=True) or {}
    user_command = data.get('command', '')
    
    print(f"Received raw voice input: '{user_command}'")
    
    # Let AI determine what the user is actually asking for
    intent = classify_voice_intent(user_command)
    print(f"AI classified intent as: {intent}")
    
    if intent == "INVOICES":
        # Clear existing workspace
        subprocess.run(f"docker rm -f {CONTAINER_NAME}", shell=True, capture_output=True)
        
        # Spin up the Streamlit docker container specifically filtered or targeted
        cmd = (
            f"docker run -d --name {CONTAINER_NAME} "
            f"-p {PORT}:8501 "
            f"-e SHEET_CSV_URL=\"{SHEET_EXPORT_LINK}\" "
            f"streamlit-dashboard-image"
        )
        subprocess.run(cmd, shell=True, check=True)
        time.sleep(2)
        webbrowser.open(f"http://localhost:{PORT}")
        
        return jsonify({"status": "success", "routing": "INVOICES", "message": "Launched invoice dashboard."})
    
    elif intent == "SALES":
        # Placeholder: You can easily route to a different container or view here
        return jsonify({"status": "success", "routing": "SALES", "message": "Sales view under construction."})
        
    elif intent == "LEADS":
        # Placeholder: Route to marketing metrics
        return jsonify({"status": "success", "routing": "LEADS", "message": "Leads view under construction."})
        
    else:
        return jsonify({"status": "ignored", "routing": "UNKNOWN", "message": "Command not recognized by AI routing engine."}), 400

if __name__ == '__main__':
    print("Preparing local Docker image context...")
    subprocess.run("docker build -t streamlit-dashboard-image .", shell=True)
    app.run(host='0.0.0.0', port=5001)'''
