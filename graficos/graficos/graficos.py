# Criar uma métrica de infraestrutura bancária total
df['BANKS'] = pd.to_numeric(df['Pr_Agencies'], errors='coerce') + pd.to_numeric(df['Pu_Agencies'], errors='coerce')

# Agrupar por Estado para ver o panorama regional
state_data = df.groupby('STATE').agg({'BANKS': 'sum', 'UBER': 'sum'}).sort_values('BANKS', ascending=False).head(15)

state_data.plot(kind='bar', figsize=(12, 6), color=['#1f77b4', '#ff7f0e'])
plt.title('Infraestrutura por Estado: Bancos vs. Cidades com Uber')
plt.ylabel('Total Acumulado')
plt.xticks(rotation=0)
plt.legend(['Total Agências Bancárias', 'Cidades com Uber'])
plt.show()
