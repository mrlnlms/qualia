# 🔬 Qualia Core

Um framework bare metal para transformação de dados qualitativos em insights quantificados, com interface interativa completa para análise qualitativa.

> **Qualia** (do latim "qualis") - experiências subjetivas qualitativas que este framework transforma em métricas objetivas para pesquisa mixed methods.

## 🎯 O Problema que Resolvemos

**Situação Atual**: 
- "Cadê aquele script de limpeza que fiz 6 meses atrás?"
- Procura em várias pastas: `lda_test_v3_final_FINAL.py`
- "Qual ambiente virtual era? Precisa instalar sklearn..."
- 30min debugando conflitos de versão
- Parâmetros diferentes da última vez

**Com Qualia**:
```bash
$ qualia menu  # Interface interativa completa!
# ou
$ qualia analyze documento.txt -p word_frequency
✅ Pronto! (usa configuração validada)
```

## 🚀 Filosofia Core

### Bare Metal = Orquestração Pura
- Core NÃO implementa features, apenas orquestra
- Core não conhece NENHUM tipo de análise
- Toda inteligência vem dos plugins
- **Zero conhecimento de domínio** no Core

### Scripts → Plugins Permanentes
Seus scripts úteis viram plugins permanentes:
```bash
# Antes: procurar script perdido
# Agora:
$ qualia process transcript.txt -p teams_cleaner -P remove_timestamps=true --save-as clean.txt
✅ Sempre disponível!
```

### Configuration as Methodology
- Cada parâmetro tem justificativa científica
- Configurações são assets reutilizáveis
- Metodologia vira código versionado

## 🏗️ Arquitetura

```
qualia/
├── core/              # Engine bare metal + Base Classes
├── cli/               # Interface CLI modular
│   ├── commands.py    # Comandos CLI
│   ├── formatters.py  # Formatadores Rich compartilhados
│   └── interactive/   # Menu interativo
│       ├── menu.py
│       ├── handlers.py
│       ├── tutorials.py
│       ├── utils.py
│       └── wizards.py
└── __main__.py

plugins/               # Inteligência específica
├── word_frequency/    # Analyzer implementado
├── teams_cleaner/     # Document processor implementado
├── wordcloud_viz/     # Visualizer implementado
├── frequency_chart/   # Visualizer implementado
└── [seu_plugin]/      # Adicione os seus!
```

## 🚀 Quickstart

```bash
# 1. Instalar
git clone https://github.com/mrlnlms/qualia.git
cd qualia
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -e .

# 2. Inicializar projeto
qualia init

# 3. Interface interativa (NOVO!)
qualia menu

# 4. Ou usar comandos diretos
qualia analyze documento.txt -p word_frequency -o analysis.json
qualia visualize analysis.json -p wordcloud_viz -o cloud.png
```

## 🎨 Menu Interativo (NOVO!)

O Qualia agora oferece uma interface interativa completa:

```bash
qualia menu
```

### Funcionalidades do Menu:
- 📄 **Análise de documentos** - Wizard guiado com configuração de parâmetros
- 🎨 **Visualização de resultados** - Escolha formato e personalização
- 🔄 **Pipelines** - Execute ou crie novos com assistente
- 🔍 **Explorar plugins** - Veja detalhes e documentação
- ⚙️ **Configurações** - Gerencie cache e dependências
- 📚 **Tutoriais integrados** - Aprenda com exemplos práticos

## 📝 Exemplos de Uso

### Análise Básica
```bash
# Análise simples
qualia analyze texto.txt -p word_frequency

# Com parâmetros customizados
qualia analyze texto.txt -p word_frequency \
  -P min_word_length=4 \
  -P remove_stopwords=true \
  -P language=portuguese
```

### Processamento de Transcrições
```bash
# Limpar transcrição do Teams (agora com -P!)
qualia process transcript.txt -p teams_cleaner -P remove_timestamps=true --save-as cleaned.txt

# Ver relatório de qualidade
qualia process transcript.txt -p teams_cleaner | grep "quality_score"
```

### Visualizações
```bash
# Nuvem de palavras
qualia visualize data.json -p wordcloud_viz -o cloud.png \
  -P background_color=black \
  -P colormap=plasma

# Gráfico interativo
qualia visualize data.json -p frequency_chart -o chart.html \
  -P chart_type=bar \
  -P top_n=20
```

### Pipeline Completo
```bash
# Executar pipeline configurado
qualia pipeline documento.txt -c configs/pipelines/example.yaml -o results/

# Pipeline exemplo (YAML):
name: research_pipeline
steps:
  - plugin: teams_cleaner
    config: {remove_timestamps: false}
  - plugin: word_frequency
    config: {min_word_length: 4}
```

## 📊 Plugins Disponíveis

### Analyzers
| Plugin | Descrição | Principais Features |
|--------|-----------|-------------------|
| **word_frequency** | Análise de frequência de palavras | Multi-idioma, stopwords, tokenização avançada |

### Document Processors
| Plugin | Descrição | Principais Features |
|--------|-----------|-------------------|
| **teams_cleaner** | Limpeza de transcrições Teams | Remove sistema, normaliza speakers, quality score |

### Visualizers
| Plugin | Descrição | Formatos |
|--------|-----------|----------|
| **wordcloud_viz** | Nuvem de palavras | PNG, SVG, HTML interativo |
| **frequency_chart** | Gráficos de frequência | Bar, horizontal_bar, line, area |

### Em Desenvolvimento
- **sentiment_analyzer**: Análise de sentimentos (TextBlob/VADER)
- **lda_analyzer**: Topic modeling com LDA
- **narrative_structure**: Análise de estrutura narrativa
- **dashboard_composer**: Relatórios combinados

## 🧪 Status: 89.5% Funcional

✅ **O que funciona**:
- Menu interativo completo com wizards e tutoriais
- Core engine com arquitetura bare metal
- Sistema de plugins com auto-descoberta
- 4 plugins totalmente funcionais
- CLI completa com todos os comandos
- Pipelines configuráveis
- Cache inteligente
- Base classes reduzindo 30% do código
- Suporte completo a parâmetros (-P)

🚧 **Em desenvolvimento**:
- [ ] Tipos faltantes no frequency_chart (pie, treemap, sunburst)
- [ ] Mais analyzers (sentiment, LDA)
- [ ] Dashboard composer
- [ ] API REST
- [ ] Testes unitários (34/38 passando)

## 🛠️ Desenvolvimento de Plugins

### Criar um Analyzer
```python
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType

class SentimentAnalyzer(BaseAnalyzerPlugin):
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="sentiment_analyzer",
            name="Sentiment Analyzer",
            type=PluginType.ANALYZER,
            version="1.0.0",
            description="Analisa sentimentos em textos",
            provides=["sentiment_score", "sentiment_label"],
            parameters={
                "language": {
                    "type": "choice",
                    "options": ["pt", "en"],
                    "default": "pt"
                }
            }
        )
    
    def _analyze_impl(self, document, config, context):
        # Implementar análise
        return {
            "sentiment_score": 0.8,
            "sentiment_label": "positive"
        }
```

### Criar um Visualizer
```python
from qualia.core import BaseVisualizerPlugin

class NetworkVisualizer(BaseVisualizerPlugin):
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="network_viz",
            name="Network Visualizer",
            type=PluginType.VISUALIZER,
            requires=["entity_relations"],
            provides=["network_graph"]
        )
    
    def _render_impl(self, data, config, output_path):
        # Implementar visualização
        # output_path já é Path object
        return output_path
```

## 🧪 Testando

```bash
# Suite de testes automatizada
python test_suite.py

# Teste rápido
echo '{"word_frequencies": {"test": 5}}' > test.json
python -m qualia visualize test.json -p wordcloud_viz -o test.png

# Limpar arquivos de teste
python cleanup.py
```

## 📚 Documentação

- **[DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md)** - História completa do desenvolvimento
- **[PROJECT_STATE.md](docs/PROJECT_STATE.md)** - Estado atual do projeto
- **[Technical Notes](docs/technical_notes.md)** - Notas técnicas e lições aprendidas
- **[Plugin Guide](docs/plugin_guide.md)** - Como criar plugins

## 🔧 Requisitos

- Python 3.8+ (testado até 3.13)
- Dependências principais:
  - click & rich (CLI e interface)
  - nltk (NLP)
  - matplotlib & plotly (visualizações)
  - wordcloud (nuvem de palavras)
  - pyyaml (configurações)
  - kaleido (export de gráficos)

## 🤝 Contribuindo

1. Fork o projeto
2. Crie um branch (`git checkout -b feature/novo-analyzer`)
3. Commit suas mudanças (`git commit -m 'Add sentiment analyzer'`)
4. Push (`git push origin feature/novo-analyzer`)
5. Abra um Pull Request

### Guidelines
- Use as base classes para reduzir código
- Adicione testes para novos plugins
- Documente parâmetros e outputs
- Siga os padrões estabelecidos

## 📜 Licença

MIT License - Livre para uso acadêmico e comercial.

## 🔗 Links

- **GitHub**: [github.com/mrlnlms/qualia](https://github.com/mrlnlms/qualia)
- **Issues**: [GitHub Issues](https://github.com/mrlnlms/qualia/issues)
- **Documentação**: [Wiki](https://github.com/mrlnlms/qualia/wiki)

---

**Visão**: Transformar análise qualitativa de "procurar scripts perdidos" para "framework permanente e extensível"

*Desenvolvido com ❤️ para pesquisadores qualitativos*

**v0.1.0** - Deze