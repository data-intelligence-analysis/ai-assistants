# AI SALES AGENT v2

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