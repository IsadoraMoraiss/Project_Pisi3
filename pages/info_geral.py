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
    "Isadora Moraes",
    "Luiz Vinicius"
]

PROJECT_INFO = {
    "Curso":       "Siatemas de Informação",
    "Disciplina":  "Projeto Interdisciplinar para Sistemas de Informação III",
    "Período":     "2026.1",
    "Professor":   "Gabriel Alves",
    "Dataset":     "Brasil em Foco — indicadores socioeconômicos brasileiros",
}

CONTEXTO = (
    "O projeto Brasil em Foco tem como propósito central investigar e visualizar "
    "indicadores socioeconômicos do território brasileiro, abrangendo múltiplas "
    "dimensões — desenvolvimento humano, mobilidade urbana, tecnologia, agronegócio "
    "e turismo. A partir de dados públicos oficiais, buscamos revelar padrões, "
    "disparidades regionais e tendências que possam subsidiar análises críticas "
    "sobre a realidade brasileira."
)

OBJETIVO_DISCIPLINA = (
    "A disciplina de Análise de Dados visa capacitar os alunos a coletar, limpar, "
    "explorar e comunicar insights a partir de conjuntos de dados reais, utilizando "
    "ferramentas modernas de visualização e análise estatística."
)

OBJETIVO_DASHBOARD = (
    "Este dashboard tem como objetivo explorar e visualizar os principais aspectos "
    "dos dados analisados, oferecendo insights iniciais sobre distribuições, "
    "correlações e outliers presentes no dataset Brasil em Foco, auxiliando na "
    "compreensão da realidade socioeconômica brasileira de forma interativa e acessível."
)

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
                    "👋  Bem-vindo ao Dashboard",
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
                    "👥  Integrantes da Equipe",
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
                    "📋  Dados do Projeto",
                    [_info_row(k, v) for k, v in PROJECT_INFO.items()],
                    anim="fade-up fade-up-3",
                ),
            ],
        ),

        # ── Contexto ──
        _section(
            "🗺️  Contexto Geral do Projeto",
            [html.P(CONTEXTO, className="info-value", style={"lineHeight": "1.75"})],
            anim="fade-up fade-up-3",
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
                    "🎓  Objetivo da Disciplina",
                    [html.P(OBJETIVO_DISCIPLINA, className="info-value", style={"lineHeight": "1.75"})],
                    anim="fade-up fade-up-4",
                ),
                _section(
                    "📊  Objetivo do Dashboard",
                    [html.P(OBJETIVO_DASHBOARD, className="info-value", style={"lineHeight": "1.75"})],
                    anim="fade-up fade-up-5",
                ),
            ],
        ),
    ],
)
