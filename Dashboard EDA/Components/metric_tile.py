"""
components/metric_tile.py
Componente reutilizável de tile de métrica com suporte a ranking.
"""

from dash import html


def create_metric_tile(
    icon: str,
    label: str,
    value: str,
    sub: str = "",
    color: str = "blue",
    ranking: dict | None = None,
    anim_class: str = "fade-up fade-up-1",
) -> html.Div:
    """
    Cria um tile de métrica estilizado.

    Parâmetros
    ----------
    icon       : classe FontAwesome, ex. 'fa-solid fa-star'
    label      : rótulo curto da métrica
    value      : valor principal
    sub        : legenda complementar
    color      : 'blue' | 'gold' | 'green' | 'teal' | 'red' | 'navy'
    ranking    : dict com 'pos', 'total', 'label' para exibir barra de ranking
    anim_class : classes CSS de animação
    """
    children = [
        html.Div(
            html.I(className=icon),
            className="metric-tile-icon",
        ),
        html.Div(label, className="metric-tile-label"),
        html.Div(value, className="metric-tile-value"),
    ]

    if sub:
        children.append(html.Div(sub, className="metric-tile-sub"))

    if ranking:
        pos   = ranking.get("pos", 1)
        total = ranking.get("total", 5)
        rlbl  = ranking.get("label", "ranking")
        pct   = round((1 - (pos - 1) / max(total - 1, 1)) * 100)
        pct_tip = (
            "Percentual derivado só da posição no ranking (1º = 100%, último = 0%), "
            "não do valor numérico do indicador."
        )

        children.append(
            html.Div(
                className="ranking-bar-wrap",
                children=[
                    html.Div(
                        className="ranking-bar-label",
                        children=[
                            html.Span(f"Ranking: {pos}º de {total} ({rlbl})"),
                            html.Span(f"{pct}% pos. relativa", title=pct_tip),
                        ],
                    ),
                    html.Div(
                        className="ranking-bar-track",
                        children=[
                            html.Div(
                                className=f"ranking-bar-fill",
                                style={
                                    "width": f"{pct}%",
                                    "background": _color_hex(color),
                                },
                            )
                        ],
                    ),
                ],
            )
        )

    return html.Div(
        children=children,
        className=f"metric-tile color-{color} {anim_class}",
    )


def _color_hex(color: str) -> str:
    MAP = {
        "blue":   "#4A6CF7",
        "gold":   "#F5A623",
        "green":  "#27AE60",
        "teal":   "#1ABC9C",
        "red":    "#E74C3C",
        "navy":   "#1A2B6B",
        "orange": "#E67E22",
        "purple": "#9B59B6",
    }
    return MAP.get(color, "#4A6CF7")
