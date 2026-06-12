# AI SALES AGENT
## - Includes:
# - Generate Lead Scope - Google Maps, X, LinkedIn
# - Multi-client SaaS mode
# - Lead scoring & filtering
# - LinkedIn DM generation
# - Excel export + notifications
# - Stripe subscription gating
# - NO-WEBSITE LEAD TARGETING
# - Maps Link Generation
# - Generate Tailored Outreach - AI written SMS copy, and CRM Sync Notion
# - Notion CRM sync (attach prompt, Loom script, pricing)
# - AI-generated Web App Prompt
# - AI-written Loom-style video script - Video consultation
# - AI-generated SMS copy
# - Auto proposal pricing logic

## - Overall Architecture:
# - Google Sheets (lead source + AI prompt storage)
# - Notion CRM sync (attach prompt, Loom script, pricing)
# - AI-generated Web App Prompt
# - AI-written Loom-style video script
# - AI-generated SMS copy
# - Auto proposal pricing logic

# Scrape Lead
# → Detect No Website
# → Generate Tailored Outreach
# → Generate AI Web App Prompt
# → Store in Google Sheet
# → Notify You (Email / SMS / Telegram)

# Each lead gets:

# * `source`
# * `platform`
# * `contact_type` (Email vs DM)

import test_tech_clients
import tech_clients
import real_estate
import logging

# =========================
# CONFIG
# =========================
# Configure logging to output to standard out for GitHub Actions
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    workflow = input("Press Enter the following to start the Lead Generation Agent (main/tst): ")
    if workflow == "tst":
        # print("Telemetry Dry Run Complete. Done.")
        logger.info("Start Test Run of Lead Generation Agent in TEST MODE.")
        test_tech_clients()
        logger.info("Telemetry Dry Run Complete. All test notifications dispatched successfully.")
    elif workflow == "main":
        logger.info("Start Main Lead Generation workflow across all channels.")
        tech_clients()
        logger.info("Main workflow execution complete. All channels processed.")
    else:
        # print("Invalid workflow selection. Program ended.")
        logger.error("Invalid workflow selection. Please choose 'main' or 'tst'.")
        raise NameError("Invalid workflow selection. Please choose 'main' or 'tst'.")
