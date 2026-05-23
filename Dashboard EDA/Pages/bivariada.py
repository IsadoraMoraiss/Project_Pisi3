"""
pages/bivariada.py
Análise Bi/Multivariada — dados reais do dataset BRAZIL_CITIES.csv
com scatter dinâmico (eixos X e Y configuráveis) e heatmap de correlação.
"""

from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from components.chart_card import create_chart_card, apply_default_layout, PLOTLY_CONFIG
from data_loader import DF, ALL_REGIONS, REG_COLOR

PALETTE = list(REG_COLOR.values())

# ─── Variáveis disponíveis para eixos dinâmicos ────────────────────────────
AXIS_OPTIONS = [
    {"label": "IDHM",                  "value": "IDHM"},
    {"label": "PIB per capita (R$)",    "value": "GDP_CAPITA"},
    {"label": "População Estimada",     "value": "ESTIMATED_POP"},
    {"label": "Hotéis",                 "value": "HOTELS"},
    {"label": "Leitos / 1000 hab",      "value": "leitos_1000hab"},
    {"label": "Empresas de Tech",       "value": "COMP_J"},
    {"label": "PIB Agropecuário",       "value": "GVA_AGROPEC"},
    {"label": "Serviços Aloj./Aliment.","value": "COMP_I"},
    {"label": "Veículos (Carros)",      "value": "Cars"},
    {"label": "Motocicletas",           "value": "Motorcycles"},
    {"label": "% Agro no GVA",          "value": "pct_agro_gva"},
]
AXIS_LABELS = {o["value"]: o["label"] for o in AXIS_OPTIONS}

# Colunas para o heatmap de correlação
CORR_COLS = {
    "IDHM":          "IDHM",
    "GDP_CAPITA":     "PIB/cap",
    "leitos_1000hab": "Leitos/1k",
    "COMP_J":         "Tech",
    "COMP_I":         "Alojam.",
    "GVA_AGROPEC":    "Agro",
    "HOTELS":         "Hotéis",
    "Cars":           "Carros",
    "pct_agro_gva":   "%Agro GVA",
}


# ─── Helpers ───────────────────────────────────────────────────────────────

def _cap(series: pd.Series, pct=0.995) -> pd.Series:
    cap = series.quantile(pct)
    return series.clip(upper=cap)


def _build_scatter(x_col: str, y_col: str, size_col: str | None = None) -> go.Figure:
    fig = go.Figure()
    sub = DF.dropna(subset=[x_col, y_col])
    for reg in ALL_REGIONS:
        mask = sub["REGIAO"] == reg
        xs   = _cap(sub.loc[mask, x_col])
        ys   = _cap(sub.loc[mask, y_col])
        if size_col and size_col in sub.columns:
            sz = _cap(sub.loc[mask, size_col])
            sz_norm = ((sz - sz.min()) / (sz.max() - sz.min() + 1e-9) * 28 + 5).clip(5, 33)
        else:
            sz_norm = 6
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers", name=reg,
            marker=dict(color=REG_COLOR[reg], size=sz_norm, opacity=0.65),
            hovertemplate=(
                f"<b>%{{customdata[0]}}</b><br>"
                f"{AXIS_LABELS.get(x_col, x_col)}: %{{x:.3f}}<br>"
                f"{AXIS_LABELS.get(y_col, y_col)}: %{{y:,.0f}}<extra>{reg}</extra>"
            ),
            customdata=sub.loc[mask, ["CITY"]].values,
        ))

    # Trend line (OLS)
    xs_all = _cap(sub[x_col]).values
    ys_all = _cap(sub[y_col]).values
    mask_valid = np.isfinite(xs_all) & np.isfinite(ys_all)
    if mask_valid.sum() > 10:
        m, b = np.polyfit(xs_all[mask_valid], ys_all[mask_valid], 1)
        x_line = np.linspace(xs_all[mask_valid].min(), xs_all[mask_valid].max(), 100)
        fig.add_trace(go.Scatter(
            x=x_line, y=m * x_line + b, mode="lines", name="Tendência",
            line=dict(color="#E74C3C", width=1.5, dash="dot"), showlegend=False,
        ))

    fig.update_layout(
        xaxis_title=AXIS_LABELS.get(x_col, x_col),
        yaxis_title=AXIS_LABELS.get(y_col, y_col),
    )
    return apply_default_layout(fig)


def _build_heatmap() -> go.Figure:
    cols   = list(CORR_COLS.keys())
    labels = list(CORR_COLS.values())
    corr   = DF[cols].corr().round(2)
    corr.index   = labels
    corr.columns = labels
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=labels, y=labels,
        colorscale="Blues", zmin=-1, zmax=1,
        text=corr.values, texttemplate="%{text:.2f}",
        showscale=True,
    ))
    fig.update_layout(margin=dict(l=8, r=8, t=24, b=8))
    return apply_default_layout(fig)


def _build_bubble(x_col: str, y_col: str) -> go.Figure:
    fig = go.Figure()
    sub = DF.dropna(subset=[x_col, y_col, "ESTIMATED_POP"])
    for reg in ALL_REGIONS:
        mask = sub["REGIAO"] == reg
        xs   = _cap(sub.loc[mask, x_col])
        ys   = _cap(sub.loc[mask, y_col])
        pop  = sub.loc[mask, "ESTIMATED_POP"]
        sz   = ((pop - pop.min()) / (pop.max() - pop.min() + 1) * 32 + 6).clip(6, 38)
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers", name=reg,
            marker=dict(size=sz, color=REG_COLOR[reg], opacity=0.60,
                        line=dict(width=1, color="white")),
            hovertemplate=(
                f"<b>%{{customdata[0]}}</b><br>"
                f"{AXIS_LABELS.get(x_col, x_col)}: %{{x:.3f}}<br>"
                f"{AXIS_LABELS.get(y_col, y_col)}: %{{y:,.0f}}<br>"
                "Pop: %{customdata[1]:,.0f}<extra></extra>"
            ),
            customdata=sub.loc[mask, ["CITY", "ESTIMATED_POP"]].values,
        ))
    fig.update_layout(
        xaxis_title=AXIS_LABELS.get(x_col, x_col),
        yaxis_title=AXIS_LABELS.get(y_col, y_col),
    )
    return apply_default_layout(fig)


def _build_violin_idh() -> go.Figure:
    fig = go.Figure()
    for reg in ALL_REGIONS:
        sub = DF[DF["REGIAO"] == reg]["IDHM"].dropna()
        fig.add_trace(go.Violin(
            y=sub, name=reg, box_visible=True, meanline_visible=True,
            line_color=REG_COLOR[reg],
            fillcolor="rgba(180,180,255,0.15)",
            opacity=0.7, points=False,
        ))
    fig.update_layout(yaxis_title="IDHM", showlegend=False)
    return apply_default_layout(fig)


# Cached heatmap (não muda)
_HEATMAP_FIG = _build_heatmap()
_VIOLIN_FIG  = _build_violin_idh()

# ─── Layout ───────────────────────────────────────────────────────────────

layout = html.Div(
    children=[
        html.Div(
            style={"marginBottom": "28px"},
            children=[
                html.Div("🔗  Análise Bi/Multivariada", className="page-title fade-up fade-up-1"),
                html.Div(
                    "Correlações e relações entre variáveis — dados reais dos 5.573 municípios",
                    className="page-subtitle fade-up fade-up-1",
                ),
            ],
        ),

        # ── Scatter dinâmico principal ──────────────────────────────
        html.Div(
            className="dash-card fade-up fade-up-2",
            style={"marginBottom": "20px"},
            children=[
                html.Div("Dispersão — Eixos Configuráveis por Região", className="section-title"),
                html.Hr(className="divider"),
                html.Div(
                    style={"display": "flex", "gap": "20px", "flexWrap": "wrap", "marginBottom": "16px"},
                    children=[
                        html.Div([
                            html.Label("Eixo X:", className="info-label",
                                       style={"marginBottom": "4px", "display": "block"}),
                            dcc.Dropdown(
                                id="biv-dd-x",
                                options=AXIS_OPTIONS, value="IDHM", clearable=False,
                                style={"width": "250px", "fontFamily": "DM Sans, sans-serif"},
                            ),
                        ]),
                        html.Div([
                            html.Label("Eixo Y:", className="info-label",
                                       style={"marginBottom": "4px", "display": "block"}),
                            dcc.Dropdown(
                                id="biv-dd-y",
                                options=AXIS_OPTIONS, value="GDP_CAPITA", clearable=False,
                                style={"width": "250px", "fontFamily": "DM Sans, sans-serif"},
                            ),
                        ]),
                    ],
                ),
                dcc.Graph(id="biv-scatter-dynamic", config=PLOTLY_CONFIG, style={"height": "380px"}),
            ],
        ),

        # ── Heatmap + Violin ────────────────────────────────────────
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1.2fr 1fr", "gap": "20px", "marginBottom": "20px"},
            children=[
                html.Div(
                    className="dash-card fade-up fade-up-3",
                    children=[
                        html.Div("Mapa de Correlação (Pearson)", className="section-title"),
                        html.Hr(className="divider"),
                        create_chart_card("heat-corr", _HEATMAP_FIG,
                                          description="Correlação de Pearson entre variáveis numéricas do dataset real",
                                          height=360),
                    ],
                ),
                html.Div(
                    className="dash-card fade-up fade-up-4",
                    children=[
                        html.Div("Distribuição do IDHM por Região (Violin)", className="section-title"),
                        html.Hr(className="divider"),
                        create_chart_card("violin-idh-biv", _VIOLIN_FIG,
                                          description="Comparação das distribuições de IDHM entre macrorregiões",
                                          height=360),
                    ],
                ),
            ],
        ),

        # ── Bubble dinâmico ─────────────────────────────────────────
        html.Div(
            className="dash-card fade-up fade-up-5",
            children=[
                html.Div("Bubble Chart — X × Y com Tamanho = População", className="section-title"),
                html.Hr(className="divider"),
                html.Div(
                    style={"display": "flex", "gap": "20px", "flexWrap": "wrap", "marginBottom": "16px"},
                    children=[
                        html.Div([
                            html.Label("Eixo X:", className="info-label",
                                       style={"marginBottom": "4px", "display": "block"}),
                            dcc.Dropdown(
                                id="biv-bbl-x",
                                options=AXIS_OPTIONS, value="IDHM", clearable=False,
                                style={"width": "240px", "fontFamily": "DM Sans, sans-serif"},
                            ),
                        ]),
                        html.Div([
                            html.Label("Eixo Y:", className="info-label",
                                       style={"marginBottom": "4px", "display": "block"}),
                            dcc.Dropdown(
                                id="biv-bbl-y",
                                options=AXIS_OPTIONS, value="pct_agro_gva", clearable=False,
                                style={"width": "240px", "fontFamily": "DM Sans, sans-serif"},
                            ),
                        ]),
                    ],
                ),
                dcc.Graph(id="biv-bubble-dynamic", config=PLOTLY_CONFIG, style={"height": "380px"}),
            ],
        ),
    ]
)


# ─── Callbacks ─────────────────────────────────────────────────────────────

@callback(
    Output("biv-scatter-dynamic", "figure"),
    Input("biv-dd-x", "value"),
    Input("biv-dd-y", "value"),
)
def update_scatter(x_col, y_col):
    return _build_scatter(x_col or "IDHM", y_col or "GDP_CAPITA")


@callback(
    Output("biv-bubble-dynamic", "figure"),
    Input("biv-bbl-x", "value"),
    Input("biv-bbl-y", "value"),
)
def update_bubble(x_col, y_col):
    return _build_bubble(x_col or "IDHM", y_col or "pct_agro_gva")
