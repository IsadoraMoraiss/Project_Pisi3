"""
pages/univariada.py
Análise Univariada — dados reais do dataset BRAZIL_CITIES.csv
com filtros dinâmicos por região e variável.
"""

from dash import html, dcc, Input, Output, callback, ctx
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from components.chart_card import create_chart_card, apply_default_layout, PLOTLY_CONFIG
from data_loader import DF, ALL_REGIONS, REG_COLOR

PALETTE = ["#4A6CF7", "#1ABC9C", "#F5A623", "#E74C3C", "#27AE60", "#1A2B6B"]

# ─── Variáveis disponíveis para o seletor dinâmico ─────────────────────────
VAR_OPTIONS = [
    {"label": "IDHM",                   "value": "IDHM"},
    {"label": "PIB per capita (R$)",     "value": "GDP_CAPITA"},
    {"label": "População Estimada",      "value": "ESTIMATED_POP"},
    {"label": "Hotéis",                  "value": "HOTELS"},
    {"label": "Leitos / 1000 hab",       "value": "leitos_1000hab"},
    {"label": "Empresas de Tech",        "value": "COMP_J"},
    {"label": "PIB Agropecuário (R$)",   "value": "GVA_AGROPEC"},
    {"label": "Serviços Alojamento",     "value": "COMP_I"},
    {"label": "Veículos (Carros)",       "value": "Cars"},
    {"label": "Motocicletas",            "value": "Motorcycles"},
]

VAR_LABELS = {o["value"]: o["label"] for o in VAR_OPTIONS}

REGIOES_ALL = ["Todas"] + ALL_REGIONS


# ─── Helpers ───────────────────────────────────────────────────────────────

def _filter_df(region: str) -> pd.DataFrame:
    if region == "Todas":
        return DF.copy()
    return DF[DF["REGIAO"] == region].copy()


def _hist(values, name, color, xlabel, nbins=30):
    fig = go.Figure(go.Histogram(
        x=values, nbinsx=nbins,
        marker_color=color, opacity=0.85, name=name,
    ))
    fig.update_layout(bargap=0.04, xaxis_title=xlabel, yaxis_title="Frequência")
    return apply_default_layout(fig)


def _build_hist_variable(col: str, region: str) -> go.Figure:
    sub = _filter_df(region)
    vals = sub[col].dropna()
    # Remove extreme outliers for display (> 99.5th pct)
    cap = vals.quantile(0.995)
    vals = vals[vals <= cap]
    fig = _hist(vals, VAR_LABELS[col], PALETTE[0], VAR_LABELS[col])
    # Add median line
    med = vals.median()
    fig.add_vline(x=med, line_dash="dot", line_color="#E74C3C", line_width=2,
                  annotation_text=f"Mediana: {med:,.1f}", annotation_position="top right",
                  annotation_font_size=11, annotation_font_color="#E74C3C")
    return fig


def _build_boxplot_regions(col: str) -> go.Figure:
    fig = go.Figure()
    for reg in ALL_REGIONS:
        sub  = DF[DF["REGIAO"] == reg][col].dropna()
        cap  = sub.quantile(0.99)
        sub  = sub[sub <= cap]
        fig.add_trace(go.Box(
            y=sub, name=reg, marker_color=REG_COLOR[reg],
            boxmean="sd", boxpoints=False, line_width=1.8,
        ))
    fig.update_layout(yaxis_title=VAR_LABELS.get(col, col), showlegend=False)
    return apply_default_layout(fig)


def _build_bar_regioes_col(col: str) -> go.Figure:
    grp = DF.groupby("REGIAO")[col].mean().reindex(ALL_REGIONS)
    fig = go.Figure(go.Bar(
        x=grp.index.tolist(),
        y=grp.values,
        marker_color=list(REG_COLOR.values()),
        opacity=0.9,
        text=grp.round(2).values,
        textposition="outside",
    ))
    fig.update_layout(xaxis_title="Região", yaxis_title=f"Média — {VAR_LABELS.get(col,col)}")
    return apply_default_layout(fig)


def _build_uber_bar() -> go.Figure:
    grp = DF.groupby("REGIAO")["UBER"].sum().reindex(ALL_REGIONS)
    fig = go.Figure(go.Bar(
        x=grp.index.tolist(), y=grp.values,
        marker_color=list(REG_COLOR.values()), opacity=0.9,
        text=grp.astype(int).values, textposition="outside",
    ))
    fig.update_layout(xaxis_title="Região", yaxis_title="Cidades com Uber")
    return apply_default_layout(fig)


def _build_quadrante_bar() -> go.Figure:
    QUAD_COLORS = {
        "Joia Escondida":      "#F7D154",
        "Alto IDH + Estrutura":"#56C596",
        "Estrutura sem IDH":   "#F7934C",
        "Outros":              "#AABBD6",
    }
    grp = DF["quadrante"].value_counts()
    fig = go.Figure(go.Bar(
        x=grp.index.tolist(),
        y=grp.values,
        marker_color=[QUAD_COLORS.get(q, "#AAB") for q in grp.index],
        opacity=0.9, text=grp.values, textposition="outside",
    ))
    fig.update_layout(xaxis_title="Perfil Turístico", yaxis_title="Nº Municípios")
    return apply_default_layout(fig)


# ─── Layout ───────────────────────────────────────────────────────────────

layout = html.Div(
    children=[
        html.Div(
            style={"marginBottom": "28px"},
            children=[
                html.Div("📊  Análise Univariada", className="page-title fade-up fade-up-1"),
                html.Div(
                    "Distribuição individual de cada variável — dados reais dos 5.573 municípios",
                    className="page-subtitle fade-up fade-up-1",
                ),
            ],
        ),

        # ── Seção 1: Histograma dinâmico ──────────────────────────────
        html.Div(
            className="dash-card fade-up fade-up-2",
            style={"marginBottom": "20px"},
            children=[
                html.Div("Histograma por Variável e Região", className="section-title"),
                html.Hr(className="divider"),

                # Controles
                html.Div(
                    style={"display": "flex", "gap": "20px", "flexWrap": "wrap", "marginBottom": "16px"},
                    children=[
                        html.Div([
                            html.Label("Variável:", className="info-label",
                                       style={"marginBottom": "4px", "display": "block"}),
                            dcc.Dropdown(
                                id="uni-dd-var",
                                options=VAR_OPTIONS,
                                value="IDHM",
                                clearable=False,
                                style={"width": "260px", "fontFamily": "DM Sans, sans-serif"},
                            ),
                        ]),
                        html.Div([
                            html.Label("Filtro de Região:", className="info-label",
                                       style={"marginBottom": "4px", "display": "block"}),
                            dcc.Dropdown(
                                id="uni-dd-regiao",
                                options=[{"label": r, "value": r} for r in REGIOES_ALL],
                                value="Todas",
                                clearable=False,
                                style={"width": "200px", "fontFamily": "DM Sans, sans-serif"},
                            ),
                        ]),
                    ],
                ),
                dcc.Graph(id="uni-hist-dynamic", config=PLOTLY_CONFIG, style={"height": "320px"}),
            ],
        ),

        # ── Seção 2: Boxplot por regiões (variável selecionável) ──────
        html.Div(
            className="dash-card fade-up fade-up-3",
            style={"marginBottom": "20px"},
            children=[
                html.Div("Box-Plot Comparativo por Região", className="section-title"),
                html.Hr(className="divider"),
                html.Div(
                    style={"marginBottom": "12px"},
                    children=[
                        html.Label("Variável:", className="info-label",
                                   style={"marginBottom": "4px", "display": "inline-block", "marginRight": "10px"}),
                        dcc.Dropdown(
                            id="uni-dd-box",
                            options=VAR_OPTIONS,
                            value="IDHM",
                            clearable=False,
                            style={"width": "260px", "fontFamily": "DM Sans, sans-serif", "display": "inline-block"},
                        ),
                    ],
                ),
                dcc.Graph(id="uni-box-dynamic", config=PLOTLY_CONFIG, style={"height": "340px"}),
            ],
        ),

        # ── Seção 3: Gráficos fixos informativos ──────────────────────
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "marginBottom": "20px"},
            children=[
                html.Div(
                    className="dash-card fade-up fade-up-4",
                    children=[
                        html.Div("Média por Região — Variável Selecionável", className="section-title"),
                        html.Hr(className="divider"),
                        html.Div(
                            style={"marginBottom": "10px"},
                            children=[
                                dcc.Dropdown(
                                    id="uni-dd-bar-reg",
                                    options=VAR_OPTIONS,
                                    value="IDHM",
                                    clearable=False,
                                    style={"fontFamily": "DM Sans, sans-serif"},
                                ),
                            ],
                        ),
                        dcc.Graph(id="uni-bar-reg", config=PLOTLY_CONFIG, style={"height": "300px"}),
                    ],
                ),
                html.Div(
                    className="dash-card fade-up fade-up-5",
                    children=[
                        html.Div("Cobertura Uber por Região", className="section-title"),
                        html.Hr(className="divider"),
                        create_chart_card("uni-uber-bar", _build_uber_bar(),
                                          description="Municípios com Uber disponível por macrorregião",
                                          height=300),
                    ],
                ),
            ],
        ),

        # ── Seção 4: Perfil turístico ──────────────────────────────────
        html.Div(
            className="dash-card fade-up fade-up-5",
            children=[
                html.Div("Perfil Turístico dos Municípios (Quadrantes)", className="section-title"),
                html.Hr(className="divider"),
                create_chart_card(
                    "uni-quadrante", _build_quadrante_bar(),
                    description="Classificação baseada em IDHM e leitos/1000hab — "
                                "\"Joia Escondida\" = alto IDH com baixa estrutura hoteleira",
                    height=300,
                ),
            ],
        ),
    ]
)


# ─── Callbacks dinâmicos ──────────────────────────────────────────────────

@callback(Output("uni-hist-dynamic", "figure"),
          Input("uni-dd-var",   "value"),
          Input("uni-dd-regiao","value"))
def update_hist(col, region):
    return _build_hist_variable(col or "IDHM", region or "Todas")


@callback(Output("uni-box-dynamic", "figure"),
          Input("uni-dd-box", "value"))
def update_box(col):
    return _build_boxplot_regions(col or "IDHM")


@callback(Output("uni-bar-reg", "figure"),
          Input("uni-dd-bar-reg", "value"))
def update_bar_reg(col):
    return _build_bar_regioes_col(col or "IDHM")
