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
| test_api_extended.py | 98 | Todos endpoints, timeout, file upload, pipeline, 413, /plugins/health |
| test_cli_extended.py | 57 | Visualize, batch, export — happy paths e edge cases |
| test_cli.py | 48 | Comandos Click: list, analyze, pipeline, batch, export, config, inspect, process + formatters |
| test_core.py | 53 | Discovery, execution, cache, _validate_and_convert |
| test_cli_final.py | 40 | Pipeline avançado, interactive/utils, commands/__init__ |
| test_config_registry.py | 39 | Normalização, validação, resolução, visão consolidada |
| test_plugin_logic.py | 37 | Lógica real: word_frequency, readability, teams_cleaner, sentiment |
| test_cli_config_watch.py | 33 | Config validate/create/list, watch command, QualiaFileHandler |
| test_cache_deps.py | 30 | CacheManager hit/miss, DependencyResolver ciclos |
| test_monitor.py | 27 | Metrics, track_request, track_webhook, SSE, dashboard, edge cases |
| test_cache_lru.py | 26 | LRU eviction, TTL expiration, stats, backward compat, invalidação seletiva |
| test_webhooks.py | 26 | WebhookProcessor, GenericWebhook, endpoints, timeout 504, integração webhook→monitor |
| test_api.py | 18 | Endpoints REST: health, plugins, analyze, file upload |
| test_transcription.py | 17 | Meta, validação, mocks Groq API |
| test_pragmatic.py | 17 | Contratos de plugin, pipeline, usage real |
| test_async.py | 9 | Concorrência, event loop, pipeline errors |
| test_performance.py | 5 | Startup <500ms, execução <100ms, cache hit vs miss |
| test_cli_plugins_check.py | 4 | `qualia list --check` diagnóstico de plugins |
| test_visualizer_execution.py | 22 | Execução real dos 3 visualizers + pipelines analyzer→visualizer |
| test_thread_safety.py | 3 | Concorrência de plugin singletons (ThreadPoolExecutor) |
| test_cache_pipeline.py | 3 | Cache hit/miss em pipelines repetidos |
| test_loader_errors.py | 7 | Discovery errors acumulados, expostos, com severity/type |
| test_loader_recursive.py | 10 | Discovery recursivo em profundidade + EAGER_LOAD |
| test_word_frequency_spacy.py | 2 | Cache de modelo spaCy no __init__ |
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
| GET | /plugins/health | Status individual por plugin (loaded/pending, eager/lazy, errors) |
| GET | /plugins/{id} | Info de plugin específico |
| GET | /plugins/{id}/schema | Schema normalizado |
| POST | /analyze/{id} | Análise de texto (404 plugin, 422 config/tipo, 504 timeout 60s) |
| POST | /analyze/{id}/file | Análise de arquivo uploaded (UTF-8/latin-1, 422 config/tipo, 504 timeout 60s) |
| POST | /process/{id} | Processamento de documento (404 plugin, 422 config/tipo, 504 timeout 60s) |
| POST | /transcribe/{id} | Transcrição áudio/vídeo (multipart, 413 >25MB, 422 config/tipo, 504 timeout 60s, 400 falha domínio) |
| POST | /visualize/{id} | Gera visualização (HTML default, PNG/SVG se kaleido funcional, 422 config/tipo, 504 timeout 60s) |
| POST | /pipeline | Executa sequência de plugins (fail-fast, encadeia texto entre steps) |
| GET | /config/consolidated | Todos schemas + text_size rules |
| POST | /config/resolve | Resolve config com text_size |
| GET | /cache/stats | Estatísticas do cache (size, hits, misses, evictions) |
| POST | /webhook/custom | Webhook genérico (extrai texto, analisa, 422 payload inválido, 504 timeout 60s) |
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
      → Walk recursivo (rglob __init__.py), ignora pastas com _
      → Para cada plugin encontrado:
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

Startup medido (8 plugins, varia por ambiente):
- Primeiro startup (cold — NLTK download/validação): ~1-2s
- Startups subsequentes (warm — NLTK em cache local): ~500ms-1s
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

**Persistência:** cache em disco (.pkl) sobrevive a restart. `get()` reintegra entradas do disco no tracking LRU automaticamente (usa `st_mtime` como timestamp). **Nota:** `stats()["size"]` reflete entradas ativas em memória, não arquivos no disco. Após restart, size começa em 0 e cresce conforme entries são acessadas via `get()`.

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

- **Analyzers/Documents:** declaram provides, engine valida com ValueError se resultado não contém os campos (contrato enforced)
- **Visualizers:** `provides=[]` (retornam figura nativa — plotly.Figure, matplotlib.Figure ou HTML string. BaseVisualizerPlugin._serialize() faz duck-typing e serializa)
- **Múltiplos providers:** dois plugins com mesmo campo coexistem (log info). Resolução automática só funciona com provider único; com múltiplos, consumer escolhe via pipeline
- **Colisão de plugin ID:** dois plugins com mesmo id em meta() → `ValueError` no startup
- **Resolver:** field names em `requires` são resolvidos automaticamente via `provides_map` → plugin ID
- **Requires não satisfeitos:** warning no log se nenhum plugin fornece um campo requerido

## Stability

Classificação de estabilidade das interfaces. **Stable** = contrato mantido entre versões. **Experimental** = pode mudar sem aviso.

### API Endpoints

| Categoria | Endpoints | Estabilidade |
|-----------|-----------|-------------|
| Core | `/health`, `/plugins`, `/plugins/{id}`, `/plugins/{id}/schema` | **Stable** |
| Análise | `/analyze/{id}`, `/analyze/{id}/file`, `/process/{id}` | **Stable** |
| Visualização | `/visualize/{id}` | **Stable** |
| Pipeline | `/pipeline` | **Stable** |
| Config | `/config/consolidated`, `/config/resolve` | **Stable** |
| Cache | `/cache/stats` | **Stable** |
| Transcrição | `/transcribe/{id}` | **Experimental** — depende de API externa (Groq) |
| Webhooks | `/webhook/custom`, `/webhook/stats` | **Experimental** — interface pode mudar |
| Monitor | `/monitor/`, `/monitor/stream` | **Experimental** — SSE, dashboard pode mudar |

### Core Python API

| Interface | Estabilidade |
|-----------|-------------|
| `QualiaCore` (engine.py) | **Stable** — `execute_plugin()`, `execute_pipeline()`, `discover_plugins()` |
| `BaseAnalyzerPlugin`, `BaseDocumentPlugin`, `BaseVisualizerPlugin` | **Stable** — contrato `meta()` + `_*_impl()` |
| `PluginMetadata`, `Document`, `PipelineConfig` | **Stable** |
| `ConfigurationRegistry` | **Stable** — `validate_config()`, `get_consolidated_view()` |
| `CacheManager` | **Stable** — `get()`, `set()`, `stats()`, `invalidate()` |
| `DependencyResolver` | **Stable** — `resolve()`, `build_graph()` |

### Plugins

| Plugin | Estabilidade | Nota |
|--------|-------------|------|
| `word_frequency` | **Stable** | Core analyzer, provides bem definidos |
| `sentiment_analyzer` | **Stable** | Core analyzer, TextBlob/langdetect |
| `readability_analyzer` | **Stable** | Core analyzer, pure Python |
| `teams_cleaner` | **Stable** | Core document processor |
| `transcription` | **Experimental** | Depende de GROQ_API_KEY e API externa |
| `wordcloud_d3` | **Stable** | D3.js, sem deps Python |
| `frequency_chart_plotly` | **Stable** | Requer plotly (extra `[viz]`) |
| `sentiment_viz_plotly` | **Stable** | Requer plotly (extra `[viz]`) |

### CLI

| Comando | Estabilidade |
|---------|-------------|
| `qualia list`, `qualia inspect`, `qualia analyze`, `qualia process`, `qualia visualize` | **Stable** |
| `qualia pipeline`, `qualia batch`, `qualia export`, `qualia config` | **Stable** |
| `qualia create`, `qualia init` | **Stable** |
| `qualia watch` | **Experimental** — file watcher |
| `qualia menu` (interactive) | **Experimental** — UI pode mudar |

### Frontend (Svelte)

**Experimental** — todo o frontend Svelte é experimental. Páginas, componentes e API client podem mudar sem aviso. O contrato estável é a API REST, não o frontend.

## Error handling

API:
- HTTPException com dict detail → `{"status": "error", "message": ..., "errors": [...]}` (desempacotado)
- HTTPException com string detail → `{"status": "error", "message": "..."}`
- Exception não tratada → 500 genérico (sem vazamento de detalhes internos, log completo server-side)
- Plugin não encontrado → 404 em todas as rotas
- Plugin tipo incompatível → 422 (e.g. analyzer em /process, document em /analyze)
- Config inválida → 422 em todas as rotas (validação centralizada via `validate_plugin_config()`)
- Timeout → 504 após 60s em analyze, process, visualize, transcribe e webhook
- Pipeline encadeia texto: `_extract_text_result()` propaga `transcription` > `cleaned_document` > `processed_text` (prioridade documentada)
- Pipeline com file + step[0] não-document → 422 descritivo (não mais erro genérico)
- Pipeline timeout 60s em todos os paths (step 0, loop analyzer/document, loop visualizer)
- FileResponse cleanup via BackgroundTask (previne temp file leak)
- Interfaces alinhadas com implementação (IDocumentPlugin.process, IVisualizerPlugin.render)
- Type conversion em BaseAnalyzerPlugin e BaseDocumentPlugin (consistente com BaseVisualizer)
- DependencyResolver ValueError tratado com mensagem descritiva
- Webhook payload JSON inválido → 422 (não 500)
- Webhook valida plugin existe (404) e tipo analyzer (422) antes de executar
- Pipeline plugin inexistente mid-step → 404 (não 400)
- Monitor `active_connections` atualizado no `finally` do SSE (sem stale após desconexão)
- CORS sem `allow_credentials` (stateless API, spec compliance)

CLI:
- Sem bare except — todos os catches são tipados (`except Exception`)
- UTF-8 com fallback latin-1 em todos os comandos de leitura de arquivo (incluindo pipeline e watch)
- Exit code 1 em todos os erros — visualize, watch, inspect, export, pipeline (não mais return silencioso)

Plugins:
- Import error no plugin → `logger.error` + acumulado em `loader.discovery_errors`
- Plugin dir sem IPlugin → `logger.warning`
- Discovery errors expostos via `core.discovery_errors` property e `/health` endpoint (quando há erros)
- `qualia list --check` classifica erros por tipo (ImportError, SyntaxError, OSError) com sugestão de fix
- Plugin retorna None → `logger.warning`, retorna `{}`
- Transcription levanta ValueError/RuntimeError (não retorna dict com status=error)
- `provides` enforced: readability sempre inclui `longest_sentence`/`shortest_sentence`, sentiment sempre inclui `sentence_sentiments`

## Thread-safety

Plugins são singletons compartilhados entre worker threads.

- `__init__` roda na main thread (discovery, sem concorrência)
- `_analyze_impl` / `_render_impl` / `_process_impl` rodam em worker threads via `asyncio.to_thread`
- Webhooks também usam `asyncio.to_thread` para `core.execute_plugin()` (consistente com rotas /analyze, /process)
- CacheManager protegido por `threading.Lock` — todas as operações (`get`, `set`, `invalidate`, `clear`, `stats`) são thread-safe
- Recursos pesados (modelos, corpora, conexões) devem ser carregados no `__init__`
- Convenção documentada em: CLAUDE.md, docstrings das base classes, templates `plugins/_templates/`

## Webhooks ↔ Monitor

Webhook tracking fiado no bootstrap: `set_tracking_callback(track_webhook)` em `api/__init__.py`. Quando um webhook é processado, `metrics.webhook_stats` é atualizado e streams SSE notificados.

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
- `conftest.py` — `_ARTIFACTS` esvaziado (não deleta mais `cache/` nem `.pytest_cache/`)
- Spec arquivada: `docs/superpowers/` → `docs/archive/claude_sources/plans/`
