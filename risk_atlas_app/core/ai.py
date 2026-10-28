"""LLM access. Works in demo mode until you return a real client from get_client()."""
import time

import pandas as pd
import streamlit as st

from core import data

MODEL = "your-model-name"
MAX_HISTORY = 20            # messages sent back to the model each turn
MAX_FILE_CHARS = 20_000     # cap per uploaded file
CONTEXT_COLS = ["ID", "Risk", "Category", "Rating", "Score", "Owner", "Status", "Due"]

SYSTEM_PROMPT = """You are Risk Atlas, an assistant for the risk management team.
Answer only from the Risk Inventory data and any attached files.
Style:
- Start with one sentence that answers the question; put key names in **bold**.
- Use a Markdown table when listing three or more risks or owners.
- When useful, end with a short "#### Recommended next steps" numbered list.
- Be concise and factual. No emojis. If the data does not contain the answer, say so."""

SUMMARY_PROMPT = """Write a 2-sentence executive summary of this risk inventory.
Name the categories with the most High risks and mention overdue mitigations. No emojis.\n\n"""

DEFAULT_FOLLOW_UPS = ["Draft a reminder to owners", "Compare with last quarter", "Show IT high risks"]


@st.cache_resource
def get_client():
    # Return your real client here, for example:
    # from openai import OpenAI
    # return OpenAI()          # reads OPENAI_API_KEY; or use st.secrets["OPENAI_API_KEY"]
    return None


def is_demo() -> bool:
    return get_client() is None


# ---------- Chat ----------
def stream_chat(messages: list[dict], df: pd.DataFrame, question: str):
    """Return something st.write_stream can render."""
    client = get_client()
    if client is None:
        return _fake_stream(demo_answer(df, question))
    full = [{"role": "system", "content": SYSTEM_PROMPT + "\n\nRisk Inventory (CSV):\n"
             + df[CONTEXT_COLS].to_csv(index=False)}] + messages[-MAX_HISTORY:]
    # OpenAI streams are parsed natively; for other SDKs, yield text chunks yourself.
    return client.chat.completions.create(model=MODEL, messages=full, stream=True)


def transcribe(audio_file) -> str:
    client = get_client()
    if client is None:
        return "Which categories carry the most high risks, and which mitigations are overdue?"
    return client.audio.transcriptions.create(model="whisper-1", file=audio_file).text


def follow_ups(question: str) -> list[str]:
    """Suggested next questions. Swap for a model call if you want them dynamic."""
    return DEFAULT_FOLLOW_UPS


def auto_chart(df: pd.DataFrame, question: str) -> dict | None:
    """Example of app-computed visuals: add a chart when the question is about categories."""
    if "categor" in question.lower():
        return data.high_by_category(df).to_dict()
    return None


# ---------- Dashboard summary (cached, shared by all users) ----------
@st.cache_data(max_entries=50, show_spinner="Writing AI summary…")
def dashboard_summary(version: float, categories: tuple, model: str) -> str:
    df = data.load_inventory(version)
    df = df[df["Category"].isin(categories)]
    client = get_client()
    if client is None:
        top = data.high_by_category(df)
        od = data.overdue(df)
        if top.empty:
            return "No High-rated risks in the current selection."
        lead = " and ".join(f"**{c}** ({n})" for c, n in top.head(2).items())
        owner = od["Owner"].mode().iat[0] if not od.empty else "the risk owners"
        return (f"High risks are concentrated in {lead}. {len(od)} mitigation actions are "
                f"overdue; prioritise the items owned by {owner} this week.")
    r = client.chat.completions.create(model=model, messages=[
        {"role": "user", "content": SUMMARY_PROMPT + df[CONTEXT_COLS].to_csv(index=False)}])
    return r.choices[0].message.content


# ---------- Category commentary (cached, shared by all users) ----------
COMMENTARY_PROMPT = """You are a senior risk analyst. Write commentary on the {category} risk profile.
Use exactly three sections with these bold labels, 1-2 short bullets each:
**Key observations**, **Emerging concerns**, **Recommended actions**.
Compare with the portfolio where useful. Be specific (IDs, owners, numbers). No emojis.

Category facts: {facts}

Category risks (CSV):
"""


@st.cache_data(max_entries=50, show_spinner="Writing risk commentary…")
def category_commentary(version: float, category: str, model: str) -> str:
    df = data.load_inventory(version)
    p = data.category_profile(df, category)
    client = get_client()
    if client is None:
        return _demo_commentary(category, p)
    facts = {k: v for k, v in p.items() if k != "top_risks"}
    rows = df[df["Category"] == category][CONTEXT_COLS].to_csv(index=False)
    r = client.chat.completions.create(model=model, messages=[{"role": "user", "content":
        COMMENTARY_PROMPT.format(category=category, facts=facts) + rows}])
    return r.choices[0].message.content


def _demo_commentary(category: str, p: dict) -> str:
    vs = "above" if p["high_share"] > p["portfolio_high_share"] else "below"
    od = p["oldest_overdue"]
    oldest = (f"; the oldest is **{od['ID']}** ({od['Risk']}, {od['Owner']}), "
              f"{od['Days overdue']} days late") if od else ""
    return (
        f"**Key observations**\n"
        f"- {p['high']} of {p['total']} risks are rated High ({p['high_share']:.0%}), "
        f"{vs} the portfolio average of {p['portfolio_high_share']:.0%}.\n"
        f"- {p['mitigated_share']:.0%} of risks are mitigated; average score is "
        f"{p['avg_score']:.1f} / 25.\n\n"
        f"**Emerging concerns**\n"
        f"- {p['overdue']} mitigation actions are overdue{oldest}.\n"
        f"- \"{p['recurring']}\" appears {p['recurring_n']} times, suggesting a systemic "
        f"control gap rather than isolated incidents.\n\n"
        f"**Recommended actions**\n"
        f"- Review High risks owned by **{p['top_owner']}** ({p['top_owner_n']} items) "
        f"with the owner this week.\n"
        f"- Run a thematic review of \"{p['recurring']}\" across {category}.\n"
    )


# ---------- Demo mode ----------
def demo_answer(df: pd.DataFrame, question: str) -> str:
    top = data.high_by_category(df)
    od = data.overdue(df).head(5)
    if top.empty:
        return "There are no High-rated risks in the current selection."
    share = top.head(2).sum() / max(top.sum(), 1)
    c1, c2 = (list(top.index) + ["-"])[:2]
    rows = "\n".join(f"| {r['ID']} | {r['Risk']} | {r['Owner']} | {r['Due']:%b %d} | "
                     f"{r['Days overdue']} days |" for _, r in od.iterrows())
    owner = od["Owner"].mode().iat[0] if not od.empty else "the owners"
    return (
        f"**{c1}** carries the most high risks ({top.iat[0]}), followed by **{c2}** "
        f"({top.iat[1] if len(top) > 1 else 0}). Together they account for {share:.0%} "
        f"of all high-rated items.\n\n"
        f"#### Overdue mitigations\n\n"
        f"| ID | Risk | Owner | Due | Overdue |\n|---|---|---|---|---|\n{rows}\n\n"
        f"#### Recommended next steps\n\n"
        f"1. Escalate the two longest-overdue items at the next risk committee.\n"
        f"2. Ask {owner} to confirm revised dates for open {c1} actions.\n"
    )


def _fake_stream(text: str):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.012)
