import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
import json
import streamlit as st
from google.oauth2.service_account import Credentials

sa_info = json.loads(st.secrets["gcp"]["service_account"])  # <-- THIS is the dict
creds = Credentials.from_service_account_info(
    sa_info,
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ],
)


gc = gspread.authorize(creds)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Ella Nails – Overview", layout="wide")

# ---------- AUTH ----------
@st.cache_resource
def get_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes,
    )
    return gspread.authorize(creds)
SHEET_ID = st.secrets["144GXa99ETKAMXvY6i9IELvmF7gF0U07ta2Z-IbIEN38"]

# ---------- LOAD DATA ----------
sh = gc.open_by_key(SHEET_ID)
ws = sh.worksheet("fact_nails_reception")

vals = ws.get_all_values()
headers = [h.strip() for h in vals[0]]
rows = vals[1:]
df = pd.DataFrame(rows, columns=headers)
df.columns = (
    pd.Index(df.columns)
    .astype(str).str.strip().str.lower()
    .str.replace(r"[^a-z0-9]+", "_", regex=True)
    .str.strip("_")
)
import streamlit as st
st.write("COLUMNS:", list(df.columns))
st.write("DUPES:", df.columns[df.columns.duplicated()].tolist())


def prep(df):
    if df.empty:
        return df
    df["date_time"] = pd.to_datetime(df["date_time"], errors="coerce")
    df["day"] = df["date_time"].dt.date
    return df

rec = prep(load_sheet("fact_nails_reception"))
tech = prep(load_sheet("fact_nails_techs"))
wax = prep(load_sheet("fact_wax"))

# ---------- DATE LOGIC ----------
today = datetime.now().date()
week_start = today - timedelta(days=today.weekday())  # Monday
week_end = week_start + timedelta(days=5)              # Saturday

def sum_between(df, col, start, end):
    if df.empty:
        return 0
    m = (df["day"] >= start) & (df["day"] <= end)
    return float(pd.to_numeric(df.loc[m, col], errors="coerce").fillna(0).sum())

# ---------- METRICS ----------
rec_today = sum_between(rec, "service_cost", today, today)
tech_today = sum_between(tech, "service_cost", today, today)
wax_today = sum_between(wax, "service_cost", today, today)

rec_week = sum_between(rec, "service_cost", week_start, week_end)
tech_week = sum_between(tech, "service_cost", week_start, week_end)
wax_week = sum_between(wax, "service_cost", week_start, week_end)

# ---------- UI ----------
st.title("Business Overview")

st.subheader("Today")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Nails (Reception)", f"{rec_today:,.0f}")
c2.metric("Nails (Tech)", f"{tech_today:,.0f}")
c3.metric("Wax", f"{wax_today:,.0f}")
c4.metric("Total", f"{(rec_today + wax_today):,.0f}")
c5.metric("Diff (Rec–Tech)", f"{(rec_today - tech_today):,.0f}")

st.divider()

st.subheader("This Week (Mon–Sat)")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Nails (Reception)", f"{rec_week:,.0f}")
c2.metric("Nails (Tech)", f"{tech_week:,.0f}")
c3.metric("Wax", f"{wax_week:,.0f}")
c4.metric("Total", f"{(rec_week + wax_week):,.0f}")
c5.metric("Diff (Rec–Tech)", f"{(rec_week - tech_week):,.0f}")

st.caption(f"Week: {week_start} → {week_end}")
