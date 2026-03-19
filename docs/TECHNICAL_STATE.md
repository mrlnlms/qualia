# Qualia Core — Estado Técnico

Última atualização: 2026-03-19

## Plugins (8)

| Plugin | Tipo | Deps pesadas | Loading |
|--------|------|-------------|---------|
| word_frequency | Analyzer | NLTK (stopwords, punkt) | Eager (warm-up no __init__) |
| sentiment_analyzer | Analyzer | TextBlob, langdetect | Eager (import no __init__) |
| readability_analyzer | Analyzer | Nenhuma (pure Python) | Lazy |
| teams_cleaner | Document | Nenhuma (pure Python) | Lazy |
| transcription | Document | Groq (guarded import) | Lazy |
| wordcloud_d3 | Visualizer | D3.js (HTML puro, sem deps Python) | Lazy |
| frequency_chart_plotly | Visualizer | plotly (lazy dentro do render) | Lazy |
| sentiment_viz_plotly | Visualizer | plotly (lazy dentro do render) | Lazy |

## Testes (rodar `pytest tests/ -v` pra contagem atual)

| Arquivo | Testes | Cobre |
|---------|--------|-------|
| test_cli_interactive.py | 126 | Handlers, menu, utils, wizards — módulo interactive completo |
| test_cli_remaining.py | 89 | Init, list, watch, export, visualize, tutorials |
| test_api_extended.py | 87 | Todos endpoints com variações, timeout, file upload, pipeline |
| test_cli_extended.py | 57 | Visualize, batch, export — happy paths e edge cases |
| test_cli.py | 49 | Comandos Click: list, analyze, pipeline, batch, export, config, inspect, process + formatters |
| test_core.py | 46 | Discovery, documents, execution, cache básico |
| test_cli_final.py | 40 | Pipeline avançado, interactive/utils, commands/__init__ |
| test_config_registry.py | 39 | Normalização, validação, resolução, visão consolidada |
| test_plugin_logic.py | 37 | Lógica real: word_frequency, readability, teams_cleaner, sentiment |
| test_cli_config_watch.py | 33 | Config validate/create/list, watch command, QualiaFileHandler |
| test_cache_deps.py | 30 | CacheManager hit/miss, DependencyResolver ciclos |
| test_monitor.py | 27 | Metrics, track_request, track_webhook, SSE, dashboard, edge cases |
| test_cache_lru.py | 26 | LRU eviction, TTL expiration, stats, backward compat, invalidação seletiva |
| test_webhooks.py | 24 | WebhookProcessor, GenericWebhook, endpoints /webhook/* |
| test_api.py | 20 | Endpoints REST: health, plugins, analyze, file upload |
| test_transcription.py | 17 | Meta, validação, mocks Groq API |
| test_pragmatic.py | 17 | Contratos de plugin, pipeline, usage real |
| test_async.py | 9 | Concorrência, event loop, pipeline errors |
| test_performance.py | 5 | Startup <500ms, execução <100ms, cache hit vs miss |
| test_engine_edges.py | 2 | Edge cases do engine |

## API — Estrutura modular

```
qualia/api/
  __init__.py     # Bootstrap: app, CORS, router mounting, SPA catch-all
  deps.py         # get_core(), track(), validate_plugin_config(), require_plugin_type()
  schemas.py      # 5 modelos Pydantic + plugin_to_info helper
  routes/
    health.py     # GET /, /api, /health, /cache/stats
    plugins.py    # GET /plugins, /plugins/{id}
    analyze.py    # POST /analyze/{id}, /analyze/{id}/file
    process.py    # POST /process/{id}
    visualize.py  # POST /visualize/{id}
    pipeline.py   # POST /pipeline
    config.py     # GET /plugins/{id}/schema, /config/consolidated, POST /config/resolve
    transcribe.py # POST /transcribe/{id}
  monitor.py      # Métricas + SSE stream
  templates/
    monitor.html  # Dashboard HTML/CSS/JS (servido pelo monitor.py)
  webhooks.py     # Webhook genérico
```

## API endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | /health | Health check com contagem de plugins |
| GET | /plugins | Lista plugins (filtro por tipo opcional) |
| GET | /plugins/{id} | Info de plugin específico |
| GET | /plugins/{id}/schema | Schema normalizado |
| POST | /analyze/{id} | Análise de texto (404 plugin, 422 config/tipo, 504 timeout 60s) |
| POST | /analyze/{id}/file | Análise de arquivo uploaded (UTF-8/latin-1, 422 config/tipo, 504 timeout 60s) |
| POST | /process/{id} | Processamento de documento (404 plugin, 422 config/tipo, 504 timeout 60s) |
| POST | /transcribe/{id} | Transcrição áudio/vídeo (multipart, 422 config/tipo, 400 falha domínio) |
| POST | /visualize/{id} | Gera visualização (PNG/SVG/HTML, 422 config/tipo, 504 timeout 60s) |
| POST | /pipeline | Executa sequência de plugins (fail-fast, encadeia texto entre steps) |
| GET | /config/consolidated | Todos schemas + text_size rules |
| POST | /config/resolve | Resolve config com text_size |
| GET | /cache/stats | Estatísticas do cache (size, hits, misses, evictions) |
| POST | /webhook/custom | Webhook genérico (extrai texto, analisa) |
| GET | /webhook/stats | Stats de webhooks processados |
| GET | /monitor/ | Dashboard HTML de monitoramento |
| GET | /monitor/stream | SSE stream de métricas tempo real |

## Core — Estrutura modular

```
qualia/core/
  __init__.py      # Fachada de re-exports
  interfaces.py    # PluginType, PluginMetadata, IPlugin, I*Plugin
  models.py        # Document, ExecutionContext, PipelineStep, PipelineConfig
  base_plugins.py  # BaseAnalyzerPlugin, BaseVisualizerPlugin, BaseDocumentPlugin
  engine.py        # QualiaCore — orquestrador principal
  loader.py        # PluginLoader (auto-descoberta eager/lazy)
  cache.py         # CacheManager (LRU + TTL + invalidação seletiva)
  resolver.py      # DependencyResolver (ordenação topológica)
  config.py        # ConfigurationRegistry (normalização, validação, calibração)
```

## CLI interativa — Estrutura modular

```
qualia/cli/interactive/
  handlers.py   # Fachada fina; delega fluxo para módulos menores
  actions.py    # Execução de analyze, visualize, pipeline e operações interativas
  services.py   # Settings, sistema, cache e tarefas operacionais
  menu.py       # Loop principal e navegação
  utils.py      # Helpers de input/output
  wizards.py    # Assistentes de criação de pipeline
  tutorials.py  # Tutoriais guiados
```

## Arquitetura de loading

```
Startup (main thread):
  QualiaCore.__init__(plugins_dir=None, cache_dir=None)
    → Resolve paths relativos ao pacote (não ao cwd)
    → PluginLoader.discover()
      → Para cada plugins/*/:
        1. exec_module() — importa módulo (stdlib + qualia.core, ~0ms)
        2. Detecta __init__ próprio: '__init__' in cls.__dict__
        3. Se eager: instancia agora (warm-up thread-safe)
        4. Se lazy: guarda classe, instancia no primeiro get_plugin()
      → Extrai metadata de todos (registry)
    → ConfigurationRegistry(registry) — schemas normalizados

Request (worker thread via asyncio.to_thread):
  core.get_plugin(plugin_id)
    → Se já instanciado: retorna do cache (lock-free)
    → Se lazy: adquire lock, double-check, instancia, cacheia, retorna
  plugin.analyze(doc, config, context)
```

Startup medido (8 plugins):
- Primeiro startup (cold — NLTK download/validação): ~910ms
- Startups subsequentes (warm — NLTK em cache local): ~500ms
- 2 eager: word_frequency (~139ms), sentiment_analyzer (~455ms)
- 6 lazy: ~0ms cada (instanciam sob demanda)

## Cache

CacheManager com LRU, TTL e invalidação seletiva (defaults: sem limite).

```python
CacheManager(cache_dir, max_size=0, ttl=0)
# max_size=0 → sem limite de entradas
# ttl=0 → sem expiração
# Ambos configuráveis por instância
```

Invalidação seletiva via índice reverso (`_doc_index`, `_plugin_index`):
```python
cache.invalidate(doc_id="doc1")              # remove tudo do documento
cache.invalidate(plugin_id="word_frequency") # remove tudo do plugin
cache.invalidate(doc_id="doc1", plugin_id="word_frequency")  # intersecção
cache.clear()                                # limpa tudo
```

Stats via `GET /cache/stats`:
```json
{"size": 42, "max_size": 0, "ttl": 0, "hits": 128, "misses": 15, "evictions": 0}
```

## Provides e dependências

`provides` é contrato: campos que o resultado do plugin DEVE conter.

- **Analyzers/Documents:** declaram provides, engine valida com warning se resultado não contém os campos
- **Visualizers:** `provides=[]` (retornam figura nativa — plotly.Figure, matplotlib.Figure ou HTML string. BaseVisualizerPlugin._serialize() faz duck-typing e serializa)
- **Múltiplos providers:** dois plugins com mesmo campo coexistem (log info). Resolução automática só funciona com provider único; com múltiplos, consumer escolhe via pipeline
- **Colisão de plugin ID:** dois plugins com mesmo id em meta() → `ValueError` no startup
- **Resolver:** field names em `requires` são resolvidos automaticamente via `provides_map` → plugin ID
- **Requires não satisfeitos:** warning no log se nenhum plugin fornece um campo requerido

## Error handling

API:
- HTTPException com dict detail → `{"status": "error", "message": ..., "errors": [...]}` (desempacotado)
- HTTPException com string detail → `{"status": "error", "message": "..."}`
- Exception não tratada → 500 genérico (sem vazamento de detalhes internos, log completo server-side)
- Plugin não encontrado → 404 em todas as rotas
- Plugin tipo incompatível → 422 (e.g. analyzer em /process, document em /analyze)
- Config inválida → 422 em todas as rotas (validação centralizada via `validate_plugin_config()`)
- Timeout → 504 após 60s em analyze, process e visualize
- Pipeline encadeia texto: `_extract_text_result()` propaga `transcription` > `cleaned_document` > `processed_text` (prioridade documentada)
- Pipeline com file + step[0] não-document → 422 descritivo (não mais erro genérico)
- Pipeline timeout 60s em todos os paths (step 0, loop analyzer/document, loop visualizer)
- FileResponse cleanup via BackgroundTask (previne temp file leak)
- Interfaces alinhadas com implementação (IDocumentPlugin.process, IVisualizerPlugin.render)
- Type conversion em BaseAnalyzerPlugin e BaseDocumentPlugin (consistente com BaseVisualizer)
- DependencyResolver ValueError tratado com mensagem descritiva

CLI:
- Sem bare except — todos os catches são tipados
- UTF-8 com fallback latin-1 em todos os comandos de leitura de arquivo
- Exit code 1 em todos os erros (não mais return silencioso)

Plugins:
- Import error no plugin → `logger.error` (não print)
- Plugin dir sem IPlugin → `logger.warning`
- Plugin retorna None → `logger.warning`, retorna `{}`

## Thread-safety

Plugins são singletons compartilhados entre worker threads.

- `__init__` roda na main thread (discovery, sem concorrência)
- `_analyze_impl` / `_render_impl` / `_process_impl` rodam em worker threads via `asyncio.to_thread`
- Recursos pesados (modelos, corpora, conexões) devem ser carregados no `__init__`
- Convenção documentada em: CLAUDE.md, docstrings das base classes, templates `plugins/_templates/`

Bug corrigido: NLTK LazyCorpusLoader race condition — warm-up forçado no `__init__` do word_frequency.

## CI/CD

GitHub Actions ativo em `.github/workflows/tests.yml`:
- Trigger: push e PR na main
- Python 3.13, `pip install -e ".[all,dev]"`, `pytest tests/ -v --cov=qualia`
- Verifica startup da API

## Refactors recentes

- `qualia/core/__init__.py` virou fachada de re-exports; implementação distribuída em módulos internos.
- `qualia/api/__init__.py` virou bootstrap fino; endpoints migrados para `qualia/api/routes/`.
- `qualia/api/monitor.py` foi reduzido a métricas + SSE; dashboard extraído para `qualia/api/templates/monitor.html`.
- `qualia/cli/interactive/handlers.py` virou fachada; lógica operacional extraída para `actions.py` e `services.py`.

## Limpeza do repo (2026-03-17)

- Renomeado `venv/` → `.venv/` (convenção moderna)
- Eliminado `requirements.txt` — `pyproject.toml` é fonte única de dependências
- CI, Dockerfile e Makefile atualizados pra usar `pip install -e ".[all,dev]"`
- Deletado `nginx.conf` (conteúdo corrompido) e service nginx do docker-compose
- Movido pra `docs/morto/`: ops/, scripts/, demos/, examples/, notebooks/, screenshots
- Removido do root: `freq_result_wordcloud_viz.png`, `qualia_core.egg-info/`

## Limpeza do repo (2026-03-19)

- Removidos artefatos: `cache/*` (903 pkl), `output/`, `data/`, `__pycache__/` root, `.coverage`, `.DS_Store`
- Movido pra `docs/morto/`: `configs/`, `DEPLOY.md`, `README_COMPLEMENTAR.md`, `KNOWN_ISSUES.md`, `ecossistema-qualia-historia-e-cases.md`, `.docx`, session logs
- `qualia init` simplificado — cria apenas `plugins/` e `cache/` (removido `output/`, `configs/`, `data/`)
- `qualia visualize` sem `-o` agora gera em `/tmp/qualia/` (não polui working directory)
- `tools/` removido — templates migrados pra `plugins/_templates/`, criação via `qualia create`
- `conftest.py` — auto-cleanup de `cache/` e `.pytest_cache/` via `pytest_sessionfinish`
- Spec arquivada: `docs/superpowers/` → `docs/archive/claude_sources/plans/`
