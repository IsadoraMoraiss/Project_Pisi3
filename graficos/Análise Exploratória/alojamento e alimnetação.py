import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv('BRAZIL_CITIES.csv', sep=';', decimal=',')
df_top = df.sort_values('COMP_I', ascending=False).head(20)

plt.figure(figsize=(12, 8))
# O 'palette' cria o efeito visual de importância
sns.barplot(data=df_top, x='COMP_I', y='CITY', palette='Blues_r', edgecolor='0.2')

plt.title('Top 20 Cidades: Volume de Serviços de Alojamento e Alimentação', fontsize=15)
plt.xlabel('Quantidade de Empresas (Setor I)')
plt.ylabel('Cidade')
plt.grid(axis='x', alpha=0.3)
plt.show()
