import base64
import json
import os
import re
from email.utils import parseaddr, parsedate_to_datetime
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
APP_EMAIL_FILTER = os.environ.get("APP_EMAIL_FILTER", "in:inbox invoice")
APP_DATA_MODE = os.environ.get("APP_DATA_MODE", "production").strip().lower()
TEST_DATA_PATH = Path(__file__).with_name("invoice_sample.csv")
PAGE_SIZE_OPTIONS = [10, 25, 50, 100]
INVOICE_COLUMNS = [
    "Supplier",
    "Ledger",
    "Invoice #",
    "Amount",
    "Created",
    "Documents",
    "Workflow",
]
SUPPLIER_DOMAIN_COLUMN = "Supplier Domain"
GENERIC_EMAIL_DOMAINS = {
    "aol.com",
    "gmail.com",
    "hotmail.com",
    "icloud.com",
    "live.com",
    "outlook.com",
    "proton.me",
    "protonmail.com",
    "yahoo.com",
}
SIMPLE_ICON_SLUGS = {
    "amazon web services": "amazonaws",
    "google workspace": "google",
    "microsoft 365": "microsoft",
    "telegram premium": "telegram",
}

st.set_page_config(page_title="Invoices", layout="wide")


def _decode_part(data: str) -> str:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode(
        "utf-8", errors="replace"
    )


def _read_payload(part: dict, body_parts: list[str], filenames: list[str]) -> None:
    filename = part.get("filename")
    if filename:
        filenames.append(filename)

    mime_type = part.get("mimeType", "")
    data = part.get("body", {}).get("data")
    if data and mime_type == "text/plain":
        body_parts.append(_decode_part(data))

    for child in part.get("parts", []):
        _read_payload(child, body_parts, filenames)


def _header_value(headers: list[dict], name: str) -> str:
    return next(
        (header.get("value", "") for header in headers if header.get("name", "").lower() == name.lower()),
        "",
    )


def _supplier_name(from_header: str) -> str:
    display_name, email_address = parseaddr(from_header)
    if display_name:
        return display_name
    if email_address:
        return email_address.rsplit("@", 1)[0].replace(".", " ").replace("_", " ").title()
    return "Unknown supplier"


def _supplier_domain(from_header: str) -> str:
    _, email_address = parseaddr(from_header)
    domain = email_address.rsplit("@", 1)[-1].lower() if "@" in email_address else ""
    if domain in GENERIC_EMAIL_DOMAINS or not re.fullmatch(r"[a-z0-9.-]+", domain):
        return ""
    return domain


def _has_logo(url: str) -> bool:
    request = Request(url, headers={"Range": "bytes=0-1023"})
    try:
        with urlopen(request, timeout=4) as response:
            return response.headers.get_content_type().startswith("image/")
    except (HTTPError, URLError, TimeoutError):
        return False


def _placeholder_logo(supplier: str) -> str:
    initials = "".join(
        word[0] for word in re.findall(r"[A-Za-z0-9]+", supplier)[:2]
    ).upper() or "?"
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<rect width="64" height="64" rx="12" fill="#e6eaed"/>'
        '<text x="32" y="41" text-anchor="middle" '
        'font-family="Arial,sans-serif" font-size="25" font-weight="600" '
        'fill="#5b6470">'
        f"{initials}</text></svg>"
    )
    encoded_svg = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded_svg}"


@st.cache_data(ttl=86400, show_spinner=False)
def _supplier_logo_url(supplier: str, domain: str, logo_dev_key: str) -> str:
    if logo_dev_key:
        identifier = (
            quote(domain, safe="")
            if domain
            else f"name/{quote(supplier, safe='')}"
        )
        logo_url = (
            f"https://img.logo.dev/{identifier}?token={quote(logo_dev_key, safe='')}"
            "&format=png&size=64&fallback=404"
        )
        if _has_logo(logo_url):
            return logo_url

    normalized_supplier = supplier.casefold().strip()
    slug = SIMPLE_ICON_SLUGS.get(
        normalized_supplier,
        re.sub(r"[^a-z0-9]", "", normalized_supplier),
    )
    if slug:
        simple_icon_url = f"https://cdn.simpleicons.org/{quote(slug, safe='')}"
        if _has_logo(simple_icon_url):
            return simple_icon_url

    return _placeholder_logo(supplier)


def _invoice_number(subject: str, body: str) -> str:
    text = f"{subject}\n{body}"
    match = re.search(
        r"\binvoice\s*(?:number|no\.?|#)\s*[:#-]?\s*([A-Z0-9][A-Z0-9/-]*)",
        text,
        re.IGNORECASE,
    )
    return match.group(1) if match else "—"


def _invoice_amount(text: str) -> str:
    match = re.search(
        r"\b(USD|CAD|AUD|EUR|GBP)\s*([0-9][0-9,]*(?:\.\d{2})?)|"
        r"([$€£])\s*([0-9][0-9,]*(?:\.\d{2})?)",
        text,
        re.IGNORECASE,
    )
    if not match:
        return "—"
    if match.group(1):
        return f"{match.group(1).upper()} {match.group(2)}"
    return f"{match.group(3)}{match.group(4)}"


def _created_date(header_date: str, internal_date: str) -> str:
    try:
        created = parsedate_to_datetime(header_date)
    except (TypeError, ValueError, OverflowError):
        created = None

    if created is None and internal_date:
        created = datetime.fromtimestamp(int(internal_date) / 1000)
    return created.strftime("%b %-d, %Y") if created else "—"


@st.cache_data(ttl=300)
def fetch_invoices(token_json: str) -> pd.DataFrame:
    token_info = json.loads(token_json)
    granted_scopes = token_info.get("scopes", [])
    if GMAIL_READONLY_SCOPE not in granted_scopes:
        raise ValueError(
            "This token does not have Gmail read-only access. Re-authorize using "
            "dashboard/generate_token.py after updating or removing dashboard/token.json."
        )

    credentials = Credentials.from_authorized_user_info(token_info)
    gmail = build("gmail", "v1", credentials=credentials)
    labels = gmail.users().labels().list(userId="me").execute().get("labels", [])
    user_labels = {
        label["id"]: label["name"]
        for label in labels
        if label.get("type") == "user"
    }

    messages = []
    page_token = None
    while True:
        response = (
            gmail.users()
            .messages()
            .list(
                userId="me",
                q=APP_EMAIL_FILTER,
                maxResults=100,
                pageToken=page_token,
            )
            .execute()
        )
        messages.extend(response.get("messages", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    rows = []
    for message in messages:
        details = (
            gmail.users()
            .messages()
            .get(userId="me", id=message["id"], format="full")
            .execute()
        )
        payload = details.get("payload", {})
        headers = payload.get("headers", [])
        body_parts: list[str] = []
        filenames: list[str] = []
        _read_payload(payload, body_parts, filenames)
        body = "\n".join(body_parts)
        subject = _header_value(headers, "Subject")
        message_labels = set(details.get("labelIds", []))
        companies = sorted(
            user_labels[label_id]
            for label_id in message_labels
            if label_id in user_labels
        )

        rows.append(
            {
                "Supplier": _supplier_name(_header_value(headers, "From")),
                SUPPLIER_DOMAIN_COLUMN: _supplier_domain(
                    _header_value(headers, "From")
                ),
                "Ledger": ", ".join(companies) or "Unassigned",
                "Invoice #": _invoice_number(subject, body),
                "Amount": _invoice_amount(f"{subject}\n{body}"),
                "Created": _created_date(
                    _header_value(headers, "Date"), details.get("internalDate", "")
                ),
                "Documents": ", ".join(filenames) or subject or "Email",
                "Workflow": "Unread" if "UNREAD" in message_labels else "Read",
            }
        )

    return pd.DataFrame(rows, columns=[*INVOICE_COLUMNS, SUPPLIER_DOMAIN_COLUMN])


def load_test_invoices() -> pd.DataFrame:
    invoices = pd.read_csv(TEST_DATA_PATH, dtype=str).fillna("")
    missing_columns = [column for column in INVOICE_COLUMNS if column not in invoices]
    if missing_columns:
        raise ValueError(
            f"Test CSV is missing required columns: {', '.join(missing_columns)}"
        )
    if SUPPLIER_DOMAIN_COLUMN not in invoices:
        invoices[SUPPLIER_DOMAIN_COLUMN] = ""
    return invoices[[*INVOICE_COLUMNS, SUPPLIER_DOMAIN_COLUMN]]


title, theme_toggle = st.columns([7, 3], vertical_alignment="center")
with title:
    st.title("Invoices")
with theme_toggle:
    dark_mode = st.toggle("Dark mode", key="dark_mode")

background = "#0e1117" if dark_mode else "#ffffff"
secondary_background = "#262730" if dark_mode else "#f0f2f6"
text_color = "#fafafa" if dark_mode else "#31333f"
border_color = "#41434f" if dark_mode else "#e6eaed"
st.markdown(
    f"""
    <style>
    :root {{
        color-scheme: {"dark" if dark_mode else "light"};
        --background-color: {background};
        --secondary-background-color: {secondary_background};
        --text-color: {text_color};
    }}
    .block-container {{ padding-top: 1.5rem; }}
    [data-testid="stAppViewContainer"] {{
        background-color: var(--background-color);
        color: var(--text-color);
    }}
    [data-testid="stHeader"] {{ background-color: var(--background-color); }}
    [data-testid="stDataFrame"] {{
        border: 1px solid {border_color};
        border-radius: 12px;
    }}
    [data-baseweb="popover"], [role="listbox"] {{
        background-color: var(--secondary-background-color);
        color: var(--text-color);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

if APP_DATA_MODE not in {"test", "production"}:
    st.error("APP_DATA_MODE must be either 'test' or 'production'.")
    st.stop()

try:
    if APP_DATA_MODE == "test":
        with st.spinner("Loading invoice sample data..."):
            invoices = load_test_invoices()
        st.caption("Test mode · sample data based on the invoice table template")
    else:
        token_json = os.environ.get("GOOGLE_TOKEN_JSON")
        if not token_json:
            st.error(
                "Google credentials are missing. Run the production dashboard "
                "launcher after setting up Gmail authorization."
            )
            st.stop()
        with st.spinner("Loading invoices from Gmail..."):
            invoices = fetch_invoices(token_json)
except Exception as error:
    source = "sample data" if APP_DATA_MODE == "test" else "Gmail"
    st.error(f"Could not load invoices from {source}: {error}")
    st.stop()

if invoices.empty:
    source = "sample data" if APP_DATA_MODE == "test" else "this Gmail account"
    st.info(f"No invoices were found in {source}.")
    st.stop()

all_ledgers = sorted(invoices["Ledger"].unique().tolist())
ledger_options = ["All", *all_ledgers]
selected_ledger = st.radio(
    "Ledger",
    ledger_options,
    horizontal=True,
    label_visibility="collapsed",
)

with st.popover("Filters"):
    suppliers = sorted(invoices["Supplier"].unique().tolist())
    selected_suppliers = st.multiselect("Supplier", suppliers)
    workflows = sorted(invoices["Workflow"].unique().tolist())
    selected_workflows = st.multiselect("Workflow", workflows, default=workflows)

filtered = invoices
if selected_ledger != "All":
    filtered = filtered[
        filtered["Ledger"]
        .str.split(", ")
        .apply(lambda labels: selected_ledger in labels)
    ]
if selected_suppliers:
    filtered = filtered[filtered["Supplier"].isin(selected_suppliers)]
filtered = filtered[filtered["Workflow"].isin(selected_workflows)]

if filtered.empty:
    st.info("No invoices match the selected filters.")
    st.stop()

if "invoice_page" not in st.session_state:
    st.session_state.invoice_page = 0

page_size = st.selectbox(
    "Results per page",
    PAGE_SIZE_OPTIONS,
    index=0,
    label_visibility="collapsed",
)
page_count = (len(filtered) + page_size - 1) // page_size
st.session_state.invoice_page = min(st.session_state.invoice_page, page_count - 1)
page_index = st.session_state.invoice_page
start = page_index * page_size
page = filtered.iloc[start : start + page_size].copy()
logo_dev_key = os.environ.get("LOGO_DEV_PUBLISHABLE_KEY", "").strip()
page.insert(
    0,
    "Logo",
    [
        _supplier_logo_url(
            row["Supplier"],
            row[SUPPLIER_DOMAIN_COLUMN],
            logo_dev_key,
        )
        for _, row in page.iterrows()
    ],
)

st.dataframe(
    page,
    hide_index=True,
    use_container_width=True,
    height=min(42 * (len(page) + 1), 520),
    column_config={
        "Logo": st.column_config.ImageColumn("Logo", width="small"),
        "Supplier": st.column_config.TextColumn("Supplier", width="medium"),
        SUPPLIER_DOMAIN_COLUMN: None,
        "Ledger": st.column_config.TextColumn("Ledger", width="medium"),
        "Invoice #": st.column_config.TextColumn("Invoice #", width="small"),
        "Amount": st.column_config.TextColumn("Amount", width="small"),
        "Created": st.column_config.TextColumn("Created", width="medium"),
        "Documents": st.column_config.TextColumn("Documents", width="large"),
        "Workflow": st.column_config.TextColumn(
            "Workflow", help="Gmail read status; the dashboard does not change it."
        ),
    },
)
if any(logo_url.startswith("https://img.logo.dev/") for logo_url in page["Logo"]):
    st.caption("[Logos provided by Logo.dev](https://logo.dev)")

previous, count, next_page = st.columns([1, 4, 1])
with previous:
    if st.button("‹ Previous", disabled=page_index == 0):
        st.session_state.invoice_page -= 1
        st.rerun()
with count:
    st.caption(
        f"Showing {start + 1}–{start + len(page)} of {len(filtered)} invoices "
        f"· Page {page_index + 1} of {page_count}"
    )
with next_page:
    if st.button("Next ›", disabled=page_index >= page_count - 1):
        st.session_state.invoice_page += 1
        st.rerun()
