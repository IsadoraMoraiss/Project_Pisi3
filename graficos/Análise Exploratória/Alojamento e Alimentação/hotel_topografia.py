import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Carregamento e limpeza
df = pd.read_csv("BRAZIL_CITIES.csv", decimal=",")
df.columns = df.columns.str.strip()
df['ALT'] = pd.to_numeric(df['ALT'], errors='coerce')
df['HOTELS'] = pd.to_numeric(df['HOTELS'], errors='coerce')

# Classificação por altitude
def classificar_relevo(alt):
    if pd.isna(alt):
        return np.nan
    return 'Litoral / Planície' if alt < 20 else 'Serra / Inverno' if alt > 800 else 'Interior Padrão'

df['Categoria_Turistica'] = df['ALT'].apply(classificar_relevo)

# Filtragem e visualização
df_turismo = df[(df['HOTELS'] > 0) & (df['Categoria_Turistica'].notna())]

plt.figure(figsize=(10, 6))
sns.boxplot(data=df_turismo, x='Categoria_Turistica', y='HOTELS', palette='Set2')
plt.yscale('log')
plt.title("Infraestrutura Hoteleira por Topografia")
plt.xlabel("Categoria por Altitude")
plt.ylabel("Número de Hotéis (Escala Log)")
plt.show()
