# Backlog — Qualia Core

Última atualização: 2026-03-18

## Pendente

_(sem itens no momento)_

---

## Roadmap

### Plugins (próxima fronteira)

A infra está pronta (DependencyResolver com ordenação topológica, cache LRU/TTL, loading eager/lazy, base classes thread-safe). Próximos plugins candidatos:

- **NLP pesado** — spaCy (NER, POS tagging), sentence-transformers (embeddings)
- **Topic modeling** — BERTopic, LDA
- **LLM** — integração com APIs de LLM pra análise semântica
- **Clustering** — agrupamento de documentos por similaridade

Cada plugin novo = criar pasta em `plugins/`, implementar `meta()` e `_analyze_impl()`. Core descobre automaticamente.

### Frontend

- Página de Workflow (pipeline builder visual)
- Sessões de análise (múltiplos plugins no mesmo documento, resultados acumulando)

### Ecossistema

- **CodeMarker** — evoluir PoC pra integração completa (hoje só word_frequency)
- **Consumers** — DeepVoC e Observatório consumindo Qualia via API

---

## Parking lot

- **Document stateful (`self.documents`)** — decidir se limpa (remove dead code) ou evolui (sessões, TTL/LRU). Design spaCy-inspired nunca usado na prática. Levantamento completo na seção "Referência" abaixo e em `memory/project_document_stateful.md`.

---

## Notas

### Coverage

756 testes, 90% coverage. Todos os módulos de produção acima de 90%. Linhas residuais são abstract methods, entry points, e exemplos.

---

## Concluído

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
- [x] 756 testes passando

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
