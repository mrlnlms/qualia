import json
from pathlib import Path
from plugins.wordcloud_viz import WordCloudVisualizer
from plugins.frequency_chart import FrequencyChartVisualizer

# Ler dados
with open('results/freq_clean.json', 'r') as f:
    data = json.load(f)

try:
    # WordCloud - Tema escuro
    wc = WordCloudVisualizer()
    wc.render(data, {
        "background_color": "black",
        "colormap": "plasma",
        "max_words": 50
    }, Path('results/wordcloud_dark.png'))
    print("✓ WordCloud dark criado")

    # WordCloud - HTML interativo
    wc.render(data, {
        "format": "html",
        "width": 1000,
        "height": 600
    }, Path('results/wordcloud_interactive.html'))
    print("✓ WordCloud HTML criado")

    # Gráfico de barras horizontal
    fc = FrequencyChartVisualizer()
    fc.render(data, {
        "chart_type": "horizontal_bar",
        "top_n": 20,
        "interactive": True,
        "title": "Top 20 Palavras - Análise Qualia"
    }, Path('results/chart_horizontal.html'))
    print("✓ Gráfico horizontal criado")

    # Gráfico estático para relatório
    fc.render(data, {
        "interactive": False,
        "top_n": 15,
        "title": "Frequência de Termos"
    }, Path('results/chart_static.png'))
    print("✓ Gráfico estático criado")

    print("\n✅ Todas as visualizações criadas em results/")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
