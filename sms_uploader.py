"""
Runs once: parses an SMS backup XML and uploads the extracted
transactions list to Firebase under /transactions.

✓ Reads the service-account JSON from st.secrets["FIREBASE_ACCOUNT"]
  (so it can also run inside Streamlit Cloud or a GitHub Action)
"""

import json, re, xmltodict, streamlit as st
import firebase_admin
from firebase_admin import credentials, db

# ── Config ─────────────────────────────────────────────────
XML_FILE = "sms_backup.xml"   # put your latest export here

service_account_info = json.loads(st.secrets["FIREBASE_ACCOUNT"])

if not firebase_admin._apps:
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(
        cred,
        {"databaseURL": "https://expense-tracker-74700-default-rtdb.firebaseio.com/"},
    )

# ── Parse XML ──────────────────────────────────────────────
with open(XML_FILE, "r", encoding="utf-8") as f:
    sms_dict = xmltodict.parse(f.read())

msgs         = sms_dict.get("smses", {}).get("sms", [])
keywords     = ["debited", "credited", "upi", "payment", "txn", "transaction"]
transactions = []

for m in msgs:
    body = m.get("@body", "")
    if any(k in body.lower() for k in keywords):
        amt = re.search(r"INR[\s₹]?([\d,]+\.\d{2})", body)
        if amt:
            transactions.append(
                {
                    "date":    m.get("@date", ""),
                    "amount":  float(amt.group(1).replace(",", "")),
                    "address": m.get("@address", ""),
                    "message": body,
                }
            )

print(f"Parsed {len(transactions)} transaction(s).")

# ── Upload ─────────────────────────────────────────────────
if transactions:
    db.reference("transactions").set(transactions)
    print("✅  Uploaded to Firebase.")
else:
    print("⚠️  No valid transactions found – nothing uploaded.")
