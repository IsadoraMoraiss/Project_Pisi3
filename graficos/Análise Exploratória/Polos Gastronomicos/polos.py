import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv('BRAZIL_CITIES.csv', sep=';', decimal=',')
# COMP_I engloba hotéis e alimentação. Como já vimos hotéis, aqui focamos no ecossistema de serviços.
df_food = df.sort_values(by='COMP_I', ascending=False).head(20)

plt.figure(figsize=(10, 8))
sns.barplot(data=df_food, x='COMP_I', y='CITY', palette='YlOrBr')
plt.title('Top 20 Polos de Gastronomia e Serviços (Coluna COMP_I)', fontsize=14)
plt.xlabel('Quantidade de Estabelecimentos (Alimentação/Alojamento)')
plt.show()
