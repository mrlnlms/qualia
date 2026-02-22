# Qualia Core

Framework para análise qualitativa de textos. Recebe textos (feedbacks, atas, transcrições) e gera análises + visualizações automaticamente.

## O que é

Qualia nasceu da necessidade de parar de reescrever os mesmos scripts de análise de texto em cada projeto. É um sistema de plugins onde cada análise é independente, reutilizável e se conecta com as outras automaticamente.

O core é "burro" de propósito — ele não sabe o que é sentimento, frequência ou nuvem de palavras. Ele só descobre quais plugins existem, resolve dependências entre eles e executa. Toda a inteligência fica nos plugins.

**Estágio atual:** Alpha (v0.1.0) — funcional para uso pessoal e experimentação.

## O que funciona hoje

7 plugins implementados:

| Plugin | Tipo | O que faz |
|--------|------|-----------|
| `word_frequency` | Analyzer | Conta palavras, filtra stopwords, identifica termos principais |
| `sentiment_analyzer` | Analyzer | Detecta sentimento do texto (positivo/negativo/neutro) via TextBlob |
| `readability_analyzer` | Analyzer | Calcula legibilidade do texto (score 0-100, nível de dificuldade) |
| `teams_cleaner` | Document | Limpa transcrições do Teams/Zoom (remove timestamps, organiza speakers) |
| `wordcloud_viz` | Visualizer | Gera nuvem de palavras (PNG, SVG ou HTML interativo) |
| `frequency_chart` | Visualizer | Cria gráficos de frequência (barras, pizza, treemap) com Plotly |
| `sentiment_viz` | Visualizer | Visualiza resultados de sentimento em dashboards |

## Como instalar

```bash
git clone https://github.com/mrlnlms/qualia.git
cd qualia
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Como usar

### CLI — linha de comando
```bash
# Ver plugins disponíveis
qualia list

# Analisar um texto
qualia analyze meu_texto.txt -p word_frequency

# Limpar transcrição do Teams
qualia process transcricao.txt -p teams_cleaner

# Com parâmetros customizados
qualia analyze texto.txt -p word_frequency -P min_word_length=4 -P language=portuguese
```

### API — interface web
```bash
python -m uvicorn qualia.api:app --port 8000
```
Abre http://localhost:8000/docs — interface Swagger onde você testa todos os endpoints pelo navegador.

Endpoints principais:
- `GET /plugins` — lista plugins disponíveis
- `POST /analyze/{plugin_id}` — executa análise em texto
- `POST /process/{plugin_id}` — processa documento
- `POST /visualize/{plugin_id}` — gera visualização
- `POST /pipeline` — executa sequência de plugins

### Menu interativo
```bash
qualia menu
```
Navegação por setas, sem precisar decorar comandos.

## Criar seu próprio plugin

O diferencial do Qualia é que criar um plugin novo é simples. O sistema descobre sozinho.

**1. Criar a pasta:**
```bash
mkdir plugins/meu_plugin
```

**2. Criar `plugins/meu_plugin/__init__.py`:**
```python
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document

class MeuPlugin(BaseAnalyzerPlugin):
    def meta(self):
        return PluginMetadata(
            id="meu_plugin",
            name="Meu Plugin",
            type=PluginType.ANALYZER,
            version="1.0.0",
            description="Faz tal coisa",
            provides=["resultado"],
            requires=[],
            parameters={}
        )

    def _analyze_impl(self, document, config, context):
        text = document.content
        # sua lógica aqui
        return {"resultado": "..."}
```

**3. Pronto.** Na próxima vez que o Qualia iniciar, ele descobre o plugin sozinho. Aparece na CLI, na API e no menu sem configuração extra.

Tipos de plugin disponíveis: `BaseAnalyzerPlugin`, `BaseDocumentPlugin`, `BaseVisualizerPlugin`.

## Estrutura do projeto

```
qualia/
├── qualia/
│   ├── core/           # Engine — descoberta, dependências, cache, execução
│   ├── cli/            # Interface de terminal (Click + Rich)
│   │   └── commands/   # 11 comandos (analyze, batch, export, watch, etc.)
│   └── api/            # REST API (FastAPI)
│       ├── monitor.py  # Dashboard de monitoramento em tempo real (SSE)
│       └── webhooks.py # Endpoints de webhook
├── plugins/            # Plugins de análise (cada um em sua pasta)
├── tests/              # Testes (pytest)
├── ops/                # Scripts operacionais (backup, monitoramento)
├── tools/              # Utilitários (gerador de plugins)
├── Dockerfile          # Build multi-stage
└── docker-compose.yml  # API + nginx + Redis + Prometheus (opcional)
```

## Stack

- **Core:** Python 3.9+
- **CLI:** Click, Rich
- **API:** FastAPI, Uvicorn, Pydantic
- **NLP:** TextBlob, NLTK, langdetect
- **Visualização:** Matplotlib, Plotly, WordCloud
- **Infra:** Docker, nginx, SSE para monitoramento

## Status e limitações

**Funciona:**
- Todos os 7 plugins executam corretamente
- API com Swagger autodocumentado
- Sistema de cache por hash de conteúdo
- Resolução automática de dependências entre plugins
- Backup automatizado com restore
- Dashboard de monitoramento em tempo real
- Docker multi-stage para deploy

**Limitações conhecidas:**
- `sentiment_analyzer` usa TextBlob, que tem suporte limitado a português (retorna polaridade 0 para muitos textos em PT)
- Aceita apenas TXT, CSV e JSON — sem suporte a PDF ainda
- Testes precisam de revisão e atualização
- CI/CD no GitHub Actions está desabilitado

## Licença

MIT — use como quiser.
