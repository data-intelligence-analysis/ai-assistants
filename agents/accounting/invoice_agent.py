import os
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
    app.run(host='0.0.0.0', port=5001)
