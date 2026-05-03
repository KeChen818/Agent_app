"""
Skill 3: Summarizer
Uses a secondary Anthropic API call to condense long text into a concise summary.
"""

import os
from langchain_core.tools import Tool


def summarize(text: str) -> str:
    """Summarize a block of text using Claude."""
    try:
        import anthropic

        # Truncate input to avoid token overruns
        MAX_CHARS = 6000
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + "\n\n[... text truncated ...]"

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Please provide a concise 3-5 sentence summary of the following text. "
                        "Capture the main ideas and key points only.\n\n"
                        f"TEXT TO SUMMARIZE:\n{text}"
                    ),
                }
            ],
        )
        return response.content[0].text

    except Exception as e:
        return f"Could not summarize: {str(e)}"


def get_tool() -> Tool:
    return Tool(
        name="summarizer",
        description=(
            "Summarize long pieces of text into a concise 3-5 sentence summary. "
            "Use this when the user pastes an article, document, or long passage "
            "and asks for a summary, TL;DR, or overview. "
            "Input should be the full text to summarize."
        ),
        func=summarize,
    )
