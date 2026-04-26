import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# 1. Configuração de nomes claros e meses
meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
regioes = ['Serra Gaúcha', 'Costa dos Corais', 'Serra da Mantiqueira', 'Chapada Diamantina']

# 2. Simulação de Procura (Baseada em comportamento real de mercado)
# Criando curvas de interesse (0 a 100)
dados_busca = {
    'Mês': meses,
    'Serra Gaúcha (Frio/Natal)': [60, 45, 40, 50, 70, 90, 100, 85, 60, 75, 90, 95],
    'Costa dos Corais (Praia)': [100, 95, 80, 50, 30, 20, 40, 35, 55, 75, 85, 95],
    'Serra da Mantiqueira (Montanha)': [50, 40, 45, 60, 80, 100, 95, 70, 55, 50, 60, 75],
    'Chapada Diamantina (Ecoturismo)': [70, 60, 75, 90, 85, 70, 80, 75, 90, 85, 70, 65]
}

df_busca = pd.DataFrame(dados_busca)
df_plot = df_busca.melt('Mês', var_name='Região', value_name='Volume de Procura')

# 3. Visualização Estilizada
plt.figure(figsize=(14, 7))
sns.set_style("whitegrid")

# Criando o gráfico de linhas
plot = sns.lineplot(data=df_plot, x='Mês', y='Volume de Procura', hue='Região', 
                    marker='o', linewidth=2, palette=palette, alpha=0.7)

palette = sns.color_palette("Blues", n_colors=4)

plt.scatter(['Jul'], [100], color='#0b3c5d', s=120, zorder=5)
plt.scatter(['Jan'], [100], color='#0b3c5d', s=120, zorder=5)



# Customização para clareza total
plt.title('Comparação de Procura por Época do Ano', fontsize=18, fontweight='bold', pad=20)
plt.ylabel('Intensidade de Procura (0-100)', fontsize=12)
plt.xlabel('Meses do Ano', fontsize=12)
plt.ylim(0, 110)

# Adicionando anotações de "Pico" para facilitar a leitura
plt.annotate('Pico de Inverno', xy=('Jul', 100), xytext=('Ago', 108),
             arrowprops=dict(facecolor='#0b3c5d', width=2))

plt.annotate('Pico de Verão', xy=('Jan', 100), xytext=('Fev', 108),
             arrowprops=dict(facecolor='#0b3c5d', width=2))

plt.legend(title='Destinos', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11)
plt.tight_layout()
plt.show()
