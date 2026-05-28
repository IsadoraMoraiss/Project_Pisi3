"""
pages/visao_geral.py
Página de Visão Geral com filtros por País / Região / Estado / Cidade.
Integrada com dataset real BRAZIL_CITIES.csv via data_loader.
"""

from dash import html, dcc, Input, Output, callback, ctx
from Components.metric_tile import create_metric_tile
from data_loader import (
    ALL_REGIONS, ALL_STATES, ALL_CITIES,
    region_summary, state_summary, city_summary,
    get_states_for_region, get_cities_for_state, DF,
)

# ─── Constantes ──────────────────────────────────────────────────────────

TABS = ["País", "Região", "Estado", "Cidade"]

ANIM_CLASSES = [
    "fade-up fade-up-1", "fade-up fade-up-2", "fade-up fade-up-3",
    "fade-up fade-up-4", "fade-up fade-up-5", "fade-up fade-up-1",
    "fade-up fade-up-2", "fade-up fade-up-3", "fade-up fade-up-4",
    "fade-up fade-up-5", "fade-up fade-up-1", "fade-up fade-up-2",
]

# Métricas nível País — valores reais do dataset
_total_pop   = DF["ESTIMATED_POP"].sum()
_idh_medio   = DF["IDHM"].mean()
_uber_cities = int(DF["UBER"].sum())
_tech_total  = int(DF["COMP_J"].sum())
_hotels_tot  = int(DF["HOTELS"].sum())
_agro_total  = DF["GVA_AGROPEC"].sum()
_pressao_media = DF["indice_pressao_turistica"].mean()
_infra_media = DF["indice_infraestrutura"].mean()
_joia_media = DF["potencial_joia_escondida"].mean()
_moderniz_media = DF["indice_modernizacao"].mean()

METRICS_PAIS = [
    dict(icon="fa-solid fa-gauge-high",    label="Pressão Turística Média",   value=f"{_pressao_media:.0f}",        sub="Índice 0-100",                      color="red"),
    dict(icon="fa-solid fa-building",      label="Infraestrutura Média",      value=f"{_infra_media:.0f}",         sub="Índice 0-100",                      color="navy"),
    dict(icon="fa-solid fa-gem",           label="Potencial Joia Escondida",  value=f"{_joia_media:.0f}",          sub="Média nacional",                    color="purple"),
    dict(icon="fa-solid fa-star",          label="IDH Médio",                 value=f"{_idh_medio:.3f}",           sub="Média nacional (IDHM)",             color="blue"),
    dict(icon="fa-solid fa-wifi",          label="Modernização Média",        value=f"{_moderniz_media:.0f}",      sub="Índice 0-100",                      color="teal"),
    dict(icon="fa-solid fa-car",           label="Cidades com Uber",          value=f"{_uber_cities} cidades",     sub="Cobertura de mobilidade",           color="teal"),
    dict(icon="fa-solid fa-laptop",        label="Empresas de Tech",          value=f"{_tech_total:,}".replace(",","."), sub="CNAE J — Tecnologia",          color="gold"),
    dict(icon="fa-solid fa-hotel",         label="Hotéis Cadastrados",        value=f"{_hotels_tot:,}".replace(",","."), sub="Total no dataset",             color="navy"),
    dict(icon="fa-solid fa-people-group",  label="População Estimada",        value=f"{_total_pop/1e6:.0f} mi",    sub="Soma municípios dataset",           color="red"),
]


# ─── Helpers ──────────────────────────────────────────────────────────────

def _tile(icon, label, value, sub, color, pos, total, lbl_rank, i):
    ranking = dict(pos=pos, total=total, label=lbl_rank) if pos and total else None
    return create_metric_tile(
        icon=icon, label=label, value=value, sub=sub, color=color,
        ranking=ranking, anim_class=ANIM_CLASSES[i % len(ANIM_CLASSES)],
    )


def _build_pais_grid():
    tiles = [
        create_metric_tile(
            icon=m["icon"], label=m["label"], value=m["value"],
            sub=m["sub"], color=m["color"],
            anim_class=ANIM_CLASSES[i % len(ANIM_CLASSES)],
        )
        for i, m in enumerate(METRICS_PAIS)
    ]
    return _grid(tiles, num_cols=3)


def _build_region_grid(region: str):
    s = region_summary(region)
    n = 5  # total de regiões
    specs = [
        ("fa-solid fa-gauge-high",   "Pressão Turística",      s["pressao_turistica"], "Nível de pressão",            "red",   s["rank_pressao"], n, "regiões"),
        ("fa-solid fa-building",     "Infraestrutura Turística",s["infraestrutura"],    "Índice 0-100",                "navy",  s["rank_infra"],   n, "regiões"),
        ("fa-solid fa-gem",          "Potencial Joia Escondida",s["joia_potencial"],   "Índice 0-100",                "purple",s["rank_joia"],    n, "regiões"),
        ("fa-solid fa-star",         "IDH Médio",               s["idh"],               "IDHM da região",              "blue",  s["rank_idh"],     n, "regiões"),
        ("fa-solid fa-wifi",         "Modernização",           s["modernizacao"],      "Índice 0-100",                "teal",  s["rank_moderniz"],n, "regiões"),
        ("fa-solid fa-sitemap",      "Diversidade Econômica",  s["diversidade_econ"],  "Índice 0-100",                "orange",s["rank_diversid"],n, "regiões"),
        ("fa-solid fa-laptop",       "Empresas de Tech",       s["tech"],              "CNAE J",                      "gold",  s["rank_tech"],    n, "regiões"),
        ("fa-solid fa-hotel",        "Hotéis",                 s["hoteis"],            "Total de hospedagem",         "navy",  s["rank_hotel"],   n, "regiões"),
        ("fa-solid fa-car",          "Cidades c/ Uber",        s["uber"],              "Cobertura Uber",              "teal",  s["rank_uber"],    n, "regiões"),
        ("fa-solid fa-people-group", "População",              s["pop"],               f"{s['municipios']} municípios","red",  None, None, None),
    ]
    tiles = [
        _tile(ic, lb, vl, sb, co, pos, tot, lbl, i)
        for i, (ic, lb, vl, sb, co, pos, tot, lbl) in enumerate(specs)
    ]
    return _grid(tiles, num_cols=4)


def _build_state_grid(state: str):
    s = state_summary(state)
    n = s["n_states"]
    specs = [
        ("fa-solid fa-gauge-high",   "Pressão Turística",      s["pressao_turistica"], "Nível de pressão",            "red",   s["rank_pressao"], n, "estados"),
        ("fa-solid fa-building",     "Infraestrutura Turística",s["infraestrutura"],    "Índice 0-100",                "navy",  s["rank_infra"],   n, "estados"),
        ("fa-solid fa-gem",          "Potencial Joia Escondida",s["joia_potencial"],   "Índice 0-100",                "purple",s["rank_joia"],    n, "estados"),
        ("fa-solid fa-star",         "IDH Médio",               s["idh"],               "IDHM estadual",               "blue",  s["rank_idh"],     n, "estados"),
        ("fa-solid fa-wifi",         "Modernização",           s["modernizacao"],      "Índice 0-100",                "teal",  s["rank_moderniz"],n, "estados"),
        ("fa-solid fa-sitemap",      "Diversidade Econômica",  s["diversidade_econ"],  "Índice 0-100",                "orange",s["rank_diversid"],n, "estados"),
        ("fa-solid fa-laptop",       "Empresas de Tech",       s["tech"],              "CNAE J",                      "gold",  s["rank_tech"],    n, "estados"),
        ("fa-solid fa-hotel",        "Hotéis",                 s["hoteis"],            "Total de hospedagem",         "navy",  s["rank_hotel"],   n, "estados"),
        ("fa-solid fa-car",          "Cidades c/ Uber",        s["uber"],              "Cobertura Uber",              "teal",  s["rank_uber"],    n, "estados"),
        ("fa-solid fa-people-group", "População",              s["pop"],               f"{s['municipios']} municípios","red",  None, None, None),
    ]
    tiles = [
        _tile(ic, lb, vl, sb, co, pos, tot, lbl, i)
        for i, (ic, lb, vl, sb, co, pos, tot, lbl) in enumerate(specs)
    ]
    return _grid(tiles, num_cols=4)


def _build_city_grid(city: str):
    s = city_summary(city)
    if not s:
        return html.Div("Cidade não encontrada.", style={"padding": "24px", "color": "#888"})
    n = s["n_cities"]
    
    # Especificações dos cards (sem ranking onde não é relevante)
    specs = [
        # Linha 1: Indicadores PRINCIPAIS 🔥
        ("fa-solid fa-gauge-high",   "Pressão Turística",      s["pressao_turistica"], f"Nível: {s['pressao_cat']}", "red",   s["rank_pressao"], n, "cidades"),
        ("fa-solid fa-building",     "Infraestrutura Turística",s["infraestrutura"],    "Índice 0-100",                 "navy",  s["rank_infra"],   n, "cidades"),
        ("fa-solid fa-gem",          "Potencial Joia Escondida",s["joia_potencial"],   "Índice 0-100",                 "purple", s["rank_joia"], n, "cidades"),
        
        # Linha 2: Desenvolvimento & Qualidade de Vida
        ("fa-solid fa-star",         "IDH Municipal",          s["idh"],               f"Estado: {s['state']}",        "blue",  s["rank_idh"],     n, "cidades"),
        ("fa-solid fa-wifi",         "Modernização/Urbanização",s["modernizacao"],     "Conveniência urbana",          "teal",  s["rank_moderniz"],n, "cidades"),
        ("fa-solid fa-hand-holding-hand", "Acessibilidade",   s["acessibilidade"],    "Turista independente",         "green", s["rank_acessib"], n, "cidades"),
        
        # Linha 3: Economia & Oportunidades
        ("fa-solid fa-suitcase",     "Economia Dominante",     s["economia_dominante"],None,                           "gold",  None, None, None),
        ("fa-solid fa-sitemap",      "Diversidade Econômica",  s["diversidade_econ"],  "Índice 0-100",                 "orange", s["rank_diversid"],n, "cidades"),
        ("fa-solid fa-laptop",       "Densidade Tech",         s["tech"],              "Empresas tecnologia",          "purple", s["rank_tech"],   n, "cidades"),
        
        # Linha 4: Dados Factuais
        ("fa-solid fa-hotel",        "Hotéis",                 s["hoteis"],            "Meios de hospedagem",          "navy",  s["rank_hotel"],  n, "cidades"),
        ("fa-solid fa-car",          "Mobilidade Urbana",      s["uber"],              "Cobertura Uber",               "teal",  None, None, None),
        ("fa-solid fa-people-group", "População",              s["pop"],               f"Perfil: {s['quadrante']}",    "red",   None, None, None),
    ]
    tiles = [
        _tile(ic, lb, vl, sb, co, pos, tot, lbl, i)
        for i, (ic, lb, vl, sb, co, pos, tot, lbl) in enumerate(specs)
    ]
    return _grid(tiles, num_cols=4)


def _grid(tiles, num_cols=3):
    return html.Div(
        tiles,
        style={
            "display": "grid",
            "gridTemplateColumns": f"repeat({num_cols}, 1fr)",
            "gap": "16px",
            "marginTop": "20px",
        },
    )


def _tab_buttons():
    return html.Div(
        [html.Button(t, id=f"tab-vg-{t.lower()}", className="tab-btn", n_clicks=0) for t in TABS],
        className="tab-strip",
    )


def _dropdown_regiao():
    return html.Div(
        id="vg-filter-regiao",
        style={"marginTop": "16px", "display": "none"},
        children=[
            html.Label("Selecione a Região:", className="info-label", style={"marginBottom": "6px", "display": "block"}),
            dcc.Dropdown(
                id="dd-regiao",
                options=[{"label": r, "value": r} for r in ALL_REGIONS],
                value=ALL_REGIONS[0],
                clearable=False,
                style={"fontFamily": "DM Sans, sans-serif"},
            ),
        ],
    )


def _dropdown_estado():
    return html.Div(
        id="vg-filter-estado",
        style={"marginTop": "16px", "display": "none"},
        children=[
            html.Label("Selecione o Estado:", className="info-label", style={"marginBottom": "6px", "display": "block"}),
            dcc.Dropdown(
                id="dd-estado",
                options=[{"label": s, "value": s} for s in ALL_STATES],
                value=ALL_STATES[0],
                clearable=False,
                style={"fontFamily": "DM Sans, sans-serif"},
            ),
        ],
    )


def _dropdown_cidade():
    return html.Div(
        id="vg-filter-cidade",
        style={"marginTop": "16px", "display": "none"},
        children=[
            html.Label("Selecione a Cidade:", className="info-label", style={"marginBottom": "6px", "display": "block"}),
            dcc.Dropdown(
                id="dd-cidade",
                options=[{"label": c, "value": c} for c in ALL_CITIES],
                value="Recife",
                clearable=False,
                style={"fontFamily": "DM Sans, sans-serif"},
            ),
        ],
    )


# ─── Layout ───────────────────────────────────────────────────────────────

layout = html.Div(
    children=[
        html.Div(
            style={"marginBottom": "28px"},
            children=[
                html.Div("🌎  Visão Geral", className="page-title fade-up fade-up-1"),
                html.Div(
                    "Indicadores socioeconômicos reais por recorte geográfico",
                    className="page-subtitle fade-up fade-up-1",
                ),
            ],
        ),
        html.Div(
            className="dash-card fade-up fade-up-2",
            children=[
                _tab_buttons(),
                _dropdown_regiao(),
                _dropdown_estado(),
                _dropdown_cidade(),
                html.Div(id="vg-metric-grid"),
            ],
        ),
    ]
)


# ─── Callbacks ─────────────────────────────────────────────────────────────

TAB_IDS  = ["tab-vg-país", "tab-vg-região", "tab-vg-estado", "tab-vg-cidade"]
TAB_MAP  = {"tab-vg-país": "País", "tab-vg-região": "Região",
            "tab-vg-estado": "Estado", "tab-vg-cidade": "Cidade"}


@callback(
    Output("vg-metric-grid",   "children"),
    Output("tab-vg-país",      "className"),
    Output("tab-vg-região",    "className"),
    Output("tab-vg-estado",    "className"),
    Output("tab-vg-cidade",    "className"),
    Output("vg-filter-regiao", "style"),
    Output("vg-filter-estado", "style"),
    Output("vg-filter-cidade", "style"),
    Input("tab-vg-país",   "n_clicks"),
    Input("tab-vg-região", "n_clicks"),
    Input("tab-vg-estado", "n_clicks"),
    Input("tab-vg-cidade", "n_clicks"),
    Input("dd-regiao",  "value"),
    Input("dd-estado",  "value"),
    Input("dd-cidade",  "value"),
)
def update_tab(n1, n2, n3, n4, reg_val, est_val, city_val):
    triggered = ctx.triggered_id or "tab-vg-país"

    # Determine active tab
    if triggered in TAB_MAP:
        active_tab = TAB_MAP[triggered]
    else:
        # dropdown changed — keep current tab inferred from which dropdown
        if triggered == "dd-regiao":
            active_tab = "Região"
        elif triggered == "dd-estado":
            active_tab = "Estado"
        elif triggered == "dd-cidade":
            active_tab = "Cidade"
        else:
            active_tab = "País"

    # Tab button classes
    reverse_map = {v: k for k, v in TAB_MAP.items()}
    classes = [
        "tab-btn active" if TAB_MAP[tid] == active_tab else "tab-btn"
        for tid in TAB_IDS
    ]

    # Show / hide dropdowns
    vis  = {"marginTop": "16px", "display": "block"}
    hide = {"marginTop": "16px", "display": "none"}
    show_reg  = vis  if active_tab == "Região"  else hide
    show_est  = vis  if active_tab == "Estado"  else hide
    show_city = vis  if active_tab == "Cidade"  else hide

    # Build metric grid
    if active_tab == "País":
        grid = _build_pais_grid()
    elif active_tab == "Região":
        grid = _build_region_grid(reg_val or ALL_REGIONS[0])
    elif active_tab == "Estado":
        grid = _build_state_grid(est_val or ALL_STATES[0])
    else:
        grid = _build_city_grid(city_val or "Recife")

    return grid, *classes, show_reg, show_est, show_city
