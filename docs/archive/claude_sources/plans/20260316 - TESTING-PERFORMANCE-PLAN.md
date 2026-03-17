# Qualia Engine — Plano de Testes e Performance

## Estado atual

**125 testes existentes** (1,953 LOC) cobrindo:
- ConfigurationRegistry (39 testes) — excelente cobertura
- Transcription plugin (17 testes) — meta, validacao, mocks da Groq API
- QualiaCore (16 testes) — discovery, documents, execution, cache basico
- REST API (20 testes) — health, plugins, analyze, file upload
- Pragmatic/integracao (17 testes) — plugin loading, execution real
- Suite manual (16 testes) — orquestrador visual

**O que NAO tem teste nenhum:**
- CLI inteiro (5,112 LOC, 20 arquivos, 0 testes)
- Logica real dos plugins (word_frequency, sentiment, readability, teams_cleaner — so meta/schema testado)
- Async/concorrencia (API usa asyncio.to_thread mas nunca testado)
- Webhooks e monitoring (webhooks.py + monitor.py)
- Cache invalidation (CacheManager.invalidate() nunca testado)
- Cycle detection no DependencyResolver (nunca testado)
- Error recovery (timeouts, circuit breakers)

---

## Parte 1 — Testes

### Fase 1: Logica dos plugins (MAIOR ROI)

Os plugins sao testados por meta/schema, mas a logica de analise real nunca eh validada.

| Plugin | O que testar | Exemplos |
|--------|-------------|----------|
| `word_frequency` | contagem, stop words, min_length, top_words, hapax legomena | "o gato e o gato" -> gato:2 |
| `sentiment_analyzer` | polaridade, subjetividade, com e sem textblob instalado | texto positivo -> polarity > 0 |
| `readability_analyzer` | scores de legibilidade, textos curtos vs longos | texto simples -> score alto |
| `teams_cleaner` | extracao de speakers, merge timestamps, limpeza formatacao | transcript Teams real -> texto limpo |
| `wordcloud_viz` | geracao de imagem, formatos (png/svg/html), parametros | input valido -> arquivo existe |
| `frequency_chart` | tipos de grafico (bar/line/area/treemap), plotly output | dados de frequencia -> chart |
| `sentiment_viz` | gauge, timeline, distribution | dados de sentiment -> visualizacao |

**Arquivo:** `tests/test_plugin_logic.py` (~40 testes)

### Fase 2: Cache e DependencyResolver

| Componente | O que testar |
|------------|-------------|
| `CacheManager.invalidate()` | invalidar por plugin_id, por doc_id, total |
| `CacheManager` hit/miss | mesmo doc+config = cache hit, config diferente = miss |
| `DependencyResolver` | ciclo A->B->A detectado, ordem topologica correta, deps ausentes |

**Arquivo:** `tests/test_cache_deps.py` (~15 testes)

### Fase 3: API async e concorrencia

| Cenario | O que valida |
|---------|-------------|
| 10 requests simultaneos | nenhum crash, todos retornam 200 |
| Timeout de 60s | plugin lento -> 504, nao trava o server |
| Plugin falha mid-execution | retorna 400 com erro descritivo, outros requests nao afetados |
| Pipeline com step que falha | retorna erro no step especifico, steps anteriores ok |

**Arquivo:** estender `tests/test_api.py` (+15 testes)

### Fase 4: Webhooks e Monitor

| Componente | O que testar |
|------------|-------------|
| `webhooks.py` | HMAC verification, GitHub/Slack/Discord payloads, webhook invalido -> 401 |
| `monitor.py` | SSE stream conecta, metricas incrementam, request tracking |

**Arquivo:** `tests/test_webhooks_monitor.py` (~15 testes)

### Fase 5: CLI (baixa prioridade)

A CLI eh secundaria — os consumers reais sao o frontend web e o plugin Obsidian. Testar se quiser, mas o ROI eh menor.

| Comando | O que testar |
|---------|-------------|
| `analyze` | arquivo valido -> resultado, arquivo inexistente -> erro |
| `pipeline` | config yaml valido -> execucao, step invalido -> erro descritivo |
| `batch` | multiplos arquivos -> todos processados |
| `list` | lista plugins por tipo |

**Arquivo:** `tests/test_cli.py` (~30 testes)

---

## Parte 2 — Performance

### Problema 1: Imports pesados no module level

**Situacao atual:**
```
wordcloud_viz/__init__.py linha 8-9:
  import matplotlib.pyplot as plt    <- MODULE LEVEL (problema!)
  from wordcloud import WordCloud    <- MODULE LEVEL (problema!)

sentiment_analyzer/__init__.py:
  textblob/nltk importados no __init__ do plugin  <- OK, lazy

frequency_chart/__init__.py:
  plotly importado dentro do metodo _render_plotly  <- OK, lazy

transcription/__init__.py:
  groq importado com try/except e flag HAS_GROQ     <- OK, guarded
```

**Fix:** mover imports do `wordcloud_viz` pra dentro dos metodos (igual o `frequency_chart` ja faz).

### Problema 2: Todos os plugins carregam no startup

**Situacao atual** (`qualia/core/__init__.py` linhas 456-493):
```python
# discover_plugins() carrega TODOS os modulos via importlib
# exec_module() executa todos os imports de cada plugin
# mesmo que o request so use 1 plugin, todos carregam
```

**Fix — Lazy plugin loading:**
1. Na discovery, carregar apenas metadata (nao instanciar o plugin)
2. Instanciar e importar deps pesadas so no primeiro request ao plugin
3. Isso muda o startup de "carregar 8 plugins + todas deps" pra "escanear 8 diretórios + ler meta"

**Impacto estimado:**
- Startup atual: ~200ms (com matplotlib) ou ~20ms (sem)
- Startup com lazy: ~5ms (so metadata scan)
- Primeiro request ao plugin: custo unico de import

### Problema 3: NLTK downloads no __init__

**Situacao atual** (`sentiment_analyzer/__init__.py` linhas 44-48):
```python
nltk.download('brown', quiet=True)   # <- NETWORK CALL no init!
nltk.download('punkt', quiet=True)   # <- NETWORK CALL no init!
```

**Fix:** mover downloads pra um metodo `ensure_dependencies()` chamado antes do primeiro `analyze()`, ou usar flag `_deps_ready`.

### Problema 4: Sem limites no cache

**Situacao atual:** `CacheManager` armazena resultados sem limite. Cache em disco tem 80+ diretorios.

**Fix:**
- LRU com tamanho maximo configuravel
- TTL (time to live) por entry
- Endpoint `GET /cache/stats` pra monitorar

### Problema 5: pandas no requirements mas nao usado

`pandas>=2.0.0` esta no `requirements.txt` mas nao eh importado em nenhum plugin. Remove ou marca como opcional.

---

## Prioridades

```
CONCLUIDO:
1. ✅ Lazy imports no wordcloud_viz
2. ✅ Mover nltk.download pra lazy (+ fix thread-safety com warm-up)
3. ✅ Remover pandas do requirements
4. ✅ Testes de logica dos plugins (40 testes)
6. ✅ Testes de cache + dependency resolver (15 testes)
7. ✅ Testes async/concorrencia (9 testes)
8. ✅ Cache com LRU + TTL (15 testes + endpoint /cache/stats)
9. ✅ Testes de webhooks/monitor (31 testes)
10. ✅ Testes de CLI (21 testes)

AVALIADO E FECHADO:
5. Lazy plugin loading — avaliado com instrumentação real.
   Imports pesados já são lazy (dentro dos métodos).
   Startup medido: 910ms (8 plugins). Aceitável pra API local.
   Não justifica complexidade de lazy loading arquitetural.
```

**Total atual: 237 testes passando (era 125 antes deste sprint)**.
**Plano 100% concluído.**
