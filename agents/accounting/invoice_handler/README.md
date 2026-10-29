# Invoice Agent

## MAC OS X - Siri

### Step-by-Step Siri Headless Configuration Integration


### Step-by-Step Siri Headfull Configuration Integration

To execute everything seamlessly via Apple Ecosystem interfaces:
1. Launch your host workstation script (python agent_trigger.py) so it listens continuously on port 5001.
2. Open the Shortcuts app on your Mac, iPhone, or iPad.
3. Add a new action block: Get Contents of URL.
4. Configure the targeted address input path using your workstation's network location: http://YOUR_LOCAL_IP:5001/trigger-dashboard and set the action header type configuration parameter to POST.
5. Save the shortcut with a voice phrase name like: "Analyze my application invoices".
6. Test your voice workflow: Saying "Hey Siri, Analyze my application invoices" will prompt your Apple device to trigger your local daemon, initialize the container instance, query Google Sheets, and open the tracking visualizer window on your monitor.
Would you like assistance in optimizing the regex configuration strings to extract data from a specific application's invoice format, or do you need help generating the secure OAuth client certificates within the Google Cloud Console dashboard interface?

Phase 1: One-Time Developer Initialization Flow

Before the background agent can run autonomously, a human developer must establish the workspace baseline.
```bash
[1. Google Cloud Console] ──► Enable Gmail API, configure Desktop OAuth Screen, download 'credentials.json'
           │
           ▼
[2. Desktop Workspace]    ──► Install core packages: pip install google-auth-oauthlib google-api-python-client
           │
           ▼
[3. Browser Handshake]    ──► Run 'generate_token.py' manually -> Authorize Gmail -> Generates persistent 'token.json'
           │
           ▼
[4. Build Container Artifact]──► Run 'docker build -t live-accounting-image .' inside the project directory
```
Phase 2: Complete System Runtime Flow (Step-by-Step)

This sequence runs every single time a voice command is captured. Use this flow to see exactly which script handles data modifications.

Step 1: Voice Command & Dictation Capture

• Actor: User & Apple Shortcut
• Action: You trigger Siri by saying your macro shortcut name. The Shortcut prompts for dictation, records your voice command string, and maps it directly into a standard JSON payload format: {"command": "your dictated speech text"}.

Step 2: HTTP Handshake Dispatch

• Actor: Apple Shortcuts Engine
• Action: The Apple client issues a headless network request using the HTTP POST protocol directed straight to your workstation's local network target entry point: http://<YOUR_LOCAL_IP>:5001/trigger-dashboard.

Step 3: Local Orchestrator Wakeup

• Actor: agent_trigger_accounting.py (Flask Service Listening on Port 5001)
• Action: The background Python daemon catches the incoming payload string, extracts the raw text from the "command" field, and boots up the Gemini client routing context.

Step 4: AI Intent Guardrail Inspection

• Actor: Google GenAI SDK (gemini-2.5-flash)
• Action: The prompt is sent to Gemini to evaluate intent.
	• Scenario A (Non-Financial): If the model returns DENIED, the orchestrator logs the security alert, blocks execution, and returns a strict 403 Forbidden response to the Apple Shortcut.
	• Scenario B (Financial/Accounting): If the model returns ALLOWED, execution safely proceeds to Step 5.

Step 5: Silent Token Maintenance Lifecycle

• Actor: refresh_token_if_expired() Function
• Action: The agent reads the local token.json file. If the short-lived access credentials have expired, it uses the embedded Google refresh token to perform a silent background API renewal handshake. The newly minted keys are saved directly back to token.json on disk without requiring any browser windows to open.

Step 6: Container Lifecycle Refresh & Boot

• Actor: Workstation Docker Engine & Subprocess Wrapper
• Action: The orchestrator drops any existing dashboard container using docker rm -f live_accounting_dashboard to wipe residual state from memory. It then immediately boots up a fresh, ephemeral instance by passing the valid contents of token.json straight into an environment parameter: -e GOOGLE_TOKEN_JSON='...'.

Step 7: Local Browser Activation

• Actor: Python Native webbrowser Engine
• Action: While the container wraps its internal boot sequence, the host machine issues a native operating system command to launch your default system web browser focused directly at the application container's portal address: http://localhost:8501.

Step 8: Live In-Memory Data Fetching & Rendering

• Actor: Streamlit Workspace Instance (app.py within Docker)
• Action: The dashboard wakes up inside the container, decodes the credentials inside GOOGLE_TOKEN_JSON, and establishes a live connection directly with the Gmail API. It searches for matching receipts, parses financial text snippets in-memory, loads data into a temporary Pandas DataFrame, streams the visual analytics onto your screen, and stores absolutely nothing on local storage or disk.

Maintenance & Update Mapping for Developers

When updating or fixing this codebase, find your specific scenario below to see which component to modify:
• To update the invoice formats parsed (Regex): Modify the matching string regex blocks inside app.py.
• To adjust your financial scope boundaries or permissions: Update the guardrail system text instructions inside agent_trigger_accounting.py.
• To alter layout widgets, charts, or color profiles: Update the frontend UI layout elements inside app.py.
• To change the local networking parameters or listening ports: Modify the host environment execution wrapper flags at the bottom of agent_trigger_accounting.py.

## Infrastructure 
### Extract information Directly from GMAIL
```bash
[ Voice Command: "Hey Siri..." ]
               │
               ▼
   [ Apple Shortcuts App ] 
               │  (Sends a direct HTTP POST network request)
               ▼
   [ invoice_local_trigger_agent.py (Flask) ] ────► Runs `docker run` natively in background
               │
               ▼
   [ Docker Container (invoice_dashboard_app.py) ] ───► Automatically opens local web browser
```




### Extract information from Google Sheets