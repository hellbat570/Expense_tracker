"""
Streamlit dashboard that reads /transactions from Firebase
and displays a summary + table.

Requires the service-account JSON in the environment variable
FIREBASE_ACCOUNT (add this in Streamlit Cloud → Secrets).
"""

import os, json
import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db

# ── Firebase init ──────────────────────────────────────────
service_account_info = json.loads(os.environ["FIREBASE_ACCOUNT"])

cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(
    cred,
    {"databaseURL": "https://expense-tracker-74700-default-rtdb.firebaseio.com/"},
)

# ── Fetch data ─────────────────────────────────────────────
data = db.reference("transactions").get()

# ── Streamlit UI ───────────────────────────────────────────
st.title("📊  SMS-Expense Dashboard")

if data:
    df = pd.DataFrame.from_dict(data)
    st.metric("Total Transactions", len(df))
    st.metric("Total Spent (₹)", f"{df['amount'].sum():,.2f}")
    st.dataframe(df)
else:
    st.info("No transactions found. Run the uploader script first.")
