"""
retrainer.py
Re-treina o modelo de regressão turística e salva o artefato .pkl
compatível com a versão atual do scikit-learn.

Executa:
    python retrainer.py
"""

import os
import warnings
import numpy as np
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error

warnings.filterwarnings("ignore")

# ── Configurações ─────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CSV_PATH   = os.path.join(BASE_DIR, "BRAZIL_CITIES.csv")
MODEL_PATH = os.path.join(BASE_DIR, "melhor_regressor_turismo.pkl")

FEATURES_NUM = ["PIB_per_capita", "Populacao", "Densidade"]
FEATURES_CAT = ["Regiao"]
TARGET       = "Leitos_por_Mil_Hab"
SEED         = 42

# Mapeamento estado → região
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

print("=" * 60)
print("  Re-treinamento do Modelo Turístico — Brasil em Foco")
print("=" * 60)

# ── 1. Carregar e preparar os dados ──────────────────────────────────────────
print("\n[1/5] Carregando BRAZIL_CITIES.csv...")
df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8", low_memory=False)
df.columns = df.columns.str.strip()

# Corrigir coluna AREA (usa vírgula como decimal)
df["AREA"] = (
    df["AREA"].astype(str)
    .str.replace(",", ".", regex=False)
    .pipe(pd.to_numeric, errors="coerce")
)

# Converter colunas numéricas relevantes
num_cols = ["GDP_CAPITA", "IBGE_RES_POP", "BEDS", "AREA"]
for col in num_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Preencher nulos numéricos com mediana
for col in df.select_dtypes(include="number").columns:
    if df[col].isnull().any():
        df[col] = df[col].fillna(df[col].median())

# Preencher nulos categóricos
for col in df.select_dtypes(include="object").columns:
    df[col] = df[col].fillna("Desconhecido")

print(f"   → {len(df):,} municípios carregados.")

# ── 2. Engenharia de Features ────────────────────────────────────────────────
print("\n[2/5] Criando features do modelo...")

# Região a partir do estado
df["Regiao"] = df["STATE"].map(STATE_TO_REGION).fillna("Desconhecido")

# PIB per capita (GDP_CAPITA já está no CSV)
df["PIB_per_capita"] = df["GDP_CAPITA"]

# Populacao
df["Populacao"] = df["IBGE_RES_POP"]

# Densidade demográfica (hab/km²)
df["Densidade"] = (df["IBGE_RES_POP"] / df["AREA"].replace(0, np.nan)).fillna(0)

# Target: Leitos por mil habitantes
df["Leitos_por_Mil_Hab"] = (df["BEDS"] / (df["IBGE_RES_POP"] + 1)) * 1000
df["Leitos_por_Mil_Hab"] = df["Leitos_por_Mil_Hab"].clip(lower=0, upper=500)

# Remover linhas sem target ou features
df_model = df[FEATURES_NUM + FEATURES_CAT + [TARGET]].dropna()
df_model = df_model[df_model[TARGET] > 0].reset_index(drop=True)

print(f"   → Dataset de treino: {len(df_model):,} municípios com leitos > 0")
print(f"   → Target (mediana): {df_model[TARGET].median():.3f} leitos/mil hab.")

# ── 3. Split treino/teste ─────────────────────────────────────────────────────
print("\n[3/5] Dividindo em treino (80%) e teste (20%)...")
X = df_model[FEATURES_NUM + FEATURES_CAT]
y = df_model[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=SEED
)
print(f"   → Treino: {len(X_train):,} | Teste: {len(X_test):,}")

# ── 4. Construir pipeline e treinar ──────────────────────────────────────────
print("\n[4/5] Construindo pipeline e treinando modelo...")

# Preprocessor
preprocessor = ColumnTransformer(transformers=[
    ("num", StandardScaler(), FEATURES_NUM),
    ("cat", Pipeline([
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ]), FEATURES_CAT),
])

# Candidatos a modelo
candidatos = {
    "GradientBoosting": GradientBoostingRegressor(
        n_estimators=200, learning_rate=0.05, max_depth=4,
        subsample=0.8, random_state=SEED
    ),
    "RandomForest": RandomForestRegressor(
        n_estimators=200, max_depth=8, min_samples_leaf=3,
        random_state=SEED, n_jobs=-1
    ),
    "Ridge": Ridge(alpha=10.0),
}

melhor_nome  = None
melhor_r2_cv = -np.inf
melhor_pipe  = None

for nome, estimador in candidatos.items():
    pipe = Pipeline([("preprocessor", preprocessor), ("model", estimador)])
    cv_scores = cross_val_score(pipe, X_train, y_train, cv=5, scoring="r2")
    r2_cv_mean = cv_scores.mean()
    print(f"   {nome:25s} → R² CV (5-fold): {r2_cv_mean:.4f} ± {cv_scores.std():.4f}")
    if r2_cv_mean > melhor_r2_cv:
        melhor_r2_cv = r2_cv_mean
        melhor_nome  = nome
        melhor_pipe  = pipe

print(f"\n   🏆 Modelo campeão: {melhor_nome} (R² CV = {melhor_r2_cv:.4f})")

# Treinar no conjunto completo de treino
melhor_pipe.fit(X_train, y_train)

# Métricas no teste
y_pred_test = melhor_pipe.predict(X_test)
r2_teste  = r2_score(y_test, y_pred_test)
mae_teste = mean_absolute_error(y_test, y_pred_test)
print(f"   R² no teste : {r2_teste:.4f}")
print(f"   MAE no teste: {mae_teste:.4f}")

# Calcular limiares de Joia / Saturação com base nos resíduos do treino
residuos_treino = y_train.values - melhor_pipe.predict(X_train)
limiar_joia     = float(np.percentile(residuos_treino, 15))   # 15% inferior
limiar_sat      = float(np.percentile(residuos_treino, 85))   # 85% superior
print(f"   Limiar Joia Escondida  : {limiar_joia:.3f}")
print(f"   Limiar Destino Saturado: {limiar_sat:.3f}")

# ── 5. Salvar artefato ────────────────────────────────────────────────────────
print(f"\n[5/5] Salvando modelo em '{MODEL_PATH}'...")

artefato = {
    "modelo":           melhor_pipe,
    "nome_modelo":      melhor_nome,
    "features_num":     FEATURES_NUM,
    "features_cat":     FEATURES_CAT,
    "target":           TARGET,
    "seed":             SEED,
    "teste_r2":         r2_teste,
    "teste_mae":        mae_teste,
    "limiar_joia":      limiar_joia,
    "limiar_saturacao": limiar_sat,
    "sklearn_version":  __import__("sklearn").__version__,
}

joblib.dump(artefato, MODEL_PATH)
print(f"   ✅ Salvo com sucesso! ({os.path.getsize(MODEL_PATH) / 1024:.1f} KB)")
print("\n" + "=" * 60)
print("  Modelo atualizado. Reinicie o dashboard para usar o novo .pkl.")
print("=" * 60)
