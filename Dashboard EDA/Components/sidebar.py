"""
components/sidebar.py
Sidebar de navegação lateral do dashboard.
"""

from dash import html


NAV_ITEMS = [
    {
        "id":    "nav-info-geral",
        "icon":  "fa-solid fa-circle-info",
        "label": "Informações Gerais",
        "color": "#4A6CF7",
    },
    {
        "id":    "nav-visao-geral",
        "icon":  "fa-solid fa-earth-americas",
        "label": "Visão Geral",
        "color": "#27AE60",
    },
    {
        "id":    "nav-univariada",
        "icon":  "fa-solid fa-chart-bar",
        "label": "Análise Univariada",
        "color": "#F5A623",
    },
    {
        "id":    "nav-bivariada",
        "icon":  "fa-solid fa-chart-bar",
        "label": "Análise Bi/Multivariada",
        "color": "#1ABC9C",
    },
    {
        "id":    "nav-outliers",
        "icon":  "fa-solid fa-triangle-exclamation",
        "label": "Outliers",
        "color": "#E74C3C",
    },
]


def create_sidebar():
    nav_buttons = []

    for item in NAV_ITEMS:
        nav_buttons.append(
            html.Button(
                id=item["id"],
                className="nav-item",
                n_clicks=0,
                children=[
                    html.Div(
                        html.I(className=item["icon"]),
                        className="nav-icon",
                    ),
                    html.Span(item["label"]),
                ],
            )
        )

    return html.Div(
        id="sidebar",
        children=[
            # ── Logo ──
            html.Div(
                className="sidebar-logo",
                style={"padding": "20px", "textAlign": "center"},
                children=[
                    html.Div(
                        html.Img(
                            src='assets/logo.png',
                            style={"width": "100%", "maxWidth": "180px"}
                        )
                    )
                ],
            ),

            # ── Nav ──
            html.Div(
                "NAVEGAÇÃO",
                className="nav-section-label",
            ),
            html.Div(
                nav_buttons,
                style={"display": "flex", "flexDirection": "column", "gap": "2px"},
            ),

            # ── Footer ──
            html.Div(
                "Brasil em Foco © 2026.1",
                className="sidebar-footer",
            ),
        ],
    )
