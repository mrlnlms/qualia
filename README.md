# 🔬 Qualia Core

Um framework bare metal para transformação de dados qualitativos em insights quantificados.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-100%25%20funcional-success.svg)](https://github.com/mrlnlms/qualia)
[![CLI](https://img.shields.io/badge/CLI-13%20comandos-green.svg)](https://github.com/mrlnlms/qualia)

> **Qualia** transforma análise qualitativa de "procurar scripts perdidos" em "funcionalidade permanente e organizada"

## 🚀 Quick Start

```bash
# Instalar e iniciar
git clone https://github.com/mrlnlms/qualia
cd qualia
pip install -e .

# Interface interativa
qualia menu
```

![Menu Demo](docs/images/menu_demo.gif) *(exemplo do menu interativo)*

## ✨ Funcionalidades Principais

### 🎨 Interface Interativa
```bash
qualia menu
```
- Wizards guiados para análise
- Configuração visual de parâmetros  
- Preview de resultados
- Tutoriais integrados

### 🔄 Processamento em Lote
```bash
# Processar múltiplos arquivos
qualia batch "docs/*.txt" -p word_frequency -j 4

# Monitorar pasta para novos arquivos
qualia watch inbox/ -p teams_cleaner -o processed/
```

### 📊 Análise e Visualização
```bash
# Análise de frequência
qualia analyze doc.txt -p word_frequency -P min_length=4

# Gerar nuvem de palavras
qualia visualize data.json -p wordcloud_viz -o cloud.png
```

### 🔁 Pipelines Configuráveis
```yaml
# pipeline.yaml
name: research_pipeline
steps:
  - plugin: teams_cleaner
    config: {remove_timestamps: true}
  - plugin: word_frequency
    config: {min_word_length: 4}
  - plugin: wordcloud_viz
    config: {colormap: viridis}
```

```bash
qualia pipeline doc.txt -c pipeline.yaml
```

## 📦 Plugins Disponíveis

| Plugin | Tipo | Descrição |
|--------|------|-----------|
| `word_frequency` | Analyzer | Análise de frequência com NLTK |
| `teams_cleaner` | Document | Limpeza de transcrições Teams |
| `wordcloud_viz` | Visualizer | Nuvem de palavras customizável |
| `frequency_chart` | Visualizer | Gráficos interativos (bar, pie, treemap) |

## 🛠️ Comandos CLI

### Comandos Básicos
- `qualia list` - Lista plugins disponíveis
- `qualia inspect <plugin>` - Detalhes do plugin
- `qualia analyze` - Executa análise
- `qualia process` - Processa documento
- `qualia visualize` - Cria visualização
- `qualia pipeline` - Executa pipeline

### Comandos Avançados (Novo!)
- `qualia watch` - Monitora pasta continuamente
- `qualia batch` - Processa múltiplos arquivos
- `qualia export` - Converte formatos (CSV, Excel, HTML)
- `qualia config` - Cria configurações interativamente

## 🔧 Desenvolvimento de Plugins

### Criar Novo Plugin
```bash
python tools/create_plugin.py sentiment_analyzer analyzer
```

### Estrutura Gerada
```python
class SentimentAnalyzer(BaseAnalyzerPlugin):
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="sentiment_analyzer",
            name="Sentiment Analyzer",
            provides=["sentiment_score"],
            parameters={
                "language": {
                    "type": "choice",
                    "options": ["pt", "en"],
                    "default": "pt"
                }
            }
        )
    
    def _analyze_impl(self, document, config, context):
        # 🚨 TODO: Implementar análise aqui!
        return {"sentiment_score": 0.8}
```

## 🏗️ Arquitetura

```
qualia/
├── core/           # Engine bare metal (não tem conhecimento de domínio)
├── cli/            # Interface modular
│   ├── commands/   # Um arquivo por comando
│   └── interactive # Menu interativo
└── plugins/        # Toda inteligência aqui
```

### Princípios
1. **Bare Metal**: Core só orquestra, não implementa
2. **Plugins**: Toda inteligência específica
3. **Base Classes**: Opcionais, reduzem 30% código
4. **Zero Coupling**: Plugins independentes

## 📊 Status do Projeto

- ✅ **100% Funcional** - Todos os testes passando
- ✅ **13 Comandos CLI** - Incluindo watch, batch, export
- ✅ **4 Plugins** - Prontos para uso
- ✅ **Menu Interativo** - Interface visual completa
- ✅ **Python 3.8-3.13** - Compatibilidade testada

## 🚀 Roadmap

### Próximo: API REST (2-3h)
```python
POST /analyze/{plugin_id}
GET /plugins
POST /pipeline
```

### Em Breve
- [ ] sentiment_analyzer - Análise de sentimentos
- [ ] dashboard_composer - Relatórios combinados
- [ ] theme_extractor - Extração de temas (LDA)
- [ ] Documentação completa (MkDocs)

## 🤝 Contribuindo

1. Fork o projeto
2. Crie plugin: `python tools/create_plugin.py meu_plugin analyzer`
3. Implemente e teste: `python plugins/meu_plugin/__init__.py`
4. Pull Request!

## 📚 Documentação

- [Development Log](DEVELOPMENT_LOG.md) - História do desenvolvimento
- [Project State](PROJECT_STATE.md) - Estado atual detalhado
- [Plugin Guide](docs/plugin_guide.md) - Como criar plugins
- [API Reference](docs/api_reference.md) - Documentação da API

## 📄 Licença

MIT License - Veja [LICENSE](LICENSE) para detalhes.

---

**Desenvolvido com ❤️ para transformar análise qualitativa**

*v0.1.0 - Dezembro 2024*