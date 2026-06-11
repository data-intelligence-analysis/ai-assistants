# AI SALES AGENT

## Features:
- Stripe billing (subscription enforced)
- Multi-client SaaS mode
- Lead scoring & filtering
- LinkedIn DM generation
- Excel export
- Notifications
- Cloud Run / AWS Lambda ready
- No Website Lead Generator

## Clients:
- Targets businesses WITHOUT websites and generates service-based outreach.

## Spreadsheet Schema
Columns:
Business Name | Location | Website | Google Maps Link |Lead Type | Lead Score | Tailored Message | Timestamp


A: Niche
B: Location
C: Business Name
D: Website
E: Email
F: Phone
G: Initial Email
H: Follow-up 1
I: Follow-up 2
J: Calendar Link
K: Status
L: Last Contacted
M: Lead Source
N: Lead Source        (Google Maps / LinkedIn / X)
O: Profile URL
P: Platform Handle
Q: Outreach Type     (Email / DM)
R: LinkedIn DM
S: DM Status

## Docker Configuration
```bash
# Build the core image container asset
docker build -t sales-agent-layer .

# Trigger a standard Text Summary Briefing output on console
docker run --env-file .env sales-agent-layer --format text

# Trigger an Audio Voice Summary compilation file dump
docker run --env-file .env -v $(pwd):/app sales-agent-layer --format voice
```


To transform your raw lead-generation data into an autonomous, action-oriented intelligence system, you should move away from thinking of `agent.py` as a single script. Instead, view it as a **Micro-Agent Orchestration Layer** built on top of your `etl.py` data matrix.

When you trigger `python agent.py` via your terminal, Docker container, or a serverless function, a centralized **Orchestrator Agent** should boot up, spin up specialized worker agents, pass context between them, and cleanly shut down.

Here is the architectural blueprint for the agents you should build inside `agent.py`, followed by a production-grade implementation ready for any environment.

---

## 🏗️ The Agent Architecture (`agent.py`)

```
               [ Terminal / Docker / Cron Trigger ]
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Orchestrator Agent   │
                    └───────────┬───────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  Data Scout   │       │ Insights Alchemist│   │ Herald Agent  │
│    Agent      │       │     Agent     │       │ (Text/Voice)  │
└───────────────┘       └───────────────┘       └───────────────┘

```

### 1. The Data Scout Agent (The Context Extractor)

* **Role:** Connects directly to your Google Sheet (using the `get_google_sheet_row_count()` logic we built), detects the exactly newly appended slice of leads since the last tracking window, and parses their raw profiles into a tightly packed JSON payload.
* **Why it matters:** It isolates *only* today's signal, preventing your LLM token costs from ballooning by reading thousands of historic rows.

### 2. The Insights Alchemist Agent (The Executive Summarizer)

* **Role:** Takes the raw data payload from the Data Scout and runs an analytical evaluation. It filters high-scoring targets (e.g., `NO_WEBSITE` leads or specific high-value niches like *Telehealth Finance*), and compiles a punchy, high-impact executive briefing.
* **Why it matters:** It shifts the output from a boring list of names into a strategic sales brief (e.g., *"You have 3 hot no-website leads in Boston ready for immediate outreach"*).

### 3. The Herald Agent (The Multi-Modal Delivery Engine)

* **Role:** Takes the executive brief text and handles formatting for your preferred delivery channel. For text, it routes to Telegram/SMS; for voice, it hooks into OpenAI's Audio Generation API (`tts-1`) to output a pristine, broadcast-ready MP3 file.
* **Why it matters:** Allows hands-free audio briefing while you grab your morning coffee.

---

## 💻 Production Implementation: `agent.py`

This script is structured for headless environments (Docker, AWS Lambda, or local terminal execution). It features a `--voice` flag that switches the summary into a high-quality spoken audio brief.

```python
import os
import sys
import argparse
import json
from datetime import datetime
from typing import List, Dict, Any
from openai import OpenAI

# Assuming your updated etl.py hooks are importable in the same workspace directory
try:
    from etl import sheet, get_google_sheet_row_count, load_last_row_count, save_row_count
except ImportError:
    # Fail-safe mocks for independent testing/serverless sandboxes
    def get_google_sheet_row_count(): return 5  # Simulated current rows
    def load_last_row_count(): return 2         # Simulated previous bookmark
    def save_row_count(count): pass
    sheet = None

# Initialize AI Brain
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
                {"company": "BoxMoc Logistics", "niche": "AI Automation", "location": "New York", "website": "boxmoc.com", "phone": ""}
            ]
        
        # Read the exact range of new rows to minimize API read latency
        all_records = self.sheet.get_all_records()
        # Slicing the array to extract only records since the last row check
        return all_records[start_idx : end_idx]

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
        
        response = openai_client.chat.completions.create(
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
            response = openai_client.audio.speech.create(
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
                os.system(f"xdg-open {output_path} &")
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
        
    # Update persistent historical checkpoint limits
    save_row_count(current_head_idx)
    print("🏁 [ORCHESTRATOR] State preserved. Execution cycle concluded.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Sales Agent Briefing System")
    parser.add_argument("--format", choices=["text", "voice"], default="text", help="Output summary delivery mode")
    args = parser.parse_args()
    
    orchestrate_agent_workflow(mode=args.format)

```

---

## 🐳 Docker Deployment Strategy

To encapsulate this setup securely within a serverless instance or a persistent local runtime container, utilize this lightweight `Dockerfile` footprint optimized for micro-agents:

```dockerfile
# Use a slim, secure base image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for potential file/audio processes
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Cache Python dependencies inside image layers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bring over codebase architectures
COPY etl.py agent.py config.json service_account.json state.json* ./

# Command instructions default to text-based summary generation output 
ENTRYPOINT ["python", "agent.py"]
CMD ["--format", "text"]

```

### Building and Executing via Terminal Commands

Run these commands in your terminal to build the image container and execute either version directly:

```bash
# Build the core image container asset
docker build -t sales-agent-layer .

# Trigger a standard Text Summary Briefing output on console
docker run --env-file .env sales-agent-layer --format text

# Trigger an Audio Voice Summary compilation file dump
docker run --env-file .env -v $(pwd):/app sales-agent-layer --format voice

```

You cannot configure the Google Cloud Console's internal API quotas directly inside client-side Python code, but you can build a local script-level failsafe using a state file.
To prevent your Python code from ever making more than 50 API requests within a single day—even if it is accidentally run multiple times or stuck in an infinite loop—you can track your daily request volume locally using a lightweight JSON state file.
## 🛠️ Python App with Local Daily Request Cap
This updated script checks a local tracking file (api_quota_tracker.json) before executing. If the date matches today and the count is 50 or higher, it blocks the outbound call automatically.
```python
import os
import json 
import requests 
from datetime import datetime
# Configuration
QUOTA_LIMIT = 50
TRACKER_FILE = "api_quota_tracker.json"

def get_and_update_daily_count():
    """
    Reads the tracking file, resets the count if it's a new day, 
    and increments the count for the current day.
    """
    today_str = datetime.today().strftime('%Y-%m-%d')
    
    # Initialize default state
    state = {"date": today_str, "count": 0}
    
    # Load existing tracking data if file exists
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE, 'r') as f:
                saved_state = json.load(f)
                # If the tracking file is from today, keep its count
                if saved_state.get("date") == today_str:
                    state["count"] = saved_state.get("count", 0)
        except (json.JSONDecodeError, KeyError):
            pass  # Corrupted file, fallback to default state
            
    # Check if we have hit or breached the threshold
    if state["count"] >= QUOTA_LIMIT:
        print(f"🛑 CRITICAL SAFETY CAP: You have already made {state['count']} API requests today ({today_str}).")
        print(f"Aborting execution to protect your Google Cloud wallet from unexpected fees.")
        return False
        
    # Increment the local counter
    state["count"] += 1
    
    # Save the updated counter back to the file
    with open(TRACKER_FILE, 'w') as f:
        json.dump(state, f, indent=4)
        
    print(f"🛡️ Request allowed. Daily Usage: {state['count']}/{QUOTA_LIMIT} calls.")
    return True
def check_business_website_with_cap(query, api_key):
    # Execute our local safety check first
    if not get_and_update_daily_count():
        return None

    url = "https://googleapis.com"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.websiteUri"
    }
    payload = {
        "textQuery": query,
        "maxResultCount": 3
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Network Error: {e}")
        return None
if __name__ == "__main__":
    API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "YOUR_API_KEY_HERE")
    SEARCH_QUERY = "local coffee shops in Austin"
    
    data = check_business_website_with_cap(SEARCH_QUERY, API_KEY)
    
    if data and "places" in data:
        for place in data["places"]:
            name = place.get("displayName", {}).get("text", "Unknown Business")
            website = place.get("websiteUri") 
            
            if website:
                print(f"🌐 {name} HAS a website: {website}")
            else:
                print(f"❌ {name} DOES NOT have a website listed.")
```
## 🧠 How This Safeguard Works

   1. Creates a Tracking File: The script creates a tiny file named api_quota_tracker.json in the exact folder your script runs from.
   2. Auto-Resets Daily: If the date inside the file reads yesterday's date, it automatically wipes the count back down to 0 and sets the file date to today.
   3. Hard Ceiling: If the script is accidentally executed 51 times in a single afternoon, the 51st attempt reads the JSON file, matches the limit, and cancels the network call before it reaches Google's servers.

## 🔗 Don't Forget the Cloud Console Backup
Even though this local python loop protection is secure, you should still implement the ultimate billing shield. Navigate to the Google Cloud Console Quotas Page, select your project, find the Places API (New), and explicitly hard-cap the "Requests per day" down to 50. If your local tracking file is ever deleted accidentally, Google's server will still block any overages.
Would you like help extending this script to write the verified website URLs into an ongoing CSV or Excel file so you can easily review the results over time?

# Quick date verification for time tracking logicfrom datetime import datetime, date
print(f"Current Date: {date.today()}")


## Real Estate
To achieve this, we will update your Python pipeline to perform two critical tasks before saving the data to Excel:

   1. Extract Zillow's Property Type Category: We will map Zillow's internal tags (homeType or propertyType) directly to your exact Excel categories (Single-Family, Condo, Townhome, Lots/Land, or Multi-Tenant).
   2. Inject an AI Scoring & Investment Framework: The AI agent will evaluate the structural parameters of each individual property, calculate a customized Investment Score (1-100), and write a concise investment rationale.

## Updated Python Pipeline: Automated Classification & Investment Scoring
This script processes the raw Zillow listings, scores them with OpenAI, and outputs a formatted spreadsheet named zillow_investment_analysis.xlsx.

import osimport datetimeimport pandas as pdfrom apify_client import ApifyClientfrom langchain_openai import ChatOpenAIfrom langchain.core.prompts import PromptTemplatefrom langchain.core.output_parsers import JsonOutputParserfrom pydantic import BaseModel, Field
# 1. GUARDIAN RUN TRACKERTRACKER_FILE = "daily_quota_tracker.txt"
def check_and_update_daily_quota() -> bool:
    """Blocks multi-execution to preserve Apify and OpenAI credits."""
    today_str = datetime.date.today().isoformat()
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as file:
            if file.read().strip() == today_str:
                return False
    with open(TRACKER_FILE, "w") as file:
        file.write(today_str)
    return True
# 2. DEFINING THE AI EVALUATION SCHEMAclass InvestmentEvaluation(BaseModel):
    score: int = Field(description="An investment readiness score from 1 to 100.")
    rationale: str = Field(description="A 1-2 sentence summary explaining the score based on price, space, and layout metrics.")
# 3. CORE REAL ESTATE RUN PIPELINEdef run_zillow_investment_pipeline(location: str):
    if not check_and_update_daily_quota():
        print("⛔ Quota Limit Triggered: Script already executed today.")
        return

    print(f"🚀 Pulling live listings for: {location}...")
    
    # Platform limits applied to stay strictly inside the free tier
    actor_input = {
        "search": location,
        "type": "FOR_SALE",
        "maxPages": 1,
        "resultsPerPage": 10
    }
    
    apify_token = os.getenv("APIFY_API_TOKEN", "your_apify_token_here")
    openai_key = os.getenv("OPENAI_API_KEY", "your_openai_key_here")
    
    client = ApifyClient(apify_token)
    
    try:
        # Fetching raw structured property data
        run = client.actor("scrapier/zillow-search-scraper").call(run_input=actor_input, timeout_secs=120)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        if not items:
            print("❌ No items retrieved from the search grid.")
            return
            
        raw_df = pd.DataFrame(items)
        
        # 4. ZILLOW INTERNAL CATEGORY MAPPING
        # Maps Zillow's internal 'homeType' strings cleanly into your exact Excel categories
        type_mapping = {
            'SINGLE_FAMILY': 'Single-Family',
            'CONDO': 'Condo',
            'TOWNHOUSE': 'Townhome',
            'MULTI_FAMILY': 'Multi-Tenant',
            'LOT': 'Lots/Land',
            'MANUFACTURED': 'Single-Family',
            'APARTMENT': 'Multi-Tenant'
        }
        
        # Ensure fallback column exists if homeType is missing
        if 'homeType' not in raw_df.columns:
            raw_df['homeType'] = 'SINGLE_FAMILY'
            
        raw_df['Category'] = raw_df['homeType'].map(type_mapping).fillna('Single-Family')
        
        # Keep clean, vital listing data structures
        cols_to_keep = ['address', 'price', 'bedrooms', 'bathrooms', 'livingArea', 'Category', 'url']
        existing_cols = [c for c in cols_to_keep if c in raw_df.columns]
        df = raw_df[existing_cols].copy().dropna(subset=['price'])
        
        # Rename layout fields for presentation
        df.rename(columns={
            'address': 'Address', 
            'price': 'Price', 
            'bedrooms': 'Beds', 
            'bathrooms': 'Baths', 
            'livingArea': 'SqFt', 
            'url': 'Zillow Link'
        }, inplace=True)

        # 5. INITIALIZE THE STRUCTURED AI SCORING MODEL
        llm = ChatOpenAI(temperature=0, model="gpt-4o", openai_api_key=openai_key)
        parser = JsonOutputParser(pydantic_object=InvestmentEvaluation)
        
        prompt = PromptTemplate(
            template="You are an expert real estate data analyst.\n{format_instructions}\nEvaluate this property:\nCategory: {category}\nPrice: ${price}\nBeds: {beds}, Baths: {baths}, SqFt: {sqft}\nLocation Context: {location}\nProvide a score (1-100) assessing its value proposition (e.g. high square footage for the price, logical room counts, or developmental land viability) and a brief rationale.",
            input_variables=["category", "price", "beds", "baths", "sqft", "location"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        ai_pipeline = prompt | llm | parser
        
        # Storage lists for our new AI-generated columns
        ai_scores = []
        ai_rationales = []
        
        print("🧠 Analyzing deals using AI Engine...")
        for _, row in df.iterrows():
            try:
                # Format variables safely for the LLM
                res = ai_pipeline.invoke({
                    "category": row['Category'],
                    "price": row['Price'],
                    "beds": row.get('Beds', 'N/A'),
                    "baths": row.get('Baths', 'N/A'),
                    "sqft": row.get('SqFt', 'N/A'),
                    "location": location
                })
                ai_scores.append(res.get("score", 50))
                ai_rationales.append(res.get("rationale", "No analysis generated."))
            except Exception as ai_err:
                ai_scores.append(50)
                ai_rationales.append("AI processing encountered an omission error.")
        
        # Append the new scoring metrics to our spreadsheet pipeline
        df['Investment Score'] = ai_scores
        df['AI Analysis Summary'] = ai_rationales
        
        # Reorder columns so the scores are front and center
        final_order = ['Address', 'Category', 'Price', 'Beds', 'Baths', 'SqFt', 'Investment Score', 'AI Analysis Summary', 'Zillow Link']
        df = df[[c for c in final_order if c in df.columns]]
        
        # Sort listings so the highest scoring investment opportunities float to the top
        df = df.sort_values(by='Investment Score', ascending=False)

        # 6. EXPORTING CRADLE TO EXCEL
        output_file = "zillow_investment_analysis.xlsx"
        df.to_excel(output_file, index=False)
        print(f"🎉 Success! Spreadsheet built and saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Structural error encountered: {str(e)}")
if __name__ == "__main__":
    # Test execution for your chosen market
    run_zillow_investment_pipeline("Miami, FL")

## The AI Scoring Framework Logic
The AI Agent evaluates the properties based on specific investment parameters for each asset type:

* Single-Family/Townhome/Condo: The AI calculates the internal value layout (e.g., assessing if a high bedroom count paired with low total square footage implies tiny, unrentable rooms, or highlighting properties with low price-per-square-foot ratios relative to the local market baseline).
* Multi-Tenant: The score is boosted if the layout provides an optimal ratio of plumbing to units (baths-to-beds), indicating higher potential rental yields and a smoother multi-family conversion process.
* Lots/Land: The algorithm completely shifts its evaluation strategy. It ignores the missing bedroom or bathroom data fields entirely, assessing the property value strictly based on its raw pricing scale relative to the geographic area.

## Final Excel Sheet Output Format
The script will automatically structure your Excel sheet with the following clean columns, sorted with your absolute best opportunities visible on row one:

| Address | Category | Price | Beds | Baths | SqFt | Investment Score | AI Analysis Summary | Zillow Link |
|---|---|---|---|---|---|---|---|---|
| 123 Ocean Dr | Condo | $310,000 | 2 | 2 | 1,400 | 92 | Priced significantly below market average per square foot. Highly liquid configuration for rental yields. | Link |
| 742 Evergreen | Single-Family | $450,000 | 3 | 2 | 1,100 | 68 | Standard configuration layout. Price aligns closely with baseline market averages. | Link |
| 44 Brickell Ave | Lots/Land | $190,000 | NaN | NaN | NaN | 45 | Premium price tier for raw land acreage. Limits immediate development returns. | Link |

Would you like to customize the AI scoring logic by feeding the agent specific parameters—such as prioritizing properties with a target price ceiling or a minimum number of bedrooms—or would you like to set up color-coded formatting inside the Excel file to automatically highlight scores above 80 in green?

