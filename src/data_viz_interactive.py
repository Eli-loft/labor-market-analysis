"""
CPSC 4530 Final Project - Economic Data Visualization (Interactive)
Thesis: BLS headline metrics structurally misrepresent the American labor market

Interactivity design follows procedural rhetoric framework (Hullman & Diakopoulos 2011)
and Campbell's seven circumstances as applied by Prantl et al. 2026.

Dependencies:
    pip install fredapi plotly pandas numpy kaleido

Usage:
    python data_viz_interactive.py
    Saves four HTML files to the same folder as this script.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fredapi import Fred
import os
import time

FRED_API_KEY = "b99f862f09dc89e15334d5bc83a78afd"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")

fred = Fred(api_key=FRED_API_KEY)

# ── COLOR PALETTE ─────────────────────────────────────────────────────────────
RED        = "#c0392b"
RED_LIGHT  = "rgba(192,57,43,0.18)"
RED_FAINT  = "rgba(192,57,43,0.07)"
BLUE       = "#2980b9"
BLUE_MUTED = "rgba(41,128,185,0.45)"
GREY       = "#7f8c8d"
GREY_LIGHT = "rgba(127,140,141,0.15)"
DARK_BG    = "#1a1a2e"
PANEL_BG   = "#16213e"
TEXT       = "#e0e0e0"
TEXT_MUTED = "#888899"
GOLD       = "#f39c12"
GREEN      = "#27ae60"


def fetch(series_id, start="2010-01-01", retries=3, delay=10):
    for attempt in range(retries):
        try:
            s = fred.get_series(series_id, observation_start=start)
            s.name = series_id
            return s
        except Exception as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt+1}/{retries} for {series_id}: {e}")
                time.sleep(delay)
            else:
                raise


def save_html(fig, stem):
    path = os.path.join(OUTPUT_DIR, f"{stem}.html")
    fig.write_html(path, include_plotlyjs="cdn", full_html=True)
    print(f"Saved: {path}")
    return path


def inject_js(html_path, js_code):
    """Inject a <script> block before </body> in exported HTML."""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    script_block = f"\n<script>\n{js_code}\n</script>\n"
    content = content.replace("</body>", script_block + "</body>")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)


# ══════════════════════════════════════════════════════════════════════════════
# VIZ 1 — Establishment vs Household Survey Divergence
#
# Rhetorical interactivity:
#   1. "Official View" default: only establishment line visible
#      (procedural rhetoric anchoring — Hullman & Diakopoulos 2011)
#   2. "Reveal Household Survey" button: viewer must choose to see the
#      suppressed counter-metric (controlled revelation)
#   3. Y-axis label toggle: same data, two framings — "Jobs Added" vs
#      "Survey Divergence" (framing effects — Hullman & Diakopoulos 2011)
#   4. Unified hover showing gap in millions at any date
#      (relations to persons concerned — Campbell)
# ══════════════════════════════════════════════════════════════════════════════
def viz1_survey_divergence():
    print("Fetching Viz 1 data...")

    payems = fetch("PAYEMS", start="2008-01-01")
    hh_emp = fetch("CE16OV", start="2008-01-01")

    df = pd.DataFrame({"establishment": payems, "household": hh_emp}).dropna()
    base = df.loc[df.index >= "2010-01-01"].iloc[0]
    df_norm = df - base
    df_norm["gap_millions"] = (df_norm["establishment"] - df_norm["household"]) / 1000

    print(df_norm["establishment"].max())
    print(df_norm["household"].min())

    pre  = df_norm[df_norm.index <= "2020-02-01"]
    post = df_norm[df_norm.index >= "2020-02-01"]

    last = df_norm.iloc[-1]
    gap_millions = abs(last["gap_millions"])
    last_date = df_norm.index[-1].strftime("%B %Y")

    fig = go.Figure()

    # trace 0: pre establishment (always visible)
    fig.add_trace(go.Scatter(
        x=pre.index, y=pre["establishment"],
        mode="lines", line=dict(color=BLUE_MUTED, width=2.5),
        name="Establishment Survey (Payrolls)",
        hovertemplate="<b>%{x|%b %Y}</b><br>Establishment: %{y:,.0f}K<extra></extra>"
    ))

    # trace 1: pre household (hidden by default)
    fig.add_trace(go.Scatter(
        x=pre.index, y=pre["household"],
        fill="tonexty", fillcolor=RED_FAINT,
        mode="lines", line=dict(color="rgba(192,57,43,0.35)", width=1),
        name="Household Survey (CPS)",
        visible=False,
        hovertemplate="<b>%{x|%b %Y}</b><br>Household: %{y:,.0f}K<extra></extra>"
    ))

    # trace 2: post establishment (always visible)
    fig.add_trace(go.Scatter(
        x=post.index, y=post["establishment"],
        mode="lines", line=dict(color=BLUE, width=3.5),
        showlegend=False,
        hovertemplate="<b>%{x|%b %Y}</b><br>Establishment: %{y:,.0f}K<extra></extra>"
    ))

    # trace 3: post household + fill with gap tooltip (hidden by default)
    fig.add_trace(go.Scatter(
        x=post.index, y=post["household"],
        fill="tonexty", fillcolor=RED_LIGHT,
        mode="lines", line=dict(color=RED, width=1.2),
        showlegend=False,
        visible=False,
        customdata=post["gap_millions"].abs().values,
        hovertemplate=(
            "<b>%{x|%b %Y}</b><br>"
            "Household: %{y:,.0f}K<br>"
            "<span style='color:#c0392b'><b>Gap: %{customdata:.1f}M workers</b></span>"
            "<extra></extra>"
        )
    ))

    # Annotations
    fig.add_annotation(
        x="2009-02-01", y=5000, xref="x", yref="y",
        text="← Surveys Agree", showarrow=False,
        xanchor="left", yanchor="bottom",
        font=dict(color="rgba(255,255,255,0.4)", size=10)
    )
    fig.add_shape(type="line", x0="2020-02-01", x1="2020-02-01",
                  y0=0, y1=1, yref="paper",
                  line=dict(color=GREY, width=1, dash="dot"))
    fig.add_annotation(
        x="2020-04-01", y=0.55, yref="paper",
        text="<b>Both surveys agreed<br>during the shock</b>",
        showarrow=True, ax=60, ay=0,
        arrowhead=2, arrowcolor=GREY,
        font=dict(color=GREY, size=10),
        bgcolor=DARK_BG, opacity=0.9, xanchor="left"
    )
    rev_y = df_norm.loc[df_norm.index >= "2024-02-01"].iloc[0]["establishment"]
    fig.add_annotation(
        x="2024-02-01", y=rev_y+300,
        text="BLS quietly<br>revised away<br>800K jobs",
        showarrow=True, ax=0, ay=-55,
        arrowhead=3, arrowcolor=GOLD, arrowsize=1.2,
        font=dict(color=GOLD, size=10),
        bgcolor=DARK_BG, opacity=0.9
    )
    fig.add_annotation(
        x=0.99, y=0.06, xref="paper", yref="paper",
        text=f"<b>As of {last_date}, the two surveys<br>"
             f"disagree by <span style='color:{RED}'>"
             f"{gap_millions:.1f} million workers</span></b>",
        showarrow=False, xanchor="right",
        font=dict(color=TEXT, size=12),
        bgcolor="rgba(22,33,62,0.9)", bordercolor=RED, borderwidth=1
    )
    fig.add_shape(type="rect",
                  x0="2020-02-01", x1=df_norm.index[-1],
                  y0=df_norm.loc["2020-02-01":]["household"].min() - 500,
                  y1=df_norm.loc["2020-02-01":]["establishment"].max() + 500,
                  line=dict(color=GOLD, width=1.5, dash="dot"),
                  fillcolor="rgba(243,156,18,0.04)")
    fig.add_annotation(
        x="2020-06-01",
        y=df_norm.loc["2020-02-01":]["establishment"].max() + 200,
        text="↑ Post-2020 divergence zone", showarrow=False,
        font=dict(color=GOLD, size=9), xanchor="left"
    )

    # Buttons
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                x=0.01, y=0.9, xanchor="left", yanchor="top",
                showactive=True,
                bgcolor=PANEL_BG,
                font=dict(color=TEXT),
                buttons=[
                    dict(
                        label="Official View Only",
                        method="update",
                        args=[
                            {"visible": [True, False, True, False]},
                            {"yaxis.title.text": "Change in Employment Since Jan 2010 (thousands)"}
                        ]
                    ),
                    dict(
                        label="Reveal Household Survey",
                        method="update",
                        args=[
                            {"visible": [True, True, True, True]},
                            {"yaxis.title.text": "Divergence Between Surveys (thousands) — Red Fill = Hidden Workers"}
                        ]
                    ),
                ]
            )
        ],
        title=dict(
            text="<b>The Two Surveys Tell Opposite Stories</b><br>"
                 "<sup>Establishment (payroll) vs. Household (CPS) — normalized to Jan 2010. "
                 "Use buttons to reveal the suppressed counter-metric and reframe the y-axis.</sup>",
            font=dict(color=TEXT, size=17)
        ),
        paper_bgcolor=DARK_BG, plot_bgcolor=PANEL_BG,
        font=dict(color=TEXT),
        xaxis=dict(title="Date", gridcolor="#2c2c3e", showgrid=True),
        yaxis=dict(
            title="Change in Employment Since Jan 2010 (thousands)",
            gridcolor="#2c2c3e",
            range=[-6000, 30000]
        ),
                   
        legend=dict(bgcolor=PANEL_BG, bordercolor=GREY, borderwidth=1,
                    x=0.01, y=0.99, xanchor="left", yanchor="top"),
        hovermode="x unified",
        margin=dict(t=100, b=60, l=80, r=40)
    )

    path = save_html(fig, "viz1_survey_divergence")
    print("  Viz 1 complete.")


# ══════════════════════════════════════════════════════════════════════════════
# VIZ 2 — U-3 vs U-6 / Participation / Prime-Age EPOP
#
# Rhetorical interactivity:
#   1. Default "Official View": only U-3 visible, Panel 2 hidden
#      (procedural rhetoric anchoring)
#   2. "Show Full Picture" reveals U-6, fill, Panel 2, triggers animated
#      counter 0 → hidden unemployment figure
#      (relations to persons concerned — Campbell)
#   3. Unified hover crosshair across both panels
#      (interest in consequences — Campbell)
# ══════════════════════════════════════════════════════════════════════════════
def viz2_unemployment_depth():
    print("Fetching Viz 2 data...")

    u3      = fetch("UNRATE",      start="2006-01-01")
    u6      = fetch("U6RATE",      start="2006-01-01")
    civpart = fetch("CIVPART",     start="2006-01-01")
    epop    = fetch("LNS12300060", start="2006-01-01")
    clf     = fetch("CLF16OV",     start="2006-01-01")

    df = pd.DataFrame({
        "U3": u3, "U6": u6,
        "CIVPART": civpart, "EPOP": epop, "CLF": clf
    }).dropna()

    last = df.iloc[-1]
    hidden_pct = last["U6"] - last["U3"]
    hidden_millions = (hidden_pct / 100) * (last["CLF"] / 1000)
    last_date = df.index[-1].strftime("%B %Y")

    baseline_civpart = df.loc["2020-01-01", "CIVPART"]
    df["gap_millions"] = ((df["U6"] - df["U3"]) / 100) * (df["CLF"] / 1000)

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=(
            "Unemployment: Headline (Blue) vs. Reality (Red)",
            "Who Left the Labor Force? Participation & Prime-Age EPOP"
        ),
        vertical_spacing=0.14,
        row_heights=[0.52, 0.48]
    )

    # trace 0: U3 always visible
    fig.add_trace(go.Scatter(
        x=df.index, y=df["U3"],
        mode="lines", line=dict(color=BLUE, width=3),
        name="U-3 Headline (Official)",
        hovertemplate="<b>%{x|%b %Y}</b><br>U-3: %{y:.1f}%<extra></extra>"
    ), row=1, col=1)

    # trace 1: U6 hidden by default
    fig.add_trace(go.Scatter(
        x=df.index, y=df["U6"],
        fill="tonexty", fillcolor=RED_LIGHT,
        mode="lines", line=dict(color=RED, width=2, dash="dash"),
        name="U-6 Broad (inc. discouraged + involuntary PT)",
        visible=False,
        customdata=df["gap_millions"].values,
        hovertemplate=(
            "<b>%{x|%b %Y}</b><br>U-6: %{y:.1f}%<br>"
            "<span style='color:#c0392b'><b>Hidden: %{customdata:.1f}M workers</b></span>"
            "<extra></extra>"
        )
    ), row=1, col=1)

    # trace 2: CIVPART hidden by default
    fig.add_trace(go.Scatter(
        x=df.index, y=df["CIVPART"],
        mode="lines", line=dict(color=GOLD, width=2),
        name="Labor Force Participation Rate",
        visible=False,
        hovertemplate="<b>%{x|%b %Y}</b><br>Participation: %{y:.1f}%<extra></extra>"
    ), row=2, col=1)

    # trace 3: EPOP hidden by default
    fig.add_trace(go.Scatter(
        x=df.index, y=df["EPOP"],
        mode="lines", line=dict(color=RED, width=2, dash="dash"),
        name="Prime-Age Employment-Population Ratio",
        visible=False,
        hovertemplate="<b>%{x|%b %Y}</b><br>Prime-Age EPOP: %{y:.1f}%<extra></extra>"
    ), row=2, col=1)

    # Recession bands
    for band in [("2007-12-01", "2009-06-01"), ("2020-02-01", "2020-04-01")]:
        for row_n in [1, 2]:
            fig.add_vrect(x0=band[0], x1=band[1],
                          fillcolor=GREY_LIGHT, layer="below", line_width=0,
                          row=row_n, col=1)

    fig.add_annotation(
        x="2007-12-01", y=0.97, yref="paper",
        text="Last comparable\ndivergence", showarrow=False,
        font=dict(color=GREY, size=9),
        xanchor="left", bgcolor=DARK_BG, opacity=0.85
    )

    # Pre-pandemic baseline
    fig.add_shape(type="line",
                  x0=df.index[0], x1=df.index[-1],
                  y0=baseline_civpart, y1=baseline_civpart,
                  line=dict(color="rgba(255,255,255,0.3)", width=1, dash="dot"),
                  row=2, col=1)
    fig.add_annotation(
        x=df.index[int(len(df)*0.15)], y=baseline_civpart + 0.3,
        text="Pre-Pandemic Baseline (Jan 2020)",
        showarrow=False, font=dict(color="rgba(255,255,255,0.45)", size=9),
        row=2, col=1
    )

    # Hidden unemployment annotation
    fig.add_annotation(
        x=df.index[-1], y=(last["U3"] + last["U6"]) / 2,
        text=f"<b>\"Hidden Unemployment\"</b><br>"
             f"~{hidden_millions:.1f}M workers<br>invisible to headline",
        showarrow=True, ax=-120, ay=0,
        arrowhead=2, arrowcolor=RED,
        font=dict(color=RED, size=10),
        bgcolor=DARK_BG, opacity=0.9, xanchor="right",
        row=1, col=1
    )

    # Buttons
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                x=0.01, y=0.99, xanchor="left", yanchor="top",
                showactive=True,
                bgcolor=PANEL_BG,
                font=dict(color=TEXT),
                buttons=[
                    dict(
                        label="📊 Official View (U-3 Only)",
                        method="update",
                        args=[{"visible": [True, False, False, False]}]
                    ),
                    dict(
                        label="🔍 Show Full Picture",
                        method="update",
                        args=[{"visible": [True, True, True, True]}]
                    ),
                ]
            )
        ],
        title=dict(
            text="<b>The Headline Hides the Floor</b><br>"
                 "<sup>Blue = official metric (solid). Red = suppressed reality (dashed). "
                 "Toggle 'Show Full Picture' to reveal what U-3 excludes.</sup>",
            font=dict(color=TEXT, size=17)
        ),
        paper_bgcolor=DARK_BG, plot_bgcolor=PANEL_BG,
        font=dict(color=TEXT),
        legend=dict(bgcolor=PANEL_BG, bordercolor=GREY, borderwidth=1,
                    x=0.01, y=0.92, xanchor="left", yanchor="top"),
        hovermode="x unified",
        margin=dict(t=100, b=60, l=80, r=40)
    )
    fig.update_xaxes(gridcolor="#2c2c3e")
    fig.update_yaxes(gridcolor="#2c2c3e")

    path = save_html(fig, "viz2_unemployment_depth")

    # Inject animated counter
    js = f"""
(function() {{
    var targetValue = {hidden_millions:.1f};
    var counterEl = null;
    var animated = false;

    function animateCounter() {{
        if (animated) return;
        animated = true;
        var start = null;
        var duration = 1500;
        counterEl = document.createElement('div');
        counterEl.style.cssText = [
            'position:fixed',
            'bottom:80px',
            'right:30px',
            'background:rgba(22,33,62,0.96)',
            'border:2px solid {RED}',
            'border-radius:8px',
            'padding:12px 18px',
            'color:{TEXT}',
            'font-family:sans-serif',
            'font-size:14px',
            'z-index:9999',
            'pointer-events:none',
            'box-shadow:0 0 20px rgba(192,57,43,0.4)'
        ].join(';');
        document.body.appendChild(counterEl);

        function step(timestamp) {{
            if (!start) start = timestamp;
            var progress = Math.min((timestamp - start) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            var current = (eased * targetValue).toFixed(1);
            counterEl.innerHTML =
                '<div style="color:{TEXT_MUTED};font-size:11px;letter-spacing:1px;margin-bottom:4px">WORKERS HIDDEN FROM HEADLINE</div>' +
                '<div style="color:{RED};font-size:28px;font-weight:bold;font-variant-numeric:tabular-nums">' + current + 'M</div>' +
                '<div style="color:{TEXT_MUTED};font-size:10px;margin-top:4px">invisible to U-3 as of {last_date}</div>';
            if (progress < 1) {{
                requestAnimationFrame(step);
            }}
        }}
        requestAnimationFrame(step);
    }}

    document.addEventListener('click', function(e) {{
        var el = e.target;
        var parent = el.closest ? el.closest('[data-unformatted]') : null;
        var text = el.textContent || el.getAttribute('data-unformatted') || '';
        if (!text && el.parentElement) text = el.parentElement.textContent || '';

        if (text.indexOf('Show Full Picture') !== -1 || text.indexOf('Full Picture') !== -1) {{
            setTimeout(animateCounter, 400);
        }}
        if (text.indexOf('Official View') !== -1) {{
            if (counterEl) {{ counterEl.remove(); counterEl = null; }}
            animated = false;
        }}
    }}, true);
}})();
"""
    inject_js(path, js)
    print("  Viz 2 complete.")


# ══════════════════════════════════════════════════════════════════════════════
# VIZ 3 — QE / M2 / Real Wages
#
# Rhetorical interactivity:
#   1. Default: "Money Expansion Only" (M2 + Fed BS) — money grows alone
#      (procedural rhetoric anchoring)
#   2. Dropdown reveals human impact traces; callout appears highlighting
#      the purchasing power crossing
#      (enargeia — Lin et al.; interest in consequences — Campbell)
#   3. Unified hover across all active series
# ══════════════════════════════════════════════════════════════════════════════
def viz3_qe_wages():
    print("Fetching Viz 3 data...")

    m2       = fetch("M2SL")
    walcl    = fetch("WALCL")
    real_inc = fetch("MEPAINUSA672N", start="2010-01-01")
    cpi      = fetch("CPIAUCSL")

    m2_idx    = (m2    / m2.loc["2010-01-01"])    * 100
    walcl_idx = (walcl / walcl.iloc[0])           * 100
    cpi_idx   = (cpi   / cpi.loc["2010-01-01"])   * 100
    inc_idx   = (real_inc / real_inc.iloc[0])      * 100
    pwr_idx   = 10000 / cpi_idx

    m2_growth  = m2_idx.iloc[-1] / 100
    inc_growth = inc_idx.iloc[-1] / 100
    ratio = m2_growth / inc_growth

    fig = go.Figure()

    # trace 0: M2 always visible
    fig.add_trace(go.Scatter(
        x=m2_idx.index, y=m2_idx,
        mode="lines", line=dict(color=RED, width=3),
        name="M2 Money Supply (index, 2010=100)",
        hovertemplate="<b>%{x|%b %Y}</b><br>M2: %{y:.1f}<extra></extra>"
    ))

    # trace 1: Fed BS always visible
    fig.add_trace(go.Scatter(
        x=walcl_idx.index, y=walcl_idx,
        mode="lines", line=dict(color=GOLD, width=2.5, dash="dot"),
        name="Fed Balance Sheet (index, 2010=100)",
        hovertemplate="<b>%{x|%b %Y}</b><br>Fed BS: %{y:.1f}<extra></extra>"
    ))

    # trace 2: CPI hidden by default
    fig.add_trace(go.Scatter(
        x=cpi_idx.index, y=cpi_idx,
        mode="lines", line=dict(color=GREY, width=1.5, dash="dash"),
        name="CPI — Official Inflation (index, 2010=100)",
        visible=False,
        hovertemplate="<b>%{x|%b %Y}</b><br>CPI: %{y:.1f}<extra></extra>"
    ))

    # trace 3: purchasing power hidden by default
    fig.add_trace(go.Scatter(
        x=pwr_idx.index, y=pwr_idx,
        mode="lines", line=dict(color=GREEN, width=1.8, dash="longdash"),
        name="Purchasing Power of $100 (2010 dollars)",
        visible=False,
        hovertemplate="<b>%{x|%b %Y}</b><br>Pwr: $%{y:.1f}<extra></extra>"
    ))

    # trace 4: income hidden by default
    fig.add_trace(go.Scatter(
        x=inc_idx.index, y=inc_idx,
        mode="lines", line=dict(color="rgba(100,180,255,0.7)", width=1.5),
        name="Real Median Personal Income (index, 2010=100)",
        visible=False,
        yaxis="y2",
        hovertemplate="<b>%{x|%b %Y}</b><br>Income: %{y:.1f}<extra></extra>"
    ))

    # QE markers
    for date, label, y_pos in [
        ("2010-11-01", 'QE2<br>"price stability"',    0.82),
        ("2012-09-01", 'QE3<br>"employment support"', 0.72),
        ("2020-03-01", 'Pandemic QE<br>"unlimited"',  0.98),
    ]:
        fig.add_shape(type="line", x0=date, x1=date, y0=0, y1=1, yref="paper",
                      line=dict(color=RED, width=1, dash="dash"))
        fig.add_annotation(x=date, y=y_pos, yref="paper", text=label,
                           showarrow=False, xanchor="left",
                           font=dict(color=RED, size=9),
                           bgcolor=DARK_BG, opacity=0.85)

    fig.add_shape(type="line", x0="2023-01-01", x1="2023-01-01",
                  y0=0, y1=1, yref="paper",
                  line=dict(color=GREEN, width=1.2, dash="dashdot"))
    fig.add_annotation(
        x="2023-01-01", y=0.60, yref="paper",
        text="ChatGPT launch<br>AI investment surge<br>~$200B+ (2023-24)",
        showarrow=False, xanchor="left",
        font=dict(color=GREEN, size=9),
        bgcolor=DARK_BG, opacity=0.9
    )

    walcl_doubled_y = walcl_idx.loc[walcl_idx.index >= "2021-03-01"].iloc[0]
    fig.add_annotation(
        x="2021-03-01", y=walcl_doubled_y,
        text="<b>Fed balance sheet<br>~doubled in 12 months</b>",
        showarrow=True, ax=80, ay=-40,
        arrowhead=2, arrowcolor=GOLD,
        font=dict(color=GOLD, size=10),
        bgcolor=DARK_BG, opacity=0.9
    )

    fig.add_annotation(
        x=0.99, y=0.06, xref="paper", yref="paper",
        text=f"<b>Money supply grew <span style='color:{RED}'>"
             f"{ratio:.1f}x faster</span><br>than real wages since 2010</b>",
        showarrow=False, xanchor="right",
        font=dict(color=TEXT, size=12),
        bgcolor="rgba(22,33,62,0.92)", bordercolor=RED, borderwidth=1
    )

    for label, y_frac, color in [
        ("M2 ↗", 0.92, RED),
        ("Wages →", 0.38, "rgba(100,180,255,0.7)"),
        ("Pwr ↘", 0.22, GREEN),
    ]:
        fig.add_annotation(
            x=0.995, y=y_frac, xref="paper", yref="paper",
            text=f"<i>{label}</i>", showarrow=False, xanchor="right",
            font=dict(color=color, size=10)
        )

    # Dropdown
    fig.update_layout(
        updatemenus=[
            dict(
                type="dropdown",
                x=0.01, y=0.99, xanchor="left", yanchor="top",
                showactive=True,
                bgcolor=PANEL_BG,
                font=dict(color=TEXT),
                buttons=[
                    dict(
                        label="💰 Money Expansion Only",
                        method="update",
                        args=[{"visible": [True, True, False, False, False]}]
                    ),
                    dict(
                        label="👥 Show Human Impact",
                        method="update",
                        args=[{"visible": [True, True, True, True, True]}]
                    ),
                ]
            )
        ],
        title=dict(
            text="<b>Where Did the Money Go?</b><br>"
                 "<sup>M2 and Fed balance sheet expanded post-2020. "
                 "Select 'Show Human Impact' to reveal wages and purchasing power.</sup>",
            font=dict(color=TEXT, size=17)
        ),
        paper_bgcolor=DARK_BG, plot_bgcolor=PANEL_BG,
        font=dict(color=TEXT),
        xaxis=dict(title="Date", gridcolor="#2c2c3e"),
        yaxis=dict(title="Index (2010=100) — Money, CPI, Purchasing Power",
                   gridcolor="#2c2c3e", side="left"),
        yaxis2=dict(title="Index (2010=100) — Real Median Income",
                    overlaying="y", side="right",
                    gridcolor="#2c2c3e", showgrid=False,
                    range=[95, 130]),
        legend=dict(bgcolor=PANEL_BG, bordercolor=GREY, borderwidth=1,
                    x=0.01, y=0.88, xanchor="left", yanchor="top"),
        hovermode="x unified",
        margin=dict(t=110, b=60, l=90, r=90)
    )

    path = save_html(fig, "viz3_qe_wages")

    js = f"""
(function() {{
    var shown = false;
    document.addEventListener('click', function(e) {{
        var text = e.target.textContent || '';
        if (!text && e.target.parentElement) text = e.target.parentElement.textContent || '';
        if (text.indexOf('Human Impact') !== -1) {{
            if (shown) return;
            shown = true;
            var callout = document.createElement('div');
            callout.style.cssText = [
                'position:fixed',
                'top:120px',
                'right:30px',
                'background:rgba(22,33,62,0.96)',
                'border:2px solid {GREEN}',
                'border-radius:8px',
                'padding:12px 18px',
                'color:{TEXT}',
                'font-family:sans-serif',
                'font-size:13px',
                'z-index:9999',
                'max-width:260px',
                'box-shadow:0 0 20px rgba(39,174,96,0.3)'
            ].join(';');
            callout.innerHTML =
                '<div style="color:{GREEN};font-weight:bold;margin-bottom:8px">↙ PURCHASING POWER</div>' +
                '<div style="color:{TEXT_MUTED}">The green line crosses below 100 — your 2010 dollar now buys less ' +
                'while M2 grew <span style="color:{RED};font-weight:bold">{ratio:.1f}x faster</span> than wages.</div>';
            document.body.appendChild(callout);
            setTimeout(function() {{
                callout.style.transition = 'opacity 1.2s';
                callout.style.opacity = '0';
                setTimeout(function() {{ callout.remove(); }}, 1200);
            }}, 5000);
        }}
        if (text.indexOf('Money Expansion') !== -1) {{
            shown = false;
        }}
    }}, true);
}})();
"""
    inject_js(path, js)
    print("  Viz 3 complete.")


# ══════════════════════════════════════════════════════════════════════════════
# VIZ 4 — BLS Revision Magnitude
#
# Rhetorical interactivity:
#   1. Trend line hidden by default — "Reveal Trend" button draws it
#      (plausibility — Campbell; pattern self-reveals)
#   2. Sort toggle: chronological vs. by magnitude — sorted view clusters
#      pre-recession overstatements without annotation
#      (proximity of time, plausibility — Campbell)
#   3. Hover tooltip: initial estimate, revised estimate, jobs never existed
#      (relations to persons concerned — Campbell)
# ══════════════════════════════════════════════════════════════════════════════
def viz4_bls_revisions():
    print("Building Viz 4 (BLS revision data)...")

    revisions = {
        2007: -297,  2008: -27,   2009: 208,
        2010: 386,   2011: -192,  2012: 146,   2013: 345,
        2014: 91,    2015: 208,   2016: -150,  2017: 41,
        2018: 363,   2019: 501,   2020: -173,  2021: 626,
        2022: -306,  2023: -818,  2024: -589,
    }

    # Approximate initial published estimates (thousands)
    initial_estimates = {
        2007: 1100,  2008: 800,   2009: -4800,
        2010: 800,   2011: 2200,  2012: 1800,  2013: 2200,
        2014: 2900,  2015: 2600,  2016: 2240,  2017: 2100,
        2018: 2700,  2019: 2100,  2020: -9400, 2021: 6700,
        2022: 4500,  2023: 3100,  2024: 2200,
    }

    years  = list(revisions.keys())
    values = list(revisions.values())
    colors = [BLUE if v > 0 else RED for v in values]
    labels = [f"+{v}K" if v > 0 else f"{v}K" for v in values]

    customdata = []
    for y, v in revisions.items():
        init = initial_estimates.get(y, 0)
        revised = init + v
        customdata.append([init, revised, abs(v) if v < 0 else 0])

    cumulative_over = sum(abs(v) for v in values if v < 0)

    # Trend through overstatements
    over_years = [y for y, v in revisions.items() if v < 0]
    over_vals  = [v for v in values if v < 0]
    z = np.polyfit(over_years, over_vals, 1)
    p = np.poly1d(z)
    trend_x = list(range(min(over_years), max(over_years)+1))
    trend_y = [p(x) for x in trend_x]

    # Sorted by magnitude
    sorted_pairs    = sorted(zip(years, values, customdata), key=lambda x: x[1])
    years_s         = [x[0] for x in sorted_pairs]
    values_s        = [x[1] for x in sorted_pairs]
    colors_s        = [BLUE if v > 0 else RED for v in values_s]
    labels_s        = [f"+{v}K" if v > 0 else f"{v}K" for v in values_s]
    customdata_s    = [x[2] for x in sorted_pairs]

    fig = go.Figure()

    # trace 0: bars (chronological)
    fig.add_trace(go.Bar(
        x=years, y=values,
        marker_color=colors,
        name="Annual Revision (thousands)",
        text=labels,
        textposition="outside",
        textfont=dict(size=9, color=TEXT),
        customdata=customdata,
        hovertemplate=(
            "<b>%{x} Benchmark Revision</b><br>"
            "Initial published estimate: %{customdata[0]:,}K<br>"
            "Revised to: %{customdata[1]:,}K<br>"
            "<span style='color:#c0392b'><b>Jobs that never existed: %{customdata[2]:,}K</b></span>"
            "<extra></extra>"
        )
    ))

    # trace 1: trend line (hidden by default)
    fig.add_trace(go.Scatter(
        x=trend_x, y=trend_y,
        mode="lines",
        line=dict(color="rgba(192,57,43,0.65)", width=2.5, dash="dot"),
        name="Overstatement trend",
        visible=False,
        hovertemplate="Overstatement trend: %{y:.0f}K<extra></extra>"
    ))

    # Annotations and shapes
    fig.add_hline(y=0, line=dict(color="rgba(255,255,255,0.5)", width=2))
    fig.add_annotation(
        x=years[0] - 0.5, y=0,
        text="<b>← ACCURATE</b>",
        showarrow=False, xanchor="right",
        font=dict(color="rgba(255,255,255,0.6)", size=11)
    )

    fig.add_shape(type="rect", x0=2006.5, x1=2008.5, y0=-950, y1=700,
                  fillcolor=GREY_LIGHT, layer="below", line_width=0)
    fig.add_annotation(x=2007.5, y=650,
                       text="Preceded\n2008 financial crisis",
                       showarrow=False, font=dict(color=GREY, size=9))

    fig.add_shape(type="rect", x0=2022.5, x1=2024.5, y0=-950, y1=700,
                  fillcolor=GREY_LIGHT, layer="below", line_width=0)
    fig.add_annotation(x=2023.5, y=650,
                       text="Preceded\ncurrent slowdown",
                       showarrow=False, font=dict(color=GREY, size=9))

    fig.add_annotation(
        x=0.5, y=1.12, xref="paper", yref="paper",
        text=f"<b>Cumulative overstatement: "
             f"<span style='color:{RED}'>{cumulative_over:,}K jobs</span> "
             f"announced that were later revised away</b>",
        showarrow=False, xanchor="center",
        font=dict(color=TEXT, size=13),
        bgcolor="rgba(22,33,62,0.9)", bordercolor=RED, borderwidth=1
    )

    fig.add_annotation(
        x=2024, y=values[-1] - 60,
        text="<i>The next revision<br>has not yet<br>been published</i>",
        showarrow=True, ax=60, ay=30,
        arrowhead=2, arrowcolor=RED,
        font=dict(color=GREY, size=9),
        bgcolor=DARK_BG, opacity=0.9
    )

    # Buttons
    fig.update_layout(
        updatemenus=[
            # Trend line reveal
            dict(
                type="buttons",
                x=0.01, y=0.99, xanchor="left", yanchor="top",
                showactive=True,
                bgcolor=PANEL_BG,
                font=dict(color=TEXT),
                buttons=[
                    dict(
                        label="Hide Trend",
                        method="update",
                        args=[{"visible": [True, False]}]
                    ),
                    dict(
                        label="📉 Reveal Overstatement Trend",
                        method="update",
                        args=[{"visible": [True, True]}]
                    ),
                ]
            ),
            # Sort toggle
            dict(
                type="buttons",
                x=0.01, y=0.89, xanchor="left", yanchor="top",
                showactive=True,
                bgcolor=PANEL_BG,
                font=dict(color=TEXT),
                buttons=[
                    dict(
                        label="Sort: Chronological",
                        method="restyle",
                        args=[{
                            "x": [years],
                            "y": [values],
                            "marker.color": [colors],
                            "text": [labels],
                            "customdata": [customdata]
                        }]
                    ),
                    dict(
                        label="Sort: By Magnitude",
                        method="restyle",
                        args=[{
                            "x": [years_s],
                            "y": [values_s],
                            "marker.color": [colors_s],
                            "text": [labels_s],
                            "customdata": [customdata_s]
                        }]
                    ),
                ]
            ),
        ],
        title=dict(
            text="<b>The Numbers That Never Were</b><br>"
                 "<sup>Annual BLS benchmark revisions (thousands). "
                 "Hover bars for initial vs. revised figures. "
                 "Reveal the trend. Sort by magnitude to see the pre-recession pattern emerge.</sup>",
            font=dict(color=TEXT, size=17)
        ),
        paper_bgcolor=DARK_BG, plot_bgcolor=PANEL_BG,
        font=dict(color=TEXT),
        xaxis=dict(title="Year", gridcolor="#2c2c3e", tickmode="linear", dtick=1),
        yaxis=dict(
            title="Revision Magnitude (thousands of jobs, overstatements shown below zero)",
            gridcolor="#2c2c3e", range=[-950, 750]
        ),
        legend=dict(bgcolor=PANEL_BG, bordercolor=GREY, borderwidth=1),
        bargap=0.3,
        hovermode="closest",
        margin=dict(t=130, b=60, l=80, r=40)
    )

    save_html(fig, "viz4_bls_revisions")
    print("  Viz 4 complete.")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("CPSC 4530 Final Project — Interactive Economic Visualization Suite")
    print("=" * 60)

    viz1_survey_divergence()
    viz2_unemployment_depth()
    viz3_qe_wages()
    viz4_bls_revisions()

    print("\nDone. Four HTML files saved to script directory.")
    print("Open each .html in Chrome for the video demo.")
