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
_beds_tot    = int(DF["BEDS"].sum())
_agro_total  = DF["GVA_AGROPEC"].sum()
_pressao_media = DF["indice_pressao_turistica"].mean()
_infra_media = DF["indice_infraestrutura"].mean()
_joia_media = DF["potencial_joia_escondida"].mean()
_moderniz_media = DF["indice_modernizacao"].mean()
_diversidade_media = DF["indice_diversidade_economica"].mean()

METRICS_PAIS = [
    dict(icon="fa-solid fa-gem",           label="Potencial Joia Escondida",  value=f"{_joia_media:.0f}",          sub="Média nacional",                    color="purple"),
    dict(icon="fa-solid fa-gauge-high",    label="Pressão Turística Média",   value=f"{_pressao_media:.0f}",        sub="Índice 0-100",                      color="red"),
    dict(icon="fa-solid fa-building",      label="Infraestrutura Média",      value=f"{_infra_media:.0f}",         sub="Índice 0-100",                      color="navy"),
    dict(icon="fa-solid fa-star",          label="IDH Médio",                 value=f"{_idh_medio:.3f}",           sub="Média nacional (IDHM)",             color="blue"),
    dict(icon="fa-solid fa-sitemap",       label="Diversidade Econômica",     value=f"{_diversidade_media:.0f}",   sub="Média nacional",                    color="orange"),
    dict(icon="fa-solid fa-people-group",  label="População Estimada",        value=f"{_total_pop/1e6:.0f} mi",    sub="Soma municípios dataset",           color="navy"),
    dict(icon="fa-solid fa-wifi",          label="Modernização Média",        value=f"{_moderniz_media:.0f}",      sub="Índice 0-100",                      color="teal"),
    dict(icon="fa-solid fa-hotel",         label="Hotéis Cadastrados",        value=f"{_hotels_tot:,}".replace(",","."), sub="Total no dataset",             color="navy"),
    dict(icon="fa-solid fa-bed",           label="Leitos Cadastrados",        value=f"{_beds_tot:,}".replace(",","."), sub="Total no dataset",               color="navy"),
    dict(icon="fa-solid fa-car",           label="Cidades com Uber",          value=f"{_uber_cities} cidades",     sub="Cobertura de mobilidade",           color="teal"),
    dict(icon="fa-solid fa-laptop",        label="Empresas de Tech",          value=f"{_tech_total:,}".replace(",","."), sub="CNAE J — Tecnologia",          color="gold"),
]


# ─── Helpers ──────────────────────────────────────────────────────────────

def _tile(icon, label, value, sub, color, pos, total, lbl_rank, i):
    ranking = dict(pos=pos, total=total, label=lbl_rank) if pos and total else None
    return create_metric_tile(
        icon=icon, label=label, value=value, sub=sub, color=color,
        ranking=ranking, anim_class=ANIM_CLASSES[i % len(ANIM_CLASSES)],
    )


def _tiles_from_specs(specs):
    return [
        _tile(ic, lb, vl, sb, co, pos, tot, lbl, i)
        for i, (ic, lb, vl, sb, co, pos, tot, lbl) in enumerate(specs)
    ]


def _story_sections(sections, num_cols=4):
    children = []
    for title, tiles in sections:
        children.extend([
            html.Div(
                title,
                className="info-label",
                style={"marginTop": "20px", "marginBottom": "8px"},
            ),
            _grid(tiles, num_cols=num_cols),
        ])
    return html.Div(children)


def _as_float(value) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


def _rank_band(pos: int | None, total: int | None, higher_label: str, middle_label: str, lower_label: str) -> str:
    if not pos or not total:
        return middle_label
    rel = pos / total
    if rel <= 0.33:
        return higher_label
    if rel >= 0.67:
        return lower_label
    return middle_label


def _geo_profile(s: dict, total: int) -> str:
    idh_top = s["rank_idh"] / total <= 0.33
    infra_top = s["rank_infra"] / total <= 0.33
    joia_top = s["rank_joia"] / total <= 0.33
    infra_low = s["rank_infra"] / total >= 0.67
    pressure_top = s["rank_pressao"] / total <= 0.33 and _as_float(s["pressao_turistica"]) > 0

    if idh_top and infra_top:
        return "base consolidada para turismo"
    if joia_top and not pressure_top:
        return "oportunidade de desenvolvimento turístico"
    if idh_top and infra_low:
        return "qualidade de vida com infraestrutura turística ainda baixa"
    if infra_top and not idh_top:
        return "estrutura relevante, mas com alerta social"
    return "perfil intermediário que pede comparação com seus pares"


def _city_profile(s: dict) -> str:
    total = s["n_cities"]
    idh_top = s["rank_idh"] / total <= 0.30
    infra_top = s["rank_infra"] / total <= 0.20
    joia_top = s["rank_joia"] / total <= 0.20
    infra_low = s["rank_infra"] / total >= 0.70
    pressure_top = s["rank_pressao"] / total <= 0.10 and _as_float(s["pressao_turistica"]) > 0

    if idh_top and infra_top:
        return "destino com base consolidada"
    if joia_top and not pressure_top:
        return "oportunidade escondida"
    if idh_top and infra_low:
        return "qualidade de vida com infraestrutura turística baixa"
    if infra_top and not idh_top:
        return "estrutura turística com vulnerabilidade social"
    return "perfil intermediário"


def _diagnosis_panel(text: str, detail: str) -> html.Div:
    return html.Div(
        style={
            "marginTop": "18px",
            "padding": "4px 0 4px 14px",
            "borderLeft": "4px solid #D1495B",
        },
        children=[
            html.Div("Leitura diagnóstica", className="info-label", style={"marginBottom": "4px"}),
            html.Div(text, className="info-value", style={"lineHeight": "1.65", "fontWeight": "500"}),
            html.Div(detail, className="info-value", style={"lineHeight": "1.6", "marginTop": "4px", "fontSize": "0.92rem"}),
        ],
    )


def _diagnosis_pais() -> html.Div:
    text = (
        f"O conjunto nacional combina IDH médio {_idh_medio:.3f}, pressão turística média "
        f"{_pressao_media:.1f} e infraestrutura média {_infra_media:.1f}. A leitura principal "
        "é separar municípios consolidados daqueles com qualidade de vida e baixa pressão turística."
    )
    detail = (
        "Use os filtros de Região, Estado e Cidade para transformar o panorama nacional em diagnóstico "
        "de oportunidade, consolidação ou carência de base turística."
    )
    return _diagnosis_panel(text, detail)


def _diagnosis_region(region: str, s: dict) -> html.Div:
    total = 5
    profile = _geo_profile(s, total)
    idh_band = _rank_band(s["rank_idh"], total, "IDH entre os mais altos", "IDH intermediário", "IDH entre os mais baixos")
    infra_band = _rank_band(s["rank_infra"], total, "infraestrutura entre as mais altas", "infraestrutura intermediária", "infraestrutura entre as mais baixas")
    text = (
        f"{region} combina IDH médio {s['idh']}, pressão turística {s['pressao_turistica']} "
        f"e infraestrutura {s['infraestrutura']}. Perfil provável: {profile}."
    )
    detail = f"Leitura de apoio: {idh_band} e {infra_band} no comparativo entre macrorregiões."
    return _diagnosis_panel(text, detail)


def _diagnosis_state(state: str, s: dict) -> html.Div:
    total = s["n_states"]
    profile = _geo_profile(s, total)
    idh_band = _rank_band(s["rank_idh"], total, "IDH no grupo superior", "IDH intermediário", "IDH no grupo inferior")
    infra_band = _rank_band(s["rank_infra"], total, "infraestrutura no grupo superior", "infraestrutura intermediária", "infraestrutura no grupo inferior")
    text = (
        f"{state} combina IDH médio {s['idh']}, pressão turística {s['pressao_turistica']} "
        f"e infraestrutura {s['infraestrutura']}. Perfil provável: {profile}."
    )
    detail = f"Leitura de apoio: {idh_band} e {infra_band} no comparativo entre estados."
    return _diagnosis_panel(text, detail)


def _diagnosis_city(city: str, s: dict) -> html.Div:
    profile = _city_profile(s)
    text = (
        f"{city} combina IDHM {s['idh']}, pressão turística {s['pressao_turistica']} "
        f"({s['pressao_cat']}) e infraestrutura {s['infraestrutura']}. Perfil provável: {profile}."
    )
    detail = (
        f"O diagnóstico cruza desenvolvimento humano, estrutura turística e potencial de joia escondida. "
        f"Quadrante atual: {s['quadrante']}."
    )
    return _diagnosis_panel(text, detail)


def _build_pais_grid():
    tiles = [
        create_metric_tile(
            icon=m["icon"], label=m["label"], value=m["value"],
            sub=m["sub"], color=m["color"],
            anim_class=ANIM_CLASSES[i % len(ANIM_CLASSES)],
        )
        for i, m in enumerate(METRICS_PAIS)
    ]
    sections = [
        ("Diagnóstico central", tiles[:4]),
        ("Contexto do território", tiles[4:7]),
        ("Sinais de suporte", tiles[7:]),
    ]
    return html.Div([_diagnosis_pais(), _story_sections(sections, num_cols=3)])


def _build_region_grid(region: str):
    s = region_summary(region)
    n = 5  # total de regiões
    core_specs = [
        ("fa-solid fa-gem",          "Potencial Joia Escondida", s["joia_potencial"],   "Índice 0-100",                "purple", s["rank_joia"],    n, "regiões"),
        ("fa-solid fa-gauge-high",   "Pressão Turística",       s["pressao_turistica"], "Nível de pressão",            "red",    s["rank_pressao"], n, "regiões"),
        ("fa-solid fa-building",     "Infraestrutura Turística",s["infraestrutura"],    "Índice 0-100",                "navy",   s["rank_infra"],   n, "regiões"),
        ("fa-solid fa-star",         "IDH Médio",               s["idh"],               "IDHM da região",              "blue",   s["rank_idh"],     n, "regiões"),
    ]
    context_specs = [
        ("fa-solid fa-sitemap",      "Diversidade Econômica",   s["diversidade_econ"],  "Índice 0-100",                "orange", s["rank_diversid"], n, "regiões"),
        ("fa-solid fa-people-group", "População",               s["pop"],               f"{s['municipios']} municípios","navy",   None, None, None),
        ("fa-solid fa-wifi",         "Modernização",            s["modernizacao"],      "Índice 0-100",                "teal",   s["rank_moderniz"], n, "regiões"),
    ]
    support_specs = [
        ("fa-solid fa-hotel",        "Hotéis",                  s["hoteis"],            "Total de hospedagem",         "navy",   s["rank_hotel"],    n, "regiões"),
        ("fa-solid fa-bed",          "Leitos",                  s["leitos"],            "Capacidade hospedagem",       "navy",   s["rank_leitos"],   n, "regiões"),
        ("fa-solid fa-car",          "Municípios com Uber",     s["uber"],              "Sinal de mobilidade",         "teal",   s["rank_uber"],     n, "regiões"),
        ("fa-solid fa-laptop",       "Empresas de Tech",        s["tech"],              "CNAE J",                      "gold",   s["rank_tech"],     n, "regiões"),
    ]
    sections = [
        ("Diagnóstico central", _tiles_from_specs(core_specs)),
        ("Contexto do território", _tiles_from_specs(context_specs)),
        ("Sinais de suporte", _tiles_from_specs(support_specs)),
    ]
    return html.Div([_diagnosis_region(region, s), _story_sections(sections, num_cols=4)])


def _build_state_grid(state: str):
    s = state_summary(state)
    n = s["n_states"]
    core_specs = [
        ("fa-solid fa-gem",          "Potencial Joia Escondida", s["joia_potencial"],   "Índice 0-100",                "purple", s["rank_joia"],    n, "estados"),
        ("fa-solid fa-gauge-high",   "Pressão Turística",       s["pressao_turistica"], "Nível de pressão",            "red",    s["rank_pressao"], n, "estados"),
        ("fa-solid fa-building",     "Infraestrutura Turística",s["infraestrutura"],    "Índice 0-100",                "navy",   s["rank_infra"],   n, "estados"),
        ("fa-solid fa-star",         "IDH Médio",               s["idh"],               "IDHM estadual",               "blue",   s["rank_idh"],     n, "estados"),
    ]
    context_specs = [
        ("fa-solid fa-sitemap",      "Diversidade Econômica",   s["diversidade_econ"],  "Índice 0-100",                "orange", s["rank_diversid"], n, "estados"),
        ("fa-solid fa-people-group", "População",               s["pop"],               f"{s['municipios']} municípios","navy",   None, None, None),
        ("fa-solid fa-wifi",         "Modernização",            s["modernizacao"],      "Índice 0-100",                "teal",   s["rank_moderniz"], n, "estados"),
    ]
    support_specs = [
        ("fa-solid fa-hotel",        "Hotéis",                  s["hoteis"],            "Total de hospedagem",         "navy",   s["rank_hotel"],    n, "estados"),
        ("fa-solid fa-bed",          "Leitos",                  s["leitos"],            "Capacidade hospedagem",       "navy",   s["rank_leitos"],   n, "estados"),
        ("fa-solid fa-car",          "Municípios com Uber",     s["uber"],              "Sinal de mobilidade",         "teal",   s["rank_uber"],     n, "estados"),
        ("fa-solid fa-laptop",       "Empresas de Tech",        s["tech"],              "CNAE J",                      "gold",   s["rank_tech"],     n, "estados"),
    ]
    sections = [
        ("Diagnóstico central", _tiles_from_specs(core_specs)),
        ("Contexto do território", _tiles_from_specs(context_specs)),
        ("Sinais de suporte", _tiles_from_specs(support_specs)),
    ]
    return html.Div([_diagnosis_state(state, s), _story_sections(sections, num_cols=4)])


def _build_city_grid(city: str):
    s = city_summary(city)
    if not s:
        return html.Div("Cidade não encontrada.", style={"padding": "24px", "color": "#888"})
    n = s["n_cities"]
    
    core_specs = [
        ("fa-solid fa-gem",          "Potencial Joia Escondida", s["joia_potencial"],   "Índice 0-100",                 "purple", s["rank_joia"],    n, "cidades"),
        ("fa-solid fa-gauge-high",   "Pressão Turística",       s["pressao_turistica"], f"Nível: {s['pressao_cat']}",   "red",    s["rank_pressao"], n, "cidades"),
        ("fa-solid fa-building",     "Infraestrutura Turística",s["infraestrutura"],    "Índice 0-100",                 "navy",   s["rank_infra"],   n, "cidades"),
        ("fa-solid fa-star",         "IDH Municipal",           s["idh"],               f"Estado: {s['state']}",        "blue",   s["rank_idh"],     n, "cidades"),
    ]
    context_specs = [
        ("fa-solid fa-sitemap",      "Diversidade Econômica",   s["diversidade_econ"],  "Índice 0-100",                 "orange", s["rank_diversid"], n, "cidades"),
        ("fa-solid fa-people-group", "População",               s["pop"],               f"Perfil: {s['quadrante']}",    "navy",   None, None, None),
        ("fa-solid fa-suitcase",     "Economia Dominante",      s["economia_dominante"],None,                           "gold",   None, None, None),
        ("fa-solid fa-wifi",         "Modernização/Urbanização",s["modernizacao"],      "Conveniência urbana",          "teal",   s["rank_moderniz"], n, "cidades"),
        ("fa-solid fa-hand-holding-hand", "Acessibilidade",     s["acessibilidade"],    "Turista independente",         "green",  s["rank_acessib"],  n, "cidades"),
    ]
    support_specs = [
        ("fa-solid fa-hotel",        "Hotéis",                  s["hoteis"],            "Meios de hospedagem",          "navy",   s["rank_hotel"],    n, "cidades"),
        ("fa-solid fa-bed",          "Leitos",                  s["leitos"],            "Capacidade hospedagem",        "navy",   s["rank_leitos"],   n, "cidades"),
        ("fa-solid fa-car",          "Mobilidade Urbana",       s["uber"],              "Uber disponível",              "teal",   None, None, None),
        ("fa-solid fa-laptop",       "Densidade Tech",          s["tech"],              "Empresas tecnologia",          "purple", s["rank_tech"],     n, "cidades"),
    ]
    sections = [
        ("Diagnóstico central", _tiles_from_specs(core_specs)),
        ("Contexto do território", _tiles_from_specs(context_specs)),
        ("Sinais de suporte", _tiles_from_specs(support_specs)),
    ]
    return html.Div([_diagnosis_city(city, s), _story_sections(sections, num_cols=4)])


def _grid(tiles, num_cols=3):
    return html.Div(
        tiles,
        style={
            "display": "grid",
            "gridTemplateColumns": f"repeat({num_cols}, 1fr)",
            "gap": "16px",
            "marginTop": "0",
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
                html.Div("Visão Geral", className="page-title fade-up fade-up-1"),
                html.Div(
                    "Diagnóstico do recorte selecionado: qualidade, infraestrutura, pressão turística e oportunidade",
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
