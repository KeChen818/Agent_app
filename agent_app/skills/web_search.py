"""
Skill 1: Web Search
Uses DuckDuckGo to fetch live search results — no API key required.
"""

from langchain_core.tools import Tool


def web_search(query: str) -> str:
    """Search the web using DuckDuckGo. Tries recent results, widens if needed."""
    try:
        from ddgs import DDGS

        # Cascade: month → year → all-time. Use the first window that returns hits.
        results = []
        with DDGS() as ddgs:
            for window in ("m", "y", None):
                try:
                    if window:
                        results = list(ddgs.text(query, max_results=5, timelimit=window))
                    else:
                        results = list(ddgs.text(query, max_results=5))
                except Exception:
                    results = []
                if results:
                    break

        if not results:
            return (
                "No results found. Note: DuckDuckGo cannot index X/Twitter posts, "
                "Instagram, Facebook, or other login-gated content. For those, "
                "tell the user to check the platform directly."
            )

        formatted = []
        for i, r in enumerate(results[:3], 1):
            date = r.get("published", "")
            date_str = f" ({date})" if date else ""
            formatted.append(
                f"**Result {i}:** {r.get('title', 'No title')}{date_str}\n"
                f"{r.get('body', 'No snippet')}\n"
                f"URL: {r.get('href', 'N/A')}"
            )
        return "\n\n".join(formatted)

    except Exception as e:
        return f"Search failed: {str(e)}"


def get_tool() -> Tool:
    return Tool(
        name="web_search",
        description=(
            "Search the internet for current information, recent news, facts, or anything "
            "that requires up-to-date knowledge. Prioritizes results from the past month. "
            "Input should be a search query string."
        ),
        func=web_search,
    )
