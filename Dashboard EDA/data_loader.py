"""
data_loader.py
Carrega e pré-processa o dataset BRAZIL_CITIES.csv uma única vez.
Todas as páginas importam daqui — evita múltiplas leituras do CSV.
"""

import pandas as pd
import numpy as np
import os

# ── Caminho do CSV ────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "BRAZIL_CITIES.csv")

# ── Mapeamento Estado → Região ────────────────────────────────────────────
STATE_TO_REGION = {
    "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte",
    "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MS": "Centro-Oeste", "MT": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}

REGIOES   = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
PALETTE   = ["#4E79A7", "#59A14F", "#F28E2B", "#E15759", "#B07AA1"]
REG_COLOR = dict(zip(REGIOES, PALETTE))


def _load() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8", low_memory=False)

    # Nomes padronizados (mantém originais em maiúsculo + cria minúsculos)
    df.columns = df.columns.str.strip()

    # Converte colunas numéricas problemáticas (AREA usa vírgula como decimal)
    for col in ["AREA"]:
        df[col] = (
            df[col].astype(str)
            .str.replace(",", ".", regex=False)
            .pipe(pd.to_numeric, errors="coerce")
        )

    # Converte demais colunas para numérico onde possível
    num_cols = [
        "IDHM", "IDHM_Renda", "IDHM_Longevidade", "IDHM_Educacao",
        "IDHM Ranking 2010",
        "ESTIMATED_POP", "IBGE_RES_POP",
        "GVA_AGROPEC", "GVA_INDUSTRY", "GVA_SERVICES", "GVA_PUBLIC", " GVA_TOTAL ",
        "GDP", "GDP_CAPITA",
        "HOTELS", "BEDS",
        "COMP_TOT", "COMP_J", "COMP_I", "COMP_G",
        "UBER", "Cars", "Motorcycles",
        "PAY_TV", "FIXED_PHONES",
        "IBGE_PLANTED_AREA",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Nessas colunas, nulo representa ausencia no cadastro, nao valor desconhecido.
    # Usar mediana aqui inflava artificialmente servicos e infraestrutura.
    zero_fill_cols = [
        "UBER", "HOTELS", "BEDS",
        "MAC", "WAL-MART", "Pr_Agencies", "Pu_Agencies",
    ]
    for col in zero_fill_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # Preenche nulos numéricos com mediana
    for col in df.select_dtypes(include="number").columns:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].median())

    # Preenche nulos categóricos
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].fillna("Desconhecido")

    # Features derivadas
    df["REGIAO"] = df["STATE"].map(STATE_TO_REGION).fillna("Desconhecido")
    df["leitos_por_hab"]  = df["BEDS"]   / (df["IBGE_RES_POP"] + 1)
    df["leitos_1000hab"]  = df["leitos_por_hab"] * 1000
    df["hoteis_por_hab"]  = df["HOTELS"] / (df["IBGE_RES_POP"] + 1)
    df["servicos_por_hab"] = df["COMP_I"] / (df["IBGE_RES_POP"] + 1)
    df["agencias_total"]  = df[["Pr_Agencies", "Pu_Agencies"]].sum(axis=1)
    df["pct_agro_gva"]    = df["GVA_AGROPEC"] / (df["GVA_TOTAL"].replace(0, np.nan)) * 100

    # ──────────────────────────────────────────────────────────────────────────
    # 🟣 1. ÍNDICE DE PRESSÃO TURÍSTICA (0-100)
    # Fórmula: (leitos por habitante) / max(leitos por hab) * 100
    # ──────────────────────────────────────────────────────────────────────────
    max_leitos_hab = df["leitos_por_hab"].max()
    df["indice_pressao_turistica"] = (df["leitos_por_hab"] / max_leitos_hab * 100).fillna(0).round(1)
    
    # Categorização
    df["pressao_turistica_cat"] = pd.cut(
        df["indice_pressao_turistica"],
        bins=[0, 25, 50, 100],
        labels=["Baixa", "Média", "Alta"],
        include_lowest=True
    )

    # ──────────────────────────────────────────────────────────────────────────
    # 🟢 2. ÍNDICE DE INFRAESTRUTURA TURÍSTICA (0-100)
    # Score normalizado usando: hotéis, leitos, bancos, Uber, agências
    # ──────────────────────────────────────────────────────────────────────────
    def _calc_infra_score(row):
        # Normalização 0-1 para cada componente
        hotels_norm = min(row["HOTELS"] / df["HOTELS"].max(), 1) if df["HOTELS"].max() > 0 else 0
        beds_norm   = min(row["BEDS"] / df["BEDS"].max(), 1) if df["BEDS"].max() > 0 else 0
        agencies_norm = min(row["agencias_total"] / df["agencias_total"].max(), 1) if df["agencias_total"].max() > 0 else 0
        uber_binary = 1 if row["UBER"] > 0 else 0
        bancos_norm = min(row["COMP_G"] / df["COMP_G"].max(), 1) if df["COMP_G"].max() > 0 else 0
        # Média ponderada
        score = (hotels_norm * 0.25 + beds_norm * 0.25 + agencies_norm * 0.20 + 
                uber_binary * 0.15 + bancos_norm * 0.15) * 100
        return score
    
    df["indice_infraestrutura"] = df.apply(_calc_infra_score, axis=1).fillna(0).round(1)

    # ──────────────────────────────────────────────────────────────────────────
    # 🔵 3. DEPENDÊNCIA ECONÔMICA
    # Descobre qual setor é dominante (%)
    # ──────────────────────────────────────────────────────────────────────────
    def _calc_economia_dominante(row):
        total_gva = row["GVA_TOTAL"]
        if total_gva == 0:
            return "Desconhecida"
        pct_agro = (row["GVA_AGROPEC"] / total_gva * 100)
        pct_ind = (row["GVA_INDUSTRY"] / total_gva * 100)
        pct_serv = (row["GVA_SERVICES"] / total_gva * 100)
        pct_pub = (row["GVA_PUBLIC"] / total_gva * 100)
        
        max_pct = max(pct_agro, pct_ind, pct_serv, pct_pub)
        if max_pct == pct_agro:
            return "Agrodependente"
        elif max_pct == pct_ind:
            return "Industrial"
        elif max_pct == pct_serv:
            return "Serviços/Turismo"
        else:
            return "Dependência Pública"
    
    df["economia_dominante"] = df.apply(_calc_economia_dominante, axis=1)

    # ──────────────────────────────────────────────────────────────────────────
    # 🟠 4. ÍNDICE DE MODERNIZAÇÃO / URBANIZAÇÃO (0-100)
    # Nível de "conveniência urbana" usando Uber, Pay TV, Telefones, Tech, Bancos
    # ──────────────────────────────────────────────────────────────────────────
    def _calc_modernizacao(row):
        uber_binary = 1 if row["UBER"] > 0 else 0
        paytv_norm = min(row["PAY_TV"] / df["PAY_TV"].max(), 1) if df["PAY_TV"].max() > 0 else 0
        phones_norm = min(row["FIXED_PHONES"] / df["FIXED_PHONES"].max(), 1) if df["FIXED_PHONES"].max() > 0 else 0
        tech_norm = min(row["COMP_J"] / df["COMP_J"].max(), 1) if df["COMP_J"].max() > 0 else 0
        bancos_norm = min(row["COMP_G"] / df["COMP_G"].max(), 1) if df["COMP_G"].max() > 0 else 0
        
        score = (uber_binary * 0.25 + paytv_norm * 0.20 + phones_norm * 0.20 + 
                tech_norm * 0.20 + bancos_norm * 0.15) * 100
        return score
    
    df["indice_modernizacao"] = df.apply(_calc_modernizacao, axis=1).fillna(0).round(1)

    # ──────────────────────────────────────────────────────────────────────────
    # 🔴 5. POTENCIAL DE "JOIA ESCONDIDA" (0-100)
    # Alto: IDH + infraestrutura + serviços + Uber
    # Baixo: fluxo turístico oficial + hotéis + visibilidade
    # ──────────────────────────────────────────────────────────────────────────
    def _calc_joia_potencial(row):
        # Componente positivo (oferta)
        idh_norm = row["IDHM"] / 1.0  # IDHM vai até 1
        infra_norm = row["indice_infraestrutura"] / 100
        moderniz_norm = row["indice_modernizacao"] / 100
        
        # Componente negativo (saturação turística)
        pressao_norm = row["indice_pressao_turistica"] / 100
        
        # Score: quanto maior o potencial, melhor
        # Alto potencial = bom desenvolvimento + baixa pressão turística
        score = ((idh_norm * 0.35 + infra_norm * 0.30 + moderniz_norm * 0.20) * (1 - pressao_norm * 0.15)) * 100
        return score
    
    df["potencial_joia_escondida"] = df.apply(_calc_joia_potencial, axis=1).fillna(0).round(1)

    # ──────────────────────────────────────────────────────────────────────────
    # 🟡 6. ÍNDICE DE ACESSIBILIDADE (0-100)
    # "Cidade preparada para turista independente"
    # Usa: Uber, Bancos, Correios (representado por serviços), Telefones
    # ──────────────────────────────────────────────────────────────────────────
    def _calc_acessibilidade(row):
        uber_binary = 1 if row["UBER"] > 0 else 0
        bancos_norm = min(row["COMP_G"] / df["COMP_G"].max(), 1) if df["COMP_G"].max() > 0 else 0
        phones_norm = min(row["FIXED_PHONES"] / df["FIXED_PHONES"].max(), 1) if df["FIXED_PHONES"].max() > 0 else 0
        servicos_norm = min(row["COMP_I"] / df["COMP_I"].max(), 1) if df["COMP_I"].max() > 0 else 0
        
        score = (uber_binary * 0.30 + bancos_norm * 0.25 + phones_norm * 0.20 + 
                servicos_norm * 0.25) * 100
        return score
    
    df["indice_acessibilidade"] = df.apply(_calc_acessibilidade, axis=1).fillna(0).round(1)

    # ──────────────────────────────────────────────────────────────────────────
    # 🟤 7. ÍNDICE DE DIVERSIDADE ECONÔMICA (0-100)
    # Quantos setores diferentes tem peso significativo
    # Usando distribuição GVA entre os 4 setores principais
    # ──────────────────────────────────────────────────────────────────────────
    def _calc_diversidade_economica(row):
        total_gva = row["GVA_TOTAL"]
        if total_gva == 0:
            return 0
        
        # Calcula proporções (0-1) de cada setor
        prop_agro = row["GVA_AGROPEC"] / total_gva
        prop_ind = row["GVA_INDUSTRY"] / total_gva
        prop_serv = row["GVA_SERVICES"] / total_gva
        prop_pub = row["GVA_PUBLIC"] / total_gva
        
        # Entropia de Shannon normalizada (quanto mais distribuído, maior)
        proportions = [prop_agro, prop_ind, prop_serv, prop_pub]
        
        # Calcula entropia
        entropy = -sum(p * np.log(p) if p > 0 else 0 for p in proportions)
        max_entropy = np.log(4)  # máxima entropia com 4 categorias
        
        # Normaliza para 0-100
        diversidade = (entropy / max_entropy) * 100 if max_entropy > 0 else 0
        
        return max(0, min(100, diversidade))  # Garante que está entre 0-100
    
    df["indice_diversidade_economica"] = df.apply(_calc_diversidade_economica, axis=1).fillna(0).round(1)

    # Quadrante turístico (P4 da EDA)
    idhm_p70      = df["IDHM"].quantile(0.70)
    mediana_leitos = df["leitos_1000hab"].median()
    df["quadrante"] = "Outros"
    df.loc[(df["IDHM"] >= idhm_p70) & (df["leitos_1000hab"] <= mediana_leitos), "quadrante"] = "Joia Escondida"
    df.loc[(df["IDHM"] >= idhm_p70) & (df["leitos_1000hab"] >  mediana_leitos), "quadrante"] = "Alto IDH + Estrutura"
    df.loc[(df["IDHM"] <  idhm_p70) & (df["leitos_1000hab"] >  mediana_leitos), "quadrante"] = "Estrutura sem IDH"

    return df


# Carrega UMA vez ao importar o módulo
DF = _load()

# ── Listas de seleção ─────────────────────────────────────────────────────
ALL_STATES  = sorted(DF["STATE"].unique().tolist())
ALL_REGIONS = REGIOES
ALL_CITIES  = sorted(DF["CITY"].unique().tolist())


def get_cities_for_state(state: str) -> list[str]:
    return sorted(DF[DF["STATE"] == state]["CITY"].unique().tolist())


def get_cities_for_region(region: str) -> list[str]:
    return sorted(DF[DF["REGIAO"] == region]["CITY"].unique().tolist())


def get_states_for_region(region: str) -> list[str]:
    return sorted(DF[DF["REGIAO"] == region]["STATE"].unique().tolist())


# ── Agregações regionais (usadas em Visão Geral) ─────────────────────────

def region_summary(region: str) -> dict:
    sub = DF[DF["REGIAO"] == region]
    n   = len(sub)
    estados = sorted(sub["STATE"].unique().tolist())
    rank_idh  = int(DF.groupby("REGIAO")["IDHM"].mean().rank(ascending=False, method="min").astype(int)[region])
    rank_tech = int(DF.groupby("REGIAO")["COMP_J"].sum().rank(ascending=False, method="min").astype(int)[region])
    rank_agro = int(DF.groupby("REGIAO")["GVA_AGROPEC"].sum().rank(ascending=False, method="min").astype(int)[region])
    rank_hotel= int(DF.groupby("REGIAO")["HOTELS"].sum().rank(ascending=False, method="min").astype(int)[region])
    rank_uber = int(DF.groupby("REGIAO")["UBER"].sum().rank(ascending=False, method="min").astype(int)[region])
    rank_pop  = int(DF.groupby("REGIAO")["ESTIMATED_POP"].sum().rank(ascending=False, method="min").astype(int)[region])
    
    # Rankings dos novos indicadores
    rank_pressao = int(DF.groupby("REGIAO")["indice_pressao_turistica"].mean().rank(ascending=False, method="min").astype(int)[region])
    rank_infra = int(DF.groupby("REGIAO")["indice_infraestrutura"].mean().rank(ascending=False, method="min").astype(int)[region])
    rank_moderniz = int(DF.groupby("REGIAO")["indice_modernizacao"].mean().rank(ascending=False, method="min").astype(int)[region])
    rank_joia = int(DF.groupby("REGIAO")["potencial_joia_escondida"].mean().rank(ascending=False, method="min").astype(int)[region])
    rank_acessib = int(DF.groupby("REGIAO")["indice_acessibilidade"].mean().rank(ascending=False, method="min").astype(int)[region])
    rank_diversid = int(DF.groupby("REGIAO")["indice_diversidade_economica"].mean().rank(ascending=False, method="min").astype(int)[region])
    
    return {
        # Métricas originais
        "idh":        f"{sub['IDHM'].mean():.3f}",
        "tech":       f"{int(sub['COMP_J'].sum()):,}".replace(",", "."),
        "agro":       f"R$ {sub['GVA_AGROPEC'].sum()/1e9:.1f} bi",
        "hoteis":     str(int(sub["HOTELS"].sum())),
        "uber":       str(int(sub["UBER"].sum())),
        "pop":        f"{sub['ESTIMATED_POP'].sum()/1e6:.1f} mi",
        "municipios": str(n),
        "estados":    ", ".join(estados),
        "rank_idh":   rank_idh,
        "rank_tech":  rank_tech,
        "rank_agro":  rank_agro,
        "rank_hotel": rank_hotel,
        "rank_uber":  rank_uber,
        "rank_pop":   rank_pop,
        
        # Novos indicadores (médias regionais)
        "pressao_turistica":    f"{sub['indice_pressao_turistica'].mean():.0f}",
        "infraestrutura":       f"{sub['indice_infraestrutura'].mean():.0f}",
        "modernizacao":         f"{sub['indice_modernizacao'].mean():.0f}",
        "joia_potencial":       f"{sub['potencial_joia_escondida'].mean():.0f}",
        "acessibilidade":       f"{sub['indice_acessibilidade'].mean():.0f}",
        "diversidade_econ":     f"{sub['indice_diversidade_economica'].mean():.0f}",
        
        # Rankings dos novos indicadores
        "rank_pressao":   rank_pressao,
        "rank_infra":     rank_infra,
        "rank_moderniz":  rank_moderniz,
        "rank_joia":      rank_joia,
        "rank_acessib":   rank_acessib,
        "rank_diversid":  rank_diversid,
    }


def state_summary(state: str) -> dict:
    sub   = DF[DF["STATE"] == state]
    all_states_idh = DF.groupby("STATE")["IDHM"].mean()
    rank_idh  = int(all_states_idh.rank(ascending=False, method="min").astype(int)[state])
    all_states_tech = DF.groupby("STATE")["COMP_J"].sum()
    rank_tech = int(all_states_tech.rank(ascending=False, method="min").astype(int)[state])
    all_states_agro = DF.groupby("STATE")["GVA_AGROPEC"].sum()
    rank_agro = int(all_states_agro.rank(ascending=False, method="min").astype(int)[state])
    all_states_hotel = DF.groupby("STATE")["HOTELS"].sum()
    rank_hotel= int(all_states_hotel.rank(ascending=False, method="min").astype(int)[state])
    all_states_uber = DF.groupby("STATE")["UBER"].sum()
    rank_uber = int(all_states_uber.rank(ascending=False, method="min").astype(int)[state])
    all_states_pop = DF.groupby("STATE")["ESTIMATED_POP"].sum()
    rank_pop  = int(all_states_pop.rank(ascending=False, method="min").astype(int)[state])
    
    # Rankings dos novos indicadores
    rank_pressao = int(DF.groupby("STATE")["indice_pressao_turistica"].mean().rank(ascending=False, method="min").astype(int)[state])
    rank_infra = int(DF.groupby("STATE")["indice_infraestrutura"].mean().rank(ascending=False, method="min").astype(int)[state])
    rank_moderniz = int(DF.groupby("STATE")["indice_modernizacao"].mean().rank(ascending=False, method="min").astype(int)[state])
    rank_joia = int(DF.groupby("STATE")["potencial_joia_escondida"].mean().rank(ascending=False, method="min").astype(int)[state])
    rank_acessib = int(DF.groupby("STATE")["indice_acessibilidade"].mean().rank(ascending=False, method="min").astype(int)[state])
    rank_diversid = int(DF.groupby("STATE")["indice_diversidade_economica"].mean().rank(ascending=False, method="min").astype(int)[state])
    
    n_states  = len(DF["STATE"].unique())
    return {
        # Métricas originais
        "idh":        f"{sub['IDHM'].mean():.3f}",
        "tech":       f"{int(sub['COMP_J'].sum()):,}".replace(",", "."),
        "agro":       f"R$ {sub['GVA_AGROPEC'].sum()/1e9:.1f} bi",
        "hoteis":     str(int(sub["HOTELS"].sum())),
        "uber":       str(int(sub["UBER"].sum())),
        "pop":        f"{sub['ESTIMATED_POP'].sum()/1e6:.2f} mi",
        "municipios": str(len(sub)),
        "rank_idh":   rank_idh,
        "rank_tech":  rank_tech,
        "rank_agro":  rank_agro,
        "rank_hotel": rank_hotel,
        "rank_uber":  rank_uber,
        "rank_pop":   rank_pop,
        "n_states":   n_states,
        
        # Novos indicadores (médias estaduais)
        "pressao_turistica":    f"{sub['indice_pressao_turistica'].mean():.0f}",
        "infraestrutura":       f"{sub['indice_infraestrutura'].mean():.0f}",
        "modernizacao":         f"{sub['indice_modernizacao'].mean():.0f}",
        "joia_potencial":       f"{sub['potencial_joia_escondida'].mean():.0f}",
        "acessibilidade":       f"{sub['indice_acessibilidade'].mean():.0f}",
        "diversidade_econ":     f"{sub['indice_diversidade_economica'].mean():.0f}",
        
        # Rankings dos novos indicadores
        "rank_pressao":   rank_pressao,
        "rank_infra":     rank_infra,
        "rank_moderniz":  rank_moderniz,
        "rank_joia":      rank_joia,
        "rank_acessib":   rank_acessib,
        "rank_diversid":  rank_diversid,
    }


def city_summary(city: str) -> dict:
    row = DF[DF["CITY"] == city]
    if row.empty:
        return {}
    row = row.iloc[0]
    n_cities = len(DF)
    city_mask = DF["CITY"] == city

    def _rank_city_col(column: str) -> int:
        """Maior valor = melhor; empates na mesma posição (alinhado a região/estado)."""
        return int(DF[column].rank(ascending=False, method="min")[city_mask].iloc[0])

    rank_idh = _rank_city_col("IDHM")
    rank_tech = _rank_city_col("COMP_J")
    rank_hotel = _rank_city_col("HOTELS")
    rank_uber = _rank_city_col("UBER")
    rank_pop = _rank_city_col("ESTIMATED_POP")
    rank_agro = _rank_city_col("GVA_AGROPEC")
    rank_pressao = _rank_city_col("indice_pressao_turistica")
    rank_infra = _rank_city_col("indice_infraestrutura")
    rank_moderniz = _rank_city_col("indice_modernizacao")
    rank_joia = _rank_city_col("potencial_joia_escondida")
    rank_acessib = _rank_city_col("indice_acessibilidade")
    rank_diversid = _rank_city_col("indice_diversidade_economica")
    
    return {
        # Métricas originais
        "idh":        f"{row['IDHM']:.3f}",
        "tech":       str(int(row["COMP_J"])),
        "agro":       f"R$ {row['GVA_AGROPEC']/1e6:.1f} mi",
        "hoteis":     str(int(row["HOTELS"])),
        "uber":       "Sim" if row["UBER"] >= 1 else "Não",
        "pop":        f"{int(row['ESTIMATED_POP']):,}".replace(",", "."),
        "state":      str(row["STATE"]),
        "regiao":     str(row["REGIAO"]),
        "quadrante":  str(row["quadrante"]),
        "rank_idh":   rank_idh,
        "rank_tech":  rank_tech,
        "rank_hotel": rank_hotel,
        "rank_uber":  rank_uber,
        "rank_pop":   rank_pop,
        "rank_agro":  rank_agro,
        "n_cities":   n_cities,
        
        # Novos indicadores
        "pressao_turistica":    f"{row['indice_pressao_turistica']:.0f}",
        "pressao_cat":          str(row["pressao_turistica_cat"]),
        "infraestrutura":       f"{row['indice_infraestrutura']:.0f}",
        "economia_dominante":   str(row["economia_dominante"]),
        "modernizacao":         f"{row['indice_modernizacao']:.0f}",
        "joia_potencial":       f"{row['potencial_joia_escondida']:.0f}",
        "acessibilidade":       f"{row['indice_acessibilidade']:.0f}",
        "diversidade_econ":     f"{row['indice_diversidade_economica']:.0f}",
        
        # Rankings dos novos indicadores
        "rank_pressao":   rank_pressao,
        "rank_infra":     rank_infra,
        "rank_moderniz":  rank_moderniz,
        "rank_joia":      rank_joia,
        "rank_acessib":   rank_acessib,
        "rank_diversid":  rank_diversid,
    }
