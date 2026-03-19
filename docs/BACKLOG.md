# Backlog — Qualia Core

Última atualização: 2026-03-19

## Pendente

### ~~Code review completo (2026-03-19) — Onda 1: Crashes em runtime~~ Concluído

- [x] **CacheManager thread-safe** — `threading.Lock` em `get()`/`set()`/`invalidate()`/`clear()`/`stats()`. Risco de pickle documentado no docstring.
- [x] **`provides` violado — readability** — `longest_sentence`/`shortest_sentence` sempre incluídos (independente de detail_level).
- [x] **`provides` violado — sentiment** — `sentence_sentiments` default `[]` quando `analyze_sentences=false`.
- [x] **Pipeline CLI: render() args corrigidos** — Agora chama `render(data, config)` com 2 args, output_format=html, salva HTML se output_dir.
- [x] **Pipeline CLI: UTF-8 fallback** — try/except UnicodeDecodeError com fallback latin-1.
- [x] **SentimentAnalyzer NLTK thread-safe** — Download movido pro `__init__` (warm-up na main thread). `validate_config` override removido (base class cuida).
- [x] **Transcription raises exceptions** — Erros agora levantam ValueError/RuntimeError em vez de retornar dicts com status=error.
- [x] **Cache TTL bypass pós-restart** — Reintegração do disco movida para antes do check de TTL.

### ~~Code review completo (2026-03-19) — Onda 2: Contratos violados~~ Concluído

- [x] **Exit codes consistentes** — `raise SystemExit(1)` em todos os error paths de visualize, watch, inspect, export.
- [x] **pytest-timeout nas deps** — Adicionado `pytest-timeout>=2.2.0` ao extra `dev`.
- [x] **conftest.py seguro** — Removidos `cache/` e `.pytest_cache` de `_ARTIFACTS`.
- [x] **Docker healthcheck** — `urllib.request.urlopen` em vez de `requests`/`curl`.
- [x] **Pipeline API: 404** — Plugin inexistente mid-pipeline retorna 404 (era 400).
- [x] **Webhook validação** — `analyze_text` valida plugin existe e é analyzer (404/422). doc_id usa content hash.
- [x] **CORS** — Removido `allow_credentials=True` (stateless API).

### ~~Code review completo (2026-03-19) — Onda 3: Qualidade e consistência~~ Concluído

- [x] **Frontend Transcribe** — Filtra por `provides.includes('transcription')`.
- [x] **Analyze.svelte** — Default `'html'` em vez de `'png'`.
- [x] **Interactive show_config** — Usa `QualiaCore().registry` em vez de contagem manual.
- [x] **_choose_file_from_recent** — Indexação corrigida (`recent[idx-1]`).
- [x] **_kaleido_works() cache** — Resultado cacheado em `_kaleido_result` (class-level).
- [x] **import asyncio duplicado** — Removido em webhooks.py.
- [x] **Visualizer template** — Adicionado `output_format` ao meta().parameters.
- [x] **Document template** — provides mudado de `cleaned_document` para `processed_output`.
- [x] **config CLI tipos** — Suporta `bool`/`int` além de `boolean`/`integer`, e `str+options` como choice.
- [x] **Dead code formatters.py** — Removidos `Syntax` import e `format_info` function.
- [x] **Dead code workflow.js** — Removido primeiro BFS não utilizado em `wouldCreateCycle`.

### ~~Code review completo (2026-03-19) — Pendente (menor prioridade)~~ Concluído

- [x] **_validate_config extraído** — `_validate_and_convert()` helper compartilhado entre os 3 base plugins.
- [x] **Branches mortas FILTER/COMPOSER removidas** — Engine agora tem fallback `else: raise ValueError`. Tipos FILTER/COMPOSER devolvidos quando tiverem base class.
- [x] **Dead code stateful removido** — `self.documents`, `self.pipelines`, `get_document()`, `save_pipeline()` removidos. `add_document()` cria doc efêmero.
- [x] **Plugin count >= 8 em testes** — 5 assertions atualizadas pra `>= 8`.
- [x] **CI com Python 3.13 + 3.14** — Matrix strategy com `allow-prereleases: true`.
- [x] **process.py passa context** — `ProcessRequest` agora tem campo `context`, passado ao `execute_plugin`.
- [x] **Duplicate fixtures removidas** — `client`/`sample_text` removidos de test_api.py e test_pragmatic.py (usam conftest).
- [x] **Test fixtures com Path absoluto** — `Path(__file__).parent.parent / "plugins"` em 6 test files.
- [x] **Pipeline API: valida tipo do plugin** — Steps com tipo não suportado (analyzer/document/visualizer) → 422.
- [x] **11 testes com assertions ambíguas** — Todos `assert status_code in [...]` substituídos por status code exato. Zero assertions ambíguas restantes.

### Higiene de código (análise Codex — 2026-03-18)

- [ ] **Pipeline com duas verdades** — A API (`api/routes/pipeline.py`) e a CLI (`cli/commands/pipeline.py`) têm lógicas de pipeline divergentes. A CLI assume dados específicos (ex: `word_frequencies`), trata visualizer de forma legada, e não está alinhada ao contrato atual de BaseVisualizerPlugin pós-refactor. Unificar a semântica de pipeline entre core/API/CLI numa única lógica.
- [x] **Arquivo .wrong sobrando** — ~~Deletar~~ Deletado (2026-03-19).
- [x] **print() em fallback de plugins** — ~~word_frequency usa print()~~ Corrigido: spaCy cached no `__init__`, print→logger (2026-03-19).
- [ ] **Blocos standalone em plugins** — word_frequency, sentiment_analyzer, readability_analyzer e teams_cleaner têm blocos `if __name__` com prints de teste. Mover pra scripts de teste ou remover (o template `create_plugin.py` já cobre isso).
- [ ] **Heurística eager/lazy frágil** — `loader.py` usa `'__init__' in cls.__dict__` pra detectar se plugin tem `__init__` próprio (eager) ou não (lazy). Funciona mas é frágil como contrato de longo prazo. Considerar atributo explícito (ex: `EAGER_LOAD = True`).
- [ ] **Upload de arquivo faz buffering integral em memória** — `/transcribe` e `/pipeline` (com file) lêem o arquivo inteiro em memória (`await file.read()`), e o plugin de transcrição lê o tempfile de novo. Um upload de 25MB consome ~50MB por request. Sem guarda de tamanho antes do processamento. Para beta local-first com uso individual é aceitável, mas não escala pra concorrência. Fix: streaming upload ou limit de tamanho no endpoint.

### Compatibilidade Python 3.14

- [x] **Testes async quebram no Python 3.14** — ~~37 testes falhavam~~ Corrigido: 37 métodos convertidos de `asyncio.get_event_loop().run_until_complete()` pra `async def` + `await`. 825 passed no 3.13, 824 passed no 3.14. (2026-03-19)

### Consolidação pós-refactor

- [ ] **Coverage do pipeline.py** — Linhas 29, 100-101 (branch visualizer e timeout no loop) ainda sem cobertura. Pendente da rodada de coverage.
- [ ] **base_plugins.py coverage** — Branches de type conversion (float/bool) em BaseAnalyzerPlugin e BaseDocumentPlugin sem cobertura (linhas 54, 56-59, 70, 87-88, 129, 162, 192, 194, 197, 201). São edge cases de config com tipos específicos.

### Pré-beta: Discovery observabilidade (C)

Preparar terreno para crescimento do ecossistema (~30 plugins candidatos no ECOSYSTEM_MAP.md). Quando a base de plugins crescer significativamente, o sistema de `discovery_errors` precisa evoluir:

- [ ] **Severidade nos erros** — Distinguir erro fatal (plugin não carrega) de warning (dependência opcional ausente, modelo faltando). Hoje tudo é um dict genérico com plugin/error/path.
- [x] **Classificação da causa** — ~~Categorizar~~ Implementado em `qualia list --check`: classifica ImportError, SyntaxError, OSError, ValueError com sugestão de fix (2026-03-19).
- [x] **CLI diagnóstico** — ~~`qualia plugins --check`~~ Implementado: `qualia list --check` mostra eager/lazy, status, erros com classificação (2026-03-19).
- [ ] **Endpoint detalhado** — `/plugins/health` com status individual por plugin (loaded/failed/degraded), tempo de loading, e erros específicos.

**Parcialmente resolvido:** CLI diagnóstico e classificação de causa já implementados. Faltam: severidade nos erros e endpoint `/plugins/health`.

### ~~Não atacar: Superfície pública documentada (D)~~ Concluído

~~Documentar quais interfaces são estáveis vs experimentais.~~ Implementado: seção Stability no TECHNICAL_STATE.md com classificação por endpoint, core API, plugin, CLI e frontend (2026-03-19).

---

## Roadmap

### Plugins (próxima fronteira)

A infra está pronta: DependencyResolver com ordenação topológica, cache LRU/TTL, loading eager/lazy, base classes thread-safe, múltiplos plugins com mesmo `provides` coexistem, extra `[ml]` disponível. Catálogo completo de candidatos em `docs/ECOSYSTEM_MAP.md`.

Cada plugin novo = criar pasta em `plugins/`, implementar `meta()` e `_analyze_impl()` (ou `_render_impl()` pra visualizers). Core descobre automaticamente. Template: `qualia create nome tipo` ou copiar de `plugins/_templates/`.

### Frontend

- Página de Workflow (pipeline builder visual) — quando plugins pesados chegarem, o Workflow é onde o pesquisador monta as transformações
- Sessões de análise (múltiplos plugins no mesmo documento, resultados acumulando)

### Novos tipos de plugin

Levantamento completo em `memory/project_plugin_types_brainstorm.md`. Checklist de criação em `memory/project_plugin_type_creation.md`.

- [ ] **Enricher** — Tipo novo. Transforma/enriquece dados estruturados sem analisar conteúdo textual. Interface: `_enrich_impl(self, data, config)`. Casos: validar CPF, normalizar telefone, detectar UF, derivar features temporais (is_weekend, hour, gap_hours). Mais simples dos 3 — começar por aqui.
- [ ] **StatAnalyzer** — Tipo novo. Recebe DataFrame/dados tabulares, roda análises quantitativas (chi-square, teste de hipótese, power analysis, correlação). Interface: `_analyze_impl(self, data: DataFrame, config, context)`. Requer evolução do core pra aceitar DataFrame como entrada (hoje é Document-centric). Análises simples que operam em resultados de outros plugins (via context) cabem no Analyzer atual sem mudanças.
- [ ] **Composer/Dashboard** — Tipo novo. Consome resultados de múltiplos analyzers + visualizers, monta visão consolidada (dashboard, relatório, PDF). Interface: `_compose_impl(self, results: Dict, config)`. Referência: `transcript-analyser-prototype/dash.pdf`. Mais complexo — depende de ter vários plugins funcionando.
- [ ] **CLI `qualia type create`** — Sistematizar criação/deleção de tipos em comando. Gera os ~8 arquivos automaticamente (interface, base class, engine elif, loader exclusion, template, rota API). Implementar quando o primeiro tipo novo for criado (validar com caso real).

**Nota:** ML não é tipo novo — é peso de dependência. Já resolvido pelo extra `[ml]` no pyproject.toml. Organização por pasta (`plugins/analyzers/ml/`).

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

835 testes (Python 3.13, kaleido funcional), ~90% coverage. Ambientes sem kaleido funcional: 834 passed, 1 skipped (PNG/SVG). Módulos API (config, health, process, transcribe, analyze) em 100%. Core engine em 96%. Linhas residuais são abstract methods, entry points, e exemplos.

---

## Concluído

### Sprint 2026-03-19 (limpeza, reorganização e discovery recursivo)

**Limpeza do repo:**
- [x] Root limpo: removidos artefatos (cache 903pkl, __pycache__, .coverage, output/, data/, .DS_Store)
- [x] Docs mortos movidos: configs/, DEPLOY.md, README_COMPLEMENTAR.md, KNOWN_ISSUES.md, .docx, session logs
- [x] `qualia init` simplificado — só cria plugins/ e cache/
- [x] `qualia visualize` sem -o gera em /tmp/qualia/ (não polui working directory)
- [x] Auto-cleanup de artefatos pós-teste (conftest.py pytest_sessionfinish)

**Plugin templates + CLI create:**
- [x] Templates copiáveis em `plugins/_templates/` (analyzer.py, visualizer.py, document.py)
- [x] Comando `qualia create <nome> <tipo>` — gera plugin a partir dos templates
- [x] Opção `--dir` — cria plugins em subpastas (`qualia create x analyzer --dir analyzers`)
- [x] `tools/` removido — templates e CLI são fonte única

**Discovery recursivo:**
- [x] PluginLoader.discover() com walk recursivo (rglob) — plugins em qualquer profundidade
- [x] Pastas com `_` no nome ignoradas automaticamente
- [x] Plugins organizados por tipo: analyzers/, documents/, visualizers/
- [x] 792 testes passando

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
