# UBER no dataset costuma ser 1 para SIM e 0 para NÃO.
# Vamos ver quais estados têm mais cidades com UBER liberado.
uber_by_state = df.groupby('STATE')['UBER'].sum().sort_values(ascending=False)

plt.figure(figsize=(12, 6))
uber_by_state.plot(kind='bar', color='black')
plt.title('Estados com Mais Cidades Atendidas por UBER')
plt.ylabel('Número de Cidades com UBER')
plt.show()
