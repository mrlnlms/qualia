# 📚 Development Log - Qualia Core

Este documento registra a evolução do projeto para facilitar continuidade entre sessões.

## 🎯 Visão Geral

**Qualia Core** é um framework bare metal para análise qualitativa que transforma a experiência de "procurar scripts perdidos" em "funcionalidade permanente e organizada".

## 📅 Timeline de Desenvolvimento

### Dezembro 2024 - Fundação

#### Sessão 1 - Arquitetura Bare Metal
- **Data**: [Inserir data]
- **Conquistas**:
  - ✅ Definição da arquitetura bare metal
  - ✅ Implementação do Core agnóstico
  - ✅ Sistema de plugins com auto-descoberta
  - ✅ Interfaces base (IPlugin, IAnalyzerPlugin, etc)
  - ✅ Document object como single source of truth
  - ✅ Dependency resolver com detecção de ciclos
  - ✅ Cache manager inteligente

- **Decisões Arquiteturais**:
  - Core não conhece NENHUM tipo de análise
  - Plugins se auto-descrevem completamente
  - Configuração como metodologia científica
  - Document-centric architecture

- **Código Principal**:
  ```python
  # qualia/core/__init__.py
  - QualiaCore: Orquestrador puro
  - PluginMetadata: Auto-descrição
  - IPlugin e subclasses: Contratos
  - Document: Container de análises
  - DependencyResolver: Grafo de dependências
  - CacheManager: Cache por hash
  ```

#### Sessão 2 - Primeiros Plugins e CLI
- **Conquistas**:
  - ✅ Plugin `word_frequency` (analyzer)
  - ✅ Plugin `teams_cleaner` (document processor)
  - ✅ Plugin `wordcloud_viz` (visualizer)
  - ✅ Plugin `frequency_chart` (visualizer)
  - ✅ CLI completa com Click + Rich
  - ✅ Setup.py para instalação
  - ✅ Comandos: list, inspect, analyze, process, pipeline
  - ✅ Visualizações funcionando (PNG e HTML interativo)
  - ✅ Pipelines com análise + visualização integradas

- **Problemas Resolvidos**:
  - Import de `cli.py` vs `cly.py` (typo)
  - Configuração do interpretador Python no VSCode
  - Instalação de dependências no ambiente virtual
  - Alias para execução simplificada
  - Template HTML do wordcloud (escape de chaves)

## 🏗️ Estado Atual da Arquitetura

### Core (Funcional)
```python
QualiaCore:
  - discover_plugins()
  - execute_plugin()
  - execute_pipeline()
  - add_document()
```

### Plugins Implementados
1. **word_frequency**
   - Conta palavras com múltiplos parâmetros
   - Suporta análise por speaker
   - Remove stopwords configurável

2. **teams_cleaner**
   - Limpa transcrições do Teams
   - Cria variantes (participants_only, etc)
   - Quality report com score

3. **wordcloud_viz**
   - Gera nuvens de palavras
   - Formatos: PNG, SVG, HTML interativo
   - Múltiplos esquemas de cores
   - Template D3.js para versão web

4. **frequency_chart**
   - Gráficos de barras (vertical/horizontal)
   - Gráficos de linha e área
   - Plotly para versões interativas
   - Matplotlib para estáticos

### CLI Comandos
- `qualia list [-t type] [-d]`
- `qualia inspect <plugin>`
- `qualia analyze <doc> -p <plugin> [-P key=value]`
- `qualia process <doc> -p <plugin> [--save-as]`
- `qualia pipeline <doc> -c <config> [-o dir]`
- `qualia init`

## 🚀 Próximos Passos Planejados

### Fase 3 - Comando Visualize (PRÓXIMO IMEDIATO)
- [x] Interface IVisualizerPlugin ✓
- [x] wordcloud_viz ✓
- [x] frequency_chart ✓
- [ ] Comando `visualize` na CLI
- [ ] dashboard_composer
- [ ] network_viz

### Fase 4 - Mais Analyzers
- [ ] sentiment_analyzer
- [ ] lda_analyzer
- [ ] narrative_structure
- [ ] speaker_dynamics

### Fase 5 - API REST
- [ ] FastAPI setup
- [ ] Endpoints básicos
- [ ] WebSocket para real-time

### Fase 6 - Obsidian Plugin
- [ ] Plugin básico
- [ ] Análise de notas
- [ ] Embed de resultados

## 🛠️ Configuração do Ambiente

### Dependências Principais
```txt
click>=8.0          # CLI
rich>=13.0          # Terminal formatting
pyyaml>=6.0         # Configurações
pydantic>=2.0       # Validação
nltk>=3.8           # NLP
pandas              # Manipulação de dados
numpy               # Computação numérica

# Próximas adições
plotly              # Visualizações interativas
matplotlib          # Visualizações estáticas
wordcloud           # Nuvens de palavras
scikit-learn        # LDA, clustering
textblob            # Sentiment analysis
```

### Estrutura de Diretórios
```
qualia/                 # Código principal
├── core/              # Engine (✓ implementado)
├── cli.py             # Interface CLI (✓ implementado)
├── document_lab/      # (próxima fase)
├── visual_engine/     # (próxima fase)
└── ...

plugins/               # Plugins instalados
├── word_frequency/    # (✓ implementado)
├── teams_cleaner/     # (✓ implementado)
└── [novos plugins]/

configs/              # Configurações do usuário
├── pipelines/        # Pipelines salvos
└── methodologies/    # Metodologias científicas

data/                 # Documentos
├── raw/             # Originais
└── processed/       # Processados
```

## 💡 Padrões Estabelecidos

### Criando um Analyzer
```python
class MyAnalyzer(IAnalyzerPlugin):
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="my_analyzer",
            type=PluginType.ANALYZER,
            provides=["output_key"],
            requires=[],  # Dependencies
            parameters={
                "param": {"type": "int", "default": 10}
            }
        )
    
    def analyze(self, document, config, context):
        # Implementação
        return {"output_key": result}
```

### Criando um Visualizer (próximo)
```python
class MyVisualizer(IVisualizerPlugin):
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            accepts=["word_frequencies"],
            outputs=["png", "html"],
            parameters={...}
        )
    
    def render(self, data, config, output_path):
        # Gerar visualização
        return str(output_path)
```

## 🐛 Issues Conhecidas

1. **Performance**: Cache não tem limite de tamanho
2. **Validação**: Parâmetros de plugin precisam melhor validação
3. **Documentação**: Falta documentação inline em alguns métodos
4. **Testes**: Precisamos de testes unitários

## 📝 Notas de Design

### Por que "Bare Metal"?
- Core não tem conhecimento de domínio
- Máxima flexibilidade para plugins
- Evolução sem breaking changes
- Complexidade fica nos plugins

### Por que "Configuration as Methodology"?
- Pesquisa precisa ser reproduzível
- Parâmetros têm justificativa científica
- Configurações são conhecimento codificado
- "tese_diabetes_2024.yaml" = metodologia reutilizável

## 🔗 Recursos

- **GitHub**: https://github.com/mrlnlms/qualia
- **Inspirações**: spaCy, Kedro, Prodigy
- **Projeto Original**: transcript-analyzer (sendo substituído)

---

**Última Atualização**: Dezembro 2024
**Próxima Sessão**: Implementar visualizadores