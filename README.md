# 🔬 Qualia Core

Um framework bare metal para transformação de dados qualitativos em insights quantificados.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-100%25%20funcional-success.svg)](https://github.com/yourusername/qualia)
[![CLI](https://img.shields.io/badge/CLI-13%20comandos-green.svg)](https://github.com/yourusername/qualia)
[![API](https://img.shields.io/badge/API-REST%20%2B%20Swagger-orange.svg)](https://github.com/yourusername/qualia)

> **Qualia** transforma análise qualitativa de "procurar scripts perdidos" em "funcionalidade permanente e organizada"

## 🚀 Quick Start

```bash
# Instalar
git clone https://github.com/yourusername/qualia
cd qualia
pip install -r requirements.txt
pip install -e .

# Interface interativa
qualia menu

# API REST
python run_api.py --reload
# Acesse: http://localhost:8000/docs
```

## ✨ Funcionalidades Principais

### 🎨 Interface Interativa
```bash
qualia menu
```
- Wizards guiados para análise
- Configuração visual de parâmetros  
- Preview de resultados
- Tutoriais integrados

### 🌐 API REST com Documentação
```bash
python run_api.py
```
- 11 endpoints RESTful
- Documentação Swagger automática
- Upload de arquivos
- Execução de pipelines via HTTP

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

# Análise de sentimento
qualia analyze feedback.txt -p sentiment_analyzer

# Gerar visualizações
qualia visualize data.json -p wordcloud_viz -o cloud.png
qualia visualize sentiment.json -p sentiment_viz -o dashboard.html
```

### 🔁 Pipelines Configuráveis
```yaml
# pipeline.yaml
name: complete_analysis
steps:
  - plugin: teams_cleaner
    config: {remove_timestamps: true}
  - plugin: sentiment_analyzer
    config: {analyze_sentences: true}
  - plugin: word_frequency
    config: {min_word_length: 4}
```

```bash
qualia pipeline transcript.txt -c pipeline.yaml
```

## 📦 Plugins Disponíveis

| Plugin | Tipo | Descrição | Novo |
|--------|------|-----------|------|
| `word_frequency` | Analyzer | Análise de frequência com NLTK | |
| `sentiment_analyzer` | Analyzer | Análise de sentimento (TextBlob) | ✨ |
| `teams_cleaner` | Document | Limpeza de transcrições Teams | |
| `wordcloud_viz` | Visualizer | Nuvem de palavras customizável | |
| `frequency_chart` | Visualizer | Gráficos interativos (bar, pie, treemap) | |
| `sentiment_viz` | Visualizer | Visualizações de sentimento | ✨ |

## 🛠️ Comandos CLI

### Comandos Básicos
- `qualia list` - Lista plugins disponíveis
- `qualia inspect <plugin>` - Detalhes do plugin
- `qualia analyze` - Executa análise
- `qualia process` - Processa documento
- `qualia visualize` - Cria visualização
- `qualia pipeline` - Executa pipeline

### Comandos Avançados
- `qualia watch` - Monitora pasta continuamente
- `qualia batch` - Processa múltiplos arquivos
- `qualia export` - Converte formatos (CSV, Excel, HTML)
- `qualia config` - Cria configurações interativamente

## 🌐 API REST

### Executar API
```bash
# Desenvolvimento (com auto-reload)
python run_api.py --reload

# Produção
python run_api.py --workers 4
```

### Endpoints Principais
- `GET /plugins` - Lista todos os plugins
- `POST /analyze/{plugin_id}` - Executa análise
- `POST /visualize/{plugin_id}` - Gera visualização
- `POST /pipeline` - Executa pipeline completo

### Exemplo de Uso
```python
import requests

# Analisar sentimento
response = requests.post(
    "http://localhost:8000/analyze/sentiment_analyzer",
    json={"text": "Este produto é incrível!"}
)
print(response.json()["result"]["sentiment_label"])  # "positivo"
```

Documentação interativa disponível em: http://localhost:8000/docs

## 🔧 Desenvolvimento de Plugins

### Criar Novo Plugin
```bash
python tools/create_plugin.py meu_analyzer analyzer
```

### Estrutura Mínima
```python
class MeuAnalyzer(BaseAnalyzerPlugin):
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="meu_analyzer",
            name="Meu Analyzer",
            provides=["minha_metrica"],
            parameters={
                "param1": {
                    "type": "integer",
                    "default": 10
                }
            }
        )
    
    def _analyze_impl(self, document, config, context):
        # Implementar análise
        return {"minha_metrica": 42}
```

Plugin aparece automaticamente em:
- CLI: `qualia list`
- API: `GET /plugins`
- Menu: Interface interativa

## 🏗️ Arquitetura

```
qualia/
├── core/           # Engine bare metal (agnóstico)
├── cli/            # Interface de linha de comando
│   ├── commands/   # Comandos modularizados
│   └── interactive # Menu interativo
├── api/            # API REST com FastAPI
└── plugins/        # Plugins com lógica específica
```

### Princípios
1. **Bare Metal**: Core só orquestra, não implementa
2. **Auto-discovery**: Plugins se registram automaticamente
3. **Base Classes**: Reduzem 30% do boilerplate
4. **Zero Coupling**: Plugins totalmente independentes

## 📊 Status do Projeto

- ✅ **100% Funcional** - Todos os testes passando
- ✅ **13 Comandos CLI** - Interface completa
- ✅ **11 Endpoints API** - REST com Swagger
- ✅ **6 Plugins** - Prontos para uso
- ✅ **Python 3.8-3.13** - Compatibilidade testada

## 🚀 Roadmap

### Próximo: Webhooks (1-2h)
```python
POST /webhook/github    # CI/CD insights
POST /webhook/slack     # Análise de conversas
POST /webhook/custom    # Qualquer serviço
```

### Em Desenvolvimento
- [ ] Dashboard Composer - Relatórios combinados
- [ ] Frontend React - Interface web
- [ ] theme_extractor - Análise de tópicos (LDA)
- [ ] Docker + Deploy - Containerização

## 🤝 Contribuindo

1. Fork o projeto
2. Crie seu plugin: `python tools/create_plugin.py nome tipo`
3. Implemente seguindo os exemplos existentes
4. Teste: `python test_suite.py`
5. Pull Request!

## 📚 Documentação

- [Development Log](DEVELOPMENT_LOG.md) - História completa do desenvolvimento
- [Project State](PROJECT_STATE.md) - Estado atual detalhado
- [API Docs](API_README.md) - Referência completa da API
- [Lessons Learned](LESSONS_LEARNED_SESSION_6.md) - Aprendizados recentes
- [Plugin Examples](plugins/) - Código dos plugins

## 📄 Licença

MIT License - Veja [LICENSE](LICENSE) para detalhes.

---

**Desenvolvido com ❤️ para transformar análise qualitativa**

*v0.1.0 - Dezembro 2024*