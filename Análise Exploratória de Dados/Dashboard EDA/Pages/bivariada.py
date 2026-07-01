"""
pages/bivariada.py
Análise bivariada focada na narrativa de aproveitamento turístico:
potencial, conversão, correlações centrais e distribuição dos quadrantes.
"""

from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from Components.chart_card import create_chart_card, apply_default_layout, PLOTLY_CONFIG, STORY_COLORS
from data_loader import DF, ALL_REGIONS, REG_COLOR


AXIS_OPTIONS = [
    {"label": "IDHM", "value": "IDHM"},
    {"label": "Potencial Turístico", "value": "indice_potencial_turistico_proxy"},
    {"label": "Potencial Não Convertido", "value": "potencial_joia_escondida"},
    {"label": "Conversão Turística", "value": "indice_conversao_turistica_proxy"},
    {"label": "Oferta Hoteleira Observada", "value": "indice_oferta_hoteleira_observada"},
    {"label": "Infraestrutura Turística", "value": "indice_infraestrutura"},
    {"label": "Conveniência Urbana", "value": "indice_modernizacao"},
    {"label": "Autonomia Turística", "value": "indice_acessibilidade"},
    {"label": "Hotéis", "value": "HOTELS"},
    {"label": "Leitos", "value": "BEDS"},
    {"label": "Serviços de Alojamento", "value": "COMP_I"},
    {"label": "Empresas de Tecnologia", "value": "COMP_J"},
    {"label": "PIB per capita (R$)", "value": "GDP_CAPITA"},
    {"label": "População Estimada", "value": "ESTIMATED_POP"},
]
AXIS_LABELS = {o["value"]: o["label"] for o in AXIS_OPTIONS}

CORR_COLS = {
    "IDHM": "IDHM",
    "indice_potencial_turistico_proxy": "Potencial",
    "potencial_joia_escondida": "Gap",
    "indice_conversao_turistica_proxy": "Conversão",
    "indice_oferta_hoteleira_observada": "Oferta hotel.",
    "indice_infraestrutura": "Infra.",
    "indice_modernizacao": "Conv. urb.",
    "indice_acessibilidade": "Autonomia",
}

AXIS_EXPLANATIONS = {
    "IDHM": "base social do município",
    "indice_potencial_turistico_proxy": "potencial estimado por IDHM, conveniência, diversidade e categoria turística",
    "potencial_joia_escondida": "diferença estimada entre potencial e estrutura observada",
    "indice_conversao_turistica_proxy": "estrutura já convertida em oferta observável no dataset",
    "indice_oferta_hoteleira_observada": "percentil composto de hotéis e leitos absolutos",
    "indice_infraestrutura": "suporte operacional ao visitante",
    "indice_modernizacao": "conveniência urbana e digital",
    "indice_acessibilidade": "autonomia do visitante por serviços e mobilidade",
    "HOTELS": "volume de meios de hospedagem cadastrados",
    "BEDS": "capacidade cadastrada de hospedagem",
    "COMP_I": "serviços de alojamento e alimentação",
    "COMP_J": "base de empresas de tecnologia",
    "GDP_CAPITA": "capacidade econômica local",
    "ESTIMATED_POP": "escala populacional, não demanda turística",
}


def _pearson_stats(x_col: str, y_col: str) -> tuple[float, int]:
    sub = DF[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(sub) < 3 or sub[x_col].nunique() < 2 or sub[y_col].nunique() < 2:
        return float("nan"), len(sub)
    return float(sub[x_col].corr(sub[y_col], method="pearson")), len(sub)


def _corr_strength(r: float) -> str:
    if not np.isfinite(r):
        return "indefinida"
    abs_r = abs(r)
    if abs_r < 0.10:
        return "muito fraca"
    if abs_r < 0.30:
        return "fraca"
    if abs_r < 0.50:
        return "moderada"
    if abs_r < 0.70:
        return "forte"
    return "muito forte"


def _relationship_description(x_col: str, y_col: str) -> str:
    r, n = _pearson_stats(x_col, y_col)
    direction = "positiva" if r > 0 else "negativa" if r < 0 else "neutra"
    if not np.isfinite(r):
        corr_text = "Pearson não foi calculado porque uma das variáveis não varia o suficiente."
    else:
        corr_text = f"Pearson r={r:.2f} ({_corr_strength(r)}, {direction}), n={n} municípios."
    return (
        f"Dispersão entre {AXIS_LABELS.get(x_col, x_col)} ({AXIS_EXPLANATIONS.get(x_col, 'indicador selecionado')}) "
        f"e {AXIS_LABELS.get(y_col, y_col)} ({AXIS_EXPLANATIONS.get(y_col, 'indicador selecionado')}). "
        f"{corr_text} O gráfico usa todos os municípios com dados válidos, sem amostragem. "
        "Correlação indica associação linear, não causalidade."
    )


def _cramers_strength(v: float) -> str:
    if v < 0.10:
        return "muito fraca"
    if v < 0.20:
        return "fraca"
    if v < 0.40:
        return "moderada"
    if v < 0.60:
        return "forte"
    return "muito forte"


def _chi_square_cramers_v(col_a: str, col_b: str) -> dict:
    tab = pd.crosstab(DF[col_a], DF[col_b])
    observed = tab.to_numpy(dtype=float)
    n = observed.sum()
    row_totals = observed.sum(axis=1, keepdims=True)
    col_totals = observed.sum(axis=0, keepdims=True)
    expected = row_totals @ col_totals / n
    valid = expected > 0
    chi2 = float(((observed[valid] - expected[valid]) ** 2 / expected[valid]).sum())
    denom = max(1, min(tab.shape) - 1)
    v = float(np.sqrt((chi2 / n) / denom))
    return {"chi2": chi2, "n": int(n), "v": v, "table": tab}


def _build_scatter(x_col: str, y_col: str) -> go.Figure:
    """
    Substitui o scatterplot massivo por um Mapa de Densidade 2D (Contour)
    e plota apenas as médias regionais (centroides) por cima para clareza visual.
    """
    sub = DF.dropna(subset=[x_col, y_col])
    PURPLE_SHADES = ["#CE93D8", "#AB47BC", "#8E24AA", "#6A1B9A", "#310F4A"]
    REG_SHADES = dict(zip(ALL_REGIONS, PURPLE_SHADES))

    fig = go.Figure()

    # 1. Densidade global (Contour 2D) para mostrar a concentração dos 5500+ dados sem poluíção visual
    fig.add_trace(go.Histogram2dContour(
        x=sub[x_col],
        y=sub[y_col],
        colorscale="Purples",
        reversescale=False,
        showscale=False,
        ncontours=15,
        contours=dict(coloring='fill'),
        line=dict(width=0),
        name="Densidade",
        hovertemplate="Concentração alta de municípios<extra></extra>"
    ))

    # 2. Centroides (Média) por Região
    for reg in ALL_REGIONS:
        reg_data = sub[sub["REGIAO"] == reg]
        if not reg_data.empty:
            mean_x = reg_data[x_col].mean()
            mean_y = reg_data[y_col].mean()
            fig.add_trace(go.Scatter(
                x=[mean_x],
                y=[mean_y],
                mode="markers+text",
                name=f"Média {reg}",
                text=[reg],
                textposition="top center",
                textfont=dict(size=12, color="#1A2B6B"),
                marker=dict(color=REG_SHADES[reg], size=14, line=dict(color="#FFF", width=2)),
                hovertemplate=(
                    f"<b>Centroide: {reg}</b><br>"
                    f"Média {AXIS_LABELS.get(x_col, x_col)}: %{{x:,.2f}}<br>"
                    f"Média {AXIS_LABELS.get(y_col, y_col)}: %{{y:,.2f}}<extra></extra>"
                ),
            ))

    # 3. Tendência OLS global
    xs_all = sub[x_col].to_numpy()
    ys_all = sub[y_col].to_numpy()
    mask_valid = np.isfinite(xs_all) & np.isfinite(ys_all)
    if mask_valid.sum() > 10 and np.ptp(xs_all[mask_valid]) > 0 and np.ptp(ys_all[mask_valid]) > 0:
        m, b = np.polyfit(xs_all[mask_valid], ys_all[mask_valid], 1)
        x_line = np.linspace(xs_all[mask_valid].min(), xs_all[mask_valid].max(), 100)
        fig.add_trace(go.Scatter(
            x=x_line,
            y=m * x_line + b,
            mode="lines",
            name="Tendência OLS",
            line=dict(color="#1A2B6B", width=2, dash="dash"),
            showlegend=False,
        ))

    fig.update_layout(
        xaxis_title=AXIS_LABELS.get(x_col, x_col),
        yaxis_title=AXIS_LABELS.get(y_col, y_col),
        annotations=[dict(
            text="Áreas escuras = mais municípios. Círculos = média de cada região.",
            xref="paper", yref="paper", x=0.01, y=-0.16,
            showarrow=False, font=dict(size=11, color="#6B7A9F"),
        )],
        margin=dict(b=65),
    )
    return apply_default_layout(fig)



def _build_heatmap() -> go.Figure:
    cols = list(CORR_COLS.keys())
    labels = list(CORR_COLS.values())
    corr = DF[cols].corr().round(2)
    corr.index = labels
    corr.columns = labels

    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=labels,
        y=labels,
        colorscale="Blues",
        zmin=-1,
        zmax=1,
        text=corr.values,
        texttemplate="%{text:.2f}",
        hovertemplate="%{y} x %{x}<br>Pearson r=%{z:.2f}<extra></extra>",
        showscale=True,
    ))
    fig.update_layout(margin=dict(l=8, r=8, t=24, b=8))
    return apply_default_layout(fig)


def _build_region_quadrante_chart(tab: pd.DataFrame) -> go.Figure:
    quadrante_order = [
        "Alto IDH + Alta Oferta Hoteleira",
        "Alto IDH + Estrutura Limitada",
        "Alta Oferta + Baixo IDH",
        "Outros",
    ]
    colors = {
        "Alto IDH + Alta Oferta Hoteleira":    "#1A237E", # Dark Indigo
        "Alto IDH + Estrutura Limitada":       "#3F51B5", # Indigo
        "Alta Oferta + Baixo IDH":             "#7986CB", # Light Indigo
        "Outros":                              "#C5CAE9", # Very Light Indigo
    }

    tab = tab.reindex(index=ALL_REGIONS, columns=quadrante_order, fill_value=0)
    pct = tab.div(tab.sum(axis=1).replace(0, np.nan), axis=0).fillna(0) * 100

    fig = go.Figure()
    for quadrante in quadrante_order:
        values = pct[quadrante]
        fig.add_trace(go.Bar(
            x=values.index,
            y=values.values,
            name=quadrante,
            marker_color=colors[quadrante],
            text=[f"{v:.0f}%" if v >= 8 else "" for v in values.values],
            textposition="inside",
            insidetextanchor="middle",
            customdata=tab[quadrante].values,
            hovertemplate=(
                f"Região: %{{x}}<br>"
                f"Quadrante: {quadrante}<br>"
                "% dos municípios: %{y:.1f}%<br>"
                "Municípios: %{customdata:,.0f}<extra></extra>"
            ),
        ))

    fig.update_layout(
        barmode="stack",
        xaxis_title="Região",
        yaxis_title="% de municípios",
        yaxis=dict(range=[0, 100], ticksuffix="%"),
        uniformtext_minsize=10,
        uniformtext_mode="hide",
        legend_title_text="Quadrante",
    )
    return apply_default_layout(fig)


def _build_region_quadrante_test() -> html.Div:
    result = _chi_square_cramers_v("REGIAO", "quadrante")
    chart_fig = _build_region_quadrante_chart(result["table"])
    strength = _cramers_strength(result["v"])
    interpretation = (
        "A composição dos quadrantes mostra se os perfis de aproveitamento turístico aparecem de forma semelhante "
        "nas regiões ou se existe um padrão territorial na desigualdade observada."
    )
    reading = (
        f"Leitura estatística: associação {strength} entre região e quadrante "
        f"(Cramer's V={result['v']:.3f}). Ou seja, os perfis de aproveitamento turístico "
        "não se distribuem de forma homogênea pelo território."
    )
    return html.Div(
        className="dash-card fade-up fade-up-5",
        style={"marginBottom": "20px"},
        children=[
            html.Div("Quadrantes por região", className="section-title"),
            html.Hr(className="divider"),
            html.Div(interpretation, className="chart-desc", style={"marginBottom": "14px"}),
            create_chart_card(
                "region-quadrante-test-chart",
                chart_fig,
                description=(
                    "Composição percentual dos quadrantes em cada região. "
                    "A leitura central é comparar onde se concentram municípios consolidados, subaproveitados ou fora do padrão."
                ),
                height=360,
            ),
            html.Div(reading, className="info-value", style={"lineHeight": "1.65", "marginTop": "14px"}),
        ],
    )


_HEATMAP_FIG = _build_heatmap()


layout = html.Div(
    children=[
        html.Div(
            style={"marginBottom": "28px"},
            children=[
                html.Div("Análise Bivariada", className="page-title fade-up fade-up-1"),
                html.Div(
                    "Quais fatores caminham juntos na formação de potencial, estrutura e conversão turística",
                    className="page-subtitle fade-up fade-up-1",
                ),
            ],
        ),

        html.Div(
            className="dash-card fade-up fade-up-2",
            style={"marginBottom": "20px"},
            children=[
                html.Div("Relação entre indicadores selecionados", className="section-title"),
                html.Hr(className="divider"),
                html.Div(
                    style={"display": "flex", "gap": "20px", "flexWrap": "wrap", "marginBottom": "16px"},
                    children=[
                        html.Div([
                            html.Label("Eixo X:", className="info-label", style={"marginBottom": "4px", "display": "block"}),
                            dcc.Dropdown(
                                id="biv-dd-x",
                                options=AXIS_OPTIONS,
                                value="indice_potencial_turistico_proxy",
                                clearable=False,
                                style={"width": "250px", "fontFamily": "DM Sans, sans-serif"},
                            ),
                        ]),
                        html.Div([
                            html.Label("Eixo Y:", className="info-label", style={"marginBottom": "4px", "display": "block"}),
                            dcc.Dropdown(
                                id="biv-dd-y",
                                options=AXIS_OPTIONS,
                                value="indice_conversao_turistica_proxy",
                                clearable=False,
                                style={"width": "250px", "fontFamily": "DM Sans, sans-serif"},
                            ),
                        ]),
                    ],
                ),
                html.Div(id="biv-scatter-desc", className="chart-desc", style={"marginBottom": "10px"}),
                dcc.Graph(id="biv-scatter-dynamic", config=PLOTLY_CONFIG, style={"height": "380px"}),
            ],
        ),

        html.Div(
            className="dash-card fade-up fade-up-3",
            style={"marginBottom": "20px"},
            children=[
                html.Div("Mapa de Correlação (Pearson)", className="section-title"),
                html.Hr(className="divider"),
                create_chart_card(
                    "heat-corr",
                    _HEATMAP_FIG,
                    description=(
                        "Matriz de Pearson entre indicadores numéricos centrais. "
                        "Valores próximos de 1 ou -1 indicam associação linear mais forte; não testam causalidade."
                    ),
                    height=380,
                ),
            ],
        ),

        _build_region_quadrante_test(),
    ]
)


@callback(
    Output("biv-scatter-dynamic", "figure"),
    Output("biv-scatter-desc", "children"),
    Input("biv-dd-x", "value"),
    Input("biv-dd-y", "value"),
)
def update_scatter(x_col, y_col):
    x_col = x_col or "indice_potencial_turistico_proxy"
    y_col = y_col or "indice_conversao_turistica_proxy"
    return _build_scatter(x_col, y_col), _relationship_description(x_col, y_col)
