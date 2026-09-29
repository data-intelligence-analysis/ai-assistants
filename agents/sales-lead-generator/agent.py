import os
import sys
import re
import argparse
import json
import subprocess
import webbrowser
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import date, datetime
from typing import List, Dict, Any
from urllib.request import urlopen
from openai import OpenAI
from google import genai
import logging

# Assuming your updated etl.py hooks are importable in the same workspace directory
# try:
#     from etl import sheet, get_google_sheet_row_count, load_last_row_count, save_row_count
# except ImportError:
#     # Fail-safe mocks for independent testing/serverless sandboxes
#     def get_google_sheet_row_count(): return 5  # Simulated current rows
#     def load_last_row_count(): return 2         # Simulated previous bookmark
#     def save_row_count(count): pass
#     sheet = None

##Lets inherently define the google auth of sheets the google_sheet_row_count,  , save_row_count
# =========================
# CONFIG
# =========================
# ---------------- Configure logging to output to standard out for GitHub Actions ---------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

STATE_FILE = "state.json" # TRACK ROW COUNT IN EXCEL STATE FILE
GC_QUOTA_LIMIT = 50
GOOGLE_SHEET_NAME = "TECH_LEADS"
GOOGLE_SERVICE_ACCOUNT_FILE="service_account.json"

# ---------------- DAILY GOOGLE CLOUD QUOTA TRACKER ---------------- #
# ---------------- Google API daily budget guard for once-daily GitHub Actions runs. ---------------- #
GOOGLE_DAILY_QUOTA_LIMIT = max(
    1,
    int(GC_QUOTA_LIMIT)
)
def _load_google_quota_state():
    today_str = date.today().isoformat()
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
            if state.get("date") == today_str:
                return {"date": today_str, "used": int(state.get("used", 0))}
        except Exception:
            pass
    return {"date": today_str, "used": 0}


def _save_google_quota_state(state):
    state["date"] = date.today().isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def reserve_google_call(operation_name, amount=1):
    state = _load_google_quota_state()
    used = int(state.get("used", 0))
    if used + amount > GOOGLE_DAILY_QUOTA_LIMIT:
        logger.warning(
            "Google daily quota exhausted (%s/%s). Skipping %s.",
            used,
            GOOGLE_DAILY_QUOTA_LIMIT,
            operation_name,
        )
        return False
    state["used"] = used + amount
    _save_google_quota_state(state)
    logger.info(
        "Reserved %s Google call(s) for %s. Remaining: %s",
        amount,
        operation_name,
        GOOGLE_DAILY_QUOTA_LIMIT - state["used"],
    )
    return True

# ---------------- GOOGLE AUTH ---------------- #
# Unified Google Services Authentication Matrix\
sheet = None
try:
    creds = Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    gc = gspread.authorize(creds)
    if reserve_google_call("google_sheets_open", amount=1):
        sheet = gc.open(GOOGLE_SHEET_NAME).sheet1
    else:
        sheet = None
except Exception as e:
    logger.error(f"⚠️ Google Service Account auth skipped or failed: {e}")
    sheet = None

def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def save_row_count(count):
    today_str = datetime.today().strftime('%Y-%m-%d')
    with open(STATE_FILE, "w") as f:
        json.dump({"date": today_str, "sheet_row_count": count}, f)

def get_google_sheet_row_count():
    """Returns the total number of populated rows, excluding the header."""
    try:
        if not sheet or not reserve_google_call("google_sheets_read_row_count", amount=1):
            return 0
        # get_all_values() returns a list of lists representing the populated grid
        all_rows = sheet.get_all_values()

        if not all_rows:
            return 0

        # Total populated rows minus 1 for the header row
        return len(all_rows) - 1
    except Exception as e:
        print(f"Error reading Google Sheet row count: {e}")
        return 0

def launch_dashboard(open_browser: bool = True):
    dashboard_url = "http://localhost:3000"
    try:
        with urlopen(f"{dashboard_url}/_stcore/health", timeout=2):
            server_running = True
    except Exception:
        server_running = False

    if not server_running:
        try:
            streamlit_command = [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                os.path.abspath(__file__),
                "--server.address=0.0.0.0" if os.getenv("SALES_AGENT_DOCKER") == "1" else "--server.address=127.0.0.1",
                "--server.port=3000",
            ]
            if os.getenv("SALES_AGENT_DOCKER") == "1":
                os.execv(sys.executable, streamlit_command)
            subprocess.Popen(streamlit_command)
            logger.info(f"Opening Sales Lead CRM at {dashboard_url}")
        except Exception as e:
            logger.error(f"Failed to launch dashboard: {e}")
    if open_browser:
        webbrowser.open(dashboard_url)

def load_last_row_count():
    if not os.path.exists(STATE_FILE):
        return 0
    with open(STATE_FILE, "r") as f:
        return json.load(f).get("sheet_row_count", 0)

# def voice_command(transcript: str) -> bool:
#     ## Use openai to synthesize the voice command and check if it matches "launch leads data"
#     normalized_transcript = " ".join(re.findall(r"[a-z0-9]+", transcript.casefold()))
#     if "launch leads data" in normalized_transcript:
#         return "Dashboard"
#     return False
def voice_command(transcript: str) -> str | None:
    if not transcript.strip():
        return None

    try:
        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Interpret a spoken command and return JSON with keys intent and normalized_query. "
                        "Set intent to launch_leads_dashboard when the user asks to open, launch, show, "
                        "or call the sales leads dashboard or CRM. Otherwise set intent to unknown. "
                        "Do not trigger on negated requests. Keep normalized_query concise."
                    ),
                },
                {"role": "user", "content": transcript[:1000]},
            ],
            temperature=0,
        )
        if response:
            ## Use openai to synthesize the voice command and check if it matches "launch leads data"
            result = json.loads(response.choices[0].message.content or "{}")
        else:
            result_normalized = {}
            normalized_transcript = " ".join(re.findall(r"[a-z0-9]+", transcript.casefold()))
            if "launch leads data" in normalized_transcript:
                result_normalized = {"query": "launch leads data"}
            elif "debrief summarize latest leads" in normalized_transcript:
                result_normalized = {"query": "debrief summarize latest leads"}
            else:
                result_normalized = {"query": "launch leads data"}
    except Exception as error:
        logger.error("Unable to classify voice command with OpenAI: %s", error)
        return None

    if result.get("intent") == "launch_leads_dashboard":
        logger.info("Voice command normalized as: %s", result.get("normalized_query", ""))
        return "Dashboard"
    elif result_normalized.get("query") == "launch leads data":
        logger.info("Voice command intent unknown. Transcript: %s", transcript)
        return "Dashboard"
    return None
def delta(mode=None):
    if mode == "leads":
        previous_bookmark = load_last_row_count()
        current_head_idx = get_google_sheet_row_count()
        return ((current_head_idx - previous_bookmark) if previous_bookmark > 0 and current_head_idx > 0 else 0)
    elif mode == "qualified_leads":
        previous_bookmark = load_last_row_count()
        current_head_idx = get_google_sheet_row_count()
        return ((current_head_idx - previous_bookmark) if previous_bookmark > 0 and current_head_idx > 0 else 0)
    elif mode == "conversion_rates":
        previous_bookmark = load_last_row_count()
        current_head_idx = get_google_sheet_row_count()
        return ((current_head_idx - previous_bookmark) if previous_bookmark > 0 and current_head_idx > 0 else 0)
    elif mode == "no_digital_presence":
        previous_bookmark = load_last_row_count()
        current_head_idx = get_google_sheet_row_count()
        return ((current_head_idx - previous_bookmark) if previous_bookmark > 0 and current_head_idx > 0 else 0)
    else:
        logger.warning("Unknown mode for delta calculation: %s", mode)
        return ValueError("Unknown mode for delta calculation: %s" % mode)
    

# =====================================================================
# 1. DATA SCOUT AGENT
# =====================================================================
class DataScoutAgent:
    """Extracts, filters, and packages newly appended data footprints."""
    def __init__(self, sheet_client):
        self.sheet = sheet_client

    def harvest_new_leads(self, start_idx: int, end_idx: int) -> List[Dict[str, Any]]:
        if not self.sheet:
            print("ℹ️ Sheet context uninitialized. Yielding mock telemetry datasets.")
            return [
                {"company": "MedVitals Inc", "niche": "Telehealth Finance", "location": "Boston", "website": "", "phone": "617-555-0199"},
                {"company": "X Logistics", "niche": "AI Automation", "location": "New York", "website": "boxmoc.com", "phone": ""},
                {"company": "GreenLeaf Organics", "niche": "Sustainable Agriculture", "location": "San Francisco", "website": "", "phone": "415-555-0123"},
                {"company": "FinTech Solutions", "niche": "Financial Software", "location": "Chicago", "website": "fintechsolutions.com", "phone": ""},
                {"company": "EduNext Learning", "niche": "EdTech Platforms", "location": "Austin", "website": "", "phone": ""},
            ]
        
        # Read the exact range of new rows to minimize API read latency
        all_records = self.sheet.get_all_records()
        # Slicing the array to extract only records since the last row check
        return all_records[start_idx : end_idx]
    def dashboard(self):
        previous_bookmark = load_last_row_count()
        current_head_idx = get_google_sheet_row_count()
        delta = ((current_head_idx - previous_bookmark) if previous_bookmark and current_head_idx else 0)
        st.set_page_config(page_title="Lead CRM", page_icon="📊", layout="wide")
        st.title("Customers")

        if st.button("Refresh data"):
            st.session_state.pop("sales_dashboard_records", None)
            st.rerun()

        if "sales_dashboard_records" not in st.session_state:
            try:
                records = self.sheet.get_all_records() if self.sheet else self.harvest_new_leads(0, 0)
                st.session_state["sales_dashboard_records"] = records
            except Exception as error:
                st.error(f"Unable to load leads: {error}")
                st.session_state["sales_dashboard_records"] = []

        records = st.session_state["sales_dashboard_records"]

        leads = pd.DataFrame(records)

        #Total Leads Delta
        previous_bookmark = load_last_row_count()
        current_head_idx = get_google_sheet_row_count()
        

        
        def field_value(record, *names):
            for name in names:
                if name in record and pd.notna(record[name]):
                    return str(record[name]).strip()
            return ""

        total_leads = len(records)
        qualified_leads = sum(
            "qualified" in field_value(record, "Status").lower()
            for record in records
        )
        no_website = sum(not field_value(record, "Website") for record in records)
        conversion_rate = qualified_leads / total_leads * 100 if total_leads else 0

        st.markdown(
            """
            <style>
            div[data-testid="stMetric"] {
                min-height: 112px;
                padding: 20px 22px;
                background: none;
                border: 1px solid rgba(229 231 235);
                border-radius: 8px;
                box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
            }
            div[data-testid="stMetricLabel"] p {
                color: #525866;
                font-size: 0.875rem;
                font-weight: 500;
            }
            div[data-testid="stMetricValue"] {
                color: #ffffff;
                font-size: 2rem;
                font-weight: 600;
            }
            .kpi {
                min-height: 112px;
                padding: 20px 22px;
                background: none;
                border: 1px solid rgba(229 231 235, 0.6);
                border-radius: 8px;
                box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
            }
            .kpi-label {
                color: #525866;
                font-size: 0.875rem;
                font-weight: 500;
            }
            .kpi-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                margin-top: 8px;
            }
            .kpi-value {
                color: #ffffff;
                font-size: 2rem;
                font-weight: 600;
                line-height: 1.2;
            }
            .kpi-delta {
                padding: 2px 8px;
                border-radius: 999px;
                background: #ecfdf5;
                color: #15803d;
                font-size: 0.8rem;
                font-weight: 600;
                white-space: nowrap;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Quantitative metrics displayed in a 4-column layout
        metric_columns = st.columns(4)
        # metric_columns[0].metric("Total Leads", f"{qualified_leads:,}", delta=None)
        total_leads_delta = ((current_head_idx - previous_bookmark) if previous_bookmark and current_head_idx else 0)
        delta_badge = (
            f'<span class="kpi-delta">{total_leads_delta*100:+.0f}%</span>'
        )
        metric_columns[0].markdown(
            f'<div class="kpi">'
            f'<div class="kpi-label">Total Leads</div>'
            f'<div class="kpi-row">'
            f'<span class="kpi-value">{total_leads:,}</span>'
            f'{delta_badge}'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        # metric_columns[1].metric("Qualified Leads", f"{qualified_leads:,}", delta=None)
        #use the qualified_leads sum to determine the percentage change
        qualified_leads_delta = ((current_head_idx - previous_bookmark) if previous_bookmark and current_head_idx else 0)
        delta_badge = (
            f'<span class="kpi-delta">{qualified_leads_delta*100:+.0f}%</span>'
        )
        metric_columns[1].markdown(
            f'<div class="kpi">'
            f'<div class="kpi-label">Qualified Leads</div>'
            f'<div class="kpi-row">'
            f'<span class="kpi-value">{qualified_leads:,}</span>'
            f'{delta_badge}'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        # metric_columns[2].metric("Conversion Rate", f"{conversion_rate:.1f}%", delta=None)
        conversion_rate_delta = ((current_head_idx - previous_bookmark) if previous_bookmark and current_head_idx else 0)
        delta_badge = (
            f'<span class="kpi-delta">{conversion_rate_delta*100:+.0f}%</span>'
        )
        metric_columns[2].markdown(
            f'<div class="kpi">'
            f'<div class="kpi-label">Conversion Rate</div>'
            f'<div class="kpi-row">'
            f'<span class="kpi-value">{conversion_rate:.1f}%</span>'
            f'{delta_badge}'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        # metric_columns[3].metric("No Digital Presence", f"{no_website:,}", delta=None)
        no_website_delta = ((current_head_idx - previous_bookmark) if previous_bookmark and current_head_idx else 0)
        delta_badge = (
            f'<span class="kpi-delta">{no_website_delta*100:+.0f}%</span>'
        )
        metric_columns[3].markdown(
            f'<div class="kpi">'
            f'<div class="kpi-label">No Digital Presence</div>'
            f'<div class="kpi-row">'
            f'<span class="kpi-value">{no_website:,}</span>'
            f'{delta_badge}'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # chart_columns = st.columns(2)
        # chart_data = [
        #     ("Lead qualification", ["Qualified", "Other leads"], [qualified_leads, total_leads - qualified_leads]),
        #     ("Website coverage", ["No website", "Has website"], [no_website, total_leads - no_website]),
        # ]
        # for chart_column, (chart_title, labels, values) in zip(chart_columns, chart_data):
        #     with chart_column:
        #         st.subheader(chart_title)
        #         if total_leads:
        #             pie_data = pd.DataFrame({"Category": labels, "Leads": values})
        #             pie_data = pie_data[pie_data["Leads"] > 0]
        #             st.vega_lite_chart(
        #                 pie_data,
        #                 {
        #                     "mark": {"type": "arc"},
        #                     "encoding": {
        #                         "theta": {"field": "Leads", "type": "quantitative"},
        #                         "color": {"field": "Category", "type": "nominal"},
        #                         "tooltip": [
        #                             {"field": "Category", "type": "nominal"},
        #                             {"field": "Leads", "type": "quantitative"},
        #                         ],
        #                     },
        #                 },
        #                 width="stretch",
        #             )
        #         else:
        #             st.info("No lead data available.")

        #Filtering options for the dashboard
        status_options = sorted({field_value(record, "Status") for record in records} - {""})
        source_options = sorted({field_value(record, "Lead Source") for record in records} - {""})
        filter_columns = st.columns([2, 2, 3])
        selected_status = filter_columns[0].selectbox("Status", ["All statuses", *status_options])
        selected_source = filter_columns[1].selectbox("Lead source", ["All sources", *source_options])
        search_text = filter_columns[2].text_input("Search leads", placeholder="Company, email, location...")

        filtered_records = [
            record for record in records
            if (selected_status == "All statuses" or field_value(record, "Status") == selected_status)
            and (selected_source == "All sources" or field_value(record, "Lead Source") == selected_source)
            and (not search_text or search_text.casefold() in " ".join(str(value) for value in record.values()).casefold())
        ]

        preferred_columns = [
            "Niche", "Location", "Company", "Business Name", "Website", "Phone",
            "Email Address", "Email", "Status", "Last Contacted", "Lead Source",
            "Profile URL", "Initial Email", "Follow-up 1", "Follow-up 2",
            "Calendar Link", "Web Prompt", "Loom Script", "SMS Copy",
        ]
        if not leads.empty:
            ordered_columns = [column for column in preferred_columns if column in leads.columns]
            ordered_columns.extend(column for column in leads.columns if column not in ordered_columns)
            display_data = pd.DataFrame(filtered_records, columns=ordered_columns)
        else:
            display_data = leads

        st.caption(f"Showing {len(filtered_records):,} of {total_leads:,} leads")
        st.dataframe(display_data, hide_index=True, use_container_width=True)
        st.download_button(
            "Export CSV",
            data=display_data.to_csv(index=False).encode("utf-8"),
            file_name="leads.csv",
            mime="text/csv",
            disabled=display_data.empty,
        )


# =====================================================================
# 2. INSIGHTS ALCHEMIST AGENT
# =====================================================================
class InsightsAlchemistAgent:
    """Transforms raw structured tabular profiles into behavioral intelligence briefings."""
    def synthesize_briefing(self, leads: List[Dict[str, Any]]) -> str:
        if not leads:
            return "Good morning. No new lead conversions were tracked in the pipeline window over the last 24 hours."

        prompt = f"""
        You are an elite Chief of Staff and Sales Strategist summarizing the morning's B2B lead generation pipeline metrics.
        Analyze these raw leads scraped today:
        {json.dumps(leads, indent=2)}

        Generate a high-energy, concise executive audio briefing.
        Rules:
        - Start with a punchy greeting summarizing the total lead volume found.
        - Group them or highlight the most valuable targets first (especially businesses with NO website).
        - Call out key actions like locations (e.g., Boston, NY) and niche domains.
        - Keep it brief, actionable, and structured for spoken audio (under 120 words). Do not use bullet points or markdown bolding symbols.
        """
        
        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

# =====================================================================
# 3. HERALD AGENT (DELIVERY LAYER)
# =====================================================================
class HeraldAgent:
    """Manages the transport of insights across text and vocal audio wave spectrums."""
    def enunciate_brief(self, text_content: str, output_path: str = "morning_brief.mp3"):
        print("🎙️ Herald Agent synthesizing voice transmission...")
        try:
            response = get_openai_client().audio.speech.create(
                model="tts-1",
                voice="onyx",  # Professional, deep executive tone
                input=text_content
            )
            response.stream_to_file(output_path)
            print(f"🔊 Audio brief synthesized cleanly! File saved to: {output_path}")
            
            # If running locally on Mac/Linux, play it directly through terminal audio drivers
            if sys.platform == "darwin":
                os.system(f"afplay {output_path} &")
            elif sys.platform.startswith("linux"):
                # os.system(f"xdg-open {output_path} &")
                subprocess.run(f"xdg-open {output_path} &", shell=True)
        except Exception as e:
            print(f"❌ Failed to generate audio stream callback: {e}")


# =====================================================================
# CENTRAL ORCHESTRATION ENGINE
# =====================================================================
def orchestrate_agent_workflow(mode: str):
    print(f"⚡ [ORCHESTRATOR] Booting Agent Layer. Tracking Window: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Check sheet index boundary thresholds
    previous_bookmark = load_last_row_count()
    current_head_idx = get_google_sheet_row_count()
    
    # 1. Run Data Scout Agent
    scout = DataScoutAgent(sheet)
    new_leads = scout.harvest_new_leads(previous_bookmark, current_head_idx)
    
    # 2. Run Insights Alchemist Agent
    alchemist = InsightsAlchemistAgent()
    summary_text = alchemist.synthesize_briefing(new_leads)


    # Print the crisp textual summary directly to standard console output
    print("\n📝 --- MORNING EXECUTIVE BRIEFING ---")
    print(summary_text)
    print("--------------------------------------\n")
    
    # 3. Run Herald Agent if voice mode is requested
    if mode == "voice":
        herald = HeraldAgent()
        herald.enunciate_brief(summary_text)

        #4. Run dashboard upon voice command recognition
        launch_dashboard(open_browser=True)
        
    # Update persistent historical checkpoint limits
    save_row_count(current_head_idx)
    print("🏁 [ORCHESTRATOR] State preserved. Execution cycle concluded.")

if __name__ == "__main__":
    if st.runtime.exists():
        DataScoutAgent(sheet).dashboard()
    else:
        parser = argparse.ArgumentParser(description="AI Sales Agent Briefing System")
        parser.add_argument("--format", choices=["text", "voice"], help="Run a text or voice sales briefing")
        parser.add_argument("--voice-command", help="Recognized voice transcript; use 'launch leads data' to open the dashboard")
        args = parser.parse_args()

        if args.voice_command is not None:
            if voice_command(args.voice_command) == "Dashboard": #Recognized voice transcript; use 'launch leads data' to open the dashboard
                launch_dashboard(open_browser=True)
            else:
                print("Voice command did not match 'launch leads data'; dashboard not opened.")
        elif args.format:
            orchestrate_agent_workflow(mode=args.format)
        else:
            launch_dashboard()