"""
Reads an SMS backup XML, extracts INR amounts, and writes the
resulting list to Firebase under /transactions.

Run this locally or in a GitHub Action whenever you have a new
sms_backup.xml file.  FIREBASE_ACCOUNT secret must be set.
"""

import os, json, re, xmltodict
import firebase_admin
from firebase_admin import credentials, db

# ── Config ─────────────────────────────────────────────────
XML_FILE = "sms_backup.xml"  # rename to your latest backup file

service_account_info = json.loads(os.environ["FIREBASE_ACCOUNT"])
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
