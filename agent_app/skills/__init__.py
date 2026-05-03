"""
Skills registry — all available skills exported here.
To add a new skill: import its get_tool() and add it to ALL_SKILLS.
"""

from skills.web_search import get_tool as get_web_search
from skills.calculator import get_tool as get_calculator
from skills.summarizer import get_tool as get_summarizer

ALL_SKILLS = {
    "🔍 Web Search": get_web_search,
    "🧮 Calculator": get_calculator,
    "📝 Summarizer": get_summarizer,
}
