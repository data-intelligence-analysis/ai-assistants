# Invoice Handler

Streamlit dashboard for reviewing invoices from Gmail in production or from a bundled CSV in test mode. Docker Compose builds and starts the dashboard; only production mode requires Google credentials.

## Architecture

```text
User runs voice_trigger_dashboard.sh [test|production]
                │
                ├── test      → bundled invoice_sample.csv
                └── production → refreshes Gmail OAuth token → Gmail API
                                  │
                                  ▼
                     Builds and starts dashboard
                                  │
                                  ▼
                       Streamlit on localhost:8501
```

The launcher is [scripts/voice_trigger_dashboard.sh](./scripts/voice_trigger_dashboard.sh), the Compose configuration is [docker_compose.yml](./docker_compose.yml), and the dashboard image is defined by [dashboard/Dockerfile](./dashboard/Dockerfile).

## Prerequisites

- Docker with the Docker Compose plugin
- Python 3 and the packages in [requirements.txt](./requirements.txt) installed on the host
- A Google Cloud project with the Gmail API enabled and OAuth desktop credentials
- macOS to use the launcher's automatic browser-opening step

## One-time Google authorization

1. Download the OAuth desktop client file from Google Cloud Console and save it as `dashboard/credentials.json`.
2. Run the token generator from the `dashboard` directory so it writes the token to the path expected by the launcher:

   ```bash
   cd dashboard
   python3 generate_token.py
   ```

3. Complete the browser authorization flow. The resulting token is written to `dashboard/token.json` with Gmail read-only access.

Keep both credential files private. The launcher expects `dashboard/token.json` and refreshes it when the access token has expired. If you have a token from the previous setup, remove it and run authorization again to grant the read-only scope.

## Run the dashboard

From this directory, make the launcher executable if needed. Run the test mode to preview the dashboard without Gmail access:

```bash
chmod +x scripts/voice_trigger_dashboard.sh
./scripts/voice_trigger_dashboard.sh test
```

Test mode uses [dashboard/invoice_sample.csv](./dashboard/invoice_sample.csv), a sample dataset modeled on [invoice_tbl_crop.png](./invoice_tbl_crop.png). It does not read Gmail or require `token.json`.

To load live invoices, first complete [one-time Google authorization](#one-time-google-authorization), then run:

```bash
./scripts/voice_trigger_dashboard.sh production
```

Production mode refreshes the Gmail read-only token, searches the inbox using `APP_EMAIL_FILTER` (default `in:inbox invoice`), and uses custom Gmail labels for ledger groupings. Messages without a custom label appear as `Unassigned`. The launcher builds the `dashboard` image, passes the selected environment as a command-line argument, publishes port `8501`, and opens `http://localhost:8501`. The shell launcher defaults to production when no mode is supplied; the dashboard app itself requires an explicit `--environment testing|production` argument and does not read its mode from an environment variable or `.env` file.

Supplier logos use the optional Logo.dev CDN when `LOGO_DEV_PUBLISHABLE_KEY` is set, then try the Simple Icons CDN, and finally show an initials placeholder. The sample dataset can use Simple Icons without credentials. Set `LOGO_DEV_PUBLISHABLE_KEY` in the invoice handler's `.env` file or export it before starting the launcher; Docker Compose passes it to the dashboard app. The supplier image embeds SVG logo markup with the supplier name so it renders in the table's existing Supplier column. The dashboard displays Logo.dev attribution when one of its logos is shown. Review Logo.dev's [pricing and attribution requirements](https://www.logo.dev/pricing) before using its free plan commercially; Simple Icons also asks users to read its [legal disclaimer](https://github.com/simple-icons/simple-icons/blob/develop/DISCLAIMER.md).

To build the image without launching the dashboard:

```bash
docker compose -f docker_compose.yml build dashboard
```

The dashboard image installs its dependencies from [requirements.txt](./requirements.txt) and runs [dashboard/invoice_dashboard_app.py](./dashboard/invoice_dashboard_app.py). To narrow the production Gmail search, set `APP_EMAIL_FILTER` before running the launcher, for example `APP_EMAIL_FILTER='in:inbox from:no-reply@specificapp.com subject:Invoice'`.

## Siri voice commands

Create two Shortcuts so the spoken phrase selects the data source: **Show Test Invoice Dashboard** for the sample CSV and **Show Production Invoice Dashboard** for Gmail. Both run the same launcher with a different mode argument.

### Prepare the Mac

1. Make sure this repository is checked out on the Mac itself. A path inside a remote Codespace or another computer is not accessible to a local Shortcut unless that location is mounted on the Mac.
2. Install and start Docker Desktop. Confirm Docker Compose works in Terminal:

   ```bash
   docker compose version
   ```

3. Install Python 3 and the host-side dependencies:

   ```bash
   python3 -m pip install -r requirements.txt
   ```

4. For the production shortcut, complete the [one-time Google authorization](#one-time-google-authorization) steps on the Mac so `dashboard/token.json` exists locally. This is not needed for test mode.
5. Before creating either Shortcut, open Terminal in the `agents/accounting/invoice_handler` directory of the Mac checkout. Make the launcher executable and run each mode once to verify Docker and (for production) Gmail authorization:

   ```bash
   chmod +x scripts/voice_trigger_dashboard.sh
   ./scripts/voice_trigger_dashboard.sh test
   ./scripts/voice_trigger_dashboard.sh production
   ```

   Let the test dashboard finish starting at `http://localhost:8501` before running the production command. The production command requires the Mac's `dashboard/token.json`; it will replace the running test dashboard with the production dashboard. Confirm both modes load successfully before continuing to **Create the Shortcut**.

### Create the Shortcut

1. Open **Shortcuts** on the Mac and select **+** to create a shortcut.
2. Name the first shortcut **Show Test Invoice Dashboard**.
3. Search for and add the **Run Shell Script** action.
4. Set **Shell** to `/bin/bash`.
4. Replace the action's script with the following, changing the example path to your Mac's local checkout:

   ```bash
   set -e
   LAUNCHER="/Users/yourname/path/to/ai-assistants/agents/accounting/invoice_handler/scripts/voice_trigger_dashboard.sh"
   chmod +x "$LAUNCHER"
   "$LAUNCHER" test
   ```

   The Shortcut runs `chmod +x` every time before launching, so it repairs the executable bit automatically. `set -e` makes the action stop if that permission change fails. Use the absolute path to the Mac checkout.
5. Save the shortcut and approve any macOS permissions prompts. Duplicate it as **Show Production Invoice Dashboard** and change the final argument from `test` to `production`.
6. Say **“Hey Siri, Show Test Invoice Dashboard”** to use the CSV or **“Hey Siri, Show Production Invoice Dashboard”** to load Gmail. Each phrase runs the matching mode, rebuilds/starts the dashboard, and opens it locally.

If Shortcuts cannot find `docker` or `python3`, add the locations used by your Mac to the beginning of the Run Shell Script action, before `set -e`:

```bash
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
set -e
LAUNCHER="/Users/yourname/path/to/ai-assistants/agents/accounting/invoice_handler/scripts/voice_trigger_dashboard.sh"
chmod +x "$LAUNCHER"
"$LAUNCHER" test
```

Use `production` instead of `test` in the second shortcut's script. To listen directly through the terminal microphone, install [requirements.txt](./requirements.txt), download the offline [Vosk small English model](https://alphacephei.com/vosk/models), and extract `vosk-model-small-en-us-0.15` under `dashboard/`. Then run `python3 scripts/manual_voice_trigger_app_dashboard.py`; it listens locally, prints recognized commands in the terminal, and launches the dashboard for supported phrases. Set `VOSK_MODEL_PATH` if the model is stored elsewhere. The voice listener does not use HTTP or send audio to an online service. Pass `--environment testing` or `--environment production` (also available as `--mode`) to force the dashboard mode regardless of which supported test/production phrase is spoken. For integrations, the optional `--http` mode starts the localhost endpoint; send JSON such as `{"command":"show test invoice dashboard"}` to `http://127.0.0.1:5001/trigger-dashboard`.

To launch a dashboard directly from Terminal without listening, pass the voice phrase to `--voice`, for example `python3 scripts/manual_voice_trigger_app_dashboard.py --voice "show test invoice dashboard"`; the phrase may also be entered without quotes.
```bash
python3 scripts/manual_voice_trigger_app_dashboard.py --voice "show test invoice dashboard"
python3 scripts/manual_voice_trigger_app_dashboard.py --voice show production invoice dashboard

python3 scripts/manual_voice_trigger_app_dashboard.py --environment testing
python3 scripts/manual_voice_trigger_app_dashboard.py --mode production --voice "show test invoice dashboard"
```

Use the same environment option to override the phrase's mode, for example `python3 scripts/manual_voice_trigger_app_dashboard.py --environment testing --voice "show production invoice dashboard"` launches the test dashboard.

## Troubleshooting

- **Missing `dashboard/token.json`:** Complete the one-time authorization steps and verify the token file is in `dashboard/`.
- **Image build fails:** Check Docker availability and confirm that `requirements.txt` and `dashboard/invoice_dashboard_app.py` are present.
- **Port `8501` is already in use:** Stop the process or container using that port before launching the dashboard again.
- **Browser does not open:** Open `http://localhost:8501` manually. The automatic `open` command is macOS-specific.

## Repository layout

```text
invoice_handler/
├── dashboard/
│   ├── credentials.json  # local only
│   ├── generate_token.py
│   ├── invoice_dashboard_app.py
│   ├── invoice_sample.csv
│   ├── token.json        # local only
│   └── Dockerfile
├── scheduler/
│   └── invoice_cloud_scheduler_ingest.py
├── scripts/
│   ├── manual_voice_trigger_dashboard.py
│   └── voice_trigger_dashboard.sh
├── docker_compose.yml
└── requirements.txt
```
