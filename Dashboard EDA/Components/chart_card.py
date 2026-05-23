"""
components/chart_card.py
Wrapper padronizado para gráficos Plotly dentro do dashboard.
"""

from dash import html, dcc
import plotly.graph_objects as go


PLOTLY_CONFIG = dict(
    displayModeBar=True,
    displaylogo=False,
    modeBarButtonsToRemove=["select2d", "lasso2d", "autoScale2d"],
    responsive=True,
)

PLOTLY_LAYOUT_DEFAULTS = dict(
    font_family="DM Sans, sans-serif",
    font_color="#1A2B6B",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=8, r=8, t=16, b=8),
    xaxis=dict(
        gridcolor="#EEF0F8",
        linecolor="#EEF0F8",
        zerolinecolor="#EEF0F8",
    ),
    yaxis=dict(
        gridcolor="#EEF0F8",
        linecolor="#EEF0F8",
        zerolinecolor="#EEF0F8",
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font_size=11,
    ),
    hoverlabel=dict(
        bgcolor="white",
        bordercolor="#E8EBF5",
        font_family="DM Sans, sans-serif",
        font_size=12,
    ),
)


def apply_default_layout(fig: go.Figure) -> go.Figure:
    """Aplica layout padrão do dashboard a qualquer figura Plotly."""
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS)
    return fig


def create_chart_card(
    graph_id: str,
    figure: go.Figure,
    title: str = "",
    description: str = "",
    anim_class: str = "fade-up fade-up-2",
    height: int = 340,
    col_width: str = "100%",
) -> html.Div:
    """
    Encapsula um gráfico Plotly em um card padronizado.

    Parâmetros
    ----------
    graph_id    : id único do componente dcc.Graph
    figure      : objeto go.Figure já montado
    title       : título do gráfico
    description : legenda/descrição
    anim_class  : classes CSS de animação
    height      : altura em px do gráfico
    col_width   : largura CSS do container (ex. '48%', '100%')
    """
    apply_default_layout(figure)

    header_children = []
    if title:
        header_children.append(html.Div(title, className="chart-title"))
    if description:
        header_children.append(html.Div(description, className="chart-desc"))

    return html.Div(
        className=f"chart-wrapper {anim_class}",
        style={"width": col_width},
        children=[
            *header_children,
            dcc.Graph(
                id=graph_id,
                figure=figure,
                config=PLOTLY_CONFIG,
                style={"height": f"{height}px"},
            ),
        ],
    )
