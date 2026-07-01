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
    "outlier": "#B71C1C", # Dark Red
    "normal": "#FFCDD2", # Light Red/Pink
    "border": "#212121", # Dark Charcoal
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
        ("IDHM", "IDHM x100", lambda v: v * 100, "#1B5E20"), # Dark Green
        ("indice_potencial_turistico_proxy", "Potencial", lambda v: v, "#2E7D32"), # Medium Dark Green
        ("indice_conversao_turistica_proxy", "Conversão", lambda v: v, "#4CAF50"), # Medium Green
        ("indice_oferta_hoteleira_observada", "Oferta hotel.", lambda v: v, "#81C784"), # Light Green
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
    ORANGE_SHADES = ["#FFB74D", "#FF9800", "#FB8C00", "#E65100", "#7A2200"]
    REG_SHADES = dict(zip(ALL_REGIONS, ORANGE_SHADES))
    for reg in ALL_REGIONS:
        sub = DF[DF["REGIAO"] == reg]["potencial_joia_escondida"].dropna()
        color = REG_SHADES[reg]
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        fill = f"rgba({r},{g},{b},0.15)"
        fig.add_trace(go.Violin(
            y=sub, name=reg, box_visible=True, meanline_visible=True,
            line_color=color,
            fillcolor=fill,
            opacity=0.75, points=False,
        ))
    fig.update_layout(yaxis_title="Potencial Não Convertido", showlegend=False)
    return apply_default_layout(fig)


# ─── Figuras dinâmicas ─────────────────────────────────────────────────

def _build_scatter_z(col_x: str, col_y: str) -> go.Figure:
    """
    Substitui o scatter massivo de normais por uma Densidade 2D, e plota os outliers isolados por cima.
    """
    sub = DF[[col_x, col_y, "CITY", "STATE", "REGIAO"]].dropna()
    zx  = _robust_zscore(sub[col_x])
    zy  = _robust_zscore(sub[col_y])
    is_out = (np.abs(zx) > ROBUST_Z_THRESHOLD) | (np.abs(zy) > ROBUST_Z_THRESHOLD)
    
    # Separar normais e outliers
    zx_normal = zx[~is_out]
    zy_normal = zy[~is_out]

    fig = go.Figure()

    # 1. Densidade (Contour) para o volume de dados normais
    fig.add_trace(go.Histogram2dContour(
        x=zx_normal,
        y=zy_normal,
        colorscale="Blues",
        reversescale=False,
        showscale=False,
        ncontours=12,
        contours=dict(coloring='fill'),
        line=dict(width=0),
        name="Massa Normal (Densidade)",
        hovertemplate="Concentração de municípios no padrão<extra></extra>"
    ))

    # 2. Scatter SOMENTE para os outliers
    fig.add_trace(go.Scatter(
        x=zx[is_out], y=zy[is_out], mode="markers", name="Outlier",
        marker=dict(color=PALETTE["outlier"], size=9, symbol="circle",
                    line=dict(width=1.5, color=PALETTE["border"])),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "UF: %{customdata[1]}<br>"
            "Z robusto x: %{x:.2f}<br>"
            "Z robusto y: %{y:.2f}<extra>Outlier</extra>"
        ),
        customdata=sub.loc[is_out, ["CITY", "STATE"]].values,
    ))
    # Linhas de threshold
    for val in [-ROBUST_Z_THRESHOLD, ROBUST_Z_THRESHOLD]:
        fig.add_hline(y=val, line_dash="dash", line_color="#E74C3C", opacity=0.5)
        fig.add_vline(x=val, line_dash="dash", line_color="#E74C3C", opacity=0.5)

    fig.update_layout(
        xaxis_title=f"Z-Score robusto ({VAR_LABELS.get(col_x, col_x)})",
        yaxis_title=f"Z-Score robusto ({VAR_LABELS.get(col_y, col_y)})",
        annotations=[dict(
            text="A área azul concentra a densidade de municípios no padrão. Pontos circulares são as exceções.",
            xref="paper", yref="paper", x=0.01, y=-0.16,
            showarrow=False, font=dict(size=11, color="#6B7A9F"),
        )],
        margin=dict(b=65),
        showlegend=False,
    )
    return apply_default_layout(fig)


def _build_hist_z(col: str) -> go.Figure:
    vals = DF[col].dropna()
    z_raw = _robust_zscore(vals)
    cap  = max(5.0, ROBUST_Z_THRESHOLD * 1.4)
    z    = z_raw.clip(-cap, cap)
    fig  = go.Figure(go.Histogram(
        x=z, nbinsx=40, marker_color="#4A90E2", opacity=0.8, name="Z-score robusto",
    ))
    fig.add_vline(x=ROBUST_Z_THRESHOLD,  line_dash="dot", line_color="#1F4E79", line_width=2)
    fig.add_vline(x=-ROBUST_Z_THRESHOLD, line_dash="dot", line_color="#1F4E79", line_width=2)
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
