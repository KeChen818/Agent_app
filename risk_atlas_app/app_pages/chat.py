"""Risk Atlas Chat: streaming answers, attachments, voice, status, sources,
feedback, copy, regenerate, export and follow-up suggestions."""
import time
from datetime import datetime

import pandas as pd
import streamlit as st

from core import ai, data, export, ui

st.set_page_config(layout="centered")   # chat reads better in a narrower column

df_all = data.load_inventory(data.data_version())
df = data.filtered(df_all)
cats = st.session_state.get("categories") or []
all_selected = not cats or len(cats) == df_all["Category"].nunique()

if "messages" not in st.session_state:
    st.session_state.messages = []      # private to this browser session
if "pending" not in st.session_state:
    st.session_state.pending = None     # set by follow-up pills / regenerate


# ======================= Callbacks =======================
def ask_follow_up(key: str):
    if st.session_state.get(key):
        st.session_state.pending = {"text": st.session_state[key], "regenerate": False}


def regenerate():
    msgs = st.session_state.messages
    if msgs and msgs[-1]["role"] == "assistant":
        msgs.pop()
        st.session_state.pending = {"text": msgs[-1]["llm_content"], "regenerate": True}


def clear_chat():
    st.session_state.messages = []


# ======================= Helpers =======================
def read_upload(f) -> str:
    name = f.name.lower()
    if name.endswith(".csv"):
        text = pd.read_csv(f).to_csv(index=False)
    elif name.endswith((".xlsx", ".xls")):
        text = pd.read_excel(f).to_csv(index=False)
    else:
        text = f.getvalue().decode("utf-8", errors="ignore")
    return f"\n\n[Attached file: {f.name}]\n{text[:ai.MAX_FILE_CHARS]}"


def size_label(n: int) -> str:
    return f"{n / 1024:.0f} KB" if n < 1024 ** 2 else f"{n / 1024 ** 2:.1f} MB"


def render_user(m: dict):
    with st.chat_message("user", avatar=ui.initials_avatar(ui.current_initials())):
        st.markdown(m["content"])
        if m.get("files"):
            with st.container(horizontal=True, gap="small"):
                for name, size in m["files"]:
                    st.badge(f"{name} · {size}", icon=":material/attach_file:", color="gray")


def render_answer_body(m: dict):
    """Lead sentence, optional chart, then the rest of the answer."""
    lead, _, rest = m["content"].partition("\n\n")
    st.markdown(lead)
    if m.get("chart"):
        with st.container(width=520):
            st.altair_chart(ui.rank_chart(pd.Series(m["chart"]), "High risks"))
    if rest:
        st.markdown(rest)


def render_assistant(i: int, m: dict, is_last: bool):
    with st.chat_message("assistant", avatar=str(ui.ICON_PNG)):
        with st.status(m["status"], state="complete", expanded=False):
            for step in m.get("steps", []):
                st.caption(f":material/check: {step}")
        render_answer_body(m)

        # Sources
        with st.container(horizontal=True, gap="small"):
            for icon, label in m.get("sources", []):
                st.badge(label, icon=icon, color="gray")

        # Action row: feedback, copy, regenerate, export
        stamp = f"{datetime.now():%Y%m%d}_{i}"
        with st.container(horizontal=True, vertical_alignment="center", gap="small",
                          key=f"actions_{i}"):
            st.feedback("thumbs", key=f"fb_{i}")
            with st.popover("", icon=":material/content_copy:", type="tertiary",
                            help="Copy"):
                st.caption("Click the copy icon in the top-right corner")
                st.code(m["content"], language="markdown", wrap_lines=True)
            if is_last:
                st.button("", icon=":material/refresh:", type="tertiary", help="Regenerate",
                          key=f"regen_{i}", on_click=regenerate)
            with st.popover("Export", icon=":material/download:"):
                st.caption("EXPORT THIS ANSWER")
                st.download_button("Word", lambda c=m["content"]: export.answer_to_docx(c),
                                   f"risk_atlas_{stamp}.docx", icon=":material/description:",
                                   on_click="ignore", key=f"docx_{i}", width="stretch")
                if export.extract_tables(m["content"]):
                    st.download_button("Excel tables",
                                       lambda c=m["content"]: export.tables_to_xlsx(c),
                                       f"risk_atlas_{stamp}.xlsx", icon=":material/table_view:",
                                       on_click="ignore", key=f"xlsx_{i}", width="stretch")
                st.download_button("Markdown", m["content"], f"risk_atlas_{stamp}.md",
                                   icon=":material/markdown:", on_click="ignore",
                                   key=f"md_{i}", width="stretch")

        # Follow-up suggestions under the latest answer only
        if is_last and m.get("follow_ups"):
            key = f"fu_{i}"
            st.pills("Suggested follow-ups", m["follow_ups"], key=key,
                     label_visibility="collapsed", on_change=ask_follow_up, args=(key,))


# ======================= Header =======================
ui.page_header("AI Assistant", "Risk Atlas Chat", rule=False)
with st.container(horizontal=True, gap="small"):
    st.badge(f"Risk Inventory · {len(df)} risks", icon=":material/database:", color="gray")
    st.badge("All categories" if all_selected else f"{len(cats)} categories",
             icon=":material/layers:", color="gray")
    st.badge(f"Data as of {data.last_updated():%H:%M}", icon=":material/schedule:", color="gray")
    if ai.is_demo():
        st.badge("Demo mode", icon=":material/science:", color="orange",
                 help="Connect a model in core/ai.py → get_client()")
st.caption("AI can make mistakes. Verify critical figures before sharing.")

with st.sidebar:
    if st.session_state.messages:
        st.divider()
        st.caption("CONVERSATION")
        msgs = st.session_state.messages
        st.download_button("Export to Word", lambda: export.chat_to_docx(msgs),
                           "risk_atlas_chat.docx", icon=":material/description:",
                           on_click="ignore", width="stretch")
        st.download_button("Export to Markdown", lambda: export.chat_to_md(msgs),
                           "risk_atlas_chat.md", icon=":material/markdown:",
                           on_click="ignore", width="stretch")
        st.button("New chat", icon=":material/add_comment:", on_click=clear_chat,
                  width="stretch")

# ======================= History =======================
msgs = st.session_state.messages
for i, m in enumerate(msgs):
    if m["role"] == "user":
        render_user(m)
    else:
        render_assistant(i, m, is_last=(i == len(msgs) - 1))

if not msgs:
    st.pills("Try asking", ["Which categories carry the most high risks?",
                            "Which mitigations are overdue?",
                            "Summarise IT risks for the committee"],
             key="starter", on_change=ask_follow_up, args=("starter",))

# ======================= Input =======================
prompt = st.chat_input(
    "Ask about risks, owners or controls, or attach a file…",
    accept_file="multiple", file_type=["csv", "xlsx", "txt", "md"],
    accept_audio=True, submit_mode="disable",
)

pending, st.session_state.pending = st.session_state.pending, None
if prompt or pending:
    t0 = time.time()
    regenerating = bool(pending and pending["regenerate"])

    if prompt:
        text = prompt.text or (ai.transcribe(prompt.audio) if prompt.audio else "")
        files = prompt.files
    else:
        text, files = pending["text"], []

    if not regenerating:
        user_msg = {"role": "user", "content": text,
                    "llm_content": text + "".join(read_upload(f) for f in files),
                    "files": [(f.name, size_label(f.size)) for f in files]}
        msgs.append(user_msg)
        render_user(user_msg)

    question = msgs[-1]["llm_content"]
    history = [{"role": m["role"], "content": m["llm_content"]} for m in msgs]
    n_files = len(msgs[-1].get("files", []))
    steps = [f"Read {len(df)} risks from the Risk Inventory"]
    if n_files:
        steps.append(f"Parsed {n_files} attached file{'s' if n_files > 1 else ''}")

    with st.chat_message("assistant", avatar=str(ui.ICON_PNG)):
        with st.status("Analysing…", expanded=False) as status:
            for s in steps:
                st.caption(f":material/check: {s}")
        try:
            reply = st.write_stream(ai.stream_chat(history, df, question))
            label = (f"Analysed {len(df)} risks"
                     + (f" and {n_files} file{'s' if n_files > 1 else ''}" if n_files else "")
                     + f" · {time.time() - t0:.1f}s")
            status.update(label=label, state="complete")
        except Exception as e:
            reply, label = f"Something went wrong: {e}", "Failed"
            status.update(label=label, state="error")

    sources = [(":material/description:", f"Risk Inventory · {data.last_updated():%b %d}")]
    sources += [(":material/attach_file:", name) for name, _ in msgs[-1].get("files", [])]
    msgs.append({
        "role": "assistant", "content": reply, "llm_content": reply,
        "status": label, "steps": steps, "sources": sources,
        "chart": ai.auto_chart(df, question), "follow_ups": ai.follow_ups(question),
    })
    st.rerun()   # redraw so the new answer gets its action row
