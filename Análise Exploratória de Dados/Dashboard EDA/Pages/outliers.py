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
ROBUST_Z_THRESHOLD = 3.5

# ─── Variáveis para análise de outliers ──────────────────────────────────
OUTLIER_VARS = [
    {"label": "IDHM",                      "value": "IDHM"},
    {"label": "Potencial Turístico", "value": "indice_potencial_turistico_proxy"},
    {"label": "Potencial Não Convertido",  "value": "potencial_joia_escondida"},
    {"label": "Conversão Turística", "value": "indice_conversao_turistica_proxy"},
    {"label": "Oferta Hoteleira Observada", "value": "indice_oferta_hoteleira_observada"},
    {"label": "Infraestrutura Turística",  "value": "indice_infraestrutura"},
    {"label": "Conveniência Urbana",       "value": "indice_modernizacao"},
    {"label": "Autonomia Turística",       "value": "indice_acessibilidade"},
    {"label": "Hotéis",                    "value": "HOTELS"},
    {"label": "Leitos",                    "value": "BEDS"},
]
VAR_LABELS = {o["value"]: o["label"] for o in OUTLIER_VARS}

VAR_EXPLANATIONS = {
    "IDHM": "desenvolvimento humano; outliers podem indicar base social muito acima ou abaixo do padrão nacional",
    "indice_potencial_turistico_proxy": "potencial estimado; outliers altos podem ser municípios com fundamentos fortes",
    "potencial_joia_escondida": "diferença estimada entre potencial e estrutura observada; outliers altos merecem investigação como possível subaproveitamento turístico",
    "indice_conversao_turistica_proxy": "estrutura já convertida; outliers altos sugerem concentração de estrutura turística",
    "indice_oferta_hoteleira_observada": "hotéis e leitos absolutos; outliers altos indicam forte oferta cadastrada",
    "indice_infraestrutura": "suporte operacional ao visitante; outliers altos indicam estrutura muito acima do padrão",
    "indice_modernizacao": "conveniência urbana e digital; outliers altos indicam base urbana diferenciada",
    "indice_acessibilidade": "autonomia turística; outliers altos indicam suporte prático ao visitante",
    "HOTELS": "volume de meios de hospedagem cadastrados",
    "BEDS": "capacidade cadastrada de hospedagem",
}


def _robust_zscore(s: pd.Series) -> pd.Series:
    values = pd.to_numeric(s, errors="coerce")
    median = values.median()
    mad = (values - median).abs().median()

    if pd.notna(mad) and mad > 1e-9:
        return 0.6745 * (values - median) / mad

    upper_tail = values[values > median]
    if len(upper_tail) > 10:
        center = upper_tail.median()
        upper_mad = (upper_tail - center).abs().median()
        if pd.notna(upper_mad) and upper_mad > 1e-9:
            scale = upper_mad / 0.6745
        else:
            iqr = upper_tail.quantile(0.75) - upper_tail.quantile(0.25)
            scale = iqr / 1.349 if pd.notna(iqr) and iqr > 1e-9 else upper_tail.std() + 1e-9
        z = pd.Series(0.0, index=values.index)
        z.loc[upper_tail.index] = (upper_tail - center) / scale
        return z

    iqr = values.quantile(0.75) - values.quantile(0.25)
    scale = iqr / 1.349 if pd.notna(iqr) and iqr > 1e-9 else values.std() + 1e-9
    return (values - median) / scale


def _n_outliers(col: str, threshold: float = ROBUST_Z_THRESHOLD) -> int:
    return int((np.abs(_robust_zscore(DF[col].dropna())) > threshold).sum())


def _outlier_description(col: str, threshold: float = ROBUST_Z_THRESHOLD) -> str:
    n_out = _n_outliers(col, threshold)
    label = VAR_LABELS.get(col, col)
    explanation = VAR_EXPLANATIONS.get(col, "indicador selecionado")
    return (
        f"{label}: {n_out} municípios têm |z-score robusto| > {threshold:.1f}. "
        "O z-score robusto usa mediana e MAD, reduzindo a distorção de caudas longas e valores extremos. "
        f"Leitura: {explanation}."
    )


def _scatter_description(col_x: str, col_y: str) -> str:
    return (
        f"Compara desvios robustos de {VAR_LABELS.get(col_x, col_x)} e {VAR_LABELS.get(col_y, col_y)}. "
        f"O retângulo central marca a zona esperada entre -{ROBUST_Z_THRESHOLD:.1f} e {ROBUST_Z_THRESHOLD:.1f}; pontos fora dela merecem investigação contextual. "
        "O gráfico usa todos os municípios com dados válidos, sem amostragem."
    )


# ─── Figuras estáticas ─────────────────────────────────────────────────

def _build_boxmulti() -> go.Figure:
    fig = go.Figure()
    # Indicadores centrais em escala 0-100 para comparar concentração e caudas.
    specs = [
        ("IDHM", "IDHM x100", lambda v: v * 100, STORY_COLORS["accent_blue"]),
        ("indice_potencial_turistico_proxy", "Potencial", lambda v: v, STORY_COLORS["positive"]),
        ("indice_conversao_turistica_proxy", "Conversão", lambda v: v, STORY_COLORS["accent"]),
        ("indice_oferta_hoteleira_observada", "Oferta hotel.", lambda v: v, STORY_COLORS["warning"]),
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


def _build_violin_gap() -> go.Figure:
    fig = go.Figure()
    for reg in ALL_REGIONS:
        sub = DF[DF["REGIAO"] == reg]["potencial_joia_escondida"].dropna()
        fig.add_trace(go.Violin(
            y=sub, name=reg, box_visible=True, meanline_visible=True,
            line_color=REG_COLOR[reg],
            fillcolor=f"rgba(180,180,255,0.15)",
            opacity=0.75, points=False,
        ))
    fig.update_layout(yaxis_title="Potencial Não Convertido", showlegend=False)
    return apply_default_layout(fig)


# ─── Figuras dinâmicas ─────────────────────────────────────────────────

def _build_scatter_z(col_x: str, col_y: str) -> go.Figure:
    sub = DF[[col_x, col_y, "CITY", "STATE", "REGIAO"]].dropna()
    zx  = _robust_zscore(sub[col_x])
    zy  = _robust_zscore(sub[col_y])
    is_out = (np.abs(zx) > ROBUST_Z_THRESHOLD) | (np.abs(zy) > ROBUST_Z_THRESHOLD)
    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        x=zx[~is_out], y=zy[~is_out], mode="markers", name="Normal",
        marker=dict(color=PALETTE["normal"], size=5, opacity=0.45),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "UF: %{customdata[1]}<br>"
            "Z robusto x: %{x:.2f}<br>"
            "Z robusto y: %{y:.2f}<extra>Normal</extra>"
        ),
        customdata=sub.loc[~is_out, ["CITY", "STATE"]].values,
    ))
    fig.add_trace(go.Scattergl(
        x=zx[is_out], y=zy[is_out], mode="markers", name="Outlier",
        marker=dict(color=PALETTE["outlier"], size=10, symbol="diamond",
                    line=dict(width=1.5, color=PALETTE["border"])),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "UF: %{customdata[1]}<br>"
            "Z robusto x: %{x:.2f}<br>"
            "Z robusto y: %{y:.2f}<extra>Outlier</extra>"
        ),
        customdata=sub.loc[is_out, ["CITY", "STATE"]].values,
    ))
    fig.add_shape(type="rect", x0=-ROBUST_Z_THRESHOLD, x1=ROBUST_Z_THRESHOLD,
                  y0=-ROBUST_Z_THRESHOLD, y1=ROBUST_Z_THRESHOLD,
                  line=dict(color=STORY_COLORS["accent"], width=1.5, dash="dot"),
                  fillcolor="rgba(209,73,91,0.05)")
    fig.update_layout(
        xaxis_title=f"Z-score robusto — {VAR_LABELS.get(col_x, col_x)}",
        yaxis_title=f"Z-score robusto — {VAR_LABELS.get(col_y, col_y)}",
    )
    return apply_default_layout(fig)


def _build_hist_z(col: str) -> go.Figure:
    vals = DF[col].dropna()
    z_raw = _robust_zscore(vals)
    cap  = max(5.0, ROBUST_Z_THRESHOLD * 1.4)
    z    = z_raw.clip(-cap, cap)
    fig  = go.Figure(go.Histogram(
        x=z, nbinsx=40, marker_color=STORY_COLORS["context"], opacity=0.8, name="Z-score robusto",
    ))
    fig.add_vline(x=ROBUST_Z_THRESHOLD,  line_dash="dot", line_color=STORY_COLORS["accent"], line_width=2)
    fig.add_vline(x=-ROBUST_Z_THRESHOLD, line_dash="dot", line_color=STORY_COLORS["accent"], line_width=2)
    n_out = int((np.abs(z_raw) > ROBUST_Z_THRESHOLD).sum())
    fig.update_layout(
        xaxis_title=f"Z-score robusto — {VAR_LABELS.get(col, col)}",
        yaxis_title="Frequência",
        title=dict(text=f"Municípios fora do intervalo robusto (|z|>{ROBUST_Z_THRESHOLD:.1f}): {n_out}", font_size=12, x=0.5),
    )
    return apply_default_layout(fig)


# ─── Métricas de resumo ───────────────────────────────────────────────────

_N_OUT_GAP = _n_outliers("potencial_joia_escondida")
_N_OUT_CONV = _n_outliers("indice_conversao_turistica_proxy")
_N_OUT_BEDS = _n_outliers("BEDS")

SUMMARY_TILES = [
    create_metric_tile("fa-solid fa-triangle-exclamation", "Outliers — Gap Turístico",
                       str(_N_OUT_GAP), "Z robusto > |3,5|", "red",
                       explanation="Municípios com potencial não convertido muito fora do padrão robusto nacional.",
                       anim_class="fade-up fade-up-2"),
    create_metric_tile("fa-solid fa-triangle-exclamation", "Outliers — Conversão Turística",
                       str(_N_OUT_CONV), "Z robusto > |3,5|", "gold",
                       explanation="Municípios com estrutura turística observada muito fora do padrão robusto.",
                       anim_class="fade-up fade-up-3"),
    create_metric_tile("fa-solid fa-triangle-exclamation", "Outliers — Leitos",
                       str(_N_OUT_BEDS), "Z robusto > |3,5|", "green",
                       explanation="Municípios com capacidade cadastrada de hospedagem muito acima do padrão robusto.",
                       anim_class="fade-up fade-up-4"),
]

_BOX_MULTI = _build_boxmulti()
_VIOLIN_GAP = _build_violin_gap()

# ─── Layout ───────────────────────────────────────────────────────────────

layout = html.Div(
    children=[
        html.Div(
            style={"marginBottom": "28px"},
            children=[
                html.Div("Outliers", className="page-title fade-up fade-up-1"),
                html.Div(
                    "Quais municípios fogem do padrão em potencial, oferta, infraestrutura e conversão turística",
                    className="page-subtitle fade-up fade-up-1",
                ),
            ],
        ),

        # Tiles
        html.Div(SUMMARY_TILES,
                 style={"display": "grid", "gridTemplateColumns": "repeat(3, 1fr)",
                        "gap": "16px", "marginBottom": "20px"}),

        # ── Box estático + Scatter robusto dinâmico ──
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1.1fr", "gap": "20px", "marginBottom": "20px"},
            children=[
                html.Div(
                    className="dash-card fade-up fade-up-3",
                    children=[
                        html.Div("Distribuição dos indicadores centrais", className="section-title"),
                        html.Hr(className="divider"),
                        create_chart_card("out-box-multi", _BOX_MULTI,
                                          description="Compara IDHM, potencial, conversão e oferta hoteleira em escala 0-100. Pontos externos ao bigode são candidatos a outliers e precisam de leitura contextual.",
                                          height=320),
                    ],
                ),
                html.Div(
                    className="dash-card fade-up fade-up-4",
                    children=[
                        html.Div("Desvios robustos combinados", className="section-title"),
                        html.Hr(className="divider"),
                        html.Div(
                            style={"display": "flex", "gap": "12px", "marginBottom": "10px"},
                            children=[
                                dcc.Dropdown(id="out-dd-zx", options=OUTLIER_VARS, value="potencial_joia_escondida",
                                             clearable=False,
                                             style={"flex": "1", "fontFamily": "DM Sans, sans-serif"}),
                                dcc.Dropdown(id="out-dd-zy", options=OUTLIER_VARS, value="indice_conversao_turistica_proxy",
                                             clearable=False,
                                             style={"flex": "1", "fontFamily": "DM Sans, sans-serif"}),
                            ],
                        ),
                        html.Div(id="out-scatter-desc", className="chart-desc", style={"marginBottom": "10px"}),
                        dcc.Graph(id="out-scatter-z", config=PLOTLY_CONFIG, style={"height": "290px"}),
                    ],
                ),
            ],
        ),

        # ── Violin + Histograma robusto dinâmico ──
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1.3fr", "gap": "20px"},
            children=[
                html.Div(
                    className="dash-card fade-up fade-up-4",
                    children=[
                        html.Div("Gap turístico por região", className="section-title"),
                        html.Hr(className="divider"),
                        create_chart_card("out-violin-gap", _VIOLIN_GAP,
                                          description="Mostra a distribuição regional do potencial não convertido. Regiões com caudas mais altas concentram mais municípios com possível subaproveitamento.",
                                          height=320),
                    ],
                ),
                html.Div(
                    className="dash-card fade-up fade-up-5",
                    children=[
                        html.Div("Distribuição dos z-scores robustos", className="section-title"),
                        html.Hr(className="divider"),
                        dcc.Dropdown(id="out-dd-hist", options=OUTLIER_VARS, value="potencial_joia_escondida",
                                     clearable=False,
                                     style={"marginBottom": "10px", "fontFamily": "DM Sans, sans-serif"}),
                        html.Div(id="out-hist-desc", className="chart-desc", style={"marginBottom": "10px"}),
                        dcc.Graph(id="out-hist-z", config=PLOTLY_CONFIG, style={"height": "290px"}),
                    ],
                ),
            ],
        ),
    ]
)


# ─── Callbacks ─────────────────────────────────────────────────────────────

@callback(Output("out-scatter-z", "figure"),
          Output("out-scatter-desc", "children"),
          Input("out-dd-zx", "value"),
          Input("out-dd-zy", "value"))
def update_scatter_z(cx, cy):
    cx = cx or "potencial_joia_escondida"
    cy = cy or "indice_conversao_turistica_proxy"
    return _build_scatter_z(cx, cy), _scatter_description(cx, cy)


@callback(Output("out-hist-z", "figure"),
          Output("out-hist-desc", "children"),
          Input("out-dd-hist", "value"))
def update_hist_z(col):
    col = col or "potencial_joia_escondida"
    return _build_hist_z(col), _outlier_description(col)
