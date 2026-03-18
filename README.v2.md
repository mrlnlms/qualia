# Qualia

API REST local para análise qualitativa. Recebe texto, áudio ou vídeo, devolve JSON. Extensível por plugins.

## Por que

Qualia nasceu de um problema prático: análises que funcionam mas ficam presas dentro do projeto onde foram feitas. Uma análise de sentimento escrita pra um TCC, um script de clustering feito pra pesquisa de VoC, uma comparação de embeddings montada pra um projeto de WhatsApp — cada um funciona no seu contexto, mas na hora de usar em outro lugar, é copiar arquivo, adaptar paths, instalar dependências de novo.

Com o tempo, o padrão ficou claro: as análises são as mesmas, os dados é que mudam. Frequência de palavras, sentimento, topic modeling, transcrição — não precisavam morar dentro de cada projeto. Precisavam de um lugar só, acessível por qualquer ferramenta, sem mandar dados pra fora.

Qualia é esse lugar. Cada análise vira um plugin independente. O engine descobre, resolve dependências, executa. A API expõe tudo. Qualquer projeto consome — um script Python, um plugin do Obsidian, um notebook, o frontend web.

Cada plugin declara seus parâmetros (tipo, default, range, opções) e o engine expõe automaticamente — na API, na CLI e no frontend. Quem consome escolhe: quantos clusters, qual modelo de embedding, qual threshold. Não é uma caixa preta com resultado fixo — é uma ferramenta configurável que o pesquisador adapta pro seu contexto.

## Plugins

| Plugin | Tipo | O que faz |
|--------|------|-----------|
| `word_frequency` | Analyzer | Frequência de palavras, stopwords, termos principais |
| `sentiment_analyzer` | Analyzer | Sentimento do texto (positivo/negativo/neutro) via TextBlob |
| `readability_analyzer` | Analyzer | Legibilidade (score 0-100, nível de dificuldade) |
| `teams_cleaner` | Document | Limpa transcrições do Teams/Zoom (timestamps, speakers) |
| `transcription` | Document | Transcreve áudio/vídeo via Groq Whisper (mp3, mp4, opus, wav) |
| `wordcloud_d3` | Visualizer | Nuvem de palavras interativa (D3.js) |
| `frequency_chart_plotly` | Visualizer | Gráficos de frequência (bar, line, area) com Plotly |
| `sentiment_viz_plotly` | Visualizer | Dashboard, gauge, timeline e distribuição de sentimento |

Novos plugins são descobertos automaticamente — basta criar uma pasta em `plugins/` com um `__init__.py`.

Múltiplos plugins podem fazer o mesmo tipo de análise (ex: dois sentiment analyzers com abordagens diferentes). O consumer escolhe qual usar.

## Quick Start

Python 3.9+. Tudo roda local — sem conta, sem cloud.

```bash
git clone https://github.com/mrlnlms/qualia.git
cd qualia && python -m venv .venv && source .venv/bin/activate
pip install -e ".[all]"
python -m uvicorn qualia.api:app --port 8000
```

Swagger em http://localhost:8000/docs. Teste direto:

```bash
curl -X POST http://localhost:8000/analyze/word_frequency \
  -H "Content-Type: application/json" \
  -d '{"text": "seu texto aqui", "config": {}}'
```

## CLI

```bash
qualia list                                          # plugins disponíveis
qualia analyze texto.txt -p word_frequency           # analisar texto
qualia analyze texto.txt -p sentiment_analyzer -P language=pt  # com parâmetros
qualia process transcricao.txt -p teams_cleaner      # processar documento
qualia visualize resultado.json -p frequency_chart_plotly  # gerar visualização
qualia menu                                          # menu interativo
```

## Crie seu próprio plugin

Gerar a estrutura:

```bash
python tools/create_plugin.py meu_analyzer analyzer
```

Cria `plugins/meu_analyzer/__init__.py` com a estrutura completa — procure por `TODO` no código gerado. Tipos disponíveis: `analyzer`, `visualizer`, `document`.

O plugin mínimo:

```python
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document

class MeuAnalyzer(BaseAnalyzerPlugin):
    def meta(self):
        return PluginMetadata(
            id="meu_analyzer",
            name="Meu Analyzer",
            type=PluginType.ANALYZER,
            version="1.0.0",
            description="Detecta padrões no texto",
            provides=["patterns"],
            requires=[],
            parameters={
                "threshold": {"type": "float", "default": 0.5, "description": "Limiar de detecção"},
                "language": {"type": "str", "default": "pt", "options": ["pt", "en", "es"]},
            },
        )

    def _analyze_impl(self, document, config, context):
        text = document.content
        threshold = config["threshold"]
        # sua lógica aqui
        return {"patterns": [...]}
```

Os parâmetros declarados em `parameters` aparecem automaticamente:
- Na **API**: `GET /config/consolidated` retorna o schema completo. `POST /analyze/meu_analyzer` valida o config contra o schema
- Na **CLI**: `qualia analyze texto.txt -p meu_analyzer -P threshold=0.8`
- No **frontend**: formulário dinâmico gerado a partir do schema — dropdowns pra options, sliders pra ranges

Três tipos de plugin: `BaseAnalyzerPlugin` (texto → dados), `BaseDocumentPlugin` (texto → texto limpo), `BaseVisualizerPlugin` (dados → figura). Visualizers retornam o objeto de figura (plotly.Figure, matplotlib.Figure ou HTML) — o BaseClass serializa pro formato que o consumer pediu.

Se o plugin usa modelos pesados (transformers, spaCy), carregue no `__init__` — o método de análise roda em worker threads.

## Instale só o que precisa

```bash
pip install -e "."                # core mínimo
pip install -e ".[api]"           # + FastAPI, uvicorn
pip install -e ".[nlp]"           # + TextBlob, NLTK, langdetect
pip install -e ".[ml]"            # + PyTorch, transformers, sentence-transformers, scikit-learn, umap-learn
pip install -e ".[viz]"           # + plotly, matplotlib, kaleido
pip install -e ".[transcription]" # + Groq Whisper (requer GROQ_API_KEY no .env — chave gratuita em console.groq.com)
pip install -e ".[all]"           # tudo acima
```

## Arquitetura

```
plugins/  →  core (discovery, deps, cache)  →  API REST  →  consumers
                                               CLI
                                               frontend
```

O core é agnóstico — descobre plugins, resolve dependências entre eles (ordenação topológica), gerencia cache, e executa. Toda a inteligência fica nos plugins. O core não sabe o que é sentimento, frequência ou transcrição.

Consumers (API, CLI, frontend, scripts, plugins do Obsidian) escolhem quais plugins rodar e interpretam os resultados. O Qualia processa — quem dá significado é quem consome.

## Ecossistema

O [qualia-coding](https://github.com/mrlnlms/qualia-coding) é um plugin do Obsidian que consome a API do Qualia pra codificação qualitativa cross-media. Envia texto do vault, recebe análise, renderiza resultados dentro do Obsidian.

## Status

776 testes (90% coverage), 8 plugins, API REST + CLI + frontend web (Svelte, dark theme). CI via GitHub Actions. Python 3.9+.

MIT
