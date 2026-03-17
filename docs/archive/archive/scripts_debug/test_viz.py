from pathlib import Path
import json
from plugins.wordcloud_viz import WordCloudVisualizer
from plugins.frequency_chart import FrequencyChartVisualizer

# Ler dados
with open('results/freq.json') as f:
    data = json.load(f)

# Criar wordcloud
wc = WordCloudVisualizer()
# Fazer o workaround aqui
output = Path("test_wordcloud.png")
wc.render(data, {"colormap": "plasma", "background_color": "black"}, output)
print(f"✓ Wordcloud criada: {output}")

# Criar gráfico
fc = FrequencyChartVisualizer()
output2 = Path("test_chart.html")
fc.render(data, {"chart_type": "horizontal_bar"}, output2)
print(f"✓ Gráfico criado: {output2}")
