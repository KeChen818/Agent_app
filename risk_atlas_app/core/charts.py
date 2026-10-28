"""ECharts option builders (plain dicts) for st.echarts_chart, in Risk Atlas colors."""
import pandas as pd

BLACK, BORDEAUX, BRONZE, BRONZE_LIGHT = "#1C1C1C", "#BD000C", "#AF8626", "#D3C39C"
GRAY, GRAY_DARK, GRAY_LIGHT, LINE = "#8E8D83", "#5A5D5C", "#EFEEEA", "#ECEAE4"
RATING_COLORS = {"High": BORDEAUX, "Medium": BRONZE, "Low": GRAY}

_TEXT = {"color": "#444444", "fontSize": 12}
_TOOLTIP = {"backgroundColor": "#FFFFFF", "borderColor": "#E0DED6", "borderWidth": 1,
            "textStyle": {"color": BLACK, "fontSize": 12}, "extraCssText": "box-shadow:none"}


def heatmap(df: pd.DataFrame) -> dict:
    """5x5 likelihood x impact matrix. Cell color = risk zone, label = number of risks."""
    counts = df.groupby(["Likelihood", "Impact"]).size()
    cells = []
    for l in range(1, 6):
        for i in range(1, 6):
            n, score = int(counts.get((l, i), 0)), l * i
            cells.append({
                "value": [i - 1, l - 1, n, score],
                # dark text on light zones, white on Bronze / Bordeaux; hide zeros
                "label": {"show": n > 0, "color": "#FFFFFF" if score >= 8 else BLACK},
                "itemStyle": {"opacity": 1 if n > 0 else 0.35},
            })
    return {
        "tooltip": {**_TOOLTIP, "formatter": "Likelihood {@[1]} × Impact {@[0]}<br/>"
                                             "Score {@[3]} · <b>{@[2]} risks</b>"},
        "grid": {"left": 70, "right": 16, "top": 12, "bottom": 74},
        "xAxis": {"type": "category", "data": ["1", "2", "3", "4", "5"], "name": "Impact",
                  "nameLocation": "middle", "nameGap": 28, "nameTextStyle": _TEXT,
                  "axisLine": {"show": False}, "axisTick": {"show": False},
                  "axisLabel": _TEXT, "splitArea": {"show": False}},
        "yAxis": {"type": "category", "data": ["1", "2", "3", "4", "5"], "name": "Likelihood",
                  "nameLocation": "middle", "nameGap": 34, "nameTextStyle": _TEXT,
                  "axisLine": {"show": False}, "axisTick": {"show": False}, "axisLabel": _TEXT},
        "visualMap": {
            "type": "piecewise", "dimension": 3, "orient": "horizontal", "left": "center",
            "bottom": 0, "itemWidth": 12, "itemHeight": 12, "textStyle": _TEXT,
            "pieces": [{"gte": 15, "label": "High (15–25)", "color": BORDEAUX},
                       {"gte": 8, "lte": 14, "label": "Medium (8–14)", "color": BRONZE},
                       {"gte": 4, "lte": 7, "label": "Low (4–7)", "color": BRONZE_LIGHT},
                       {"lte": 3, "label": "Minimal (1–3)", "color": "#E4E2DC"}],
        },
        "series": [{
            "type": "heatmap", "data": cells, "encode": {"x": 0, "y": 1},
            "label": {"show": True, "formatter": "{@[2]}", "fontSize": 13, "fontWeight": 600},
            "itemStyle": {"borderColor": "#FFFFFF", "borderWidth": 3, "borderRadius": 3},
            "emphasis": {"itemStyle": {"borderColor": BLACK, "borderWidth": 2}},
        }],
    }


def rating_mix(df: pd.DataFrame) -> dict:
    """Stacked horizontal bars: High / Medium / Low per category, most High on top."""
    t = (df.pivot_table(index="Category", columns="Rating", values="ID", aggfunc="count",
                        fill_value=0)
           .reindex(columns=["High", "Medium", "Low"], fill_value=0)
           .sort_values("High"))
    return {
        "tooltip": {**_TOOLTIP, "trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"top": 0, "left": 0, "itemWidth": 10, "itemHeight": 10, "icon": "rect",
                   "textStyle": _TEXT},
        "grid": {"left": 90, "right": 24, "top": 34, "bottom": 8},
        "xAxis": {"type": "value", "splitLine": {"lineStyle": {"color": LINE}},
                  "axisLabel": _TEXT},
        "yAxis": {"type": "category", "data": list(t.index), "axisLine": {"show": False},
                  "axisTick": {"show": False}, "axisLabel": {**_TEXT, "fontSize": 12.5}},
        "series": [{"name": r, "type": "bar", "stack": "total", "barWidth": 14,
                    "data": [int(v) for v in t[r]],
                    "itemStyle": {"color": RATING_COLORS[r]},
                    "label": {"show": r == "High", "position": "insideLeft", "color": "#FFFFFF",
                              "fontSize": 11, "fontWeight": 600}}
                   for r in ["High", "Medium", "Low"]],
    }


def trend(h: pd.DataFrame) -> dict:
    """High risks (black area) and overdue actions (red dashed) over recent months."""
    return {
        "tooltip": {**_TOOLTIP, "trigger": "axis"},
        "legend": {"top": 0, "left": 0, "itemWidth": 14, "itemHeight": 2, "textStyle": _TEXT},
        "grid": {"left": 36, "right": 16, "top": 34, "bottom": 24},
        "xAxis": {"type": "category", "data": list(h["Month"]), "boundaryGap": False,
                  "axisLine": {"lineStyle": {"color": "#E0DED6"}}, "axisTick": {"show": False},
                  "axisLabel": _TEXT},
        "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": LINE}},
                  "axisLabel": _TEXT},
        "series": [
            {"name": "High risks", "type": "line", "data": [int(v) for v in h["High"]],
             "symbol": "circle", "symbolSize": 6, "lineStyle": {"color": BLACK, "width": 2},
             "itemStyle": {"color": BLACK},
             "areaStyle": {"color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                     "colorStops": [{"offset": 0, "color": "rgba(28,28,28,0.12)"},
                                                    {"offset": 1, "color": "rgba(28,28,28,0)"}]}},
             "endLabel": {"show": True, "fontWeight": 600, "color": BLACK}},
            {"name": "Overdue actions", "type": "line", "data": [int(v) for v in h["Overdue"]],
             "symbol": "circle", "symbolSize": 5,
             "lineStyle": {"color": BORDEAUX, "width": 1.5, "type": "dashed"},
             "itemStyle": {"color": BORDEAUX},
             "endLabel": {"show": True, "fontWeight": 600, "color": BORDEAUX}},
        ],
    }


def status_donut(df: pd.DataFrame) -> dict:
    """Open / In progress / Mitigated, with the total in the middle."""
    order = [("Open", BLACK), ("In progress", BRONZE), ("Mitigated", GRAY)]
    counts = df["Status"].value_counts()
    return {
        "tooltip": {**_TOOLTIP, "trigger": "item", "formatter": "{b}: {c} ({d}%)"},
        "legend": {"bottom": 0, "left": "center", "itemWidth": 10, "itemHeight": 10,
                   "icon": "circle", "textStyle": _TEXT},
        "title": {"text": str(len(df)), "subtext": "risks", "left": "center", "top": "34%",
                  "textStyle": {"fontSize": 26, "fontWeight": 600, "color": BLACK},
                  "subtextStyle": {"fontSize": 12, "color": "#6E6C65"}, "itemGap": 2},
        "series": [{
            "type": "pie", "radius": ["58%", "76%"], "center": ["50%", "45%"],
            "avoidLabelOverlap": True, "label": {"show": False},
            "itemStyle": {"borderColor": "#FFFFFF", "borderWidth": 3},
            "data": [{"name": n, "value": int(counts.get(n, 0)), "itemStyle": {"color": c}}
                     for n, c in order],
        }],
    }

