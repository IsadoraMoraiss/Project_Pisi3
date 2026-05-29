"""
pages/univariada.py
Análise Univariada — dados reais do dataset BRAZIL_CITIES.csv
com filtros dinâmicos por região e variável.
"""

from dash import html, dcc, Input, Output, callback, ctx
import plotly.graph_objects as go
import pandas as pd

from Components.chart_card import create_chart_card, apply_default_layout, PLOTLY_CONFIG, STORY_COLORS
from data_loader import DF, ALL_REGIONS, REG_COLOR

PALETTE = [
    STORY_COLORS["accent_blue"],
    STORY_COLORS["positive"],
    STORY_COLORS["warning"],
    STORY_COLORS["accent"],
    STORY_COLORS["context"],
    STORY_COLORS["text"],
]

# ─── Variáveis disponíveis para o seletor dinâmico ─────────────────────────
VAR_OPTIONS = [
    {"label": "IDHM",                      "value": "IDHM"},
    {"label": "Oferta Hoteleira Observada", "value": "indice_oferta_hoteleira_observada"},
    {"label": "Infraestrutura Turística",  "value": "indice_infraestrutura"},
    {"label": "Potencial Não Convertido",  "value": "potencial_joia_escondida"},
    {"label": "Conversão Turística Proxy", "value": "indice_conversao_turistica_proxy"},
    {"label": "Conveniência Urbana",       "value": "indice_modernizacao"},
    {"label": "Autonomia Turística",       "value": "indice_acessibilidade"},
    {"label": "Hotéis",                    "value": "HOTELS"},
    {"label": "Leitos",                    "value": "BEDS"},
    {"label": "População Estimada",        "value": "ESTIMATED_POP"},
    {"label": "PIB per capita (R$)",       "value": "GDP_CAPITA"},
    {"label": "Empresas de Tecnologia",    "value": "COMP_J"},
    {"label": "Serviços de Alojamento",    "value": "COMP_I"},
]

VAR_LABELS = {o["value"]: o["label"] for o in VAR_OPTIONS}

VAR_EXPLANATIONS = {
    "IDHM": "Usado como base social: valores altos indicam melhores condições humanas, mas não garantem turismo convertido.",
    "indice_oferta_hoteleira_observada": "Mede a posição do município em hotéis e leitos absolutos, sem penalizar cidades populosas.",
    "indice_infraestrutura": "Resume estrutura operacional de apoio ao turista: hospedagem, agências, bancos e mobilidade por app.",
    "potencial_joia_escondida": "Mostra o gap proxy entre potencial estimado e estrutura observada; alto valor sugere subaproveitamento.",
    "indice_conversao_turistica_proxy": "Representa estrutura turística já convertida em oferta observável no dataset.",
    "indice_modernizacao": "Indica conveniência urbana e digital, com sinais de mobilidade, tecnologia, telefonia e bancos.",
    "indice_acessibilidade": "Avalia autonomia do visitante por serviços, comunicação, bancos e mobilidade cadastrada.",
    "HOTELS": "Conta meios de hospedagem cadastrados; valores zerados podem indicar ausência de registro no dataset.",
    "BEDS": "Conta leitos cadastrados e ajuda a dimensionar capacidade real de hospedagem.",
    "ESTIMATED_POP": "Contextualiza escala urbana; não deve ser lida como demanda turística.",
    "GDP_CAPITA": "Ajuda a comparar capacidade econômica do município, sem medir turismo diretamente.",
    "COMP_J": "Conta empresas de tecnologia, usadas como sinal de base digital e serviços modernos.",
    "COMP_I": "Conta empresas de alojamento e alimentação, aproximação setorial ligada à experiência do visitante.",
}

REGIOES_ALL = ["Todas"] + ALL_REGIONS


# ─── Helpers ───────────────────────────────────────────────────────────────

def _filter_df(region: str) -> pd.DataFrame:
    if region == "Todas":
        return DF.copy()
    return DF[DF["REGIAO"] == region].copy()


def _var_explanation(col: str) -> str:
    return VAR_EXPLANATIONS.get(col, "Ajuda a posicionar o município dentro da distribuição observada no dataset.")


def _hist_description(col: str, region: str) -> str:
    scope = "Brasil" if region == "Todas" else region
    return (
        f"Mostra a distribuição de {VAR_LABELS.get(col, col)} em {scope}. "
        f"A linha pontilhada marca a mediana; concentração à esquerda indica muitos municípios com valores baixos. "
        f"{_var_explanation(col)}"
    )


def _box_description(col: str) -> str:
    return (
        f"Compara a dispersão regional de {VAR_LABELS.get(col, col)}. "
        "Caixas mais altas ou assimétricas indicam maior desigualdade interna entre municípios. "
        f"{_var_explanation(col)}"
    )


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
    fig.add_vline(x=med, line_dash="dot", line_color=STORY_COLORS["accent"], line_width=2,
                  annotation_text=f"Mediana: {med:,.1f}", annotation_position="top right",
                  annotation_font_size=11, annotation_font_color=STORY_COLORS["accent"])
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


def _build_quadrante_bar() -> go.Figure:
    QUAD_COLORS = {
        "Alto IDH + Estrutura Limitada":       STORY_COLORS["warning"],
        "Alto IDH + Alta Oferta Hoteleira":    STORY_COLORS["positive"],
        "Alta Oferta + Baixo IDH":             STORY_COLORS["accent"],
        "Outros":                              STORY_COLORS["context"],
    }
    grp = DF["quadrante"].value_counts()
    fig = go.Figure(go.Bar(
        x=grp.index.tolist(),
        y=grp.values,
        marker_color=[QUAD_COLORS.get(q, "#AAB") for q in grp.index],
        opacity=0.9,
        text=grp.values,
        textposition="outside",
        textfont=dict(color=STORY_COLORS["text"], size=12),
        cliponaxis=False,
    ))
    ymax = max(grp.max() * 1.18, 1)
    fig.update_layout(
        xaxis_title="Perfil de aproveitamento",
        yaxis_title="Nº Municípios",
        yaxis=dict(range=[0, ymax]),
        margin=dict(t=30),
    )
    return apply_default_layout(fig)


# ─── Layout ───────────────────────────────────────────────────────────────

layout = html.Div(
    children=[
        html.Div(
            style={"marginBottom": "28px"},
            children=[
                html.Div("Análise Univariada", className="page-title fade-up fade-up-1"),
                html.Div(
                    "Onde os municípios se posicionam nas distribuições de potencial, estrutura e conversão turística proxy",
                    className="page-subtitle fade-up fade-up-1",
                ),
            ],
        ),

        # ── Seção 1: Histograma dinâmico ──────────────────────────────
        html.Div(
            className="dash-card fade-up fade-up-2",
            style={"marginBottom": "20px"},
            children=[
                html.Div("Distribuição da variável selecionada", className="section-title"),
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
                html.Div(id="uni-hist-desc", className="chart-desc", style={"marginBottom": "10px"}),
                dcc.Graph(id="uni-hist-dynamic", config=PLOTLY_CONFIG, style={"height": "320px"}),
            ],
        ),

        # ── Seção 2: Boxplot por regiões (variável selecionável) ──────
        html.Div(
            className="dash-card fade-up fade-up-3",
            style={"marginBottom": "20px"},
            children=[
                html.Div("Comparação regional da distribuição", className="section-title"),
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
                html.Div(id="uni-box-desc", className="chart-desc", style={"marginBottom": "10px"}),
                dcc.Graph(id="uni-box-dynamic", config=PLOTLY_CONFIG, style={"height": "340px"}),
            ],
        ),

        # ── Seção 4: Quadrantes de aproveitamento ──────────────────────
        html.Div(
            className="dash-card fade-up fade-up-5",
            children=[
                html.Div("Quadrantes de aproveitamento turístico", className="section-title"),
                html.Hr(className="divider"),
                create_chart_card(
                    "uni-quadrante", _build_quadrante_bar(),
                    description="Classifica municípios por IDHM e oferta hoteleira observada. O quadrante de alto IDH com estrutura limitada aponta possível subaproveitamento, não uma conclusão sobre fluxo turístico real.",
                    height=300,
                ),
            ],
        ),
    ]
)


# ─── Callbacks dinâmicos ──────────────────────────────────────────────────

@callback(Output("uni-hist-dynamic", "figure"),
          Output("uni-hist-desc", "children"),
          Input("uni-dd-var",   "value"),
          Input("uni-dd-regiao","value"))
def update_hist(col, region):
    col = col or "IDHM"
    region = region or "Todas"
    return _build_hist_variable(col, region), _hist_description(col, region)


@callback(Output("uni-box-dynamic", "figure"),
          Output("uni-box-desc", "children"),
          Input("uni-dd-box", "value"))
def update_box(col):
    col = col or "IDHM"
    return _build_boxplot_regions(col), _box_description(col)
