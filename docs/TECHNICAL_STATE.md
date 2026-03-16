# Qualia Core — Estado Técnico

Última atualização: 2026-03-16

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

## Testes (237 passando)

| Arquivo | Testes | Cobre |
|---------|--------|-------|
| test_config_registry.py | 39 | Normalização, validação, resolução, visão consolidada |
| test_plugin_logic.py | 40 | Lógica real: word_frequency, readability, teams_cleaner, sentiment |
| test_cli.py | 21 | Comandos Click: list, analyze, pipeline, batch, export, config |
| test_api.py | 20 | Endpoints REST: health, plugins, analyze, file upload |
| test_webhooks.py | 19 | WebhookProcessor, GenericWebhook, endpoints /webhook/* |
| test_pragmatic.py | 18 | Contratos de plugin, pipeline, usage real |
| test_transcription.py | 17 | Meta, validação, mocks Groq API |
| test_core.py | 16 | Discovery, documents, execution, cache básico |
| test_cache_lru.py | 15 | LRU eviction, TTL expiration, stats, backward compat |
| test_cache_deps.py | 15 | CacheManager hit/miss, DependencyResolver ciclos |
| test_monitor.py | 12 | Metrics, track_request, track_webhook, SSE, dashboard |
| test_async.py | 9 | Concorrência, event loop, pipeline errors |
| test_performance.py | 5 | Startup <500ms, execução <100ms, cache hit vs miss |
| test_suite.py | ~11 | Suite manual orquestradora |

## API endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | /health | Health check com contagem de plugins |
| GET | /plugins | Lista plugins (filtro por tipo opcional) |
| GET | /plugins/{id} | Info de plugin específico |
| GET | /plugins/{id}/schema | Schema normalizado |
| POST | /analyze/{id} | Análise de texto (valida config, 422 com erros) |
| POST | /analyze/{id}/file | Análise de arquivo uploaded |
| POST | /process/{id} | Processamento de documento |
| POST | /transcribe/{id} | Transcrição áudio/vídeo (multipart) |
| POST | /visualize/{id} | Gera visualização (PNG/SVG/HTML) |
| POST | /pipeline | Executa sequência de plugins |
| GET | /config/consolidated | Todos schemas + text_size rules |
| POST | /config/resolve | Resolve config com text_size |
| GET | /cache/stats | Estatísticas do cache (size, hits, misses, evictions) |
| POST | /webhook/custom | Webhook genérico (extrai texto, analisa) |
| GET | /webhook/stats | Stats de webhooks processados |
| GET | /monitor/ | Dashboard HTML de monitoramento |
| GET | /monitor/stream | SSE stream de métricas tempo real |

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
    → Se já instanciado: retorna do cache
    → Se lazy: instancia agora, cacheia, retorna
  plugin.analyze(doc, config, context)
```

Startup medido (8 plugins): ~910ms
- 2 eager: word_frequency (139ms), sentiment_analyzer (455ms)
- 6 lazy: ~0ms cada (instanciam sob demanda)

## Cache

CacheManager com LRU e TTL (defaults: sem limite).

```python
CacheManager(cache_dir, max_size=0, ttl=0)
# max_size=0 → sem limite de entradas
# ttl=0 → sem expiração
# Ambos configuráveis por instância
```

Stats via `GET /cache/stats`:
```json
{"size": 42, "max_size": 0, "ttl": 0, "hits": 128, "misses": 15, "evictions": 0}
```

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
- Python 3.13, `pip install -r requirements.txt`, `pytest tests/ -v`
- Verifica startup da API
