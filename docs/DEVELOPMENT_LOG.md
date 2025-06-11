# 📚 Development Log - Qualia Core

Este documento registra a evolução do projeto para facilitar continuidade entre sessões.

## 🎯 Visão Geral

**Qualia Core** é um framework bare metal para análise qualitativa que transforma a experiência de "procurar scripts perdidos" em "funcionalidade permanente e organizada".

## 📅 Timeline de Desenvolvimento

### Dezembro 2024 - Fundação

#### Sessão 1 - Arquitetura Bare Metal
- **Data**: Início Dezembro 2024
- **Conquistas**:
  - ✅ Definição da arquitetura bare metal
  - ✅ Implementação do Core agnóstico
  - ✅ Sistema de plugins com auto-descoberta
  - ✅ Interfaces base (IPlugin, IAnalyzerPlugin, etc)
  - ✅ Document object como single source of truth
  - ✅ Dependency resolver com detecção de ciclos
  - ✅ Cache manager inteligente

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

#### Sessão 3 - Comando Visualize e Base Classes (11 Dez 2024)
- **Conquistas**:
  - ✅ Comando `visualize` implementado na CLI
  - ✅ Base classes para reduzir código repetitivo
  - ✅ Refatoração mínima dos plugins (mantendo funcionalidades)
  - ✅ Correção de compatibilidade Python 3.13
  - ✅ Sistema completo funcionando end-to-end

- **Problemas Resolvidos**:
  - TypeError com Path objects vs strings
  - click.Exit não existe no Python 3.13 → SystemExit
  - validate_config retornando bool vs Tuple[bool, Optional[str]]
  - PluginLoader tentando instanciar base classes
  - PluginMetadata não aceita campo 'author'

- **Arquitetura de Base Classes**:
  ```python
  BaseAnalyzerPlugin → analyze() → _analyze_impl()
  BaseVisualizerPlugin → render() → _render_impl()
  BaseDocumentPlugin → process() → _process_impl()
  ```

## 🏗️ Estado Atual da Arquitetura

### Core (Funcional)
```python
QualiaCore:
  - discover_plugins()
  - execute_plugin()
  - execute_pipeline()
  - add_document()

Base Classes (novo):
  - BaseAnalyzerPlugin
  - BaseVisualizerPlugin
  - BaseDocumentPlugin
```

### Plugins Implementados (4)
1. **word_frequency** - Análise de frequência com NLTK
2. **teams_cleaner** - Limpeza de transcrições Teams
3. **wordcloud_viz** - Nuvem de palavras (PNG/SVG/HTML)
4. **frequency_chart** - Gráficos diversos (Plotly/Matplotlib)

### CLI Comandos Funcionais
- `qualia list [-t type] [-d]`
- `qualia inspect <plugin>`
- `qualia analyze <doc> -p <plugin> [-P key=value]`
- `qualia process <doc> -p <plugin> [--save-as]`
- `qualia pipeline <doc> -c <config> [-o dir]`
- `qualia visualize <data> -p <plugin> [-o output]` ← NOVO!
- `qualia list-visualizers`
- `qualia init`

## 🎨 Comando Visualize

### Uso
```bash
qualia visualize data.json -p wordcloud_viz -o cloud.png
qualia visualize data.json -p frequency_chart -o chart.html -P chart_type=horizontal_bar
```

### Características
- Auto-detecção de formato pela extensão
- Suporte a parâmetros via CLI (-P)
- Validação automática de dados
- Criação de diretórios se necessário

## 🔧 Padrões Estabelecidos

### Plugin com Base Class
```python
from qualia.core import BaseAnalyzerPlugin

class MyAnalyzer(BaseAnalyzerPlugin):
    def meta(self) -> PluginMetadata:
        return PluginMetadata(...)
    
    def _analyze_impl(self, document, config, context):
        # Apenas lógica de negócio
        # Validações já feitas pela base class
```

### Benefícios das Base Classes
- 30% menos código nos plugins
- Validações automáticas
- Conversão de tipos (str → Path)
- Aplicação de defaults
- Compatibilidade futura (API, GUI)

## 🐛 Issues Resolvidas

### Python 3.13 Compatibility
- `click.Exit` → `SystemExit`
- Type hints atualizados

### Validações
- `validate_config` retorna `Tuple[bool, Optional[str]]`
- Todos os plugins implementam corretamente

### PluginLoader
- Ignora classes Base* e abstratas
- Carrega apenas plugins concretos

## 📝 Notas Técnicas

### Decisão: Base Classes vs Interfaces Puras
- Optamos por base classes para reduzir repetição
- Mantém filosofia bare metal (base classes são opcionais)
- Facilita evolução sem breaking changes

### Refatoração Mínima
- Mudanças mínimas nos plugins existentes
- Preservação de exemplos e documentação
- Foco em compatibilidade

## 🚀 Próximos Passos

1. **Mais Analyzers**
   - sentiment_analyzer
   - lda_analyzer
   - narrative_structure

2. **Dashboard Composer**
   - Combinar múltiplas visualizações
   - Templates de relatórios

3. **API REST**
   - FastAPI
   - Endpoints para análise
   - WebSocket para real-time

4. **Testes Unitários**
   - pytest
   - Coverage > 80%

## 🔗 Recursos

- **GitHub**: https://github.com/mrlnlms/qualia
- **Python**: 3.8+ (testado em 3.13)
- **Dependências principais**: click, rich, nltk, matplotlib, wordcloud, plotly

---

**Última Atualização**: 11 Dezembro 2024, 06:00 UTC
**Versão**: 0.1.0
**Status**: Funcional com comando visualize ✅