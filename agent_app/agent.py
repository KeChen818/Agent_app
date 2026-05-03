"""
agent.py — LangChain ReAct agent factory.
Builds an AgentExecutor with a configurable set of skills (tools).
"""

import os
from typing import Optional
from langchain_anthropic import ChatAnthropic
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_classic.memory import ConversationBufferWindowMemory
# hub not needed
from langchain_core.tools import Tool
from langchain_classic.prompts import PromptTemplate


SYSTEM_PROMPT = """You are a helpful AI assistant with access to a set of skills (tools).

Important limitations to be aware of:
- The web_search tool uses DuckDuckGo. It CANNOT access posts on X/Twitter, Instagram,
  Facebook, LinkedIn, or other login-gated platforms. If the user asks for a specific
  user's latest tweets/posts on those platforms, do NOT loop on web_search — answer
  directly that this isn't accessible and suggest they check the platform.
- After at most 2 web_search calls, stop searching and answer with what you have.
  Do not retry the same query with minor wording variations.
- For the date of "latest" content, today's date is roughly mid-2026. "Latest" may
  mean "most recent significant item" rather than "this week".

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

If you don't need any tools, you can answer directly:
Question: the input question you must answer
Thought: I can answer this directly without tools
Final Answer: your answer here

Previous conversation history:
{chat_history}

Question: {input}
Thought: {agent_scratchpad}"""


def build_agent(
    tools: list[Tool],
    model_name: str = "claude-sonnet-4-6",
    max_iterations: int = 5,
    memory: Optional[ConversationBufferWindowMemory] = None,
) -> AgentExecutor:
    """
    Build and return a LangChain ReAct AgentExecutor.

    Args:
        tools: List of LangChain Tool objects (skills)
        model_name: Claude model to use
        max_iterations: Max ReAct loop iterations
        memory: Conversation memory instance (shared across calls)
    """
    llm = ChatAnthropic(
        model=model_name,
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        temperature=0.3,
        max_tokens=1024,
    )

    prompt = PromptTemplate.from_template(SYSTEM_PROMPT)

    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

    if memory is None:
        memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=10,
            return_messages=False,
        )

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        max_iterations=max_iterations,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    return executor


def create_memory() -> ConversationBufferWindowMemory:
    """Create a fresh conversation memory instance."""
    return ConversationBufferWindowMemory(
        memory_key="chat_history",
        k=10,
        return_messages=False,
    )
