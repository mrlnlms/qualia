import json
from pathlib import Path
from plugins.wordcloud_viz import WordCloudVisualizer
from plugins.frequency_chart import FrequencyChartVisualizer

# Ler dados
with open('results/freq.json', 'r') as f:
    data = json.load(f)

# Testar WordCloud
wc = WordCloudVisualizer()
output_path = Path('results/wordcloud.png')
result = wc.render(data, {}, output_path)
print(f"WordCloud salvo em: {result}")

# Testar Frequency Chart
fc = FrequencyChartVisualizer()
output_path = Path('results/freq_chart.html')
result = fc.render(data, {"interactive": True}, output_path)
print(f"Gráfico salvo em: {result}")
