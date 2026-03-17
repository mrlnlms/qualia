# Qualia Core — CLAUDE.md

Motor de análise qualitativa. API REST local stateless — recebe texto/áudio/vídeo, devolve JSON. Qualia não sabe o que os dados significam; quem interpreta é o consumer.

## Comandos essenciais

```bash
# Ativar venv
source venv/bin/activate

# Rodar API
python -m uvicorn qualia.api:app --port 8000

# Testes
pytest tests/ -v

# Testes com coverage
pytest tests/ --cov=qualia --cov-report=term-missing

# Frontend dev (porta 5173, proxy → 8000)
make frontend-dev

# Frontend build (gera dist/ servido pelo FastAPI)
make frontend-build
```

## Arquitetura

```
qualia/
  core/           # Engine — descoberta de plugins, dependências, cache, execução
    __init__.py   # QualiaCore — orquestrador principal
    config.py     # ConfigurationRegistry (normalização, validação, calibração)
  cli/commands/   # 11 comandos Click (analyze, batch, export, watch, etc.)
  api/            # FastAPI — REST endpoints + monitor SSE + webhooks
    __init__.py   # App FastAPI, monta StaticFiles + SPA catch-all
    monitor.py    # Dashboard tempo real via SSE
  frontend/       # Svelte 5 + Vite (Home, Analyze, Transcribe, Monitor, Workflow)
plugins/          # Cada plugin em sua pasta, auto-descoberto pelo core
tests/            # pytest
```

## Plugins

Tipos: `BaseAnalyzerPlugin`, `BaseDocumentPlugin`, `BaseVisualizerPlugin`.

O core descobre plugins automaticamente — basta criar pasta em `plugins/` com `__init__.py` que exporte a classe. Sem registro manual.

**Existentes:** word_frequency, sentiment_analyzer, readability_analyzer, teams_cleaner, transcription, wordcloud_viz, frequency_chart, sentiment_viz.

**Thread-safety:** plugins são singletons — `__init__` roda na main thread, `_analyze_impl`/`_process_impl`/`_render_impl` rodam em worker threads via `asyncio.to_thread`. Carregar modelos, corpora e recursos pesados sempre no `__init__`, nunca no método de execução. Template: `tools/create_plugin.py`.

## ConfigurationRegistry (`qualia/core/config.py`)

- Normaliza schemas dos plugins (integer→int, string→str, boolean→bool)
- Valida configs: tipo, range, options
- Calibra parâmetros por tamanho de texto (`text_size_adjustments`)
- Cascata: default → text_size adjustments
- `get_consolidated_view()` — snapshot único para consumers

**Sem perfis de domínio.** Perfis são responsabilidade do consumer.

**Loading:** plugins com `__init__` próprio carregam no startup (eager, thread-safe). Os demais carregam no primeiro uso (lazy). Detecção automática via `'__init__' in cls.__dict__`. Ver `docs/TECHNICAL_STATE.md`.

## API endpoints principais

- `GET /plugins` — lista plugins
- `POST /analyze/{plugin_id}` — análise de texto (valida config, 422 com erros)
- `POST /process/{plugin_id}` — processamento de documento
- `POST /transcribe/{plugin_id}` — transcreve áudio/vídeo (multipart/form-data)
- `POST /visualize/{plugin_id}` — gera visualização
- `POST /pipeline` — executa sequência de plugins
- `GET /config/consolidated` — todos os schemas + rules
- `GET /cache/stats` — estatísticas do cache (size, hits, misses, evictions)
- `POST /webhook/custom` — webhook genérico (extrai texto, analisa)

## Convenções

- **Commits:** mensagens descritivas em português, sem Co-Authored-By
- **API:** doc_id inclui hash do conteúdo (evita colisão de cache)
- **Python:** venv em `./venv/`
- **Secrets:** `.env` no `.gitignore`, `.env.example` commitado como template
- **Load env:** `python-dotenv` com `load_dotenv()` no topo de `qualia/api/__init__.py`
- **Frontend:** operações async sempre com loading/progress feedback visual
- **README:** tom honesto e acessível, sem hype
- **Pipeline:** fail-fast — se um step falha, pipeline para com RuntimeError descritivo
- **Packaging:** `pyproject.toml` (não tem mais setup.py). Extras: `api`, `viz`, `nlp`, `transcription`, `dev`, `all`
- **Docs mortos:** ficam em `docs/morto/` (ignorado pelo git), docs ativos em `docs/`

## Ecossistema

- **Qualia Engine** (este repo) — API REST, motor agnóstico
- **qualia-coding** (plugin Obsidian) — codificação qualitativa cross-media, consome Qualia
- **Consumers** (DeepVoC, Observatório) — pipelines de domínio que chamam o Qualia
