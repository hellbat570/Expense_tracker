"""
Streamlit dashboard – reads /transactions from Firebase and shows
totals + a table.  Expects the Firebase service-account JSON in the
Streamlit Secrets panel under the key FIREBASE_ACCOUNT.
"""

import json, streamlit as st, pandas as pd
import firebase_admin
from firebase_admin import credentials, db, get_app, initialize_app

# ── Firebase initialisation (thread-safe) ────────────────────────────
service_account_info = json.loads(st.secrets["FIREBASE_ACCOUNT"])

try:
    app = get_app()                       # reuse if one already exists
except ValueError:                        # else create it
    cred = credentials.Certificate(service_account_info)
    app = initialize_app(
        cred,
        {"databaseURL": "https://expense-tracker-74700-default-rtdb.firebaseio.com/"},
    )

# ── Fetch data and build UI ──────────────────────────────────────────
data = db.reference("transactions").get()
st.title("📊  SMS-Expense Dashboard")

if data:
    df = pd.DataFrame.from_dict(data)
    st.metric("Total Transactions", len(df))
    st.metric("Total Spent (₹)", f"{df['amount'].sum():,.2f}")
    st.dataframe(df)
else:
    st.info("No transactions found – run the uploader.")
