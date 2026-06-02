"""
components/chart_card.py
Wrapper padronizado para gráficos Plotly dentro do dashboard.
"""

from dash import html, dcc
import plotly.graph_objects as go


STORY_COLORS = {
    "text": "#243042",
    "muted": "#6B7280",
    "grid": "#E7EAF0",
    "context": "#A0A7B4",
    "accent": "#D1495B",
    "accent_blue": "#2F6BFF",
    "positive": "#2A9D8F",
    "warning": "#E9A23B",
}

STORY_COLORWAY = [
    "#4E79A7",
    "#59A14F",
    "#F28E2B",
    "#E15759",
    "#B07AA1",
    "#76B7B2",
]

PLOTLY_CONFIG = dict(
    displayModeBar=True,
    displaylogo=False,
    modeBarButtonsToRemove=["select2d", "lasso2d", "autoScale2d"],
    responsive=True,
)

PLOTLY_LAYOUT_DEFAULTS = dict(
    font_family="DM Sans, sans-serif",
    font_color=STORY_COLORS["text"],
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    colorway=STORY_COLORWAY,
    margin=dict(l=8, r=8, t=16, b=8),
    xaxis=dict(
        gridcolor=STORY_COLORS["grid"],
        linecolor=STORY_COLORS["grid"],
        zerolinecolor=STORY_COLORS["grid"],
    ),
    yaxis=dict(
        gridcolor=STORY_COLORS["grid"],
        linecolor=STORY_COLORS["grid"],
        zerolinecolor=STORY_COLORS["grid"],
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font_size=11,
        font_color=STORY_COLORS["muted"],
    ),
    hoverlabel=dict(
        bgcolor="white",
        bordercolor="#E8EBF5",
        font=dict(
            family="DM Sans, sans-serif",
            size=12,
            color=STORY_COLORS["text"],
        ),
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
