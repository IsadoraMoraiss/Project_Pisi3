"""
Pages/clusterizacao.py
Aba de Clusterização (Aprendizado Não Supervisionado)
Permite agrupar os municípios com base em indicadores selecionados.
"""

import pandas as pd
import numpy as np
import plotly.express as px
from dash import html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from data_loader import DF
from Components.chart_card import PLOTLY_LAYOUT_DEFAULTS, STORY_COLORS

# Variáveis disponíveis para clusterização
AVAILABLE_FEATURES = {
    "IDHM": "IDHM",
    "GDP_CAPITA": "PIB per Capita",
    "ESTIMATED_POP": "População Estimada",
    "HOTELS": "Número de Hotéis",
    "BEDS": "Número de Leitos",
    "COMP_J": "Empresas de Tecnologia",
    "GVA_AGROPEC": "PIB Agropecuária",
    "indice_infraestrutura": "Índice de Infraestrutura",
    "indice_modernizacao": "Índice de Modernização",
    "indice_acessibilidade": "Índice de Acessibilidade",
}

def _card_container(*children, extra_style=None):
    base = {
        "background": "white",
        "borderRadius": "12px",
        "padding": "24px",
        "boxShadow": "0 2px 12px rgba(0,0,0,0.07)",
        "marginBottom": "24px",
    }
    if extra_style:
        base.update(extra_style)
    return html.Div(children, style=base)

layout = html.Div(
    className="fade-up fade-up-1",
    children=[
        html.Div(
            style={"marginBottom": "32px"},
            children=[
                html.H2(
                    [
                        html.I(className="fa-solid fa-project-diagram", style={"marginRight": "12px", "color": "#4A6CF7"}),
                        "Clusterização de Municípios",
                    ],
                    style={"fontWeight": "700", "color": STORY_COLORS["text"], "marginBottom": "6px"},
                ),
                html.P(
                    "Agrupe os municípios brasileiros por similaridade utilizando o algoritmo K-Means. "
                    "Selecione as variáveis e o número de grupos (clusters) para descobrir padrões ocultos.",
                    style={"color": STORY_COLORS["muted"], "fontSize": "0.95rem"},
                ),
            ],
        ),

        html.Div(
            style={"display": "flex", "gap": "24px", "flexWrap": "wrap", "marginBottom": "24px"},
            children=[
                _card_container(
                    html.Div([
                        html.I(className="fa-solid fa-sliders", style={"marginRight": "8px", "color": "#4A6CF7"}),
                        html.Span("Parâmetros do Modelo", style={"fontWeight": "bold"})
                    ], style={"marginBottom": "16px", "fontSize": "1rem"}),
                    
                    html.Label("Selecione as Variáveis (mínimo 2):", style={"fontWeight": "600", "fontSize": "0.85rem"}),
                    dcc.Dropdown(
                        id="drop-cluster-features",
                        options=[{"label": v, "value": k} for k, v in AVAILABLE_FEATURES.items()],
                        value=["IDHM", "GDP_CAPITA", "HOTELS"],
                        multi=True,
                        style={"marginBottom": "16px"}
                    ),

                    html.Label("Número de Clusters (k):", style={"fontWeight": "600", "fontSize": "0.85rem"}),
                    dcc.Slider(
                        id="slider-cluster-k",
                        min=2, max=10, step=1, value=4,
                        marks={i: str(i) for i in range(2, 11)},
                        className="mb-3"
                    ),

                    html.Button(
                        "Executar Clusterização",
                        id="btn-cluster",
                        n_clicks=0,
                        style={
                            "width": "100%", "padding": "12px",
                            "background": "#4A6CF7", "color": "white",
                            "border": "none", "borderRadius": "8px",
                            "fontWeight": "bold", "cursor": "pointer",
                        }
                    ),
                    html.Div(id="cluster-alert", style={"marginTop": "16px"}),
                    extra_style={"flex": "0 0 320px"}
                ),

                html.Div(
                    id="cluster-results-container",
                    style={"flex": "1", "minWidth": "300px"},
                    children=[
                        _card_container(
                            html.Div(
                                "Configure os parâmetros e clique em Executar para ver os resultados.",
                                style={"textAlign": "center", "padding": "40px", "color": STORY_COLORS["muted"]}
                            )
                        )
                    ]
                )
            ]
        )
    ]
)

@callback(
    Output("cluster-results-container", "children"),
    Output("cluster-alert", "children"),
    Input("btn-cluster", "n_clicks"),
    State("drop-cluster-features", "value"),
    State("slider-cluster-k", "value"),
    prevent_initial_call=True
)
def run_clustering(n_clicks, features, k):
    if not features or len(features) < 2:
        return no_update, dbc.Alert("Selecione pelo menos 2 variáveis.", color="warning")

    # Filtra dados válidos
    df_cluster = DF[["CITY", "STATE"] + features].dropna()
    if df_cluster.empty:
        return no_update, dbc.Alert("Dados insuficientes para as variáveis selecionadas.", color="danger")

    X = df_cluster[features].copy()
    
    # Alguns valores como PIB per Capita podem ter skewness alta, aplicando log+1 pra estabilizar se necessário
    # Para simplificar, vamos apenas usar StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Roda KMeans
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    df_cluster["Cluster"] = [f"Cluster {c}" for c in clusters]

    # Redução de dimensionalidade para plotar se > 2 features (usaremos as 2 primeiras ou PCA simples)
    if len(features) == 2:
        x_col = features[0]
        y_col = features[1]
    else:
        # Pega as 2 com maior variância
        vars_std = X.std().sort_values(ascending=False)
        x_col = vars_std.index[0]
        y_col = vars_std.index[1]

    # Plot
    fig = px.scatter(
        df_cluster, x=x_col, y=y_col, color="Cluster",
        hover_data=["CITY", "STATE"],
        title=f"Dispersão por Clusters (mostrando {AVAILABLE_FEATURES.get(x_col, x_col)} vs {AVAILABLE_FEATURES.get(y_col, y_col)})",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS)
    fig.update_layout(height=450, margin=dict(l=20, r=20, t=50, b=20))

    # Tabela de médias por cluster
    means = df_cluster.groupby("Cluster")[features].mean().round(2).reset_index()
    # Format the datatable
    table_header = [html.Thead(html.Tr([html.Th(col) for col in means.columns]))]
    rows = []
    for i in range(len(means)):
        row = []
        for col in means.columns:
            row.append(html.Td(str(means.iloc[i][col])))
        rows.append(html.Tr(row))
    table_body = [html.Tbody(rows)]
    table = dbc.Table(table_header + table_body, bordered=True, hover=True, striped=True, size="sm")

    results = html.Div([
        _card_container(dcc.Graph(figure=fig, config={"displayModeBar": False})),
        _card_container(
            html.H5("Médias por Cluster", style={"marginBottom": "16px"}),
            html.Div(table, style={"overflowX": "auto"})
        )
    ])

    return results, ""
