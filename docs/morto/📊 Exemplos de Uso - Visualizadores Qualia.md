# 📊 Exemplos de Uso - Visualizadores Qualia

## Instalação dos Visualizadores

```bash
# 1. Criar estrutura para os plugins
mkdir -p plugins/wordcloud_viz
mkdir -p plugins/frequency_chart

# 2. Copiar os arquivos dos artifacts

# 3. Instalar dependências
pip install matplotlib wordcloud plotly kaleido

# 4. Verificar se foram descobertos
qualia list --type visualizer
```

## 🌤️ WordCloud - Nuvem de Palavras

### Uso Básico
```bash
# Gerar nuvem de palavras após análise
qualia analyze doc.txt -p word_frequency | \
qualia visualize -p wordcloud_viz -o nuvem.png
```

### Com Pipeline
```bash
# Pipeline com análise + visualização
cat > configs/pipelines/wordcloud_pipeline.yaml << 'EOF'
name: wordcloud_analysis
description: Análise com nuvem de palavras

steps:
  # 1. Limpar documento
  - plugin: teams_cleaner
    config:
      remove_timestamps: true
      remove_system_messages: true
    
  # 2. Análise de frequência
  - plugin: word_frequency
    config:
      min_word_length: 4
      remove_stopwords: true
      max_words: 200
    output_name: frequencies
  
  # 3. Nuvem de palavras
  - plugin: wordcloud_viz
    config:
      max_words: 100
      width: 1200
      height: 800
      background_color: white
      colormap: viridis
      format: png
    output_name: wordcloud
EOF

# Executar
qualia pipeline transcript.txt \
  --config configs/pipelines/wordcloud_pipeline.yaml \
  --output-dir results/visualizations/
```

### Customizações Avançadas
```bash
# Nuvem escura com cores plasma
qualia visualize data.json -p wordcloud_viz \
  -P background_color=black \
  -P colormap=plasma \
  -P max_words=150 \
  -o nuvem_escura.png

# HTML interativo
qualia visualize data.json -p wordcloud_viz \
  -P format=html \
  -P width=1000 \
  -P height=600 \
  -o nuvem_interativa.html

# Alta resolução para publicação
qualia visualize data.json -p wordcloud_viz \
  -P width=2000 \
  -P height=1500 \
  -P format=svg \
  -o nuvem_publicacao.svg
```

## 📊 Frequency Chart - Gráficos de Frequência

### Gráfico de Barras
```bash
# Top 20 palavras em barras
qualia analyze doc.txt -p word_frequency | \
qualia visualize -p frequency_chart \
  -P chart_type=bar \
  -P top_n=20 \
  -P title="20 Palavras Mais Frequentes" \
  -o barras.html
```

### Gráfico Horizontal (melhor para muitas palavras)
```bash
qualia visualize frequencies.json -p frequency_chart \
  -P chart_type=horizontal_bar \
  -P top_n=30 \
  -P color_scheme=blues \
  -o barras_horizontal.html
```

### Comparação entre Documentos
```bash
# Analisar múltiplos documentos
for doc in data/interviews/*.txt; do
    name=$(basename "$doc" .txt)
    qualia analyze "$doc" -p word_frequency \
      --output "results/freq_${name}.json"
done

# Visualizar cada um
for freq in results/freq_*.json; do
    name=$(basename "$freq" .json)
    qualia visualize "$freq" -p frequency_chart \
      -P title="Frequências - ${name}" \
      -o "results/chart_${name}.html"
done
```

## 🎨 Pipelines Completos com Visualização

### Pipeline de Análise Completa
```yaml
# configs/pipelines/full_analysis_viz.yaml
name: complete_visual_analysis
description: Análise completa com múltiplas visualizações

steps:
  # 1. Limpeza
  - plugin: teams_cleaner
    config:
      remove_timestamps: true
      create_variants: ["full", "participants_only"]
  
  # 2. Análise geral
  - plugin: word_frequency
    config:
      min_word_length: 4
      remove_stopwords: true
    output_name: freq_geral
  
  # 3. Análise por speaker
  - plugin: word_frequency
    config:
      by_speaker: true
      min_word_length: 5
    output_name: freq_speaker
  
  # 4. Nuvem de palavras geral
  - plugin: wordcloud_viz
    config:
      max_words: 100
      format: html
      colormap: viridis
    input_from: freq_geral
    output_name: cloud_geral
  
  # 5. Gráfico de barras
  - plugin: frequency_chart
    config:
      chart_type: horizontal_bar
      top_n: 25
      interactive: true
    input_from: freq_geral
    output_name: chart_geral
  
  # 6. Dashboard compositor (futuro)
  # - plugin: dashboard_composer
  #   config:
  #     template: research_report
  #     include: [cloud_geral, chart_geral]
```

### Pipeline para Múltiplas Entrevistas
```bash
#!/bin/bash
# Script: analyze_all_interviews.sh

# Criar diretório de resultados com timestamp
OUTPUT_DIR="results/batch_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

# Configuração do pipeline
PIPELINE_CONFIG="configs/pipelines/interview_analysis.yaml"

# Processar cada entrevista
for interview in data/interviews/*.txt; do
    basename=$(basename "$interview" .txt)
    echo "Processando: $basename"
    
    # Executar pipeline
    qualia pipeline "$interview" \
        --config "$PIPELINE_CONFIG" \
        --output-dir "$OUTPUT_DIR/$basename/"
    
    # Gerar visualizações adicionais
    qualia visualize "$OUTPUT_DIR/$basename/freq_geral.json" \
        -p wordcloud_viz \
        -P format=png \
        -P width=1600 \
        -P height=1200 \
        -o "$OUTPUT_DIR/$basename/wordcloud_hd.png"
done

# Gerar índice HTML com todas as visualizações
python generate_report.py "$OUTPUT_DIR"
```

## 🔧 Configurações Metodológicas com Visualização

```yaml
# configs/methodologies/qualitative_research_2024.yaml
name: "Metodologia Pesquisa Qualitativa 2024"
author: "Equipe de Pesquisa"
version: "1.0"

analysis_params:
  word_frequency:
    min_word_length: 4
    remove_stopwords: true
    language: portuguese
    justification: "Palavras < 4 letras geralmente não carregam significado"

visualization_params:
  wordcloud:
    max_words: 100
    colormap: viridis
    background_color: white
    justification: "100 palavras captura essência sem poluir visualização"
  
  frequency_chart:
    top_n: 25
    chart_type: horizontal_bar
    justification: "25 termos mais relevantes, horizontal para legibilidade"

pipeline:
  - analyze: word_frequency
  - visualize: wordcloud_viz
  - visualize: frequency_chart
```

## 📈 Análise Temporal (Exemplo Avançado)

```python
# Script Python para análise temporal com visualizações
import subprocess
import json
from pathlib import Path
import plotly.graph_objects as go

# Analisar transcrições por mês
months = ['janeiro', 'fevereiro', 'marco']
word_evolution = {}

for month in months:
    # Executar análise
    result = subprocess.run([
        'qualia', 'analyze', 
        f'data/{month}_transcript.txt',
        '-p', 'word_frequency',
        '--format', 'json'
    ], capture_output=True, text=True)
    
    data = json.loads(result.stdout)
    
    # Coletar top 10 palavras
    for word, freq in data['top_words'][:10]:
        if word not in word_evolution:
            word_evolution[word] = {}
        word_evolution[word][month] = freq

# Criar gráfico de evolução
fig = go.Figure()

for word, freqs in word_evolution.items():
    x = list(freqs.keys())
    y = list(freqs.values())
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name=word))

fig.update_layout(
    title="Evolução de Termos Chave ao Longo do Tempo",
    xaxis_title="Mês",
    yaxis_title="Frequência"
)

fig.write_html("results/evolucao_temporal.html")
```

## 🎯 Dicas e Boas Práticas

### 1. Escolher Formato Apropriado
- **PNG**: Para incluir em documentos/apresentações
- **SVG**: Para publicações (escala infinita)
- **HTML**: Para exploração interativa

### 2. Cores e Estética
- `viridis`: Boa para impressão P&B
- `plasma`: Vibrante para apresentações
- `blues/reds`: Monotemático profissional

### 3. Tamanhos Recomendados
- Apresentação: 1024x768
- Publicação: 2000x1500
- Web: 800x600

### 4. Pipeline Otimizado
```bash
# Criar alias para pipeline comum
alias qa-visual='qualia pipeline --config configs/pipelines/standard_visual.yaml'

# Usar
qa-visual documento.txt --output-dir results/
```

## 🔮 Próximos Visualizadores Planejados

1. **timeline_viz**: Visualização temporal de eventos
2. **network_viz**: Grafos de relações entre conceitos
3. **heatmap_viz**: Mapas de calor para padrões
4. **dashboard_composer**: Combina múltiplas visualizações
5. **comparison_viz**: Compara múltiplos documentos

Estes exemplos mostram o poder de combinar análise com visualização no Qualia! 🚀