import json
from pathlib import Path
from plugins.wordcloud_viz import WordCloudVisualizer
from plugins.frequency_chart import FrequencyChartVisualizer

# Ler dados
with open('results/freq_clean.json', 'r') as f:
    data = json.load(f)

# WordCloud - Tema escuro
wc = WordCloudVisualizer()
wc.render(data, {
    "background_color": "black",
    "colormap": "plasma",
    "max_words": 50
}, Path('results/wordcloud_dark.png'))

# WordCloud - HTML interativo
wc.render(data, {
    "format": "html",
    "width": 1000,
    "height": 600
}, Path('results/wordcloud_interactive.html'))

# Gráfico de barras horizontal
fc = FrequencyChartVisualizer()
fc.render(data, {
    "chart_type": "horizontal_bar",
    "top_n": 20,
    "interactive": True,
    "title": "Top 20 Palavras - Análise Qualia"
}, Path('results/chart_horizontal.html'))

# Gráfico estático para relatório
fc.render(data, {
    "interactive": False,
    "top_n": 15,
    "title": "Frequência de Termos"
}, Path('results/chart_static.png'))

print("✅ Todas as visualizações criadas em results/")
