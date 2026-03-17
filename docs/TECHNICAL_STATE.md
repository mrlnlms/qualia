# Qualia Core — Estado Técnico

Última atualização: 2026-03-17

## Plugins (8)

| Plugin | Tipo | Deps pesadas | Loading |
|--------|------|-------------|---------|
| word_frequency | Analyzer | NLTK (stopwords, punkt) | Eager (warm-up no __init__) |
| sentiment_analyzer | Analyzer | TextBlob, langdetect | Eager (import no __init__) |
| readability_analyzer | Analyzer | Nenhuma (pure Python) | Lazy |
| teams_cleaner | Document | Nenhuma (pure Python) | Lazy |
| transcription | Document | Groq (guarded import) | Lazy |
| wordcloud_viz | Visualizer | matplotlib, wordcloud (lazy dentro do render) | Lazy |
| frequency_chart | Visualizer | plotly (lazy dentro do render) | Lazy |
| sentiment_viz | Visualizer | plotly (lazy dentro do render) | Lazy |

## Testes (700+ passando, 90% coverage)

| Arquivo | Testes | Cobre |
|---------|--------|-------|
| test_config_registry.py | 39 | Normalização, validação, resolução, visão consolidada |
| test_plugin_logic.py | 40 | Lógica real: word_frequency, readability, teams_cleaner, sentiment |
| test_cli.py | 49 | Comandos Click: list, analyze, pipeline, batch, export, config, inspect, process + formatters |
| test_cli_extended.py | 46 | Visualize, batch, export — happy paths e edge cases |
| test_cli_config_watch.py | 33 | Config validate/create/list, watch command, QualiaFileHandler |
| test_cli_interactive.py | 95 | Handlers, menu, utils, wizards — módulo interactive completo |
| test_cli_remaining.py | 72 | Init, list, watch, export, visualize, tutorials — gaps restantes |
| test_cli_final.py | 40 | Pipeline avançado, interactive/utils, commands/__init__ |
| test_api.py | 20 | Endpoints REST: health, plugins, analyze, file upload |
| test_api_extended.py | 44 | Todos endpoints com variações, timeout, file upload, pipeline |
| test_webhooks.py | 19 | WebhookProcessor, GenericWebhook, endpoints /webhook/* |
| test_pragmatic.py | 18 | Contratos de plugin, pipeline, usage real |
| test_transcription.py | 17 | Meta, validação, mocks Groq API |
| test_core.py | 16 | Discovery, documents, execution, cache básico |
| test_cache_lru.py | 26 | LRU eviction, TTL expiration, stats, backward compat, invalidação seletiva, limpeza de índices |
| test_cache_deps.py | 15 | CacheManager hit/miss, DependencyResolver ciclos |
| test_monitor.py | 27 | Metrics, track_request, track_webhook, SSE, dashboard, edge cases |
| test_async.py | 9 | Concorrência, event loop, pipeline errors |
| test_performance.py | 5 | Startup <500ms, execução <100ms, cache hit vs miss |

## API — Estrutura modular

```
qualia/api/
  __init__.py     # Bootstrap (~110 linhas): app, CORS, router mounting, SPA catch-all
  deps.py         # get_core(), track(), HAS_EXTENSIONS
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
  monitor.py      # Métricas + SSE stream (~155 linhas)
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
| POST | /analyze/{id} | Análise de texto (valida config, 422 com erros) |
| POST | /analyze/{id}/file | Análise de arquivo uploaded (UTF-8, fallback latin-1) |
| POST | /process/{id} | Processamento de documento |
| POST | /transcribe/{id} | Transcrição áudio/vídeo (multipart, 400 em falha de domínio) |
| POST | /visualize/{id} | Gera visualização (PNG/SVG/HTML) |
| POST | /pipeline | Executa sequência de plugins (fail-fast) |
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
  __init__.py      # Fachada de re-exports (~47 linhas)
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
  QualiaCore.__init__()
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
- **Visualizers:** `provides=[]` (retornam Path, engine envolve em `{"output_path": ...}`)
- **Colisão:** dois plugins com mesmo campo em provides → `ValueError` no startup (fail-fast)
- **Resolver:** field names em `requires` são resolvidos automaticamente via `provides_map` → plugin ID

## Thread-safety

Plugins são singletons compartilhados entre worker threads.

- `__init__` roda na main thread (discovery, sem concorrência)
- `_analyze_impl` / `_render_impl` / `_process_impl` rodam em worker threads via `asyncio.to_thread`
- Recursos pesados (modelos, corpora, conexões) devem ser carregados no `__init__`
- Convenção documentada em: CLAUDE.md, docstrings das base classes, template `tools/create_plugin.py`

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
