# 📊 Estado Atual do Projeto Qualia Core

**Data**: Dezembro 2024  
**Versão**: 0.1.0  
**Status**: Funcional com 4 plugins

## ✅ O que está Pronto

### Core Engine
- **Arquitetura Bare Metal**: Core não conhece tipos de análise
- **Sistema de Plugins**: Auto-descoberta e carregamento dinâmico
- **Resolução de Dependências**: Grafo com detecção de ciclos
- **Cache Inteligente**: Por hash de documento+plugin+config
- **Document Object**: Single source of truth para análises

### Plugins Implementados (4)

#### Analyzers (2)
1. **word_frequency**
   - Frequência de palavras com configurações avançadas
   - Suporte para múltiplos idiomas (stopwords)
   - Análise por speaker/segmento
   - Output: frequencies, vocabulary_size, top_words

2. **teams_cleaner**
   - Limpeza de transcrições Microsoft Teams
   - Normalização de speakers
   - Criação de variantes (participants_only, etc)
   - Quality report com score

#### Visualizers (2)
3. **wordcloud_viz**
   - Nuvem de palavras em PNG/SVG/HTML
   - HTML interativo com D3.js
   - Múltiplos esquemas de cores
   - Configuração de tamanho e densidade

4. **frequency_chart**
   - Gráficos de barras (vertical/horizontal)
   - Gráficos de linha e área
   - Versões interativas (Plotly) e estáticas (Matplotlib)
   - Export HTML e PNG

### CLI (Comandos Funcionais)
- `qualia list [--type] [--detailed]` - Lista plugins
- `qualia inspect <plugin>` - Detalhes do plugin
- `qualia analyze <doc> -p <plugin>` - Executa analyzer
- `qualia process <doc> -p <plugin>` - Processa documento
- `qualia pipeline <doc> -c <config>` - Executa pipeline
- `qualia init` - Inicializa estrutura

### Infraestrutura
- **setup.py**: Instalação com `pip install -e .`
- **Ambiente Virtual**: Dependências isoladas
- **Rich CLI**: Interface colorida e tabelas
- **YAML/JSON**: Configurações e pipelines

## 🏗️ Estrutura de Arquivos

```
qualia/
├── __init__.py
├── __main__.py          # Entry point
├── cli.py               # Interface CLI (Click + Rich)
├── core/
│   └── __init__.py      # QualiaCore, interfaces, Document
├── document_lab/        # [Futuro]
├── para_meta/           # [Futuro]  
├── quali_metrics/       # [Futuro]
└── visual_engine/       # [Futuro]

plugins/
├── word_frequency/
│   └── __init__.py
├── teams_cleaner/
│   └── __init__.py
├── wordcloud_viz/
│   ├── __init__.py
│   └── requirements.txt
└── frequency_chart/
    ├── __init__.py
    └── requirements.txt

configs/
├── pipelines/
│   ├── example.yaml
│   └── full_visual.yaml
└── methodologies/       # [Futuro]

results/                 # Outputs gerados
data/                    # Documentos para análise
```

## 📦 Dependências Principais

### Core
- click>=8.0 (CLI)
- rich>=13.0 (Terminal formatting)
- pyyaml>=6.0 (Configurações)
- pydantic>=2.0 (Validação)

### Análise
- nltk>=3.8 (NLP)
- pandas (Manipulação)
- numpy (Computação)

### Visualização
- matplotlib>=3.5.0 (Gráficos estáticos)
- wordcloud>=1.9.0 (Nuvens de palavras)
- plotly>=5.0.0 (Gráficos interativos)
- kaleido>=0.2.0 (Export Plotly)

## 🔄 Pipelines Funcionais

### Pipeline Básico (example.yaml)
```yaml
steps:
  - plugin: teams_cleaner
    config: {remove_timestamps: false}
  - plugin: word_frequency
    config: {min_word_length: 4}
```

### Pipeline Visual (full_visual.yaml)
```yaml
steps:
  - plugin: teams_cleaner
    config: {remove_system_messages: true}
  - plugin: word_frequency  
    config: {remove_stopwords: true}
  # Visualizadores via script separado por enquanto
```

## 🐛 Limitações Atuais

1. **Sem comando `visualize`**: Visualizadores precisam ser chamados via Python
2. **Pipeline não conecta analyzers→visualizers**: Precisa salvar JSON intermediário
3. **Sem composer**: Não combina múltiplas visualizações ainda
4. **Sem API REST**: Apenas CLI disponível
5. **Sem testes unitários**: Precisamos adicionar

## 🎯 Próximo Passo Imediato

### Adicionar comando `visualize` na CLI
```python
@cli.command()
@click.argument('data_path')
@click.option('--plugin', '-p', required=True)
@click.option('--output', '-o')
def visualize(data_path, plugin, output):
    """Visualiza dados com plugin específico"""
    # Implementar...
```

Isso permitirá:
```bash
qualia analyze doc.txt -p word_frequency -o freq.json
qualia visualize freq.json -p wordcloud_viz -o cloud.png
qualia visualize freq.json -p frequency_chart -P chart_type=horizontal_bar
```

## 📈 Métricas do Projeto

- **Linhas de Código**: ~2000 (estimado)
- **Plugins**: 4 funcionais
- **Comandos CLI**: 6 implementados
- **Formatos de Output**: JSON, YAML, PNG, SVG, HTML
- **Cobertura de Testes**: 0% (a implementar)

## 🔗 Recursos

- **GitHub**: https://github.com/mrlnlms/qualia
- **Documentação**: Em desenvolvimento
- **Exemplos**: Ver pasta `configs/pipelines/`

---

**Nota**: Este documento reflete o estado exato do projeto após a segunda sessão de desenvolvimento. Use como referência para continuar o trabalho.