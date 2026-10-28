"""Data loading and shared calculations. No UI code here."""
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "risk_inventory.xlsx"  # Drop your file here
RATING_ORDER = ["High", "Medium", "Low"]


def data_version() -> float:
    """File modified time. When the file changes, every cache keyed on it refreshes."""
    return os.path.getmtime(DATA_FILE) if DATA_FILE.exists() else 0.0


def last_updated() -> datetime:
    v = data_version()
    return datetime.fromtimestamp(v) if v else datetime.now().replace(minute=30, hour=7)


@st.cache_data(max_entries=3, show_spinner=False)
def load_inventory(version: float) -> pd.DataFrame:
    if DATA_FILE.exists():
        df = pd.read_excel(DATA_FILE)
    else:
        df = _sample_inventory()
    df["Due"] = pd.to_datetime(df["Due"])
    return df


def filtered(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the sidebar category filter set in streamlit_app.py."""
    cats = st.session_state.get("categories")
    return df[df["Category"].isin(cats)] if cats else df


def overdue(df: pd.DataFrame) -> pd.DataFrame:
    today = pd.Timestamp(date.today())
    out = df[(df["Status"] != "Mitigated") & (df["Due"] < today)].copy()
    out["Days overdue"] = (today - out["Due"]).dt.days
    return out.sort_values("Days overdue", ascending=False)


def high_by_category(df: pd.DataFrame) -> pd.Series:
    return (df[df["Rating"] == "High"].groupby("Category").size()
            .sort_values(ascending=False))


def kpis(df: pd.DataFrame) -> dict:
    return {
        "high": int((df["Rating"] == "High").sum()),
        "mitigated": int((df["Status"] == "Mitigated").sum()),
        "overdue": len(overdue(df)),
    }


def previous_kpis(df: pd.DataFrame) -> dict:
    """Last month's figures. Replace with a real snapshot (e.g. last month's file)."""
    now = kpis(df)
    return {"high": now["high"] - 5, "mitigated": now["mitigated"] - 12, "overdue": now["overdue"]}


HISTORY_FILE = ROOT / "data" / "history.csv"  # columns: Month, High, Medium, Low, Overdue, Mitigated, AvgScore


@st.cache_data(max_entries=3, show_spinner=False)
def history(version: float) -> pd.DataFrame:
    """Monthly snapshot counts for trend charts. Sample numbers until history.csv exists."""
    if HISTORY_FILE.exists():
        return pd.read_csv(HISTORY_FILE)
    df = load_inventory(version)
    now = df["Rating"].value_counts()
    months = pd.date_range(end=pd.Timestamp(date.today()), periods=6, freq="MS")
    drift = np.array([9, 7, 6, 4, 5, 0])  # sample: high risks were higher earlier
    return pd.DataFrame({
        "Month": months.strftime("%b"),
        "High": now.get("High", 0) + drift,
        "Medium": now.get("Medium", 0) + np.array([-4, -3, -1, -2, 1, 0]),
        "Low": now.get("Low", 0) + np.array([-5, -4, -5, -2, -6, 0]),
        "Overdue": len(overdue(df)) + np.array([6, 9, 4, 2, 0, 0]),
        "Mitigated": int((df["Status"] == "Mitigated").sum()) + np.array([-40, -31, -22, -18, -12, 0]),
        "AvgScore": round(df["Score"].mean(), 1) + np.array([1.1, 0.9, 0.6, 0.5, 0.2, 0]),
    })


def category_profile(df: pd.DataFrame, category: str) -> dict:
    c = df[df["Category"] == category]
    od = overdue(c)
    high = c[c["Rating"] == "High"]
    return {
        "total": len(c),
        "high": len(high),
        "high_share": len(high) / max(len(c), 1),
        "portfolio_high_share": (df["Rating"] == "High").mean(),
        "overdue": len(od),
        "oldest_overdue": od.iloc[0].to_dict() if not od.empty else None,
        "mitigated_share": (c["Status"] == "Mitigated").mean() if len(c) else 0,
        "avg_score": c["Score"].mean() if len(c) else 0,
        "top_owner": high["Owner"].value_counts().idxmax() if not high.empty else None,
        "top_owner_n": int(high["Owner"].value_counts().max()) if not high.empty else 0,
        "recurring": c["Risk"].value_counts().idxmax() if len(c) else None,
        "recurring_n": int(c["Risk"].value_counts().max()) if len(c) else 0,
        "top_risks": c.sort_values("Score", ascending=False).head(5),
    }


# ---------- Sample data so the template runs out of the box ----------
_TITLES = {
    "Compliance": ["Sanctions screening gaps", "KYC refresh backlog", "Record-keeping breach",
                   "Cross-border data transfer", "Conduct risk in sales"],
    "IT": ["Legacy system outage", "Privileged access review", "Patch backlog",
           "Third-party cloud dependency", "Backup restore failure"],
    "Credit": ["Concentration in real estate", "Collateral valuation lag", "Covenant monitoring",
               "Counterparty downgrade", "Model override volume"],
    "Market": ["FX hedge mismatch", "Liquidity in stressed markets", "VaR model limits",
               "Basis risk", "Interest rate repricing"],
    "Operational": ["Manual reconciliation errors", "Key person dependency", "Vendor SLA breach",
                    "Payment processing errors", "Business continuity test gaps"],
}


def _sample_inventory(n: int = 300) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    cats = rng.choice(list(_TITLES), n, p=[.25, .22, .2, .15, .18])
    likelihood, impact = rng.integers(1, 6, n), rng.integers(1, 6, n)
    score = likelihood * impact  # 1-25
    today = date.today()
    return pd.DataFrame({
        "ID": [f"R-{i:03d}" for i in range(1, n + 1)],
        "Risk": [rng.choice(_TITLES[c]) for c in cats],
        "Category": cats,
        "Rating": np.where(score >= 15, "High", np.where(score >= 8, "Medium", "Low")),
        "Likelihood": likelihood,
        "Impact": impact,
        "Score": score,
        "Owner": rng.choice(["Alice", "Bob", "Carol", "David", "Emma"], n),
        "Status": rng.choice(["Open", "In progress", "Mitigated"], n, p=[.3, .3, .4]),
        "Due": [today + timedelta(days=int(d)) for d in rng.integers(-25, 120, n)],
        "Mitigation": "Mitigation plan in place",
    })
