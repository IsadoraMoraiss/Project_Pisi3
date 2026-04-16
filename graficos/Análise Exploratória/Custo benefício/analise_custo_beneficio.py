import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Carregamento e limpeza
df = pd.read_csv("BRAZIL_CITIES.csv", decimal=",")
df.columns = df.columns.str.strip()
df['GDP_CAPITA'] = pd.to_numeric(df['GDP_CAPITA'], errors='coerce')
df['IDHM'] = pd.to_numeric(df['IDHM'], errors='coerce')

# Classificação: cidades com PIB abaixo da mediana e IDHM > 0.7
mediana_pib = df['GDP_CAPITA'].median()
df['Perfil_Destino'] = np.where(
    (df['GDP_CAPITA'] < mediana_pib) & (df['IDHM'] > 0.7),
    'Achado Econômico',
    'Outros Destinos'
)

# Visualização
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='GDP_CAPITA', y='IDHM', hue='Perfil_Destino', 
                palette=['gray', 'blue'], alpha=0.6)
plt.axvline(mediana_pib, color='red', linestyle='--', label='Mediana do PIB per Capita')
plt.axhline(0.7, color='green', linestyle='--', label='IDHM > 0.7')
plt.title("Mapeamento de Destinos de Alto Custo-Benefício")
plt.xlabel("PIB per Capita (R$)")
plt.ylabel("Índice de Desenvolvimento Humano (IDHM)")
plt.legend()
plt.show()