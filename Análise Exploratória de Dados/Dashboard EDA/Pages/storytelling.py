"""
pages/storytelling.py
Aba de Storytelling — narrativa analítica baseada nos resultados do dashboard,
clusterização e classificação turística dos municípios brasileiros.
"""

from dash import html, dcc
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from Components.chart_card import create_chart_card, apply_default_layout, PLOTLY_CONFIG, STORY_COLORS
from data_loader import DF, ALL_REGIONS, REG_COLOR

# ─── Paleta Semântica ─────────────────────────────────────────────────────────
SEM = {
    "positivo":  "#27AE60",   # verde — indicadores bons
    "negativo":  "#E74C3C",   # vermelho — alertas e problemas
    "atencao":   "#F5A623",   # laranja — atenção / subaproveitamento
    "neutro":    "#4A6CF7",   # azul — informação contextual
    "positivo2": "#1ABC9C",   # teal — destaque positivo secundário
}

# ─── Helpers de gráficos ───────────────────────────────────────────────────────

def _build_top10_gap() -> go.Figure:
    """Top 10 municípios com maior potencial turístico não convertido."""
    top10 = (
        DF[["CITY", "STATE", "potencial_joia_escondida", "IDHM", "indice_infraestrutura"]]
        .dropna()
        .nlargest(10, "potencial_joia_escondida")
    )
    labels = [f"{row.CITY}/{row.STATE}" for row in top10.itertuples()]
    BLUE_SHADES = ["#0A2540", "#0D47A1", "#1565C0", "#1976D2", "#1E88E5", "#2196F3", "#42A5F5", "#64B5F6", "#90CAF9", "#BBDEFB"]
    colors = BLUE_SHADES[:len(top10)]

    fig = go.Figure(go.Bar(
        x=top10["potencial_joia_escondida"].values,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.1f}" for v in top10["potencial_joia_escondida"]],
        textposition="outside",
        textfont=dict(size=11, color=STORY_COLORS["text"]),
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Potencial Não Convertido: %{x:.1f}<extra></extra>"
        ),
    ))
    fig.update_layout(
        title=dict(text="Municípios com maior potencial turístico subaproveitado", font_size=13, x=0.01),
        xaxis_title="Índice de Potencial Não Convertido (0–100)",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=8, r=40, t=40, b=8),
    )
    return apply_default_layout(fig)


def _build_quadrante_pizza() -> go.Figure:
    """Distribuição dos municípios brasileiros por quadrante turístico (rosca)."""
    QUAD_COLORS = {
        "Alto IDH + Alta Oferta Hoteleira":    "#1A237E", # Dark Indigo
        "Alto IDH + Estrutura Limitada":       "#3F51B5", # Indigo
        "Alta Oferta + Baixo IDH":             "#7986CB", # Light Indigo
        "Outros":                              "#C5CAE9", # Very Light Indigo
    }
    grp = DF["quadrante"].value_counts()
    fig = go.Figure(go.Pie(
        labels=grp.index.tolist(),
        values=grp.values,
        hole=0.50,
        marker_colors=[QUAD_COLORS.get(q, "#AAB") for q in grp.index],
        texttemplate="%{label}<br><b>%{percent}</b>",
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>Municípios: %{value:,}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Distribuição por quadrante turístico — Brasil", font_size=13, x=0.01),
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
        margin=dict(l=8, r=8, t=40, b=8),
    )
    return apply_default_layout(fig)


def _build_linha_idh_infra() -> go.Figure:
    """Gráfico de linha comparando IDH médio e Infraestrutura média por região."""
    reg_stats = (
        DF.groupby("REGIAO")[["IDHM", "indice_infraestrutura", "potencial_joia_escondida"]]
        .mean()
        .reindex(ALL_REGIONS)
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ALL_REGIONS,
        y=(reg_stats["IDHM"] * 100).round(1),
        mode="lines+markers",
        name="IDH Médio (×100)",
        line=dict(color="#1B5E20", width=2.5),
        marker=dict(size=9, color="#1B5E20"),
        hovertemplate="<b>%{x}</b><br>IDH×100: %{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=ALL_REGIONS,
        y=reg_stats["indice_infraestrutura"].round(1),
        mode="lines+markers",
        name="Infraestrutura Turística",
        line=dict(color="#4CAF50", width=2.5),
        marker=dict(size=9, color="#4CAF50"),
        hovertemplate="<b>%{x}</b><br>Infraestrutura: %{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=ALL_REGIONS,
        y=reg_stats["potencial_joia_escondida"].round(1),
        mode="lines+markers",
        name="Potencial Não Convertido",
        line=dict(color="#A5D6A7", width=2.5, dash="dot"),
        marker=dict(size=9, color="#A5D6A7", symbol="diamond"),
        hovertemplate="<b>%{x}</b><br>Potencial Não Convertido: %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="IDH, Infraestrutura e Potencial Não Convertido por Região", font_size=13, x=0.01),
        xaxis_title="Região",
        yaxis_title="Índice Médio",
        legend=dict(orientation="h", y=1.12, x=0),
        margin=dict(l=8, r=8, t=60, b=8),
    )
    return apply_default_layout(fig)


def _build_cluster_bar() -> go.Figure:
    """Barras comparando indicadores médios por quadrante (perfil dos clusters)."""
    quad_order = [
        "Alto IDH + Alta Oferta Hoteleira",
        "Alto IDH + Estrutura Limitada",
        "Alta Oferta + Baixo IDH",
        "Outros",
    ]
    cols = {
        "IDH (×100)": "IDHM",
        "Oferta Hoteleira": "indice_oferta_hoteleira_observada",
        "Infraestrutura": "indice_infraestrutura",
        "Potencial Gap": "potencial_joia_escondida",
    }
    stats = DF.groupby("quadrante")[list(cols.values())].mean()
    stats["IDHM"] = stats["IDHM"] * 100

    PURPLE_SHADES = ["#4A148C", "#7B1FA2", "#BA68C8", "#E1BEE7"]

    fig = go.Figure()
    for i, (label, col) in enumerate(cols.items()):
        fig.add_trace(go.Bar(
            name=label,
            x=[q.split(" + ")[-1] if " + " in q else q for q in quad_order],
            y=[stats.loc[q, col] if q in stats.index else 0 for q in quad_order],
            marker_color=PURPLE_SHADES[i],
            hovertemplate=f"<b>%{{x}}</b><br>{label}: %{{y:.1f}}<extra></extra>",
        ))
    fig.update_layout(
        title=dict(text="Perfil médio dos indicadores por quadrante turístico", font_size=13, x=0.01),
        barmode="group",
        xaxis_title="Quadrante",
        yaxis_title="Valor Médio (0–100)",
        legend=dict(orientation="h", y=1.12, x=0),
        margin=dict(l=8, r=8, t=60, b=8),
    )
    return apply_default_layout(fig)


# ─── Tabela resumida por região ────────────────────────────────────────────────

def _build_tabela_regiao() -> html.Div:
    """Tabela com métricas consolidadas por região."""
    cols_display = {
        "IDHM": "IDH Médio",
        "indice_infraestrutura": "Infraestrutura",
        "indice_oferta_hoteleira_observada": "Oferta Hoteleira",
        "potencial_joia_escondida": "Potencial Gap",
        "indice_modernizacao": "Conveniência Urbana",
    }
    stats = DF.groupby("REGIAO")[list(cols_display.keys())].mean().reindex(ALL_REGIONS).round(2)
    stats["IDHM"] = stats["IDHM"].apply(lambda v: f"{v:.3f}")

    header_cells = [html.Th("Região", style={"textAlign": "left"})] + [
        html.Th(lbl, style={"textAlign": "right"}) for lbl in list(cols_display.values())[1:]
    ]

    rows = []
    for reg in ALL_REGIONS:
        row_data = stats.loc[reg]
        cells = [html.Td(reg, style={"fontWeight": "600", "color": "#1A2B6B"})]
        for i, (col, lbl) in enumerate(cols_display.items()):
            val = row_data[col]
            if col == "IDHM":
                txt = str(val)
                color = SEM["positivo"] if float(val) >= 0.7 else (SEM["atencao"] if float(val) >= 0.6 else SEM["negativo"])
            else:
                txt = f"{float(val):.1f}"
                color = SEM["positivo"] if float(val) >= 50 else (SEM["atencao"] if float(val) >= 25 else SEM["negativo"])
            if i == 0:
                continue
            cells.append(html.Td(
                txt,
                style={"textAlign": "right", "color": color, "fontWeight": "600"}
            ))
        rows.append(html.Tr(cells, style={"borderBottom": "1px solid #EEF0F8"}))

    return html.Div(
        style={"overflowX": "auto"},
        children=[
            html.Table(
                style={
                    "width": "100%",
                    "borderCollapse": "collapse",
                    "fontFamily": "DM Sans, sans-serif",
                    "fontSize": "13px",
                },
                children=[
                    html.Thead(
                        html.Tr(header_cells),
                        style={
                            "background": "#F0F2F8",
                            "color": "#1A2B6B",
                            "fontWeight": "700",
                            "fontSize": "11px",
                            "textTransform": "uppercase",
                            "letterSpacing": "0.8px",
                        }
                    ),
                    html.Tbody(rows),
                ],
            )
        ]
    )


# ─── Bloco de insight (card narrativo) ────────────────────────────────────────

def _insight(icon: str, title: str, text: str, color: str = SEM["neutro"]) -> html.Div:
    return html.Div(
        style={
            "display": "flex",
            "gap": "16px",
            "padding": "20px 24px",
            "background": f"rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.06,)}",
            "borderLeft": f"4px solid {color}",
            "borderRadius": "12px",
            "marginBottom": "14px",
        },
        children=[
            html.Div(
                html.I(className=icon),
                style={
                    "fontSize": "22px",
                    "color": color,
                    "minWidth": "28px",
                    "marginTop": "2px",
                },
            ),
            html.Div([
                html.Div(title, style={
                    "fontFamily": "Sora, sans-serif",
                    "fontWeight": "700",
                    "fontSize": "14px",
                    "color": "#1A2B6B",
                    "marginBottom": "6px",
                }),
                html.P(text, style={
                    "fontSize": "13.5px",
                    "color": "#6B7A9F",
                    "lineHeight": "1.7",
                    "margin": 0,
                }),
            ]),
        ],
    )


def _section_header(title: str, subtitle: str = "", icon: str = "") -> html.Div:
    title_content = [html.I(className=icon, style={"marginRight": "8px", "color": "#1A2B6B"}), title] if icon else title
    children = [
        html.Div(title_content, className="section-title", style={"fontSize": "17px", "display": "flex", "alignItems": "center"}),
    ]
    if subtitle:
        children.append(html.P(subtitle, style={
            "fontSize": "13px",
            "color": "#6B7A9F",
            "marginTop": "6px",
            "lineHeight": "1.6",
        }))
    children.append(html.Hr(className="divider"))
    return html.Div(children, style={"marginBottom": "8px"})


# ─── Pré-computar figuras estáticas ───────────────────────────────────────────
_FIG_TOP10 = _build_top10_gap()
_FIG_PIZZA = _build_quadrante_pizza()
_FIG_LINHA = _build_linha_idh_infra()
_FIG_CLUSTER = _build_cluster_bar()


# ─── Layout ───────────────────────────────────────────────────────────────────

layout = html.Div(
    children=[

        # ── Cabeçalho ──
        html.Div(
            style={"marginBottom": "28px"},
            children=[
                html.Div("Storytelling Analítico", className="page-title fade-up fade-up-1"),
                html.Div(
                    "Do dado bruto à decisão: a história do turismo nos municípios brasileiros",
                    className="page-subtitle fade-up fade-up-1",
                ),
            ],
        ),

        # ── Seção 1: Contexto ──
        html.Div(
            className="dash-card fade-up fade-up-2",
            style={"marginBottom": "20px"},
            children=[
                _section_header(
                    "O Problema Central",
                    "O Brasil possui 5.570 municípios com perfis socioeconômicos muito distintos. "
                    "A questão central deste projeto é: quais municípios têm os melhores fundamentos "
                    "para o turismo, mas ainda não desenvolveram uma estrutura de hospedagem compatível? "
                    "Para responder isso, construímos índices compostos que separam potencial de estrutura observada.",
                    icon="fa-solid fa-book-open"
                ),
                html.Div(
                    style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "14px", "marginTop": "8px"},
                    children=[
                        _insight(
                            "fa-solid fa-magnifying-glass-chart",
                            "Hipótese Central",
                            "Municípios com alto IDH e boa conveniência urbana, mas baixa oferta hoteleira, "
                            "representam oportunidades subaproveitadas de turismo — as chamadas 'joias escondidas'.",
                            SEM["neutro"],
                        ),
                        _insight(
                            "fa-solid fa-database",
                            "Base de Dados",
                            "Foram analisados indicadores de 5.570 municípios do dataset BRAZIL_CITIES: "
                            "hotéis, leitos, IDHM, PIB per capita, Uber, telefonia, agências e empresas setoriais.",
                            SEM["neutro"],
                        ),
                    ],
                ),
            ],
        ),

        # ── Seção 2: Insights Principais ──
        html.Div(
            className="dash-card fade-up fade-up-3",
            style={"marginBottom": "20px"},
            children=[
                _section_header(
                    "Principais Descobertas",
                    "A análise exploratória revelou padrões consistentes de desigualdade no aproveitamento turístico.",
                    icon="fa-solid fa-lightbulb"
                ),
                _insight(
                    "fa-solid fa-triangle-exclamation",
                    "A maioria dos municípios está no quadrante de 'Estrutura Limitada'",
                    "Mais de 70% dos municípios brasileiros com IDH acima da mediana nacional ainda não "
                    "desenvolveram oferta hoteleira compatível com seu potencial. Isso indica uma lacuna "
                    "estrutural sistemática, não pontual.",
                    SEM["atencao"],
                ),
                _insight(
                    "fa-solid fa-arrow-trend-up",
                    "Sudeste e Sul concentram os municípios consolidados",
                    "As regiões Sul e Sudeste apresentam os maiores índices de conversão turística — "
                    "estrutura já alinhada ao potencial. O Norte, apesar do potencial natural expressivo, "
                    "tem a menor infraestrutura de suporte ao visitante.",
                    SEM["positivo"],
                ),
                _insight(
                    "fa-solid fa-gem",
                    "O Nordeste apresenta o maior gap de potencial não convertido",
                    "Com IDH médio intermediário mas potencial turístico natural elevado (biodiversidade, "
                    "litoral, cultura), o Nordeste acumula o maior número de municípios no quadrante de "
                    "'potencial não convertido'. São candidatos a investimento e política pública de turismo.",
                    SEM["atencao"],
                ),
                _insight(
                    "fa-solid fa-circle-xmark",
                    "Outliers indicam desequilíbrios extremos",
                    "Municípios com z-score robusto acima de 3,5 em leitos ou hotéis concentram estrutura "
                    "muito acima do padrão nacional — são hubs turísticos consolidados como Gramado/RS e "
                    "Bombinhas/SC. No extremo oposto, municípios com alto IDH e zero hotéis cadastrados "
                    "representam os casos mais claros de subaproveitamento.",
                    SEM["negativo"],
                ),
            ],
        ),

        # ── Seção 3: Visualizações de Suporte ──
        html.Div(
            className="dash-card fade-up fade-up-3",
            style={"marginBottom": "20px"},
            children=[
                _section_header("Top 10 Municípios com Maior Potencial Não Convertido", icon="fa-solid fa-chart-bar"),
                html.P(
                    "Os municípios abaixo combinam IDH elevado e boa conveniência urbana, mas têm "
                    "oferta hoteleira muito abaixo do esperado. São os candidatos mais urgentes a "
                    "políticas de atração de investimento turístico.",
                    className="chart-desc",
                    style={"marginBottom": "14px"},
                ),
                dcc.Graph(
                    id="story-top10-gap",
                    figure=_FIG_TOP10,
                    config=PLOTLY_CONFIG,
                    style={"height": "360px"},
                ),
            ],
        ),

        # ── Seção 4: Pizza + Linha side by side ──
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1.4fr", "gap": "20px", "marginBottom": "20px"},
            children=[
                html.Div(
                    className="dash-card fade-up fade-up-4",
                    children=[
                        _section_header("Quadrantes Turísticos", icon="fa-solid fa-chart-pie"),
                        html.P(
                            "Verde = base consolidada · Laranja = alto potencial subaproveitado · "
                            "Vermelho = estrutura sem fundamento social proporcional",
                            className="chart-desc",
                        ),
                        dcc.Graph(
                            id="story-pizza-quad",
                            figure=_FIG_PIZZA,
                            config=PLOTLY_CONFIG,
                            style={"height": "320px"},
                        ),
                    ],
                ),
                html.Div(
                    className="dash-card fade-up fade-up-4",
                    children=[
                        _section_header("Comparativo Regional", icon="fa-solid fa-chart-line"),
                        html.P(
                            "Azul = IDH (×100) · Verde = Infraestrutura Turística · "
                            "Laranja pontilhado = Potencial Não Convertido. "
                            "Observe que o Norte tem IDH relativamente alto, mas infraestrutura baixíssima.",
                            className="chart-desc",
                        ),
                        dcc.Graph(
                            id="story-linha-regiao",
                            figure=_FIG_LINHA,
                            config=PLOTLY_CONFIG,
                            style={"height": "320px"},
                        ),
                    ],
                ),
            ],
        ),

        # ── Seção 5: Perfil dos Clusters ──
        html.Div(
            className="dash-card fade-up fade-up-4",
            style={"marginBottom": "20px"},
            children=[
                _section_header(
                    "Perfil dos Quadrantes (Clusters Analíticos)",
                    "Cada quadrante funciona como um cluster com características médias distintas. "
                    "O gráfico compara os principais indicadores entre os grupos.",
                    icon="fa-solid fa-magnifying-glass-chart"
                ),
                dcc.Graph(
                    id="story-cluster-bar",
                    figure=_FIG_CLUSTER,
                    config=PLOTLY_CONFIG,
                    style={"height": "360px"},
                ),
            ],
        ),

        # ── Seção 6: Tabela por Região ──
        html.Div(
            className="dash-card fade-up fade-up-5",
            style={"marginBottom": "20px"},
            children=[
                _section_header(
                    "Tabela Resumo por Região",
                    "Médias regionais dos indicadores centrais. "
                    "Verde = desempenho acima de 50 · Laranja = entre 25–50 · Vermelho = abaixo de 25.",
                    icon="fa-solid fa-table-list"
                ),
                _build_tabela_regiao(),
            ],
        ),

        # ── Seção 7: Conclusões ──
        html.Div(
            className="dash-card fade-up fade-up-5",
            style={"marginBottom": "20px"},
            children=[
                _section_header(
                    "Conclusões e Recomendações",
                    "O que os dados sugerem para tomada de decisão.",
                    icon="fa-solid fa-bullseye"
                ),
                _insight(
                    "fa-solid fa-1",
                    "Priorizar municípios com alto IDH e infraestrutura baixa",
                    "O quadrante 'Alto IDH + Estrutura Limitada' é o mais numeroso e indica onde "
                    "o investimento em hospedagem teria maior aproveitamento imediato, pois a base social "
                    "e a conveniência urbana já estão presentes.",
                    SEM["neutro"],
                ),
                _insight(
                    "fa-solid fa-2",
                    "Desenvolver políticas regionais diferenciadas",
                    "O Norte e o Nordeste não são iguais: o Norte tem infraestrutura quase inexistente, "
                    "enquanto o Nordeste tem uma base de hospedagem nascente. As políticas precisam "
                    "refletir essa distinção.",
                    SEM["neutro"],
                ),
                _insight(
                    "fa-solid fa-3",
                    "Monitorar os outliers positivos como benchmarks",
                    "Os municípios com oferta hoteleira muito acima do padrão (Gramado, Bombinhas, etc.) "
                    "servem como modelos de desenvolvimento turístico e podem orientar estratégias para "
                    "municípios com potencial similar.",
                    SEM["positivo"],
                ),
                _insight(
                    "fa-solid fa-4",
                    "O IDH sozinho não prediz turismo",
                    "A análise bivariada mostrou que a correlação entre IDH e oferta hoteleira é "
                    "moderada — um município com IDH alto não necessariamente tem estrutura turística. "
                    "Infraestrutura e conveniência urbana completam o diagnóstico.",
                    SEM["atencao"],
                ),
            ],
        ),

        # ── Rodapé IA ──
        html.Div(
            "Conteúdo gerado e estruturado com auxílio de Inteligência Artificial.",
            className="fade-up fade-up-5",
            style={
                "textAlign": "center", 
                "color": "#A8B3D1", 
                "fontSize": "12.5px", 
                "marginTop": "30px", 
                "fontStyle": "italic"
            }
        ),

    ]
)
