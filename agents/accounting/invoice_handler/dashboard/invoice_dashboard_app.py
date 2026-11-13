import argparse
import base64
import html
from io import BytesIO
import json
import os
import re

from email.utils import parseaddr, parsedate_to_datetime
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree

import pandas as pd
import streamlit as st
from PIL import Image
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()  # searches up the directory tree
environment_parser = argparse.ArgumentParser()
environment_parser.add_argument(
    "--environment",
    "--mode",
    choices=("testing", "production"),
    required=True,
)
ENVIRONMENT_MODE = environment_parser.parse_args().environment

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
APP_EMAIL_FILTER = os.environ.get("APP_EMAIL_FILTER", "in:inbox invoice")
LOGO_DEV_PUBLISHABLE_KEY = os.environ.get("LOGO_DEV_PUBLISHABLE_KEY", "").strip()
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
    except (HTTPError, URLError, TimeoutError, OSError):
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
        encoded_slug = quote(slug, safe="")
        simple_icon_urls = (
            f"https://cdn.jsdelivr.net/npm/simple-icons@16.10.0/icons/{encoded_slug}.svg",
            f"https://cdn.simpleicons.org/{encoded_slug}",
        )
        for simple_icon_url in simple_icon_urls:
            if _has_logo(simple_icon_url):
                return simple_icon_url

    return _placeholder_logo(supplier)


@st.cache_data(ttl=86400, show_spinner=False)
def _inline_svg_icon(image_data: bytes, color: str) -> str | None:
    try:
        root = ElementTree.fromstring(image_data)
    except ElementTree.ParseError:
        return None

    if root.tag.rsplit("}", 1)[-1] != "svg":
        return None
    view_box = root.get("viewBox")
    if not view_box:
        return None

    allowed_tags = {
        "circle",
        "ellipse",
        "g",
        "line",
        "path",
        "polygon",
        "polyline",
        "rect",
        "text",
    }
    allowed_attributes = {
        "cx",
        "cy",
        "d",
        "fill",
        "fill-rule",
        "opacity",
        "points",
        "r",
        "rx",
        "ry",
        "stroke",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-width",
        "transform",
        "font-family",
        "font-size",
        "font-weight",
        "text-anchor",
        "x",
        "x1",
        "x2",
        "y",
        "y1",
        "y2",
    }

    def render_element(element: ElementTree.Element) -> str:
        tag = element.tag.rsplit("}", 1)[-1]
        if tag not in allowed_tags:
            return ""
        if tag == "path" and not element.get("d"):
            return ""
        if tag in {"polygon", "polyline"} and not element.get("points"):
            return ""

        attributes = {
            key: value.replace("currentColor", color)
            for key, value in element.attrib.items()
            if key in allowed_attributes
        }
        rendered_attributes = " ".join(
            f'{key}="{html.escape(value, quote=True)}"'
            for key, value in attributes.items()
        )
        opening_tag = (
            f"<{tag} {rendered_attributes}>"
            if rendered_attributes
            else f"<{tag}>"
        )
        if tag in {"circle", "ellipse", "line", "path", "polygon", "polyline", "rect"}:
            return opening_tag[:-1] + "/>"
        children = "".join(render_element(child) for child in element)
        text = html.escape(element.text or "")
        if tag == "g" and not children:
            return ""
        return f"{opening_tag}{text}{children}</{tag}>"

    root_fill = root.get("fill", color).replace("currentColor", color)
    content = "".join(render_element(child) for child in root)
    if not content:
        return None
    return (
        f'<svg x="2" y="5" width="32" height="32" '
        f'viewBox="{html.escape(view_box, quote=True)}" '
        f'fill="{html.escape(root_fill, quote=True)}" '
        'preserveAspectRatio="xMidYMid meet">'
        f"{content}</svg>"
    )


@st.cache_data(ttl=86400, show_spinner=False)
def _supplier_cell_image(supplier: str, logo_url: str, dark_mode: bool) -> str:
    text_color = "#fafafa" if dark_mode else "#31333f"
    placeholder_image = _placeholder_logo(supplier)
    placeholder_data = base64.b64decode(placeholder_image.split(",", 1)[1])
    if logo_url.startswith("data:image/"):
        encoded_image = logo_url.split(",", 1)[1]
        image_data = base64.b64decode(encoded_image)
        content_type = logo_url[5:].split(";", 1)[0].lower()
    else:
        image_request = Request(logo_url)
        try:
            with urlopen(image_request, timeout=4) as response:
                content_type = response.headers.get_content_type()
                image_data = response.read(256 * 1024 + 1)
            if not content_type.startswith("image/") or len(image_data) > 256 * 1024:
                image_data = placeholder_data
                content_type = "image/svg+xml"
        except (HTTPError, URLError, TimeoutError, OSError):
            image_data = placeholder_data
            content_type = "image/svg+xml"

    icon_markup = (
        _inline_svg_icon(image_data, text_color)
        if content_type == "image/svg+xml"
        else None
    )
    if icon_markup is None:
        if content_type == "image/svg+xml":
            icon_markup = _inline_svg_icon(placeholder_data, text_color)
        else:
            try:
                with Image.open(BytesIO(image_data)) as image:
                    image.verify()
            except (OSError, ValueError):
                icon_markup = _inline_svg_icon(placeholder_data, text_color)
            else:
                encoded_image = base64.b64encode(image_data).decode("ascii")
                icon_markup = (
                    '<image x="2" y="5" width="32" height="32" '
                    f'href="data:{html.escape(content_type, quote=True)};base64,{encoded_image}" '
                    'preserveAspectRatio="xMidYMid meet"/>'
                )
    if icon_markup is None:
        raise ValueError(f"Could not create a supplier placeholder for {supplier!r}.")

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="42" '
        'viewBox="0 0 200 42" role="img">'
        f"<title>{html.escape(supplier)}</title>"
        f"{icon_markup}"
        f'<text x="42" y="26" fill="{text_color}" '
        'font-family="system-ui,-apple-system,BlinkMacSystemFont,sans-serif" '
        f'font-size="14">{html.escape(supplier)}</text>'
        "</svg>"
    )
    encoded_svg = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded_svg}"


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


# title, theme_toggle = st.columns([8, 3], vertical_alignment="center")
with st.container(
    horizontal=True,
    horizontal_alignment="distribute",
    vertical_alignment="center",
    wrap=False,
):
    st.title("Invoices")
    dark_mode = st.toggle("Dark mode", value=True, key="dark_mode")

# with title:
#     st.title("Invoices")
# with theme_toggle:
#     dark_mode = st.toggle("Dark mode", value=True, key="dark_mode")
background = "#0e1117" if dark_mode else "#ffffff"
secondary_background = "#262730" if dark_mode else "#f8fafc"
text_color = "#fafafa" if dark_mode else "#111827"
border_color = "#41434f" if dark_mode else "#e5e7eb"
control_border = "#41434f" if dark_mode else "#cbd5e1"
muted_text_color = "#aab4c0" if dark_mode else "#475569"
disabled_background = "#262730" if dark_mode else "#f1f5f9"
disabled_text_color = "#7d8590" if dark_mode else "#64748b"
disabled_border = "#41434f" if dark_mode else "#cbd5e1"
light_mode_styles = ""
if not dark_mode:
    light_mode_styles = f"""
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
        background-color: {background} !important;
        color: {text_color} !important;
        border-color: {control_border} !important;
    }}

    [data-testid="stTextInputRootElement"] {{
        background-color: {background} !important;
        border-color: {control_border};
        opacity: 1;
    }}
    [data-testid="stTextInputIcon"] {{
        color: {text_color} !important;
    }}
    [data-testid="stTextInput"] input::placeholder {{
        color: {muted_text_color} !important;
        opacity: 1;
    }}
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {{
        background-color: #e2e8f0;
        color: #1e293b;
    }}
    [data-baseweb="popover"], [role="listbox"] {{
        background-color: {background} !important;
        color: {text_color} !important;
        border-color: {control_border} !important;
    }}
    [role="option"], [data-testid="stWidgetLabel"],
    [data-testid="stRadio"] label {{
        color: {text_color} !important;
    }}
    [data-testid="stButton"] button,
    [data-testid="stPopover"] button,
    [data-testid="stSelectbox"] button,
    [data-testid="stSelectbox"] input {{
        background-color: {background};
        color: {text_color};
        border-color: {control_border};
    }}
    [data-testid="stSelectbox"] {{
        background-color: {background};
        color: {text_color};
        border-color: {control_border};
    }}
    [data-testid="stButton"] button:hover,
    [data-testid="stPopover"] button:hover {{
        background-color: {secondary_background};
        color: {text_color};
        border-color: {control_border};
    }}
    [data-testid="stCaptionContainer"] {{
        color: {muted_text_color};
    }}
    """
st.markdown(
    f"""
    <style>
    :root {{
        color-scheme: {"dark" if dark_mode else "light"};
        --background-color: {background};
        --secondary-background-color: {secondary_background};
        --text-color: {text_color};
    }}
    .body {{
        padding: 0
        margin: 0 auto;
    }}
    .block-container {{ padding-top: 4rem; }}
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
    [data-testid="stButton"] button:disabled,
    [data-testid="stPopover"] button:disabled {{
        background-color: {disabled_background} !important;
        color: {disabled_text_color} !important;
        border-color: {disabled_border} !important;
        opacity: 1 !important;
        cursor: not-allowed;
    }}
    {light_mode_styles}
    </style>
    """,
    unsafe_allow_html=True,
)

try:
    if ENVIRONMENT_MODE == "testing":
        with st.spinner("Loading invoice sample data..."):
            invoices = load_test_invoices()
        # st.caption("Test mode · sample data based on the invoice table template")
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
    source = "sample data" if ENVIRONMENT_MODE == "testing" else "Gmail"
    st.error(f"Could not load invoices from {source}: {error}")
    st.stop()

if invoices.empty:
    source = "sample data" if ENVIRONMENT_MODE == "testing" else "this Gmail account"
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

if "invoice_page" not in st.session_state:
    st.session_state.invoice_page = 0


def _reset_invoice_page() -> None:
    st.session_state.invoice_page = 0


def _refresh_invoice_data() -> None:
    fetch_invoices.clear()
    _supplier_logo_url.clear()
    _supplier_cell_image.clear()


with st.container(
    horizontal=True,
    horizontal_alignment="distribute",
    vertical_alignment="center",
    wrap=True,
):
    search_query = st.text_input(
        "Search invoices",
        key="invoice_search",
        type="search",
        placeholder="Search invoices...",
        label_visibility="collapsed",
        width=320,
        on_change=_reset_invoice_page,
    )
    with st.container(
        horizontal=True,
        horizontal_alignment="right",
        vertical_alignment="center",
        gap="small",
        wrap=False,
    ):
        st.button(
            " ",
            key="refresh_invoice_data",
            help="Refresh invoice data and supplier logos",
            type="secondary",
            icon=":material/refresh:",
            on_click=_refresh_invoice_data,
        )
        with st.popover("Filters"):
            suppliers = sorted(invoices["Supplier"].unique().tolist())
            selected_suppliers = st.multiselect("Supplier", suppliers)
            workflows = sorted(invoices["Workflow"].unique().tolist())
            selected_workflows = st.multiselect(
                "Workflow", workflows, default=workflows
            )
        page_size = st.selectbox(
            "Results per page",
            PAGE_SIZE_OPTIONS,
            index=0,
            width=80,
            label_visibility="collapsed",
        )

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
if search_query:
    searchable_columns = [
        column for column in INVOICE_COLUMNS if column in filtered.columns
    ]
    matches = filtered[searchable_columns].astype(str).apply(
        lambda column: column.str.contains(search_query, case=False, regex=False)
    )
    filtered = filtered[matches.any(axis=1)]

if filtered.empty:
    st.info("No invoices match the selected filters.")
    st.stop()

page_count = (len(filtered) + page_size - 1) // page_size
st.session_state.invoice_page = min(st.session_state.invoice_page, page_count - 1)
page_index = st.session_state.invoice_page
start = page_index * page_size
page = filtered.iloc[start : start + page_size].copy()
supplier_logo_urls = [
    _supplier_logo_url(
        row["Supplier"],
        row[SUPPLIER_DOMAIN_COLUMN],
        LOGO_DEV_PUBLISHABLE_KEY,
    )
    for _, row in page.iterrows()
]
page["Supplier"] = [
    _supplier_cell_image(supplier, logo_url, dark_mode)
    for supplier, logo_url in zip(page["Supplier"], supplier_logo_urls)
]

table_data = page
if not dark_mode:
    table_data = page.style.set_properties(color=text_color).apply(
        lambda column: [
            f"background-color: {background}"
            if row_index % 2 == 0
            else f"background-color: {secondary_background}"
            for row_index in range(len(column))
        ],
        axis=0,
    ).set_table_styles(
        [
            {
                "selector": "th",
                "props": [
                    ("background-color", secondary_background),
                    ("color", muted_text_color),
                ],
            }
        ]
    )

st.dataframe(
    table_data,
    hide_index=True,
    use_container_width=True,
    height="content",
    column_config={
        "Supplier": st.column_config.ImageColumn(
            "Supplier", width="medium", alignment="left"
        ),
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


previous, count, next_page = st.columns([2, 3, 1], vertical_alignment="center")
with previous:
    if st.button("‹ Previous", disabled=page_index == 0):
        st.session_state.invoice_page -= 1
        st.rerun()

with count:
    with st.container(
        horizontal=True,
        horizontal_alignment="center",
        vertical_alignment="center",
        wrap=False,
    ):
        st.caption(
            f"Showing {start + 1}–{start + len(page)} of {len(filtered)} invoices "
            f"· Page {page_index + 1} of {page_count}"
        )
    
with next_page:
    with st.container(
        horizontal=True,
        horizontal_alignment="right",
        vertical_alignment="center",
        wrap=False,
    ):
        if st.button("Next ›", disabled=page_index >= page_count - 1):
            st.session_state.invoice_page += 1
            st.rerun()
