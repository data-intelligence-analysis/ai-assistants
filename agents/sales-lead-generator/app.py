from flask import Flask, render_template, send_from_directory, request, redirect, url_for, flash
import pandas as pd
import os
from pathlib import Path
import requests
import io

# optional gspread import for service-account access to Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials
    GSPREAD_AVAILABLE = True
except Exception:
    GSPREAD_AVAILABLE = False

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')


DEFAULT_LEAD_COLUMNS = [
    'Niche', 'Location', 'Company', 'Website', 'Phone', 'Email Address',
    'Initial Email', 'Follow-up 1', 'Follow-up 2', 'Calendar Link',
    'Status', 'Last Contacted', 'Lead Source', 'Profile URL',
    'Web Prompt', 'Loom Script', 'SMS Copy'
]


def get_data_paths():
    base = Path(__file__).resolve().parents[0]
    extracts = base / 'extracts'
    extracts.mkdir(parents=True, exist_ok=True)
    return {
        'csv': extracts / 'outreach.csv',
        'xlsx': extracts / 'outreach.xlsx',
        'test_csv': extracts / 'outreach_tst.csv'
    }


def load_data():
    paths = get_data_paths()
    csv_path = paths['csv']
    xlsx_path = paths['xlsx']
    test_csv = paths['test_csv']

    if csv_path.exists() and csv_path.stat().st_size > 0:
        try:
            return pd.read_csv(csv_path)
        except Exception:
            pass

    if xlsx_path.exists() and xlsx_path.stat().st_size > 0:
        try:
            return pd.read_excel(xlsx_path, engine='openpyxl')
        except Exception:
            pass

    if test_csv.exists() and test_csv.stat().st_size > 0:
        try:
            return pd.read_csv(test_csv)
        except Exception:
            pass

    return pd.DataFrame(columns=DEFAULT_LEAD_COLUMNS)


def save_data(df):
    csv_path = get_data_paths()['csv']
    df.to_csv(csv_path, index=False)


def fetch_google_sheet_csv(sheet_id, gid=0):
    """Try to fetch Google Sheet as CSV via export URL (works for public or shared sheets)."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            s = io.StringIO(r.text)
            df = pd.read_csv(s)
            return df
    except Exception:
        pass
    return None


def fetch_google_sheet_service(sheet_id, sheet_name=None):
    """Fetch Google Sheet using a service account JSON pointed by GOOGLE_SERVICE_ACCOUNT_FILE env var.
    Requires gspread to be installed and a valid service account JSON file path set in env.
    """
    if not GSPREAD_AVAILABLE:
        return None
    sa_file = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE')
    if not sa_file or not Path(sa_file).exists():
        return None
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        creds = ServiceAccountCredentials.from_service_account_file(sa_file, scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_key(sheet_id)
        worksheet = sh.sheet1 if sheet_name is None else sh.worksheet(sheet_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception:
        return None
    return df


def compute_metrics(df):
    total_leads = int(len(df))

    # Best-effort detection for verified email column
    verified_count = 0
    if 'verified' in df.columns:
        verified_count = int(df['verified'].astype(bool).sum())
    elif 'email_verified' in df.columns:
        verified_count = int(df['email_verified'].astype(bool).sum())
    elif 'verification_status' in df.columns:
        verified_count = int((df['verification_status'].astype(str).str.lower() == 'valid').sum())
    else:
        # fallback: count non-null emails as "verified"
        if 'email' in df.columns:
            verified_count = int(df['email'].notna().sum())

    verification_rate = round((verified_count / total_leads * 100), 1) if total_leads else 0

    # total exports: try to detect an 'exported' or 'exports' column
    exports = 0
    if 'exported' in df.columns:
        exports = int(df['exported'].astype(bool).sum())
    elif 'exports' in df.columns:
        exports = int(df['exports'].astype(bool).sum())

    # lead sources
    source_col = None
    for candidate in ['source', 'lead_source', 'platform']:
        if candidate in df.columns:
            source_col = candidate
            break

    lead_sources = {}
    if source_col:
        lead_sources = df[source_col].fillna('Unknown').value_counts().to_dict()

    # generate a simple trend: count per year or per date column if present
    trend_labels = []
    trend_values = []
    date_col = None
    for c in ['created_at', 'date', 'timestamp']:
        if c in df.columns:
            date_col = c
            break
    if date_col and not df.empty:
        try:
            s = pd.to_datetime(df[date_col], errors='coerce')
            by_period = s.dt.to_period('M').value_counts().sort_index()
            trend_labels = [str(p) for p in by_period.index.astype(str)]
            trend_values = [int(v) for v in by_period.values]
        except Exception:
            pass
    else:
        # fallback: simple monthly buckets from index
        trend_labels = []
        trend_values = []

    # recent leads
    recent = []
    if not df.empty:
        # determine name and email columns
        name_col = None
        for c in ['name', 'full_name', 'contact_name']:
            if c in df.columns:
                name_col = c
                break
        email_col = None
        for c in ['email', 'contact_email']:
            if c in df.columns:
                email_col = c
                break

        sample = df.tail(6).fillna('')
        for _, r in sample[::-1].iterrows():
            recent.append({
                'name': r[name_col] if name_col else (r[email_col] if email_col else 'Lead'),
                'email': r[email_col] if email_col else '',
                'company': r.get('company', ''),
                'status': r.get('verification_status', '')
            })

    return {
        'total_leads': total_leads,
        'verified_count': verified_count,
        'verification_rate': verification_rate,
        'exports': exports,
        'lead_sources': lead_sources,
        'trend_labels': trend_labels,
        'trend_values': trend_values,
        'recent': recent,
    }


@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static', path)


@app.route('/')
def index():
    df = load_data()
    metrics = compute_metrics(df)

    # Provide sane defaults if empty
    if not metrics['trend_labels']:
        metrics['trend_labels'] = ['2022-01','2022-02','2022-03','2022-04','2022-05','2022-06']
        metrics['trend_values'] = [120,150,200,250,300,450]

    if not metrics['lead_sources']:
        metrics['lead_sources'] = {'LinkedIn': 645, 'Sales Navigator': 123, 'Manual Upload': 74}

    if not metrics['recent']:
        metrics['recent'] = [
            {'name':'Sarah Johnson','email':'sarah.j@techcorp.com','company':'TechCorp Inc.','status':'valid'},
            {'name':'Michael Chen','email':'michael@dataflow.io','company':'DataFlow Systems','status':'valid'},
            {'name':'Emma Williams','email':'emma.w@cloudsync.com','company':'CloudSync Ltd','status':'valid'},
            {'name':'James Anderson','email':'james@aisolutions.net','company':'AI Solutions','status':'risky'},
            {'name':'Lisa Martinez','email':'lisa@devtools.com','company':'DevTools Pro','status':'valid'},
            {'name':'Michael Chen','email':'michael@dataflow.io','company':'DataFlow Systems','status':'valid'},
        ]

    return render_template('index.html', **metrics)


@app.route('/leads')
def leads():
    df = load_data()
    columns = list(df.columns) if not df.empty else DEFAULT_LEAD_COLUMNS
    records = df.fillna('').to_dict(orient='records')

    total_leads = len(df)
    qualified_leads = int(df['Status'].astype(str).str.contains('Qualified', case=False, na=False).sum()) if 'Status' in df.columns else 0
    conversion_rate = round((qualified_leads / total_leads * 100), 1) if total_leads else 0
    pipeline_value = f"${total_leads * 1200:,.0f}" if total_leads else '$0'
    avg_response = f"{max(1, min(5, total_leads // 20))}h {max(0, min(59, total_leads * 3 % 60))}m"

    return render_template(
        'leads.html',
        columns=columns,
        records=records,
        total_leads=total_leads,
        qualified_leads=qualified_leads,
        conversion_rate=conversion_rate,
        pipeline_value=pipeline_value,
        avg_response=avg_response,
    )


@app.route('/lead/create', methods=['POST'])
def create_lead():
    df = load_data()
    row = {col: request.form.get(col, '') for col in df.columns}
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_data(df)
    flash('Lead created successfully')
    return redirect(url_for('leads'))


@app.route('/lead/update/<int:index>', methods=['POST'])
def update_lead(index):
    df = load_data()
    if 0 <= index < len(df):
        for col in df.columns:
            df.at[index, col] = request.form.get(col, df.at[index, col])
        save_data(df)
        flash('Lead updated successfully')
    else:
        flash('Lead not found')
    return redirect(url_for('leads'))


@app.route('/lead/delete/<int:index>', methods=['POST'])
def delete_lead(index):
    df = load_data()
    if 0 <= index < len(df):
        df = df.drop(index).reset_index(drop=True)
        save_data(df)
        flash('Lead deleted successfully')
    else:
        flash('Lead not found')
    return redirect(url_for('leads'))


@app.route('/upload', methods=['POST'])
def upload():
    # handle file upload from form
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    f = request.files['file']
    if f.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    # save to extracts/outreach.xlsx (or outreach.csv if csv)
    base = Path(__file__).resolve().parents[0]
    extracts = base / 'extracts'
    extracts.mkdir(parents=True, exist_ok=True)

    filename = f.filename
    dest = extracts / filename
    f.save(dest)

    # normalize to outreach.xlsx or outreach.csv
    target = extracts / 'outreach.xlsx'
    # if uploaded csv, also allow csv
    if dest.suffix.lower() in ['.xls', '.xlsx', '.csv']:
        # rename to outreach with same suffix
        final = extracts / ('outreach' + dest.suffix.lower())
        if final.exists():
            final.unlink()
        dest.rename(final)
        flash('File uploaded')
    else:
        flash('Unsupported file type')

    return redirect(url_for('index'))


@app.route('/load')
def load_from_source():
    """Load data from either a provided local path or a Google Sheet ID (via query params).
    Example: /load?local_path=extracts/outreach.xlsx
             /load?google_sheet_id=SPREADSHEET_ID
    """
    local_path = request.args.get('local_path', '').strip()
    sheet_id = request.args.get('google_sheet_id', '').strip()

    base = Path(__file__).resolve().parents[0]
    extracts = base / 'extracts'
    extracts.mkdir(parents=True, exist_ok=True)

    # 1) local path
    if local_path:
        cand = Path(local_path)
        # if relative, resolve relative to agent folder
        if not cand.exists():
            cand = base / local_path
        if not cand.exists():
            flash(f'Local file not found: {local_path}')
            return redirect(url_for('index'))

        # try reading as excel or csv and save to extracts
        try:
            if cand.suffix.lower() in ['.xls', '.xlsx']:
                df = pd.read_excel(cand, engine='openpyxl')
                target = extracts / 'outreach.xlsx'
                df.to_excel(target, index=False)
            else:
                df = pd.read_csv(cand)
                target = extracts / 'outreach.csv'
                df.to_csv(target, index=False)
            flash('Loaded local file successfully')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Failed to load local file: {e}')
            return redirect(url_for('index'))

    # 2) google sheet id
    if sheet_id:
        # try export CSV first
        df = fetch_google_sheet_csv(sheet_id)
        if df is not None:
            target = extracts / 'outreach.csv'
            df.to_csv(target, index=False)
            flash('Loaded Google Sheet via export URL')
            return redirect(url_for('index'))

        # try service account
        df = fetch_google_sheet_service(sheet_id)
        if df is not None:
            target = extracts / 'outreach.csv'
            df.to_csv(target, index=False)
            flash('Loaded Google Sheet via service account')
            return redirect(url_for('index'))

        flash('Could not load Google Sheet. Ensure the sheet is shared or service account is configured.')
        return redirect(url_for('index'))

    flash('No source provided')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
