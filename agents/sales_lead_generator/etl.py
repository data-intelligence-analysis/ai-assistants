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
