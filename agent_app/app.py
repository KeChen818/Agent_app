"""
app.py — Streamlit UI for the Skill-Powered AI Agent
Run with: streamlit run app.py
"""

import os
import sys
import html
import streamlit as st

# Ensure local imports work
sys.path.insert(0, os.path.dirname(__file__))

from skills import ALL_SKILLS
from agent import build_agent, create_memory

# ─── Page Config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Skill Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* Dark background */
.stApp {
    background: #0d0f14;
    color: #e2e8f0;
}

/* Main header */
.agent-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 20px 0 8px 0;
    border-bottom: 1px solid #1e2433;
    margin-bottom: 24px;
}

.agent-title {
    font-size: 1.6rem;
    font-weight: 600;
    color: #f0f4ff;
    letter-spacing: -0.5px;
}

.agent-badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    background: #1a2040;
    color: #7c9ef5;
    border: 1px solid #2d3d6b;
    border-radius: 4px;
    padding: 2px 8px;
    letter-spacing: 1px;
}

/* Chat messages */
.chat-message {
    display: flex;
    gap: 14px;
    margin-bottom: 20px;
    animation: fadeSlideIn 0.2s ease-out;
}

@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}

.chat-avatar {
    width: 34px;
    height: 34px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    margin-top: 2px;
}

.avatar-user  { background: #1e2d5a; }
.avatar-agent { background: #1a3327; }

.chat-bubble {
    flex: 1;
    background: #131720;
    border: 1px solid #1e2433;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.92rem;
    line-height: 1.65;
    color: #d4daf2;
}

.bubble-user  { border-left: 3px solid #4a6fa5; }
.bubble-agent { border-left: 3px solid #3d8c6a; }

.bubble-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 6px;
    opacity: 0.55;
}

/* Skill steps */
.skill-step {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    background: #0d1520;
    border: 1px solid #1a2840;
    border-radius: 6px;
    padding: 8px 12px;
    margin: 6px 0;
    color: #7ca8e0;
}

.skill-step-label {
    color: #f0b860;
    font-weight: 500;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0a0c11 !important;
    border-right: 1px solid #1e2433;
}

section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #7c9ef5;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 12px;
    border-bottom: 1px solid #1e2433;
    padding-bottom: 6px;
}

/* Input area */
.stChatInput > div {
    background: #131720 !important;
    border: 1px solid #2a3050 !important;
    border-radius: 10px !important;
}

.stChatInput input {
    color: #e2e8f0 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}

/* Skill pills */
.skill-pill {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    background: #111827;
    border: 1px solid #2d3d6b;
    color: #7c9ef5;
    border-radius: 20px;
    padding: 2px 10px;
    margin: 2px 3px;
}

/* Rendered markdown inside agent bubble */
.agent-content p { margin: 0 0 8px 0; }
.agent-content p:last-child { margin-bottom: 0; }
.agent-content ul, .agent-content ol { margin: 4px 0 8px 18px; padding: 0; }
.agent-content li { margin-bottom: 3px; }
.agent-content strong { color: #e8eeff; }
.agent-content code {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82em;
    background: #0d1520;
    border: 1px solid #1a2840;
    border-radius: 3px;
    padding: 1px 5px;
    color: #7ca8e0;
}
.agent-content pre {
    background: #0d1520;
    border: 1px solid #1a2840;
    border-radius: 6px;
    padding: 10px 14px;
    overflow-x: auto;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8em;
    color: #7ca8e0;
}

/* Error banner */
.error-banner {
    background: #2d1515;
    border: 1px solid #7a2020;
    border-radius: 8px;
    padding: 12px 16px;
    color: #f08080;
    font-size: 0.85rem;
    margin-bottom: 16px;
}

/* Welcome screen */
.welcome-box {
    max-width: 560px;
    margin: 60px auto 0;
    text-align: center;
}

.welcome-icon {
    font-size: 3.5rem;
    margin-bottom: 16px;
}

.welcome-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #f0f4ff;
    margin-bottom: 10px;
}

.welcome-sub {
    color: #6b7a9a;
    font-size: 0.9rem;
    line-height: 1.7;
    margin-bottom: 28px;
}

.example-prompts {
    display: flex;
    flex-direction: column;
    gap: 10px;
    text-align: left;
}

.example-prompt {
    background: #131720;
    border: 1px solid #1e2433;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 0.85rem;
    color: #a0b0d0;
    cursor: pointer;
}

.example-prompt:hover {
    border-color: #2d3d6b;
    color: #d0daf5;
}

.example-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #f0b860;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 3px;
}
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ─────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory" not in st.session_state:
    st.session_state.memory = create_memory()
if "agent" not in st.session_state:
    st.session_state.agent = None
if "active_skills" not in st.session_state:
    st.session_state.active_skills = list(ALL_SKILLS.keys())
if "model_name" not in st.session_state:
    st.session_state.model_name = "claude-sonnet-4-6"
if "max_iterations" not in st.session_state:
    st.session_state.max_iterations = 8

# ─── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        placeholder="sk-ant-...",
        help="Your Anthropic API key"
    )
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key

    st.markdown("---")
    st.markdown("### 🛠 Active Skills")

    new_active = []
    for skill_name in ALL_SKILLS:
        enabled = st.checkbox(
            skill_name,
            value=skill_name in st.session_state.active_skills,
            key=f"skill_{skill_name}",
        )
        if enabled:
            new_active.append(skill_name)

    if set(new_active) != set(st.session_state.active_skills):
        st.session_state.active_skills = new_active
        st.session_state.agent = None  # Rebuild on next message

    st.markdown("---")
    st.markdown("### 🤖 Model")

    model_choice = st.selectbox(
        "Claude Model",
        options=[
            "claude-sonnet-4-6",
            "claude-haiku-4-5",
            "claude-opus-4-7",
        ],
        index=0,
        label_visibility="collapsed",
    )
    if model_choice != st.session_state.model_name:
        st.session_state.model_name = model_choice
        st.session_state.agent = None

    max_iter = st.slider("Max iterations", min_value=1, max_value=15, value=st.session_state.max_iterations)
    if max_iter != st.session_state.max_iterations:
        st.session_state.max_iterations = max_iter
        st.session_state.agent = None

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.memory = create_memory()
        st.session_state.agent = None
        st.rerun()

    # Status
    st.markdown("---")
    st.markdown("### 📊 Status")
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    st.markdown(f"{'🟢' if has_key else '🔴'} API Key: {'Set' if has_key else 'Missing'}")
    st.markdown(f"🔧 Skills active: **{len(st.session_state.active_skills)}**")
    st.markdown(f"💬 Messages: **{len(st.session_state.messages)}**")

# ─── Header ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="agent-header">
    <span style="font-size:1.5rem">⚡</span>
    <span class="agent-title">Skill Agent</span>
    <span class="agent-badge">LANGCHAIN + CLAUDE</span>
</div>
""", unsafe_allow_html=True)

# ─── API Key Warning ───────────────────────────────────────────────────────────

if not os.environ.get("ANTHROPIC_API_KEY"):
    st.markdown("""
    <div class="error-banner">
        ⚠️ <strong>No API key set.</strong> Enter your Anthropic API key in the sidebar to get started.
    </div>
    """, unsafe_allow_html=True)

# ─── Welcome Screen ────────────────────────────────────────────────────────────

if not st.session_state.messages:
    active_skill_list = "".join(
        f'<span class="skill-pill">{s}</span>'
        for s in (st.session_state.active_skills or ["No skills active"])
    )
    st.markdown(f"""
    <div class="welcome-box">
        <div class="welcome-icon">⚡</div>
        <div class="welcome-title">Your Skills-Powered Agent</div>
        <div class="welcome-sub">
            Ask anything. The agent will decide which skill to use — or answer directly from its knowledge.
        </div>
        <div style="margin-bottom: 20px; text-align: center">{active_skill_list}</div>
        <div class="example-prompts">
            <div class="example-prompt">
                <div class="example-label">🔍 Web Search</div>
                What are the latest developments in quantum computing?
            </div>
            <div class="example-prompt">
                <div class="example-label">🧮 Calculator</div>
                What is sqrt(1764) + factorial(6) / 2?
            </div>
            <div class="example-prompt">
                <div class="example-label">📝 Summarizer</div>
                Summarize this for me: [paste any long text]
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── Render Chat History ───────────────────────────────────────────────────────

for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    steps = msg.get("steps", [])

    if role == "user":
        with st.chat_message("user"):
            st.write(content)
    else:
        with st.chat_message("assistant"):
            if steps:
                for step in steps:
                    tool_name = str(step.get("tool", "unknown"))
                    tool_input = str(step.get("input", ""))
                    tool_output = str(step.get("output", ""))
                    in_preview = tool_input[:120] + ("…" if len(tool_input) > 120 else "")
                    out_preview = tool_output[:200] + ("…" if len(tool_output) > 200 else "")
                    st.markdown(
                        f'<div class="skill-step">'
                        f'<span class="skill-step-label">▶ {html.escape(tool_name)}</span><br/>'
                        f'Input: {html.escape(in_preview)}<br/>'
                        f'Result: {html.escape(out_preview)}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            st.markdown(content)

# ─── Chat Input ────────────────────────────────────────────────────────────────

user_input = st.chat_input("Ask anything…")

if user_input:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.error("Please enter your Anthropic API key in the sidebar first.")
        st.stop()

    # Truncate very long inputs
    MAX_INPUT = 4000
    if len(user_input) > MAX_INPUT:
        user_input = user_input[:MAX_INPUT]
        st.warning(f"Input truncated to {MAX_INPUT} characters.")

    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Build agent if needed
    if st.session_state.agent is None:
        tools = [ALL_SKILLS[name]() for name in st.session_state.active_skills]
        st.session_state.agent = build_agent(
            tools=tools,
            model_name=st.session_state.model_name,
            max_iterations=st.session_state.max_iterations,
            memory=st.session_state.memory,
        )

    # Run agent
    with st.spinner("⚡ Agent thinking…"):
        try:
            result = st.session_state.agent.invoke({"input": user_input})
            answer = result.get("output", "I wasn't able to produce an answer.")

            # Extract intermediate steps for display
            steps = []
            for action, observation in result.get("intermediate_steps", []):
                steps.append({
                    "tool": getattr(action, "tool", "unknown"),
                    "input": getattr(action, "tool_input", ""),
                    "output": str(observation),
                })

            st.session_state.messages.append({
                "role": "agent",
                "content": answer,
                "steps": steps,
            })

        except Exception as e:
            error_msg = f"Agent error: {str(e)}"
            st.session_state.messages.append({
                "role": "agent",
                "content": f"⚠️ {error_msg}",
                "steps": [],
            })

    st.rerun()
