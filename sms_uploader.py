"""
One-shot uploader:
1. Reads an SMS-backup XML file.
2. Extracts UPI / debit messages (amount, date, sender, full text).
3. Writes the list to Firebase under /transactions.

Can be run locally, in Replit, or in a GitHub Action.
Requires the Firebase service-account JSON in environment variable
FIREBASE_ACCOUNT (via st.secrets when run in Streamlit Cloud).
"""

import json, re, xmltodict, streamlit as st
import firebase_admin
from firebase_admin import credentials, db, get_app, initialize_app

# ── Config ───────────────────────────────────────────────────────────
XML_FILE = "sms_backup.xml"   # supply the latest export here

# ── Firebase init (same thread-safe pattern) ─────────────────────────
service_account_info = json.loads(st.secrets["FIREBASE_ACCOUNT"])

try:
    app = get_app()
except ValueError:
    cred = credentials.Certificate(service_account_info)
    app = initialize_app(
        cred,
        {"databaseURL": "https://expense-tracker-74700-default-rtdb.firebaseio.com/"},
    )

# ── Parse XML ────────────────────────────────────────────────────────
with open(XML_FILE, "r", encoding="utf-8") as f:
    sms_dict = xmltodict.parse(f.read())

keywords     = ["debited", "credited", "upi", "payment", "txn", "transaction"]
transactions = []

for sms in sms_dict.get("smses", {}).get("sms", []):
    body = sms.get("@body", "")
    if any(k in body.lower() for k in keywords):
        m = re.search(r"INR[\s₹]?([\d,]+\.\d{2})", body)
        if m:
            transactions.append(
                {
                    "date":    sms.get("@date", ""),
                    "amount":  float(m.group(1).replace(",", "")),
                    "address": sms.get("@address", ""),
                    "message": body,
                }
            )

print(f"Parsed {len(transactions)} transaction(s).")

# ── Upload to Firebase ───────────────────────────────────────────────
if transactions:
    db.reference("transactions").set(transactions)
    print("✅  Uploaded to Firebase.")
else:
    print("⚠️  No valid transactions found – nothing uploaded.")
