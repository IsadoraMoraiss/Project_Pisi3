"""
pages/info_geral.py
Página de Informações Gerais do Dashboard.
"""

from dash import html

# ─── Dados da equipe e projeto ─────────────────────────────────────────────

TEAM_MEMBERS = [
    "Arthur Barbosa",
    "Danielly Nunes",
    "Gabriel Sabino",
    "Isadora Morais",
    "Luiz Vinicius"
]

PROJECT_INFO = {
    "Curso":       "Sistemas de Informação",
    "Disciplina":  "Projeto Interdisciplinar para Sistemas de Informação III",
    "Período":     "2026.1",
    "Professor":   "Gabriel Alves",
    "Dataset":     "Brasil em Foco — indicadores socioeconômicos brasileiros",
}

CONTEXTO = (
    "O projeto Brasil em Foco tem como propósito central investigar e visualizar "
    "indicadores socioeconômicos do território brasileiro, abrangendo múltiplas "
    "dimensões — desenvolvimento humano, mobilidade urbana, tecnologia, agronegócio "
    "e turismo. A narrativa principal é analisar desigualdades de aproveitamento "
    "turístico entre municípios brasileiros semelhantes, separando territórios "
    "consolidados daqueles com bons fundamentos e estrutura ainda pouco convertida."
)

OBJETIVO_DISCIPLINA = (
    "A disciplina de Análise de Dados visa capacitar os alunos a coletar, limpar, "
    "explorar e comunicar insights a partir de conjuntos de dados reais, utilizando "
    "ferramentas modernas de visualização e análise estatística."
)

OBJETIVO_DASHBOARD = (
    "Este dashboard foi organizado como uma jornada de análise: primeiro diagnostica "
    "o recorte escolhido, depois mostra onde ele se posiciona nas distribuições, "
    "investiga quais fatores caminham juntos e, por fim, destaca municípios que "
    "fogem do padrão e merecem explicação."
)

JORNADA_ANALITICA = [
    ("Visão Geral", "diagnosticar potencial, infraestrutura, oferta hoteleira e aproveitamento do recorte selecionado."),
    ("Univariada", "mostrar onde o recorte se posiciona nas distribuições nacionais e regionais."),
    ("Bivariada", "investigar quais fatores caminham juntos na formação de estrutura e aproveitamento turístico."),
    ("Outliers", "explicar quais municípios fogem do padrão e por que essas exceções importam."),
]

# ─── Layout ────────────────────────────────────────────────────────────────


def _info_row(label, value):
    return html.Div(
        className="info-block",
        children=[
            html.Span(f"{label}:", className="info-label"),
            html.Span(value, className="info-value"),
        ],
    )


def _section(title, children, anim="fade-up fade-up-2"):
    return html.Div(
        className=f"dash-card {anim}",
        style={"marginBottom": "20px"},
        children=[
            html.Div(title, className="section-title", style={"marginBottom": "16px"}),
            html.Hr(className="divider", style={"marginTop": "0", "marginBottom": "16px"}),
            *children,
        ],
    )


layout = html.Div(
    className="fade-up",
    children=[

        # ── Cabeçalho ──
        html.Div(
            style={"marginBottom": "32px"},
            children=[
                html.Div(
                    "Bem-vindo ao Dashboard",
                    className="page-title fade-up fade-up-1",
                ),
                html.Div(
                    "Brasil em Foco — Dashboard de Análises Exploratórias · 2026.1",
                    className="page-subtitle fade-up fade-up-1",
                ),
            ],
        ),

        # ── Grid 2 colunas ──
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "20px",
                "marginBottom": "20px",
            },
            children=[

                # Card: Equipe
                _section(
                    "Integrantes da Equipe",
                    [
                        html.Ul(
                            className="bullet-list",
                            children=[html.Li(m) for m in TEAM_MEMBERS],
                        )
                    ],
                    anim="fade-up fade-up-2",
                ),

                # Card: Dados do projeto
                _section(
                    "Dados do Projeto",
                    [_info_row(k, v) for k, v in PROJECT_INFO.items()],
                    anim="fade-up fade-up-3",
                ),
            ],
        ),

        # ── Contexto ──
        _section(
            "Contexto Geral do Projeto",
            [html.P(CONTEXTO, className="info-value", style={"lineHeight": "1.75"})],
            anim="fade-up fade-up-3",
        ),

        _section(
            "Jornada Analítica",
            [
                html.Ol(
                    className="bullet-list",
                    children=[
                        html.Li([
                            html.Strong(f"{titulo}: "),
                            html.Span(descricao),
                        ])
                        for titulo, descricao in JORNADA_ANALITICA
                    ],
                )
            ],
            anim="fade-up fade-up-4",
        ),

        # ── Grid 2 colunas (objetivos) ──
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "20px",
            },
            children=[
                _section(
                    "Objetivo da Disciplina",
                    [html.P(OBJETIVO_DISCIPLINA, className="info-value", style={"lineHeight": "1.75"})],
                    anim="fade-up fade-up-4",
                ),
                _section(
                    "Objetivo do Dashboard",
                    [html.P(OBJETIVO_DASHBOARD, className="info-value", style={"lineHeight": "1.75"})],
                    anim="fade-up fade-up-5",
                ),
            ],
        ),
    ],
)
