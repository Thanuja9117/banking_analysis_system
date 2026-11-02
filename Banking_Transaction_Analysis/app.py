import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

st.set_page_config(page_title="Banking Transaction Analysis", page_icon="🏦", layout="wide")
st.title("🏦 Banking Transaction Analysis System")
st.caption("A student mini-project using sample transaction data. No real bank connection.")

sample_csv = '''Transaction_ID,Date,Type,Category,Amount,Description
T001,2026-10-01,Credit,Salary,10000,Monthly salary
T002,2026-10-02,Debit,Food,500,Lunch and snacks
T003,2026-10-03,Debit,Shopping,1500,Clothes
T004,2026-10-05,Credit,Transfer,2000,Money received
T005,2026-10-06,Debit,Education,1000,Books
T006,2026-10-08,Debit,Transport,250,Bus and auto
T007,2026-10-10,Debit,Food,400,Dinner
T008,2026-10-12,Credit,Other,1500,Refund received
T009,2026-10-15,Debit,Shopping,700,Accessories
T010,2026-10-18,Debit,Bills,800,Phone and internet
T011,2026-11-01,Credit,Salary,10000,Monthly salary
T012,2026-11-02,Debit,Food,650,Groceries
'''

with st.sidebar:
    st.header("Settings")
    opening_balance = st.number_input("Opening balance (₹)", min_value=0.0, value=5000.0, step=500.0)
    st.write("Upload your own CSV file (optional). Required columns: Transaction_ID, Date, Type, Category, Amount, Description")
    uploaded = st.file_uploader("Upload transactions CSV", type=["csv"])
    st.download_button("Download sample CSV", sample_csv, file_name="sample_transactions.csv", mime="text/csv")

try:
    df = pd.read_csv(uploaded) if uploaded else pd.read_csv(StringIO(sample_csv))
    required = {"Transaction_ID", "Date", "Type", "Category", "Amount"}
    if not required.issubset(df.columns):
        st.error("CSV missing required columns: " + ", ".join(sorted(required - set(df.columns))))
        st.stop()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df["Type"] = df["Type"].astype(str).str.strip().str.title()
    df = df.dropna(subset=["Date", "Amount"])
    df = df[df["Type"].isin(["Credit", "Debit"])]
except Exception as e:
    st.error(f"Could not read the data: {e}")
    st.stop()

if df.empty:
    st.warning("No valid transactions found in the file.")
    st.stop()

credits = df.loc[df.Type == "Credit", "Amount"].sum()
debits = df.loc[df.Type == "Debit", "Amount"].sum()
closing = opening_balance + credits - debits
c1,c2,c3,c4 = st.columns(4)
c1.metric("Total Credits", f"₹{credits:,.2f}")
c2.metric("Total Debits", f"₹{debits:,.2f}")
c3.metric("Closing Balance", f"₹{closing:,.2f}")
c4.metric("Transactions", f"{len(df)}")

st.subheader("Transaction History")
col1,col2,col3 = st.columns(3)
with col1: chosen_type = st.selectbox("Transaction type", ["All", "Credit", "Debit"])
with col2: categories = ["All"] + sorted(df.Category.astype(str).unique().tolist()); chosen_cat = st.selectbox("Category", categories)
with col3: search = st.text_input("Search description or transaction ID")
view = df.copy()
if chosen_type != "All": view = view[view.Type == chosen_type]
if chosen_cat != "All": view = view[view.Category.astype(str) == chosen_cat]
if search:
    desc = view["Description"].astype(str) if "Description" in view.columns else pd.Series("", index=view.index)
    view = view[view.Transaction_ID.astype(str).str.contains(search, case=False, na=False) | desc.str.contains(search, case=False, na=False)]
st.dataframe(view.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)

left,right = st.columns(2)
with left:
    st.subheader("Spending by Category")
    expenses = df[df.Type == "Debit"].groupby("Category")["Amount"].sum().sort_values(ascending=False)
    if not expenses.empty:
        fig, ax = plt.subplots()
        ax.bar(expenses.index.astype(str), expenses.values)
        ax.set_ylabel("Amount (₹)")
        ax.tick_params(axis="x", rotation=35)
        fig.tight_layout()
        st.pyplot(fig)
    else: st.info("No debit transactions to chart.")
with right:
    st.subheader("Credits vs Debits")
    totals = pd.Series({"Credits": credits, "Debits": debits})
    fig2, ax2 = plt.subplots()
    ax2.bar(totals.index, totals.values)
    ax2.set_ylabel("Amount (₹)")
    fig2.tight_layout()
    st.pyplot(fig2)

st.subheader("Monthly Analysis")
monthly = df.assign(Month=df.Date.dt.to_period("M").astype(str)).pivot_table(index="Month", columns="Type", values="Amount", aggfunc="sum", fill_value=0)
st.dataframe(monthly, use_container_width=True)

st.subheader("Large Transactions for Review")
threshold = st.number_input("Flag transactions at or above (₹)", min_value=1.0, value=5000.0, step=500.0)
flagged = df[df.Amount >= threshold].sort_values("Amount", ascending=False)
if flagged.empty: st.success("No transactions meet this review threshold.")
else:
    st.warning(f"{len(flagged)} transaction(s) meet the threshold. This is only a review flag, not proof of fraud.")
    st.dataframe(flagged, use_container_width=True, hide_index=True)

st.download_button("Download analyzed transactions", df.to_csv(index=False).encode("utf-8"), file_name="analyzed_transactions.csv", mime="text/csv")
st.caption("Academic demo only. Uses sample data unless you upload a CSV. Do not upload real account numbers, passwords, PINs, OTPs, or sensitive banking records.")
