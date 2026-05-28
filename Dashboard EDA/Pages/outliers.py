"""
pages/outliers.py
Outliers — detecção e análise com dados reais do BRAZIL_CITIES.csv
"""

from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from Components.chart_card import create_chart_card, apply_default_layout, PLOTLY_CONFIG, STORY_COLORS
from Components.metric_tile import create_metric_tile
from data_loader import DF, ALL_REGIONS, REG_COLOR

PALETTE = {
    "outlier": STORY_COLORS["accent"],
    "normal": STORY_COLORS["context"],
    "border": STORY_COLORS["text"],
}

# ─── Variáveis para análise de outliers ──────────────────────────────────
OUTLIER_VARS = [
    {"label": "IDHM",                "value": "IDHM"},
    {"label": "PIB per capita (R$)",  "value": "GDP_CAPITA"},
    {"label": "Leitos / 1000 hab",   "value": "leitos_1000hab"},
    {"label": "Empresas de Tech",    "value": "COMP_J"},
    {"label": "PIB Agropecuário",    "value": "GVA_AGROPEC"},
    {"label": "% Agro no GVA",       "value": "pct_agro_gva"},
    {"label": "Hotéis",              "value": "HOTELS"},
    {"label": "Carros",              "value": "Cars"},
]
VAR_LABELS = {o["value"]: o["label"] for o in OUTLIER_VARS}


def _zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / (s.std() + 1e-9)


def _n_outliers(col: str, threshold: float = 2.0) -> int:
    return int((np.abs(_zscore(DF[col].dropna())) > threshold).sum())


# ─── Figuras estáticas ─────────────────────────────────────────────────

def _build_boxmulti() -> go.Figure:
    fig = go.Figure()
    # IDHM, leitos_1000hab, pct_agro_gva — normalizado para mesma escala
    specs = [
        ("IDHM",          "IDHM ×100",     lambda v: v * 100,   STORY_COLORS["accent_blue"]),
        ("pct_agro_gva",  "% Agro GVA",   lambda v: v,          STORY_COLORS["positive"]),
        ("leitos_1000hab","Leitos/1k hab", lambda v: v,          STORY_COLORS["warning"]),
    ]
    for col, name, fn, color in specs:
        vals = DF[col].dropna()
        cap  = vals.quantile(0.99)
        vals = vals[vals <= cap]
        fig.add_trace(go.Box(
            y=fn(vals), name=name, marker_color=color,
            boxpoints="outliers", marker_size=4, line_width=1.8,
        ))
    fig.update_layout(yaxis_title="Valor")
    return apply_default_layout(fig)


def _build_violin_gdp() -> go.Figure:
    fig = go.Figure()
    for reg in ALL_REGIONS:
        sub = DF[DF["REGIAO"] == reg]["GDP_CAPITA"].dropna()
        cap = sub.quantile(0.98)
        sub = sub[sub <= cap]
        fig.add_trace(go.Violin(
            y=sub, name=reg, box_visible=True, meanline_visible=True,
            line_color=REG_COLOR[reg],
            fillcolor=f"rgba(180,180,255,0.15)",
            opacity=0.75, points=False,
        ))
    fig.update_layout(yaxis_title="PIB per capita (R$)", showlegend=False)
    return apply_default_layout(fig)


# ─── Figuras dinâmicas ─────────────────────────────────────────────────

def _build_scatter_z(col_x: str, col_y: str) -> go.Figure:
    sub = DF[[col_x, col_y, "CITY", "REGIAO"]].dropna()
    zx  = _zscore(sub[col_x])
    zy  = _zscore(sub[col_y])
    is_out = (np.abs(zx) > 2) | (np.abs(zy) > 2)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=zx[~is_out], y=zy[~is_out], mode="markers", name="Normal",
        marker=dict(color=PALETTE["normal"], size=5, opacity=0.45),
        hovertemplate="%{customdata}<extra>Normal</extra>",
        customdata=sub.loc[~is_out, "CITY"].values,
    ))
    fig.add_trace(go.Scatter(
        x=zx[is_out], y=zy[is_out], mode="markers", name="Outlier",
        marker=dict(color=PALETTE["outlier"], size=10, symbol="diamond",
                    line=dict(width=1.5, color=PALETTE["border"])),
        hovertemplate="%{customdata}<extra>Outlier</extra>",
        customdata=sub.loc[is_out, "CITY"].values,
    ))
    fig.add_shape(type="rect", x0=-2, x1=2, y0=-2, y1=2,
                  line=dict(color=STORY_COLORS["accent"], width=1.5, dash="dot"),
                  fillcolor="rgba(209,73,91,0.05)")
    fig.update_layout(
        xaxis_title=f"Z-score — {VAR_LABELS.get(col_x, col_x)}",
        yaxis_title=f"Z-score — {VAR_LABELS.get(col_y, col_y)}",
    )
    return apply_default_layout(fig)


def _build_hist_z(col: str) -> go.Figure:
    vals = DF[col].dropna()
    z    = _zscore(vals)
    cap  = 4.5
    z    = z.clip(-cap, cap)
    fig  = go.Figure(go.Histogram(
        x=z, nbinsx=40, marker_color=STORY_COLORS["context"], opacity=0.8, name="Z-score",
    ))
    fig.add_vline(x=2,  line_dash="dot", line_color=STORY_COLORS["accent"], line_width=2)
    fig.add_vline(x=-2, line_dash="dot", line_color=STORY_COLORS["accent"], line_width=2)
    n_out = int((np.abs(z) > 2).sum())
    fig.update_layout(
        xaxis_title=f"Z-score — {VAR_LABELS.get(col, col)}",
        yaxis_title="Frequência",
        title=dict(text=f"Outliers (|z|>2): {n_out}", font_size=12, x=0.5),
    )
    return apply_default_layout(fig)


# ─── Métricas de resumo ───────────────────────────────────────────────────

_N_OUT_IDH   = _n_outliers("IDHM")
_N_OUT_GDP   = _n_outliers("GDP_CAPITA")
_N_OUT_LEITO = _n_outliers("leitos_1000hab")

SUMMARY_TILES = [
    create_metric_tile("fa-solid fa-triangle-exclamation", "Outliers — IDHM",
                       str(_N_OUT_IDH),  "Z-score > |2|", "red",   anim_class="fade-up fade-up-2"),
    create_metric_tile("fa-solid fa-triangle-exclamation", "Outliers — PIB/cap",
                       str(_N_OUT_GDP),  "Z-score > |2|", "gold",  anim_class="fade-up fade-up-3"),
    create_metric_tile("fa-solid fa-triangle-exclamation", "Outliers — Leitos/1k",
                       str(_N_OUT_LEITO),"Z-score > |2|", "green", anim_class="fade-up fade-up-4"),
]

_BOX_MULTI = _build_boxmulti()
_VIOLIN_GDP = _build_violin_gdp()

# ─── Layout ───────────────────────────────────────────────────────────────

layout = html.Div(
    children=[
        html.Div(
            style={"marginBottom": "28px"},
            children=[
                html.Div("⚠️  Outliers", className="page-title fade-up fade-up-1"),
                html.Div(
                    "Detecção e caracterização de valores atípicos — 5.573 municípios reais",
                    className="page-subtitle fade-up fade-up-1",
                ),
            ],
        ),

        # Tiles
        html.Div(SUMMARY_TILES,
                 style={"display": "grid", "gridTemplateColumns": "repeat(3, 1fr)",
                        "gap": "16px", "marginBottom": "20px"}),

        # ── Box estático + Scatter Z dinâmico ──
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1.1fr", "gap": "20px", "marginBottom": "20px"},
            children=[
                html.Div(
                    className="dash-card fade-up fade-up-3",
                    children=[
                        html.Div("Box-Plot Múltiplo com Outliers", className="section-title"),
                        html.Hr(className="divider"),
                        create_chart_card("out-box-multi", _BOX_MULTI,
                                          description="Pontos externos ao bigode (1.5×IQR) são candidatos a outliers",
                                          height=320),
                    ],
                ),
                html.Div(
                    className="dash-card fade-up fade-up-4",
                    children=[
                        html.Div("Dispersão Z-score — Eixos Configuráveis", className="section-title"),
                        html.Hr(className="divider"),
                        html.Div(
                            style={"display": "flex", "gap": "12px", "marginBottom": "10px"},
                            children=[
                                dcc.Dropdown(id="out-dd-zx", options=OUTLIER_VARS, value="IDHM",
                                             clearable=False,
                                             style={"flex": "1", "fontFamily": "DM Sans, sans-serif"}),
                                dcc.Dropdown(id="out-dd-zy", options=OUTLIER_VARS, value="GDP_CAPITA",
                                             clearable=False,
                                             style={"flex": "1", "fontFamily": "DM Sans, sans-serif"}),
                            ],
                        ),
                        dcc.Graph(id="out-scatter-z", config=PLOTLY_CONFIG, style={"height": "290px"}),
                    ],
                ),
            ],
        ),

        # ── Violin GDP + Histograma Z dinâmico ──
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1.3fr", "gap": "20px"},
            children=[
                html.Div(
                    className="dash-card fade-up fade-up-4",
                    children=[
                        html.Div("Violin — PIB per capita por Região", className="section-title"),
                        html.Hr(className="divider"),
                        create_chart_card("out-violin-gdp", _VIOLIN_GDP,
                                          description="Distribuição do PIB per capita por macrorregião (p98 recortado)",
                                          height=320),
                    ],
                ),
                html.Div(
                    className="dash-card fade-up fade-up-5",
                    children=[
                        html.Div("Histograma de Z-scores — Variável Selecionável", className="section-title"),
                        html.Hr(className="divider"),
                        dcc.Dropdown(id="out-dd-hist", options=OUTLIER_VARS, value="IDHM",
                                     clearable=False,
                                     style={"marginBottom": "10px", "fontFamily": "DM Sans, sans-serif"}),
                        dcc.Graph(id="out-hist-z", config=PLOTLY_CONFIG, style={"height": "290px"}),
                    ],
                ),
            ],
        ),
    ]
)


# ─── Callbacks ─────────────────────────────────────────────────────────────

@callback(Output("out-scatter-z", "figure"),
          Input("out-dd-zx", "value"),
          Input("out-dd-zy", "value"))
def update_scatter_z(cx, cy):
    return _build_scatter_z(cx or "IDHM", cy or "GDP_CAPITA")


@callback(Output("out-hist-z", "figure"),
          Input("out-dd-hist", "value"))
def update_hist_z(col):
    return _build_hist_z(col or "IDHM")
