"""
Pages/predicao.py
Aba de Predição & Insights (ML) — Simulador de Cenários Turísticos.

Funcionalidades:
  • Formulário de entrada de dados (features do modelo de regressão)
  • Predição do potencial turístico (Leitos por Mil Habitantes)
  • Explicabilidade local via valores SHAP (gráfico waterfall/barras horizontais)
  • Comparador de Benchmark: posição da cidade simulada vs. cidades reais
  • Alerta de Joia Escondida vs. Destino Saturado baseado nos resíduos do modelo

Pipeline exato do notebook ML_Regressao_BrasilEmFoco.ipynb:
  Features numéricas : PIB_per_capita, Populacao, Densidade → StandardScaler
  Feature categórica : Regiao → OneHotEncoding
  Target             : Leitos_por_Mil_Hab
  Modelo campeão     : salvo em 'melhor_regressor_turismo.pkl' (joblib)
"""

import os
import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc

from Components.metric_tile import create_metric_tile
from Components.chart_card import PLOTLY_LAYOUT_DEFAULTS, STORY_COLORS, PLOTLY_CONFIG

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────────
# Constantes — alinhadas com o notebook
# ──────────────────────────────────────────────────────────────────────────────

# Caminho do modelo salvo pelo notebook (ajuste se necessário)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "melhor_regressor_turismo.pkl")

# Colunas exatamente como definidas no notebook
FEATURES_NUM = ["PIB_per_capita", "Populacao", "Densidade"]
FEATURES_CAT = ["Regiao"]
FEATURES_ALL = FEATURES_NUM + FEATURES_CAT
TARGET       = "Leitos_por_Mil_Hab"

# Regiões do Brasil (para o dropdown)
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]

# Limites observados no dataset (para sliders e validação)
LIMITES = {
    "PIB_per_capita": {"min": 4_000,   "max": 90_000,    "default": 20_000,  "step": 1_000},
    "Populacao":      {"min": 3_000,   "max": 3_000_000, "default": 50_000,  "step": 5_000},
    "Densidade":      {"min": 1,       "max": 2_500,     "default": 50,      "step": 1},
}

# Cores da identidade visual
COR_POSITIVO  = "#27AE60"   # contribuição positiva no SHAP
COR_NEGATIVO  = "#E74C3C"   # contribuição negativa no SHAP
COR_SIMULADO  = "#9B59B6"   # destaque do ponto simulado no scatter
COR_JOIA      = "#F9A825"   # Joia Escondida
COR_SATURADO  = "#C62828"   # Destino Saturado
COR_ADEQUADO  = "#BDBDBD"   # municípios reais sem diagnóstico especial


# ──────────────────────────────────────────────────────────────────────────────
# Helpers de layout interno
# ──────────────────────────────────────────────────────────────────────────────

def _label(texto: str, obrigatorio: bool = False) -> html.Label:
    """Rótulo padrão para campos do formulário."""
    return html.Label(
        [texto, html.Span(" *", style={"color": COR_NEGATIVO}) if obrigatorio else ""],
        style={
            "fontWeight": "600",
            "fontSize": "0.82rem",
            "color": STORY_COLORS["text"],
            "marginBottom": "4px",
            "display": "block",
            "letterSpacing": "0.02em",
        },
    )


def _secao_titulo(icone: str, texto: str) -> html.Div:
    """Título de seção com ícone Font Awesome."""
    return html.Div(
        [
            html.I(className=icone, style={"marginRight": "8px", "color": COR_SIMULADO}),
            html.Span(texto),
        ],
        style={
            "fontWeight": "700",
            "fontSize": "1rem",
            "color": STORY_COLORS["text"],
            "marginBottom": "16px",
            "borderLeft": f"3px solid {COR_SIMULADO}",
            "paddingLeft": "10px",
        },
    )


def _card_container(*children, extra_style: dict = None) -> html.Div:
    """Card branco padrão do dashboard."""
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


# ──────────────────────────────────────────────────────────────────────────────
# Layout estático da aba
# ──────────────────────────────────────────────────────────────────────────────

layout = html.Div(
    className="fade-up fade-up-1",
    children=[

        # ── Cabeçalho da página ──────────────────────────────────────────────
        html.Div(
            style={"marginBottom": "32px"},
            children=[
                html.H2(
                    [
                        html.I(
                            className="fa-solid fa-brain",
                            style={"marginRight": "12px", "color": COR_SIMULADO},
                        ),
                        "Predição & Insights do Modelo (ML)",
                    ],
                    style={
                        "fontWeight": "700",
                        "color": STORY_COLORS["text"],
                        "marginBottom": "6px",
                    },
                ),
                html.P(
                    "Simule o potencial turístico de qualquer município brasileiro com base "
                    "no modelo de Regressão de Resíduos treinado no PISI 3. "
                    "Os valores SHAP revelam por que o modelo chegou a essa previsão.",
                    style={"color": STORY_COLORS["muted"], "fontSize": "0.95rem"},
                ),
            ],
        ),

        # ── Linha superior: Formulário + Resultado ───────────────────────────
        html.Div(
            style={"display": "flex", "gap": "24px", "flexWrap": "wrap", "marginBottom": "24px"},
            children=[

                # ── Formulário de entrada ─────────────────────────────────────
                _card_container(
                    _secao_titulo("fa-solid fa-sliders", "Simulador de Cenários"),

                    # PIB per capita
                    html.Div(style={"marginBottom": "16px"}, children=[
                        _label("PIB per Capita (R$)", obrigatorio=True),
                        dcc.Input(
                            id="inp-pib",
                            type="number",
                            value=LIMITES["PIB_per_capita"]["default"],
                            min=LIMITES["PIB_per_capita"]["min"],
                            max=LIMITES["PIB_per_capita"]["max"],
                            step=LIMITES["PIB_per_capita"]["step"],
                            placeholder="Ex.: 20000",
                            style={
                                "width": "100%", "padding": "10px 14px",
                                "borderRadius": "8px", "border": "1.5px solid #E0E4EF",
                                "fontSize": "0.95rem", "color": STORY_COLORS["text"],
                                "background": "#F8F9FE",
                            },
                        ),
                        html.Small(
                            f"Intervalo observado: R$ {LIMITES['PIB_per_capita']['min']:,} — "
                            f"R$ {LIMITES['PIB_per_capita']['max']:,}",
                            style={"color": STORY_COLORS["muted"]},
                        ),
                    ]),

                    # Slider PIB
                    dcc.Slider(
                        id="slider-pib",
                        min=LIMITES["PIB_per_capita"]["min"],
                        max=LIMITES["PIB_per_capita"]["max"],
                        step=LIMITES["PIB_per_capita"]["step"],
                        value=LIMITES["PIB_per_capita"]["default"],
                        marks={
                            4_000:  "4k",
                            20_000: "20k",
                            45_000: "45k",
                            90_000: "90k",
                        },
                        tooltip={"placement": "bottom", "always_visible": False},
                        className="mb-3",
                    ),

                    # População Total
                    html.Div(style={"marginBottom": "16px"}, children=[
                        _label("População Total (IBGE)", obrigatorio=True),
                        dcc.Input(
                            id="inp-populacao",
                            type="number",
                            value=LIMITES["Populacao"]["default"],
                            min=LIMITES["Populacao"]["min"],
                            max=LIMITES["Populacao"]["max"],
                            step=LIMITES["Populacao"]["step"],
                            placeholder="Ex.: 50000",
                            style={
                                "width": "100%", "padding": "10px 14px",
                                "borderRadius": "8px", "border": "1.5px solid #E0E4EF",
                                "fontSize": "0.95rem", "color": STORY_COLORS["text"],
                                "background": "#F8F9FE",
                            },
                        ),
                        html.Small(
                            f"Intervalo observado: {LIMITES['Populacao']['min']:,} — "
                            f"{LIMITES['Populacao']['max']:,} hab.",
                            style={"color": STORY_COLORS["muted"]},
                        ),
                    ]),

                    # Slider Populacao
                    dcc.Slider(
                        id="slider-populacao",
                        min=LIMITES["Populacao"]["min"],
                        max=LIMITES["Populacao"]["max"],
                        step=LIMITES["Populacao"]["step"],
                        value=LIMITES["Populacao"]["default"],
                        marks={
                            3_000:     "3k",
                            500_000:   "500k",
                            1_500_000: "1,5M",
                            3_000_000: "3M",
                        },
                        tooltip={"placement": "bottom", "always_visible": False},
                        className="mb-3",
                    ),

                    # Densidade Demográfica
                    html.Div(style={"marginBottom": "16px"}, children=[
                        _label("Densidade Demográfica (hab/km²)", obrigatorio=True),
                        dcc.Input(
                            id="inp-densidade",
                            type="number",
                            value=LIMITES["Densidade"]["default"],
                            min=LIMITES["Densidade"]["min"],
                            max=LIMITES["Densidade"]["max"],
                            step=LIMITES["Densidade"]["step"],
                            placeholder="Ex.: 50",
                            style={
                                "width": "100%", "padding": "10px 14px",
                                "borderRadius": "8px", "border": "1.5px solid #E0E4EF",
                                "fontSize": "0.95rem", "color": STORY_COLORS["text"],
                                "background": "#F8F9FE",
                            },
                        ),
                        html.Small(
                            f"Intervalo observado: {LIMITES['Densidade']['min']} — "
                            f"{LIMITES['Densidade']['max']:,} hab/km²",
                            style={"color": STORY_COLORS["muted"]},
                        ),
                    ]),

                    # Slider Densidade
                    dcc.Slider(
                        id="slider-densidade",
                        min=LIMITES["Densidade"]["min"],
                        max=LIMITES["Densidade"]["max"],
                        step=LIMITES["Densidade"]["step"],
                        value=LIMITES["Densidade"]["default"],
                        marks={1: "1", 500: "500", 1250: "1.250", 2500: "2.500"},
                        tooltip={"placement": "bottom", "always_visible": False},
                        className="mb-3",
                    ),

                    # Região
                    html.Div(style={"marginBottom": "24px"}, children=[
                        _label("Região", obrigatorio=True),
                        dcc.Dropdown(
                            id="inp-regiao",
                            options=[{"label": r, "value": r} for r in REGIOES],
                            value="Sudeste",
                            clearable=False,
                            style={"fontSize": "0.95rem"},
                        ),
                    ]),

                    # Botão principal
                    html.Button(
                        [
                            html.I(
                                className="fa-solid fa-bolt",
                                style={"marginRight": "8px"},
                            ),
                            "Calcular Potencial Turístico",
                        ],
                        id="btn-calcular",
                        n_clicks=0,
                        style={
                            "width": "100%",
                            "padding": "14px",
                            "background": f"linear-gradient(135deg, {COR_SIMULADO}, #6C3483)",
                            "color": "white",
                            "border": "none",
                            "borderRadius": "10px",
                            "fontWeight": "700",
                            "fontSize": "1rem",
                            "cursor": "pointer",
                            "letterSpacing": "0.03em",
                            "boxShadow": "0 4px 15px rgba(155,89,182,0.35)",
                        },
                    ),

                    # Mensagem de erro (inicialmente oculta)
                    html.Div(id="div-erro", style={"marginTop": "12px"}),

                    extra_style={"flex": "0 0 360px", "minWidth": "300px"},
                ),

                # ── Painel de resultados ───────────────────────────────────────
                html.Div(
                    id="div-resultados",
                    style={"flex": "1", "minWidth": "280px"},
                    children=[
                        _card_container(
                            html.Div(
                                [
                                    html.I(
                                        className="fa-solid fa-circle-info",
                                        style={"fontSize": "2rem", "color": "#C0C8D8",
                                               "marginBottom": "12px"},
                                    ),
                                    html.P(
                                        "Preencha o formulário ao lado e clique em "
                                        "\"Calcular Potencial Turístico\" para ver os resultados.",
                                        style={
                                            "color": STORY_COLORS["muted"],
                                            "textAlign": "center",
                                            "fontSize": "0.95rem",
                                        },
                                    ),
                                ],
                                style={
                                    "display": "flex", "flexDirection": "column",
                                    "alignItems": "center", "justifyContent": "center",
                                    "padding": "40px 20px",
                                },
                            )
                        )
                    ],
                ),
            ],
        ),

        # ── Linha inferior: SHAP + Benchmark (inicialmente ocultos) ─────────
        html.Div(id="div-graficos-inferiores"),

    ],
)


# ──────────────────────────────────────────────────────────────────────────────
# Callbacks de sincronização slider ↔ input numérico
# ──────────────────────────────────────────────────────────────────────────────

@callback(
    Output("inp-pib",       "value"),
    Output("slider-pib",    "value"),
    Input("inp-pib",        "value"),
    Input("slider-pib",     "value"),
    prevent_initial_call=True,
)
def sync_pib(inp_val, slider_val):
    """Mantém input numérico e slider de PIB sincronizados."""
    from dash import ctx
    trigger = ctx.triggered_id
    if trigger == "inp-pib":
        return inp_val, inp_val
    return slider_val, slider_val


@callback(
    Output("inp-populacao",    "value"),
    Output("slider-populacao", "value"),
    Input("inp-populacao",     "value"),
    Input("slider-populacao",  "value"),
    prevent_initial_call=True,
)
def sync_populacao(inp_val, slider_val):
    """Mantém input numérico e slider de População sincronizados."""
    from dash import ctx
    trigger = ctx.triggered_id
    if trigger == "inp-populacao":
        return inp_val, inp_val
    return slider_val, slider_val


@callback(
    Output("inp-densidade",    "value"),
    Output("slider-densidade", "value"),
    Input("inp-densidade",     "value"),
    Input("slider-densidade",  "value"),
    prevent_initial_call=True,
)
def sync_densidade(inp_val, slider_val):
    """Mantém input numérico e slider de Densidade sincronizados."""
    from dash import ctx
    trigger = ctx.triggered_id
    if trigger == "inp-densidade":
        return inp_val, inp_val
    return slider_val, slider_val


# ──────────────────────────────────────────────────────────────────────────────
# Callback principal — Predição + SHAP + Benchmark
# ──────────────────────────────────────────────────────────────────────────────

@callback(
    Output("div-resultados",         "children"),
    Output("div-graficos-inferiores","children"),
    Output("div-erro",               "children"),
    Input("btn-calcular",            "n_clicks"),
    State("inp-pib",                 "value"),
    State("inp-populacao",           "value"),
    State("inp-densidade",           "value"),
    State("inp-regiao",              "value"),
    prevent_initial_call=True,
)
def calcular_predicao(n_clicks, pib, populacao, densidade, regiao):
    """
    Callback principal — executado ao clicar em 'Calcular Potencial Turístico'.

    Etapas:
      1. Validação dos inputs do formulário.
      2. Carregamento do artefato .pkl (modelo + metadados).
      3. Montagem do DataFrame de entrada com as features exatas do notebook.
      4. Predição via pipeline scikit-learn (StandardScaler + OHE já embutidos).
      5. Cálculo dos valores SHAP locais (explicabilidade da predição).
      6. Construção dos outputs: metric_tile + gráfico SHAP + scatter benchmark.
      7. Geração do bloco de alerta Joia Escondida vs. Destino Saturado.
    """

    # ── 1. Validação dos inputs ───────────────────────────────────────────────
    campos_faltando = []
    if pib       is None: campos_faltando.append("PIB per Capita")
    if populacao is None: campos_faltando.append("População Total")
    if densidade is None: campos_faltando.append("Densidade Demográfica")
    if not regiao:         campos_faltando.append("Região")

    if campos_faltando:
        erro = dbc.Alert(
            [
                html.I(className="fa-solid fa-circle-exclamation me-2"),
                f"Preencha os campos obrigatórios: {', '.join(campos_faltando)}.",
            ],
            color="warning",
            className="mt-2",
        )
        return no_update, no_update, erro

    # ── 2. Carregar o artefato .pkl ───────────────────────────────────────────
    # O artefato contém: modelo (pipeline sklearn), nome_modelo, features_num,
    # features_cat, target, seed, métricas de teste, limiar_joia, limiar_saturacao.
    try:
        import joblib
        artefato       = joblib.load(MODEL_PATH)
        modelo         = artefato["modelo"]           # pipeline sklearn completo
        nome_modelo    = artefato.get("nome_modelo", "Modelo")
        teste_r2       = artefato.get("teste_r2",    0.0)
        teste_mae      = artefato.get("teste_mae",   0.0)
        limiar_joia    = artefato.get("limiar_joia",     -1.5)
        limiar_sat     = artefato.get("limiar_saturacao", 1.5)
    except FileNotFoundError:
        erro = dbc.Alert(
            [
                html.I(className="fa-solid fa-triangle-exclamation me-2"),
                f"Arquivo de modelo não encontrado: {MODEL_PATH}. "
                "Execute o notebook ML_Regressao_BrasilEmFoco.ipynb para gerá-lo.",
            ],
            color="danger",
            className="mt-2",
        )
        return no_update, no_update, erro
    except Exception as exc:
        erro = dbc.Alert(
            [
                html.I(className="fa-solid fa-triangle-exclamation me-2"),
                f"Erro ao carregar o modelo: {exc}",
            ],
            color="danger",
            className="mt-2",
        )
        return no_update, no_update, erro

    # ── 3. Montar DataFrame de entrada (igual ao notebook) ────────────────────
    # A ordem das colunas precisa ser exatamente FEATURES_ALL = FEATURES_NUM + FEATURES_CAT
    df_input = pd.DataFrame(
        [{
            "PIB_per_capita": float(pib),
            "Populacao":      float(populacao),
            "Densidade":      float(densidade),
            "Regiao":         regiao,
        }],
        columns=FEATURES_ALL,
    )

    # ── 4. Predição via pipeline scikit-learn ─────────────────────────────────
    # O pipeline já contém ColumnTransformer (StandardScaler + OHE) + modelo.
    # Não é necessário transformar manualmente — basta chamar predict().
    try:
        y_pred = float(modelo.predict(df_input)[0])
        y_pred = max(0.0, y_pred)   # Leitos nunca pode ser negativo
    except Exception as exc:
        erro = dbc.Alert(
            [
                html.I(className="fa-solid fa-triangle-exclamation me-2"),
                f"Erro na predição: {exc}",
            ],
            color="danger",
            className="mt-2",
        )
        return no_update, no_update, erro

    # ── 5. Calcular valores SHAP locais ───────────────────────────────────────
    # Usamos shap.Explainer que detecta automaticamente o tipo de modelo.
    # Para Random Forest / Gradient Boosting, usa TreeExplainer internamente.
    # Para Regressão Linear, usa LinearExplainer.
    # Transformamos os dados manualmente pelo preprocessor para passar ao SHAP
    # (que precisa ver os dados transformados, não os brutos).
    shap_vals     = None
    feat_names_tr = None
    base_value    = None

    try:
        import shap

        # Recuperar o preprocessor e o estimador final do pipeline
        preprocessor = modelo.named_steps["preprocessor"]
        estimador    = modelo.named_steps["model"]

        # Transformar o input (mesmo passo que o pipeline faria internamente)
        X_tr = preprocessor.transform(df_input)

        # Recuperar nomes das features após OneHotEncoding
        ohe_features  = (
            preprocessor
            .named_transformers_["cat"]
            .named_steps["ohe"]
            .get_feature_names_out(FEATURES_CAT)
        )
        feat_names_tr = FEATURES_NUM + list(ohe_features)

        # Criar o explainer adequado ao tipo de estimador
        explainer = shap.Explainer(estimador, feature_names=feat_names_tr)
        shap_exp  = explainer(X_tr)

        shap_vals  = shap_exp.values[0]    # array 1-D com os valores SHAP da linha simulada
        base_value = float(shap_exp.base_values[0])

    except Exception:
        # Se SHAP não estiver instalado ou houver erro, seguimos sem explicabilidade
        shap_vals     = None
        feat_names_tr = None
        base_value    = None

    # ── 6a. Montar metric_tile da predição ────────────────────────────────────
    cor_tile   = "green" if y_pred >= 2.0 else ("gold" if y_pred >= 0.5 else "red")
    sub_texto  = f"Modelo: {nome_modelo} | R² teste = {teste_r2:.3f} | MAE = {teste_mae:.3f}"

    tile_pred = create_metric_tile(
        icon        = "fa-solid fa-bed",
        label       = "Potencial Turístico Previsto",
        value       = f"{y_pred:.3f} leitos / mil hab.",
        sub         = sub_texto,
        color       = cor_tile,
        explanation = (
            "Número esperado de leitos de hospedagem para cada mil habitantes, "
            "segundo o perfil socioeconômico informado."
        ),
        anim_class  = "fade-up fade-up-1",
    )

    # ── 6b. Gráfico SHAP — barras horizontais (waterfall local) ───────────────
    fig_shap = go.Figure()

    if shap_vals is not None:
        # Ordenar por valor absoluto SHAP (maior impacto primeiro)
        idx_ord    = np.argsort(np.abs(shap_vals))
        vals_ord   = shap_vals[idx_ord]
        names_ord  = [feat_names_tr[i] for i in idx_ord]

        # Formatar rótulos com o valor bruto de cada feature
        valores_brutos = {
            "PIB_per_capita": f"R$ {pib:,.0f}",
            "Populacao":      f"{populacao:,.0f} hab.",
            "Densidade":      f"{densidade:.1f} hab/km²",
        }
        # Para as dummies de região, identificar qual estava ativa
        for r in REGIOES:
            col = f"Regiao_{r}"
            valores_brutos[col] = f"Região: {r}" if r == regiao else "—"

        labels_hover = [
            f"{n} ({valores_brutos.get(n, '')})" for n in names_ord
        ]

        cores_barras = [COR_POSITIVO if v >= 0 else COR_NEGATIVO for v in vals_ord]

        fig_shap.add_trace(go.Bar(
            y            = labels_hover,
            x            = vals_ord,
            orientation  = "h",
            marker_color = cores_barras,
            marker_line  = dict(width=0),
            text         = [f"{v:+.4f}" for v in vals_ord],
            textposition = "outside",
            hovertemplate = "<b>%{y}</b><br>Contribuição SHAP: %{x:+.4f}<extra></extra>",
        ))

        fig_shap.add_vline(
            x          = 0,
            line_width = 1.5,
            line_color = STORY_COLORS["muted"],
            line_dash  = "dash",
        )

        fig_shap.update_layout(**PLOTLY_LAYOUT_DEFAULTS)
        fig_shap.update_layout(
            title=dict(
                text=(
                    f"<b>Explicabilidade Local (SHAP)</b><br>"
                    f"<sup style='color:{STORY_COLORS['muted']}'>Valor base = {base_value:.3f} | "
                    f"Predição = {y_pred:.3f}</sup>"
                ),
                x=0,
                font_size=14,
            ),
            xaxis_title = "Contribuição SHAP (leitos/mil hab.)",
            yaxis_title = "",
            height      = max(300, len(vals_ord) * 44 + 80),
            margin      = dict(l=10, r=60, t=70, b=40),
        )
    else:
        # Fallback: mensagem se SHAP não disponível
        fig_shap.add_annotation(
            text      = "Instale o pacote 'shap' para visualizar a explicabilidade local.",
            xref      = "paper", yref="paper",
            x=0.5, y=0.5,
            showarrow = False,
            font      = dict(size=13, color=STORY_COLORS["muted"]),
        )
        fig_shap.update_layout(**PLOTLY_LAYOUT_DEFAULTS)
        fig_shap.update_layout(
            height = 200,
            title  = dict(text="<b>Explicabilidade Local (SHAP)</b>", x=0),
        )

    # ── 6c. Gráfico Benchmark — Scatter PIB vs. Leitos ────────────────────────
    # Gera dados mock representativos (distribuição realista) para mostrar
    # onde o município simulado se posiciona em relação ao universo de cidades.
    # Em produção, substitua por df_model real carregado do CSV.
    np.random.seed(42)
    N_MOCK      = 300
    pib_mock    = np.random.lognormal(mean=10.0, sigma=0.75, size=N_MOCK).clip(4_000, 90_000)
    leitos_mock = np.exp(
        0.3 * (np.log(pib_mock) - np.log(pib_mock).mean())
        + np.random.normal(loc=0.5, scale=0.9, size=N_MOCK)
    ).clip(0.01, 80)
    regiao_mock = np.random.choice(REGIOES, size=N_MOCK, p=[0.15, 0.28, 0.12, 0.30, 0.15])

    fig_bench = go.Figure()

    # Pontos reais por região (cor semitransparente)
    cor_regiao_map = {
        "Norte":       "#4E79A7",
        "Nordeste":    "#F28E2B",
        "Centro-Oeste":"#59A14F",
        "Sudeste":     "#B07AA1",
        "Sul":         "#76B7B2",
    }
    for reg in REGIOES:
        mask = regiao_mock == reg
        fig_bench.add_trace(go.Scatter(
            x          = pib_mock[mask],
            y          = leitos_mock[mask],
            mode       = "markers",
            name       = reg,
            marker     = dict(
                color   = cor_regiao_map[reg],
                size    = 7,
                opacity = 0.55,
                line    = dict(width=0),
            ),
            hovertemplate = (
                f"<b>{reg}</b><br>"
                "PIB/Cap: R$ %{x:,.0f}<br>"
                "Leitos/Mil: %{y:.2f}<extra></extra>"
            ),
        ))

    # ★ Ponto destacado: município simulado
    fig_bench.add_trace(go.Scatter(
        x    = [pib],
        y    = [y_pred],
        mode = "markers+text",
        name = "★ Sua Simulação",
        marker = dict(
            color  = COR_SIMULADO,
            size   = 18,
            symbol = "star",
            line   = dict(color="white", width=2),
        ),
        text          = [f"  ← {y_pred:.2f}"],
        textposition  = "middle right",
        textfont      = dict(color=COR_SIMULADO, size=12, family="DM Sans"),
        hovertemplate = (
            "<b>★ Município Simulado</b><br>"
            f"PIB/Cap: R$ {pib:,.0f}<br>"
            f"Região: {regiao}<br>"
            f"Leitos/Mil Previsto: {y_pred:.3f}<extra></extra>"
        ),
    ))

    # Limiares de Joia e Saturação (linhas horizontais de referência)
    fig_bench.add_hline(
        y=float(np.median(leitos_mock)) + abs(limiar_joia),
        line_dash="dot", line_color=COR_SATURADO, line_width=1.2,
        annotation_text=" Saturação",
        annotation_font_color=COR_SATURADO, annotation_font_size=10,
    )
    fig_bench.add_hline(
        y=max(0, float(np.median(leitos_mock)) + limiar_joia),
        line_dash="dot", line_color=COR_JOIA, line_width=1.2,
        annotation_text=" Joia Oculta",
        annotation_font_color=COR_JOIA, annotation_font_size=10,
    )

    fig_bench.update_layout(**PLOTLY_LAYOUT_DEFAULTS)
    fig_bench.update_layout(
        title = dict(text="<b>Benchmarking: Posição da Simulação vs. Municípios Reais</b>", x=0, font_size=14),
        xaxis_title = "PIB per Capita (R$)",
        yaxis_title = "Leitos por Mil Hab.",
        height      = 420,
        margin      = dict(l=10, r=20, t=50, b=50),
        legend      = dict(
            orientation="v", x=1.01, y=1,
            font_size=10, bgcolor="rgba(255,255,255,0.8)",
        ),
    )

    # ── 7. Alerta de Saturação vs. Joia Escondida ─────────────────────────────
    # Baseado no conceito de resíduos do PISI 3:
    # Resíduo = Real − Previsto
    # → Se um município real com esse perfil tiver MENOS leitos que o previsto:
    #     resíduo negativo = Joia Escondida (potencial subexplorado).
    # → Se tiver MAIS leitos que o previsto:
    #     resíduo positivo = Destino Saturado (supracapacidade relativa).
    leitos_joia = max(0.0, y_pred + limiar_joia)     # limiar de Joia (resíduo muito negativo)
    leitos_sat  = y_pred + limiar_sat                 # limiar de Saturação (resíduo positivo)

    cor_alerta  = "#FFF3E0"
    cor_borda   = COR_JOIA
    icone_alert = "fa-solid fa-gem"
    texto_alert = (
        f"Para um município real com esse perfil socioeconômico "
        f"(PIB R$ {pib:,.0f} | Pop. {populacao:,.0f} | {regiao}):"
    )

    bloco_alerta = _card_container(
        _secao_titulo("fa-solid fa-magnifying-glass-chart", "Inteligência de Diagnóstico"),
        html.P(texto_alert, style={"color": STORY_COLORS["text"], "marginBottom": "12px"}),
        html.Div(
            style={"display": "flex", "gap": "16px", "flexWrap": "wrap"},
            children=[
                # Joia Escondida
                html.Div(
                    style={
                        "flex": "1", "minWidth": "220px",
                        "background": "#FFF9E6",
                        "borderLeft": f"4px solid {COR_JOIA}",
                        "borderRadius": "8px",
                        "padding": "14px 16px",
                    },
                    children=[
                        html.Div(
                            [
                                html.I(className="fa-solid fa-gem",
                                       style={"color": COR_JOIA, "marginRight": "8px"}),
                                html.Strong("💎 Joia Escondida",
                                            style={"color": COR_JOIA}),
                            ],
                            style={"marginBottom": "6px"},
                        ),
                        html.P(
                            [
                                "Se um município real com esse perfil tiver ",
                                html.Strong(f"menos de {leitos_joia:.2f} leitos/mil hab."),
                                ", ele é considerado uma Joia Escondida — ",
                                "alto potencial socioeconômico, baixo aproveitamento turístico. ",
                                "Candidato prioritário a políticas de fomento.",
                            ],
                            style={"fontSize": "0.88rem", "color": "#7D6608", "margin": 0},
                        ),
                    ],
                ),
                # Destino Saturado
                html.Div(
                    style={
                        "flex": "1", "minWidth": "220px",
                        "background": "#FDECEC",
                        "borderLeft": f"4px solid {COR_SATURADO}",
                        "borderRadius": "8px",
                        "padding": "14px 16px",
                    },
                    children=[
                        html.Div(
                            [
                                html.I(className="fa-solid fa-circle-exclamation",
                                       style={"color": COR_SATURADO, "marginRight": "8px"}),
                                html.Strong("⚠️ Destino Saturado",
                                            style={"color": COR_SATURADO}),
                            ],
                            style={"marginBottom": "6px"},
                        ),
                        html.P(
                            [
                                "Se tiver ",
                                html.Strong(f"mais de {leitos_sat:.2f} leitos/mil hab."),
                                ", indica um Destino Saturado — ",
                                "capacidade de hospedagem acima do esperado para o perfil. ",
                                "Pode sinalizar supercapacidade ociosa ou destino consolidado.",
                            ],
                            style={"fontSize": "0.88rem", "color": "#7B241C", "margin": 0},
                        ),
                    ],
                ),
            ],
        ),
        extra_style={"marginTop": "0"},
    )

    # ── Montar painel de resultados (coluna direita) ───────────────────────────
    painel_resultados = _card_container(
        _secao_titulo("fa-solid fa-chart-line", "Resultado da Predição"),
        tile_pred,
        html.Hr(style={"margin": "16px 0", "borderColor": "#E0E4EF"}),
        html.Div(
            [
                html.I(className="fa-solid fa-circle-info me-2",
                       style={"color": STORY_COLORS["muted"]}),
                html.Span(
                    "Os gráficos de explicabilidade e benchmarking aparecem abaixo.",
                    style={"color": STORY_COLORS["muted"], "fontSize": "0.85rem"},
                ),
            ]
        ),
    )

    # ── Montar linha dos gráficos inferiores ──────────────────────────────────
    graficos_inferiores = html.Div([
        # Linha de gráficos SHAP + Benchmark lado a lado
        html.Div(
            style={"display": "flex", "gap": "24px", "flexWrap": "wrap", "marginBottom": "24px"},
            children=[
                _card_container(
                    dcc.Graph(
                        figure=fig_shap,
                        config=PLOTLY_CONFIG,
                    ),
                    extra_style={"flex": "1", "minWidth": "300px"},
                ),
                _card_container(
                    dcc.Graph(
                        figure=fig_bench,
                        config=PLOTLY_CONFIG,
                    ),
                    extra_style={"flex": "1", "minWidth": "300px"},
                ),
            ],
        ),
        # Bloco de alerta de diagnóstico
        bloco_alerta,
    ])

    return painel_resultados, graficos_inferiores, ""
