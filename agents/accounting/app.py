from flask import Flask, request, render_template, send_file, send_from_directory, redirect, url_for, flash, jsonify
from connectors.google_sheets import fetch_google_sheets
from connectors.excel import fetch_excel_from_url
from statements import income_statement, balance_sheet
from pdf_render import income_statement_pdf, balance_sheet_pdf
from categorizer import Categorizer
from send_reports import send_telegram_reports, send_whatsapp_reports
import os, werkzeug, subprocess
import pandas as pd
from pathlib import Path

# Add missing functions
def classify_transactions(df):
    """Classify transactions using the categorizer"""
    categorizer = Categorizer('config.yaml') #rules.yaml
    return categorizer.categorize(df)


BASE = Path(__file__).parent
UPLOAD_DIR = BASE / 'data' / 'transactions'
OUTPUT_DIR = BASE / 'output'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET','dev-secret')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/advanced')
def advanced():
    return render_template('advanced_index.html')

@app.route('/api/status')
def api_status():
    """API endpoint to check app status"""
    try:
        import requests
        response = requests.get('http://localhost:8080/', timeout=5)
        return jsonify({'running': response.status_code == 200})
    except:
        return jsonify({'running': False})

@app.route('/api/process', methods=['POST'])
def api_process():
    """API endpoint to process natural language commands"""
    try:
        data = request.get_json()
        message = data.get('message', '').lower()
        
        response = "I'm processing your request..."
        
        if 'start' in message and 'app' in message:
            # Start the app
            response = "✅ Starting the accounting app..."
            # Here you would start the app process
        elif 'stop' in message and 'app' in message:
            # Stop the app
            response = "✅ Stopping the accounting app..."
        elif 'google sheets' in message or 'sheets' in message:
            # Process Google Sheets
            response = "📊 Processing Google Sheets data and generating reports..."
        elif 'csv' in message:
            # Process CSV
            response = "📄 Processing CSV file and generating reports..."
        elif 'status' in message:
            # Check status
            try:
                import requests
                requests.get('http://localhost:8080/', timeout=5)
                response = "✅ App is running and responding"
            except:
                response = "❌ App is not running"
        else:
            response = "I understand you want help with: " + message + ". How can I assist you further?"
        
        return jsonify({
            'response': response,
            'status': {'running': True}  # You'd check actual status here
        })
        
    except Exception as e:
        return jsonify({'response': f'Error: {str(e)}'})

@app.route('/legacy')
def legacy_index():
    report_generated = False
    error = None

    if request.method == "POST":
        try:
            source = request.form["source"]

            if source == "csv":
                file = request.files["file"]
                df = pd.read_csv(file, parse_dates=["date"])
            elif source == "sheets":
                sheet_name = request.form["sheet_name"]
                worksheet = request.form["worksheet"]
                df = fetch_google_sheets(sheet_name, worksheet)
            elif source == "excel":
                url = request.form["excel_url"]
                sheet_name = request.form.get("excel_sheet") or None
                df = fetch_excel_from_url(url, sheet_name=sheet_name)
            else:
                raise ValueError("Invalid source selected.")

            # Process Data
            df = classify_transactions(df)
            inc = income_statement(df)
            bal = balance_sheet({"assets": {}, "liabilities": {}, "equity": {}}, df, df["date"].max())

            # Generate PDFs
            income_statement_pdf(inc, "income_statement.pdf")
            balance_sheet_pdf(bal, "balance_sheet.pdf")

            # Send to Telegram
            send_telegram_reports("Reports generated & sent via Flask UI!")

            report_generated = True

        except Exception as e:
            error = str(e)

    return render_template("index.html", report_generated=report_generated, error=error)


@app.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('file')
    if not f:
        flash('No file uploaded','error')
        return redirect(url_for('index'))
    filename = werkzeug.utils.secure_filename(f.filename)
    if not filename.lower().endswith('.csv'):
        flash('Only CSV files supported','error')
        return redirect(url_for('index'))
    f.save(UPLOAD_DIR / filename)
    flash(f'Uploaded {filename}','success')
    return redirect(url_for('index'))

@app.route('/generate', methods=['POST'])
def generate():
    subprocess.run(['python','agent.py'], cwd=str(BASE))
    flash('Generated PDFs','success')
    return redirect(url_for('index'))

# @app.route('/output/<path:filename>')
# def download(filename):
#     return send_from_directory(str(OUTPUT_DIR), filename, as_attachment=True)

@app.route("/download/<report>")
def download(report):
    if report == "income":
        return send_file("income_statement.pdf", as_attachment=True)
    elif report == "balance":
        return send_file("balance_sheet.pdf", as_attachment=True)
    else:
        return "Invalid report"

if __name__=='__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
