import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Invoice Analytics Workspace", layout="wide")
st.title("📊 Modern Invoice Analytics Dashboard")

# Streamlit references the shared live link or downloaded CSV exported data snapshot
SHEET_CSV_URL = os.environ.get("SHEET_CSV_URL", "https://google.com")

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(SHEET_CSV_URL)
    df.columns = ['Date', 'Invoice ID', 'Amount']
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    return df.dropna()

try:
    data = load_data()

    # High-level Metrics Row
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Expenses Listed", f"${data['Amount'].sum():,.2f}")
    m2.metric("Total Invoices Count", len(data))
    m3.metric("Average Monthly Cost", f"${data['Amount'].mean():,.2f}")

    # Visual Analytics Split
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Spending Profile Distribution")
        st.bar_chart(data=data, x='Date', y='Amount')
    with col2:
        st.subheader("Invoice History Log")
        st.dataframe(data, use_container_width=True)

except Exception as e:
    st.error(f"Error accessing Google Sheet repository source: {e}")
