"""Shared look and feel: CSS, headers, AI summary box, avatars."""
import io
from datetime import datetime
from functools import lru_cache
from html import escape
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parent.parent / "assets"
LOGO = ASSETS / "risk_atlas_logo_light.svg"
ICON = ASSETS / "risk_atlas_icon_light.svg"
ICON_PNG = ASSETS / "risk_atlas_icon_light_512.png"

RED, BLACK, BRONZE_DARK, MUTED = "#E60000", "#1C1C1C", "#7A5C14", "#6E6C65"

# Cell styles for the Rating column in st.dataframe (via pandas Styler)
RATING_CELL = {
    "High": "background-color:#FBE9E9;color:#BD000C;font-weight:600",
    "Medium": "background-color:#F5EEDC;color:#7A5C14;font-weight:600",
    "Low": "background-color:#EFEEEA;color:#5A5D5C;font-weight:600",
}

CSS = f"""<style>
/* Page header: red eyebrow, title, short red rule */
.ra-eyebrow {{font-size:.72rem; letter-spacing:.09em; text-transform:uppercase;
              color:{RED}; font-weight:600; margin:0 0 .15rem}}
.ra-title {{font-size:1.75rem; font-weight:600; letter-spacing:-.01em; line-height:1.2;
            color:{BLACK}; margin:0}}
.ra-rule {{width:28px; height:3px; background:{RED}; margin:.65rem 0 .2rem}}

/* AI boxes (summary, commentary): sandstone background, bronze bar */
[class*="st-key-aibox_"] {{background:#FBF9EE; border-left:3px solid #AF8626;
                          border-radius:2px 4px 4px 2px; padding:.8rem 1rem .4rem}}

/* Analyst comments */
.ra-comment {{border-left:2px solid #E0DED6; padding:.3rem .8rem; margin:.1rem 0 .3rem}}
.ra-c-head {{font-size:.78rem; color:{MUTED}; display:flex; gap:.5rem; align-items:center}}
.ra-c-author {{font-weight:600; color:{BLACK}; font-size:.85rem}}
.ra-c-body {{font-size:.9rem; color:{BLACK}; margin-top:.15rem; white-space:pre-wrap}}
.ra-tag {{font-size:.66rem; font-weight:600; padding:1px 7px; border-radius:10px;
          letter-spacing:.02em}}
.ra-tag-Observation {{background:#EFEEEA; color:#5A5D5C}}
.ra-tag-Action {{background:#F5EEDC; color:#7A5C14}}
.ra-tag-Escalation {{background:#FBE9E9; color:#BD000C}}
.ra-ai-label {{font-size:.7rem; font-weight:600; letter-spacing:.08em;
               text-transform:uppercase; color:{BRONZE_DARK}}}

/* Section titles with a small red dot (e.g. "Overdue mitigations") */
.ra-section {{font-weight:600; font-size:.95rem; display:flex; align-items:center; gap:.5rem}}
.ra-dot {{width:7px; height:7px; border-radius:50%; background:{RED}; display:inline-block}}

/* Sidebar category filter: neutral tags instead of red.
   [data-tag] is internal Streamlit markup (checked on 1.66); re-check after upgrades. */
.st-key-categories [data-tag] {{background:#FFFFFF !important; color:#1C1C1C !important;
                                border:1px solid #E0DED6}}
.st-key-categories [data-tag] * {{color:#5A5D5C !important}}

/* Chat: quieter assistant action row */
[class*="st-key-actions_"] button {{color:#5A5D5C}}
</style>"""


def inject_css():
    st.html(CSS)


def page_header(eyebrow: str, title: str, rule: bool = True):
    st.html(f'<div class="ra-eyebrow">{escape(eyebrow)}</div>'
            f'<div class="ra-title">{escape(title)}</div>'
            + ('<div class="ra-rule"></div>' if rule else ""))


def section(title: str, dot: bool = False):
    st.html(f'<div class="ra-section">{"<span class=ra-dot></span>" if dot else ""}'
            f'{escape(title)}</div>')


def ai_summary(text: str, label: str = "AI Summary", key: str = "summary"):
    with st.container(key=f"aibox_{key}"):
        st.html(f'<div class="ra-ai-label">{escape(label)}</div>')
        st.markdown(text)


@lru_cache(maxsize=32)
def initials_avatar(initials: str) -> bytes:
    """Black square with white initials, used as the user's chat avatar."""
    size = 128
    img = Image.new("RGB", (size, size), BLACK)
    d = ImageDraw.Draw(img)
    font = None
    for f in ["Inter-SemiBold.otf", "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
              "seguisb.ttf", "Arial Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"]:
        try:
            font = ImageFont.truetype(f, 48)
            break
        except OSError:
            continue
    font = font or ImageFont.load_default(size=48)
    text = initials[:2].upper()
    box = d.textbbox((0, 0), text, font=font)
    d.text(((size - box[2] - box[0]) / 2, (size - box[3] - box[1]) / 2), text,
           fill="white", font=font)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def comment_html(author: str, body: str, tag: str | None, created: str) -> str:
    when = datetime.fromisoformat(created).strftime("%b %d, %H:%M")
    tag_html = f'<span class="ra-tag ra-tag-{escape(tag)}">{escape(tag)}</span>' if tag else ""
    return (f'<div class="ra-comment"><div class="ra-c-head"><span class="ra-c-author">'
            f'{escape(author)}</span>{tag_html}<span>{when}</span></div>'
            f'<div class="ra-c-body">{escape(body)}</div></div>')


def current_name() -> str | None:
    """Display name from st.login, if authentication is configured."""
    try:
        return st.user.get("name") or st.user.get("email")
    except Exception:
        return None


def current_initials() -> str:
    """Initials from the signed-in user (st.login), otherwise 'ME'."""
    try:
        name = st.user.get("name") or st.user.get("email") or ""
    except Exception:
        name = ""
    parts = [p for p in name.replace(".", " ").split() if p]
    return "".join(p[0] for p in parts[:2]) or "ME"


def rank_chart(s: pd.Series, value_label: str = "Count"):
    """Thin ranked bars: #1 black, #2 bronze, the rest warm gray, values at the end."""
    d = s.rename(value_label).reset_index()
    d.columns = ["Item", value_label]
    d["Color"] = (["#1C1C1C", "#AF8626"] + ["#8E8D83"] * len(d))[:len(d)]
    base = alt.Chart(d).encode(
        y=alt.Y("Item:N", sort=None, title=None,
                axis=alt.Axis(domain=False, ticks=False, labelColor="#444444",
                              labelFontSize=12.5, labelPadding=10, labelLimit=160)))
    bars = base.mark_bar(size=9, cornerRadiusEnd=2).encode(
        x=alt.X(f"{value_label}:Q", axis=None, scale=alt.Scale(nice=False)),
        color=alt.Color("Color:N", scale=None), tooltip=["Item", value_label])
    labels = base.mark_text(align="left", dx=6, fontWeight=600, fontSize=12.5,
                            color="#1C1C1C").encode(x=f"{value_label}:Q", text=f"{value_label}:Q")
    return ((bars + labels).properties(height=30 * len(d))
            .configure_view(stroke=None).configure_axis(grid=False))
