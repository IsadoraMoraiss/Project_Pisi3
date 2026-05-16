"""
Brasil em Foco — Dashboard de Análises Exploratórias
Entry point principal da aplicação.
"""

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

from components.sidebar import create_sidebar
from pages import (
    info_geral,
    visao_geral,
    univariada,
    bivariada,
    outliers,
)

# ─── App Init ────────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap",
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css",
    ],
    suppress_callback_exceptions=True,
    title="Brasil em Foco",
)

server = app.server

# ─── Layout ──────────────────────────────────────────────────────────────────

app.layout = html.Div(
    id="root",
    style={"display": "flex", "minHeight": "100vh", "background": "#F0F2F8"},
    children=[
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="active-page", data="info-geral"),

        # Sidebar fixa
        create_sidebar(),

        # Área de conteúdo
        html.Div(
            id="page-content",
            style={
                "flex": "1",
                "padding": "40px 48px",
                "overflowY": "auto",
                "minHeight": "100vh",
            },
        ),
    ],
)

# ─── Callbacks ────────────────────────────────────────────────────────────────

PAGE_MAP = {
    "info-geral":   info_geral.layout,
    "visao-geral":  visao_geral.layout,
    "univariada":   univariada.layout,
    "bivariada":    bivariada.layout,
    "outliers":     outliers.layout,
}


@app.callback(
    Output("page-content", "children"),
    Output("active-page", "data"),
    Input("nav-info-geral",  "n_clicks"),
    Input("nav-visao-geral", "n_clicks"),
    Input("nav-univariada",  "n_clicks"),
    Input("nav-bivariada",   "n_clicks"),
    Input("nav-outliers",    "n_clicks"),
    State("active-page", "data"),
    prevent_initial_call=False,
)
def render_page(n1, n2, n3, n4, n5, current):
    ctx = dash.callback_context
    if not ctx.triggered or ctx.triggered[0]["value"] is None:
        page = current or "info-geral"
    else:
        btn_id = ctx.triggered[0]["prop_id"].split(".")[0]
        page = btn_id.replace("nav-", "")

    return PAGE_MAP.get(page, info_geral.layout), page


@app.callback(
    Output("nav-info-geral",  "className"),
    Output("nav-visao-geral", "className"),
    Output("nav-univariada",  "className"),
    Output("nav-bivariada",   "className"),
    Output("nav-outliers",    "className"),
    Input("active-page", "data"),
)
def update_nav_active(page):
    base    = "nav-item"
    active  = "nav-item active"
    pages   = ["info-geral", "visao-geral", "univariada", "bivariada", "outliers"]
    return [active if p == page else base for p in pages]


# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=8050)
