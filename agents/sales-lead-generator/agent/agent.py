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