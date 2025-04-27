"""
Enhanced dashboard

• Category bar-chart + table
• Income vs Expense totals
• Weekly spend line-chart
"""

import json, streamlit as st, pandas as pd, datetime as dt
import firebase_admin
from firebase_admin import credentials, db, get_app, initialize_app

# ──────────────────────────────────────────────────────────────
# Firebase init  (reads JSON from Streamlit Secrets)
# ──────────────────────────────────────────────────────────────
info = json.loads(st.secrets["FIREBASE_ACCOUNT"])

try:
    app = get_app()
except ValueError:
    cred = credentials.Certificate(info)
    initialize_app(
        cred,
        {"databaseURL": "https://expense-tracker-74700-default-rtdb.firebaseio.com/"},
    )

# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────
raw = db.reference("transactions").get()
st.title("📊 SMS-Expense Dashboard")

if not raw:
    st.info("No transactions found. Run the uploader first.")
    st.stop()

df = pd.DataFrame.from_dict(raw)
df["amount"] = pd.to_numeric(df["amount"])
df["date"]   = pd.to_datetime(df["date"].astype("int64"), unit="ms")

# ──────────────────────────────────────────────────────────────
# 1  Categorise rows (simple keyword → category mapping)
# ──────────────────────────────────────────────────────────────
cat_map = {
    "amazon":       "Shopping",
    "flipkart":     "Shopping",
    "food":         "Food",
    "swiggy":       "Food",
    "zomato":       "Food",
    "ola":          "Transport",
    "uber":         "Transport",
    "rent":         "Housing",
    "salary":       "Income",
    "credited":     "Income",
}

def categorise(row):
    body = row["message"].lower()
    for kw, cat in cat_map.items():
        if kw in body:
            return cat
    return "Other"

df["category"] = df.apply(categorise, axis=1)

# ──────────────────────────────────────────────────────────────
# 2  Income vs Expense summary
# ──────────────────────────────────────────────────────────────
df["sign"] = df["category"].eq("Income").map({True: 1, False: -1})
df["signed_amount"] = df["amount"] * df["sign"]

total_income  = df.loc[df["category"] == "Income",  "amount"].sum()
total_expense = df.loc[df["category"] != "Income", "amount"].sum()

col1, col2 = st.columns(2)
col1.metric("💰 Total Income (₹)",  f"{total_income:,.2f}")
col2.metric("💸 Total Expense (₹)", f"{total_expense:,.2f}")

# ──────────────────────────────────────────────────────────────
# 3  Category-wise spend (bar-chart + table)
# ──────────────────────────────────────────────────────────────
st.subheader("Category-wise Expense")
cat_spend = (
    df.loc[df["category"] != "Income"]
      .groupby("category")["amount"]
      .sum()
      .sort_values(ascending=False)
)

st.bar_chart(cat_spend)
st.dataframe(cat_spend.reset_index().rename(columns={"amount": "₹ Spent"}))

# ──────────────────────────────────────────────────────────────
# 4  Weekly spend trend
# ──────────────────────────────────────────────────────────────
st.subheader("Weekly Spend (calendar week)")
df["year_week"] = df["date"].dt.strftime("%Y-%U")
weekly = (
    df.loc[df["category"] != "Income"]
      .groupby("year_week")["amount"]
      .sum()
      .reset_index()
)

weekly = weekly.sort_values("year_week")
weekly_chart = weekly.set_index("year_week")

st.line_chart(weekly_chart)

# ──────────────────────────────────────────────────────────────
# 5  Raw transaction table  (message hidden by default)
# ──────────────────────────────────────────────────────────────
with st.expander("Show raw data (message column hidden)"):
    st.dataframe(
        df.drop(columns=["message"])
          .sort_values("date", ascending=False)
          .reset_index(drop=True)
    )
