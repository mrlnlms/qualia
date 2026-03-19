# Backlog — Qualia Core

Última atualização: 2026-03-18

## Pendente

### Higiene de código (análise Codex — 2026-03-18)

- [ ] **Pipeline com duas verdades** — A API (`api/routes/pipeline.py`) e a CLI (`cli/commands/pipeline.py`) têm lógicas de pipeline divergentes. A CLI assume dados específicos (ex: `word_frequencies`), trata visualizer de forma legada, e não está alinhada ao contrato atual de BaseVisualizerPlugin pós-refactor. Unificar a semântica de pipeline entre core/API/CLI numa única lógica.
- [ ] **Arquivo .wrong sobrando** — `plugins/sentiment_analyzer/__init__.py.wrong` é resíduo de transição. Deletar.
- [ ] **print() em fallback de plugins** — `word_frequency/__init__.py:225` usa `print()` pra fallback de spaCy ao invés de `logger.warning()`. Revisar todos os plugins e trocar prints por logging.
- [ ] **Blocos standalone em plugins** — word_frequency, sentiment_analyzer, readability_analyzer têm blocos `if __name__` com prints de teste. Mover pra scripts de teste ou remover (o template `create_plugin.py` já cobre isso).
- [ ] **Heurística eager/lazy frágil** — `loader.py` usa `'__init__' in cls.__dict__` pra detectar se plugin tem `__init__` próprio (eager) ou não (lazy). Funciona mas é frágil como contrato de longo prazo. Considerar atributo explícito (ex: `EAGER_LOAD = True`).

### Consolidação pós-refactor

- [ ] **Coverage do pipeline.py** — Linhas 29, 100-101 (branch visualizer e timeout no loop) ainda sem cobertura. Pendente da rodada de coverage.
- [ ] **base_plugins.py coverage** — Branches de type conversion (float/bool) em BaseAnalyzerPlugin e BaseDocumentPlugin sem cobertura (linhas 54, 56-59, 70, 87-88, 129, 162, 192, 194, 197, 201). São edge cases de config com tipos específicos.

---

## Roadmap

### Plugins (próxima fronteira)

A infra está pronta: DependencyResolver com ordenação topológica, cache LRU/TTL, loading eager/lazy, base classes thread-safe, múltiplos plugins com mesmo `provides` coexistem, extra `[ml]` disponível. Catálogo completo de candidatos em `docs/ECOSYSTEM_MAP.md`.

Cada plugin novo = criar pasta em `plugins/`, implementar `meta()` e `_analyze_impl()` (ou `_render_impl()` pra visualizers). Core descobre automaticamente. Template: `qualia create nome tipo` ou copiar de `plugins/_templates/`.

### Frontend

- Página de Workflow (pipeline builder visual) — quando plugins pesados chegarem, o Workflow é onde o pesquisador monta as transformações
- Sessões de análise (múltiplos plugins no mesmo documento, resultados acumulando)

### Ecossistema

- **qualia-coding** — evoluir PoC pra integração completa (hoje só word_frequency)
- **Consumers** — DeepVoC e Observatório consumindo Qualia via API
- **qualia-gsheets** — DataLab (sidebar Google Sheets pra preparação de dados)

---

## Parking lot

- **Document stateful (`self.documents`)** — decidir se limpa (remove dead code) ou evolui (sessões, TTL/LRU). Design spaCy-inspired nunca usado na prática. Levantamento completo na seção "Referência" abaixo e em `memory/project_document_stateful.md`.

---

## Notas

### Coverage

776 testes, 90% coverage. Módulos API (config, health, process, transcribe, analyze) em 100%. Core engine em 96%. Linhas residuais são abstract methods, entry points, e exemplos.

---

## Concluído

### Sprint 2026-03-18 (sessão completa — coverage, refactor, ecossistema, identidade)

**Coverage gaps fechados:**
- [x] Testes de timeout 504, exception 400, encoding UTF-8/latin-1 nos endpoints
- [x] Config endpoints retornam 503 quando registry indisponível
- [x] Pipeline timeout mid-step, encadeamento não-texto
- [x] Transcribe domain error → 400
- [x] Process Document → content extraction
- [x] Health root sem frontend → API info
- [x] Engine dependency cycle + None result
- [x] Fix __main__.py quebrado + filtros de warnings

**Visualizer rendering refactor:**
- [x] BaseVisualizerPlugin._serialize() — duck-typing (plotly.Figure, matplotlib.Figure, HTML str)
- [x] Plugins renomeados: wordcloud_d3, frequency_chart_plotly, sentiment_viz_plotly
- [x] Rota /visualize simplificada (sem temp files, sem FileResponse)
- [x] Frontend default PNG → HTML
- [x] Template create_plugin.py atualizado
- [x] 13 arquivos de teste atualizados

**Ecosystem readiness:**
- [x] ECOSYSTEM_MAP.md — 5 projetos, ~30 plugins candidatos
- [x] Provides relaxado — múltiplos plugins com mesmo campo coexistem
- [x] Extra [ml] adicionado (PyTorch, transformers, sentence-transformers)

**Identidade:**
- [x] Repo renomeado qualia → qualia-core
- [x] README v3 — workbench local-first, conceito de transformação de dados
- [x] 776 testes passando

### Sprint 2026-03-18 (code review completo — 11 bugs corrigidos)

**Análise Codex (4 bugs):**
- [x] `plugins_dir` relativo ao pacote, não ao cwd (engine.py)
- [x] Pipeline encadeia `current_text` entre steps (pipeline.py)
- [x] Validação de config centralizada em todas as rotas (deps.py → `validate_plugin_config()`)
- [x] Checagem de tipo de plugin por rota (deps.py → `require_plugin_type()`)

**Code review interno (7 bugs):**
- [x] Interfaces alinhadas: IDocumentPlugin.process e IVisualizerPlugin.render (interfaces.py)
- [x] FileResponse temp file leak corrigido via BackgroundTask (visualize.py)
- [x] Timeout 60s em todos os paths do pipeline (pipeline.py)
- [x] DependencyResolver ValueError tratado no execute_plugin (engine.py)
- [x] Type conversion em BaseAnalyzerPlugin e BaseDocumentPlugin (base_plugins.py)
- [x] ConfigRegistry warning para tipo desconhecido (config.py)
- [x] Test always-passing corrigido (test_pragmatic.py)
- [x] 772 testes passando

### Sprint 2026-03-17 (saneamento)

- [x] Dividir `api/__init__.py` (694→111 linhas) em deps, schemas, routes/
- [x] Quebrar `core/__init__.py` (902→47 linhas) em 7 módulos
- [x] Integrar DependencyResolver no execute_plugin (field-name→plugin-id, detecção de ciclos)
- [x] Limpar dívidas técnicas (validate_config consistente, wizard stubs, TODOs)
- [x] Pipeline fail-fast com RuntimeError descritivo
- [x] Coverage de 42% → 90% (237→726 testes, todos módulos de produção acima de 90%)
- [x] Remover código morto (run_api.py, módulos vazios, protection morta)
- [x] Migrar setup.py → pyproject.toml
- [x] Organizar docs (mortos → docs/morto/)
- [x] CI com coverage no GitHub Actions
- [x] Dockerfile + docker-compose limpos
- [x] Makefile corrigido
- [x] Instalar pytest-timeout
- [x] Renomear venv → .venv
- [x] Eliminar requirements.txt (pyproject.toml fonte única)
- [x] Deletar nginx.conf corrompido + service nginx
- [x] Limpar root: mover ops/, scripts/, demos/, examples/, notebooks/ → docs/morto/

---

## Referência: Document stateful

O design original (jun/2025) era inspirado no spaCy — Document como hub central que acumula análises. Na prática, o Qualia é stateless (cada request cria Document efêmero, executa, descarta).

**Dead code confirmado:**
- `get_document()` — 0 chamadas em produção
- `get_analysis()` — 0 chamadas
- `add_variant()` / `get_variant()` — 0 chamadas
- `self.documents` dict — só cresce, nunca limpo
- `self.pipelines` / `save_pipeline()` — nunca usado

**Cenários futuros onde faria sentido:**
- Sessões de análise interativa no frontend
- Pipeline stateful (plugin B lê resultado do plugin A via doc)
- Consumers stateful (DeepVoC, Observatório)

**Hoje já coberto por:** CacheManager (resultados por doc_id+plugin_id+config) e DependencyResolver (deps automáticas).

**Arquivos envolvidos (não deletar sem decisão):**
- `qualia/core/models.py` — Document class (`_analyses`, `_variants`, `_cache`)
- `qualia/core/engine.py` — `self.documents`, `add_document()`, `get_document()`, `self.pipelines`, `save_pipeline()`
