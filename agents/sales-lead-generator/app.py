from fastapi import FastAPI, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import os
import json
from pathlib import Path
import requests
import io
import asyncio

# optional gspread import for service-account access to Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials
    GSPREAD_AVAILABLE = True
except Exception:
    GSPREAD_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except Exception:
    FPDF_AVAILABLE = False

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parents[0]
TEMPLATES_DIR = BASE_DIR / 'templates'
STATIC_DIR = BASE_DIR / 'static'

app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


DEFAULT_LEAD_COLUMNS = [
    'Niche', 'Location', 'Company', 'Website', 'Phone', 'Email Address',
    'Initial Email', 'Follow-up 1', 'Follow-up 2', 'Calendar Link',
    'Status', 'Last Contacted', 'Lead Source', 'Profile URL',
    'Web Prompt', 'Loom Script', 'SMS Copy'
]


def get_data_paths():
    extracts = BASE_DIR / 'extracts'
    extracts.mkdir(parents=True, exist_ok=True)
    return {
        'csv': extracts / 'outreach.csv',
        'xlsx': extracts / 'outreach.xlsx',
        'test_csv': extracts / 'outreach_tst.csv'
    }


def get_config():
    config_path = BASE_DIR / 'config.json'
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())
        except Exception:
            return {}
    return {}


def get_google_sheet_id():
    config = get_config()
    return (
        os.environ.get('GOOGLE_SHEET_ID')
        or config.get('spreadsheet_id')
        or config.get('real_estate_config', {}).get('spreadsheet_id')
    )


def fetch_google_sheet_service_sync(sheet_id, sheet_name=None):
    """Fetch Google Sheet using a service account JSON."""
    if not GSPREAD_AVAILABLE:
        return None
    sa_file = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE')
    sa_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    if not sa_file and not sa_json:
        return None
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        if sa_json:
            creds = ServiceAccountCredentials.from_service_account_info(json.loads(sa_json), scopes=scopes)
        else:
            if not Path(sa_file).exists():
                return None
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


def load_data_from_google_sync():
    sheet_id = get_google_sheet_id()
    if not sheet_id:
        return None
    if GSPREAD_AVAILABLE:
        df = fetch_google_sheet_service_sync(sheet_id)
        if df is not None and not df.empty:
            return df
    df = fetch_google_sheet_csv_sync(sheet_id)
    if df is not None and not df.empty:
        return df
    return None


def load_data_sync():
    google_df = load_data_from_google_sync()
    if google_df is not None and not google_df.empty:
        return google_df

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


async def load_data():
    return await asyncio.to_thread(load_data_sync)


def save_data_sync(df):
    csv_path = get_data_paths()['csv']
    df.to_csv(csv_path, index=False)


async def save_data(df):
    await asyncio.to_thread(save_data_sync, df)


def fetch_google_sheet_csv_sync(sheet_id, gid=0):
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


async def fetch_google_sheet_csv(sheet_id, gid=0):
    return await asyncio.to_thread(fetch_google_sheet_csv_sync, sheet_id, gid)


def compute_metrics_sync(df):
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
        if 'email' in df.columns:
            verified_count = int(df['email'].notna().sum())

    verification_rate = round((verified_count / total_leads * 100), 1) if total_leads else 0

    exports = 0
    if 'exported' in df.columns:
        exports = int(df['exported'].astype(bool).sum())
    elif 'exports' in df.columns:
        exports = int(df['exports'].astype(bool).sum())

    source_col = None
    for candidate in ['source', 'lead_source', 'platform', 'Lead Source']:
        if candidate in df.columns:
            source_col = candidate
            break

    lead_sources = {}
    if source_col:
        lead_sources = df[source_col].fillna('Unknown').value_counts().to_dict()

    trend_labels = []
    trend_values = []
    date_col = None
    for c in ['created_at', 'date', 'timestamp', 'Last Contacted']:
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

    recent = []
    if not df.empty:
        name_col = None
        for c in ['name', 'full_name', 'contact_name', 'Company']:
            if c in df.columns:
                name_col = c
                break
        email_col = None
        for c in ['email', 'contact_email', 'Email Address', 'Email']:
            if c in df.columns:
                email_col = c
                break

        sample = df.tail(6).fillna('')
        for _, r in sample[::-1].iterrows():
            recent.append({
                'name': r[name_col] if name_col else (r[email_col] if email_col else 'Lead'),
                'email': r[email_col] if email_col else '',
                'company': r.get('Company', ''),
                'status': r.get('Status', '')
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

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("Starting up...")
#     asyncio.create_task(simulated_obd_listener(obd=False)) #set to true to connect to obd, false for simulated data
#     yield
#     print("Shutting down...")

# app = FastAPI(lifespan=lifespan)

async def compute_metrics(df):
    return await asyncio.to_thread(compute_metrics_sync, df)


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    df = await load_data()
    metrics = await compute_metrics(df)

    if not metrics['trend_labels']:
        metrics['trend_labels'] = ['2022-01','2022-02','2022-03','2022-04','2022-05','2022-06']
        metrics['trend_values'] = [120,150,200,250,300,450]

    if not metrics['lead_sources']:
        metrics['lead_sources'] = {'LinkedIn': 645, 'Sales Navigator': 123, 'Manual Upload': 74}

    if not metrics['recent']:
        metrics['recent'] = [
            {'name':'Sarah Johnson','email':'sarah.j@techcorp.com','company':'TechCorp Inc.','status':'valid'},
            {'name':'Michael Chen','email':'michael@dataflow.io','company':'DataFlow Systems','status':'valid'},
        ]

    context = {**metrics, 'request': request, 'current_page': 'overview'}
    return templates.TemplateResponse(request, 'index.html', context)


@app.get('/leads', response_class=HTMLResponse)
async def leads(request: Request, message: str = ''):
    df = await load_data()
    columns = list(df.columns) if not df.empty else DEFAULT_LEAD_COLUMNS
    records = df.fillna('').to_dict(orient='records')

    total_leads = len(df)
    qualified_leads = int(df['Status'].astype(str).str.contains('Qualified', case=False, na=False).sum()) if 'Status' in df.columns else 0
    conversion_rate = round((qualified_leads / total_leads * 100), 1) if total_leads else 0
    pipeline_value = f"${total_leads * 1200:,.0f}" if total_leads else '$0'
    avg_response = f"{max(1, min(5, total_leads // 20))}h {max(0, min(59, total_leads * 3 % 60))}m"
    status_options = sorted(df['Status'].dropna().unique().tolist()) if 'Status' in df.columns else []
    source_options = sorted(df['Lead Source'].dropna().unique().tolist()) if 'Lead Source' in df.columns else []

    context = dict(
        request=request,
        current_page='leads',
        columns=columns,
        records=records,
        total_leads=total_leads,
        qualified_leads=qualified_leads,
        conversion_rate=conversion_rate,
        pipeline_value=pipeline_value,
        avg_response=avg_response,
        status_options=status_options,
        source_options=source_options,
        message=message,
        get_flashed_messages=(lambda: [message] if message else []),
    )
    return templates.TemplateResponse(request, 'leads.html', context)


@app.get('/export/csv')
async def export_csv():
    df = await load_data()
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    return StreamingResponse(io.BytesIO(csv_bytes), media_type='text/csv', headers={'Content-Disposition': 'attachment; filename="leads_export.csv"'})


@app.get('/export/pdf')
async def export_pdf():
    df = await load_data()
    if not FPDF_AVAILABLE:
        return JSONResponse({'error': 'PDF export unavailable: missing fpdf library.'}, status_code=503)

    pdf = FPDF('L', 'mm', 'A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    cols = list(df.columns)
    col_width = max(20, min(40, int(270 / max(1, len(cols)))))
    for col in cols:
        pdf.cell(col_width, 10, col[:18], border=1)
    pdf.ln()
    pdf.set_font('Arial', '', 10)
    for _, row in df.astype(str).fillna('').iterrows():
        for col in cols:
            text = str(row[col])[:20]
            pdf.cell(col_width, 8, text, border=1)
        pdf.ln()
    pdf_stream = io.BytesIO()
    pdf.output(pdf_stream)
    pdf_stream.seek(0)
    return StreamingResponse(pdf_stream, media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="leads_export.pdf"'})


@app.get('/sync')
async def sync_crm():
    google_df = await asyncio.to_thread(load_data_from_google_sync)
    if google_df is not None and not google_df.empty:
        local_path = get_data_paths()['csv']
        await asyncio.to_thread(google_df.to_csv, local_path, index=False)
        return RedirectResponse(url='/leads?message=CRM+synced+from+Google+Sheets', status_code=303)

    fallback_path = get_data_paths()['test_csv']
    if fallback_path.exists() and fallback_path.stat().st_size > 0:
        try:
            fallback_df = pd.read_csv(fallback_path)
            await asyncio.to_thread(fallback_df.to_csv, get_data_paths()['csv'], index=False)
            return RedirectResponse(url='/leads?message=CRM+synced+from+fallback+template', status_code=303)
        except Exception:
            pass

    return RedirectResponse(url='/leads?message=Sync+failed+no+Google+Sheet+or+fallback+available', status_code=303)


@app.post('/analyze')
async def analyze_leads(request: Request):
    if not OPENAI_AVAILABLE:
        return JSONResponse({'error': 'AI analysis unavailable: missing OpenAI library.'}, status_code=503)

    df = await load_data()
    rows = df.astype(str).fillna('').head(40).to_dict(orient='records')
    sample_text = '\n'.join([', '.join([f"{k}: {v}" for k,v in row.items() if v]) for row in rows])
    prompt = (
        'Analyze these leads and provide a short summary with three key insights, the strongest leads, and one tactical recommendation for follow-up. '
        'Use simple language.\n\nLeads data:\n' + sample_text
    )

    try:
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        response = client.responses.create(
            model='gpt-4.1-mini',
            input=prompt,
            max_output_tokens=400
        )
        content = ''
        if hasattr(response, 'output'):
            if isinstance(response.output, list):
                content = ' '.join([str(item) for item in response.output])
            else:
                content = str(response.output)
        elif hasattr(response, 'text'):
            content = response.text
        else:
            content = json.dumps(response)
    except Exception as exc:
        return JSONResponse({'error': str(exc)}, status_code=500)

    return JSONResponse({'analysis': content})


@app.post('/lead/create')
async def create_lead(request: Request):
    form = await request.form()
    df = await load_data()
    row = {col: form.get(col, '') for col in df.columns}
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    await save_data(df)
    return RedirectResponse(url='/leads?message=Lead+created', status_code=303)


@app.post('/lead/update/{index}')
async def update_lead(index: int, request: Request):
    form = await request.form()
    df = await load_data()
    if 0 <= index < len(df):
        for col in df.columns:
            df.at[index, col] = form.get(col, df.at[index, col])
        await save_data(df)
        return RedirectResponse(url='/leads?message=Lead+updated', status_code=303)
    return RedirectResponse(url='/leads?message=Lead+not+found', status_code=303)


@app.post('/lead/delete/{index}')
async def delete_lead(index: int):
    df = await load_data()
    if 0 <= index < len(df):
        df = df.drop(index).reset_index(drop=True)
        await save_data(df)
        return RedirectResponse(url='/leads?message=Lead+deleted', status_code=303)
    return RedirectResponse(url='/leads?message=Lead+not+found', status_code=303)


@app.post('/upload')
async def upload(file: UploadFile = File(...)):
    extracts = get_data_paths()
    extracts_dir = BASE_DIR / 'extracts'
    extracts_dir.mkdir(parents=True, exist_ok=True)
    dest = extracts_dir / file.filename
    content = await file.read()
    dest.write_bytes(content)

    if dest.suffix.lower() in ['.xls', '.xlsx', '.csv']:
        final = extracts_dir / ('outreach' + dest.suffix.lower())
        if final.exists():
            final.unlink()
        dest.rename(final)
        return RedirectResponse(url='/?message=File+uploaded', status_code=303)
    return RedirectResponse(url='/?message=Unsupported+file+type', status_code=303)


@app.get('/load')
async def load_from_source(local_path: str = '', google_sheet_id: str = ''):
    extracts_dir = BASE_DIR / 'extracts'
    extracts_dir.mkdir(parents=True, exist_ok=True)

    if local_path:
        cand = Path(local_path)
        if not cand.exists():
            cand = BASE_DIR / local_path
        if not cand.exists():
            return RedirectResponse(url='/leads?message=Local+file+not+found', status_code=303)
        try:
            if cand.suffix.lower() in ['.xls', '.xlsx']:
                df = await asyncio.to_thread(pd.read_excel, cand, engine='openpyxl')
                target = extracts_dir / 'outreach.xlsx'
                await asyncio.to_thread(df.to_excel, target, index=False)
            else:
                df = await asyncio.to_thread(pd.read_csv, cand)
                target = extracts_dir / 'outreach.csv'
                await asyncio.to_thread(df.to_csv, target, index=False)
            return RedirectResponse(url='/leads?message=Loaded+local+file', status_code=303)
        except Exception as e:
            return RedirectResponse(url=f'/leads?message=Failed+to+load+local+file:+{e}', status_code=303)

    if google_sheet_id:
        df = await fetch_google_sheet_csv(google_sheet_id)
        if df is not None:
            target = extracts_dir / 'outreach.csv'
            await asyncio.to_thread(df.to_csv, target, index=False)
            return RedirectResponse(url='/leads?message=Loaded+Google+Sheet+via+export', status_code=303)
        df = await fetch_google_sheet_service(google_sheet_id)
        if df is not None:
            target = extracts_dir / 'outreach.csv'
            await asyncio.to_thread(df.to_csv, target, index=False)
            return RedirectResponse(url='/leads?message=Loaded+Google+Sheet+via+service', status_code=303)
        return RedirectResponse(url='/leads?message=Could+not+load+Google+Sheet', status_code=303)

    return RedirectResponse(url='/leads?message=No+source+provided', status_code=303)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app:app', host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), reload=True)
