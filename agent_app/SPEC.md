# SPEC.md — Skill-Powered AI Agent

**Version:** 1.0.0
**Status:** Draft
**Last Updated:** 2026-05-02

---

## 1. Overview

A conversational AI agent built with Python, Streamlit, and LangChain that exposes a chat interface and dynamically invokes modular **Skills** (LangChain tools) to answer user queries. The agent decides autonomously which skill(s) to invoke based on the user's message.

---

## 2. Goals

- Provide a clean, single-page chat UI for interacting with an LLM-powered agent
- Allow the agent to use distinct, swappable Skills to extend its capabilities
- Make Skills easy to add, remove, or replace without touching core agent logic
- Persist conversation context across turns within a session

---

## 3. Non-Goals

- Multi-user authentication or persistent storage across sessions
- Fine-tuning or training the underlying model
- Deploying to production (this spec covers local dev only)

---

## 4. Architecture

```
┌─────────────────────────────────┐
│         Streamlit UI (app.py)   │
│  - Chat input / message history │
│  - Sidebar: model + skill config│
└────────────────┬────────────────┘
                 │ user message
                 ▼
┌─────────────────────────────────┐
│      LangChain Agent (agent.py) │
│  - ReAct agent loop             │
│  - Maintains conversation memory│
│  - Routes to Skills via tools   │
└──────┬──────────┬───────────────┘
       │          │
       ▼          ▼
┌──────────┐ ┌────────────┐ ┌──────────────┐
│  Skill 1 │ │  Skill 2   │ │   Skill 3    │
│  Web     │ │ Calculator │ │ Summarizer   │
│  Search  │ │            │ │              │
└──────────┘ └────────────┘ └──────────────┘
```

### Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| UI Layer | `app.py` | Render chat, handle user input, display agent output |
| Agent Core | `agent.py` | Orchestrate LLM + tools, manage memory, stream responses |
| Skill: Web Search | `skills/web_search.py` | Query DuckDuckGo and return summarized results |
| Skill: Calculator | `skills/calculator.py` | Evaluate math expressions safely |
| Skill: Summarizer | `skills/summarizer.py` | Condense long text passed by user |

---

## 5. Skills Specification

### 5.1 Skill Interface Contract

Every skill must expose:
- A `name: str` — unique snake_case identifier
- A `description: str` — plain English description for the LLM to decide when to use it
- A callable `func(input: str) -> str` — receives a string, returns a string

```python
# Minimal skill shape
Tool(
    name="skill_name",
    description="When to use this skill and what it does.",
    func=my_function,
)
```

### 5.2 Skill: Web Search

| Field | Value |
|-------|-------|
| Name | `web_search` |
| Trigger | User asks about current events, facts, or anything requiring live data |
| Input | A search query string |
| Output | Top 3 results as formatted text (title + snippet + URL) |
| Backend | DuckDuckGo Search API (no API key required) |
| Error Handling | Returns `"Search failed: <reason>"` on exception |

### 5.3 Skill: Calculator

| Field | Value |
|-------|-------|
| Name | `calculator` |
| Trigger | User asks to compute, calculate, or evaluate a math expression |
| Input | A math expression string (e.g., `"(12 * 4) / 2 + sqrt(9)"`) |
| Output | The numeric result as a string |
| Backend | Python `numexpr` / `ast.literal_eval` safe evaluator |
| Error Handling | Returns `"Invalid expression: <reason>"` on exception |
| Security | No `eval()` on arbitrary strings; uses a restricted evaluator |

### 5.4 Skill: Summarizer

| Field | Value |
|-------|-------|
| Name | `summarizer` |
| Trigger | User pastes long text and asks for a summary or TL;DR |
| Input | Raw text to summarize (up to ~4000 chars) |
| Output | 3–5 sentence summary |
| Backend | Secondary LLM call (same model) with a summarization prompt |
| Error Handling | Returns `"Could not summarize: <reason>"` on exception |

---

## 6. Data Flow

```
User types message
  → app.py captures input
  → agent.py receives message + conversation history
  → LangChain ReAct loop:
      ┌── LLM decides: answer directly OR invoke skill
      │     if skill → skill.func(input) → result returned to LLM
      │     LLM may chain multiple skill calls
      └── LLM produces final Answer
  → app.py streams/displays response
  → Message appended to st.session_state history
```

---

## 7. State Management

All state lives in `st.session_state`:

| Key | Type | Description |
|-----|------|-------------|
| `messages` | `list[dict]` | Full chat history `{role, content}` |
| `agent` | `AgentExecutor` | Initialized once per session |
| `model_name` | `str` | Selected Claude model |
| `active_skills` | `list[str]` | Which skills are enabled |

---

## 8. Configuration (Sidebar)

Users can configure at runtime:

- **Model selector** — choose Claude model variant
- **Skill toggles** — enable/disable individual skills
- **Max iterations** — cap the agent's ReAct loop (default: 5)
- **Clear chat** — wipe session history

---

## 9. Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit ≥ 1.32 |
| Agent Framework | LangChain ≥ 0.2 |
| LLM | Anthropic Claude (via `langchain-anthropic`) |
| Skill: Search | `duckduckgo-search` |
| Skill: Math | Python `math` stdlib + `numexpr` |
| Skill: Summarize | Anthropic API (secondary call) |
| Python | 3.11+ |

---

## 10. Error Handling & Edge Cases

| Scenario | Behavior |
|----------|----------|
| Missing `ANTHROPIC_API_KEY` | Show warning banner in sidebar; disable agent |
| Skill throws exception | Return error string to LLM; LLM reports gracefully |
| Agent exceeds max iterations | Surface "I couldn't complete this in time" message |
| Empty user input | Ignore, do not invoke agent |
| Very long input | Truncate to 4000 chars, notify user |

---

## 11. File Structure

```
agent_app/
├── app.py              # Streamlit UI entry point
├── agent.py            # LangChain agent factory + executor
├── skills/
│   ├── __init__.py     # Exports all skills as a list
│   ├── web_search.py   # Skill 1: DuckDuckGo search
│   ├── calculator.py   # Skill 2: Safe math evaluator
│   └── summarizer.py   # Skill 3: LLM-powered summarizer
├── requirements.txt
└── SPEC.md             # This file
```

---

## 12. Running Locally

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
streamlit run app.py
```

---

## 13. Adding a New Skill

1. Create `skills/my_skill.py` with a `get_tool() -> Tool` function
2. Import and append it in `skills/__init__.py`
3. It automatically appears in the sidebar toggles and is available to the agent

No changes to `agent.py` or `app.py` required.

---

## 14. Acceptance Criteria

- [ ] Chat UI renders and accepts input
- [ ] Agent responds without any skills enabled (plain LLM)
- [ ] Web Search skill returns live results for factual queries
- [ ] Calculator skill correctly evaluates math expressions
- [ ] Summarizer skill condenses pasted text
- [ ] Disabling a skill in the sidebar removes it from the agent's toolbelt
- [ ] Conversation history persists across turns within a session
- [ ] Clear chat resets history
- [ ] Graceful error messages when API key is missing
