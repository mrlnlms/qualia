# Backlog — Qualia Core

Última atualização: 2026-03-17

## Pendente

### Decisões arquiteturais

- [ ] **Document stateful (`self.documents`)** — limpar ou evoluir? Design spaCy-inspired nunca usado na prática. `get_document()`, `get_analysis()`, `add_variant()`, `get_variant()` são dead code. `self.documents` dict cresce sem limite. Deferida até haver use case concreto (sessões no frontend, consumers stateful). Levantamento completo abaixo em "Referência".

### Cobertura de testes

615 testes, 84% coverage. Módulos abaixo de 90%:

| Módulo | Coverage | Gap |
|--------|----------|-----|
| `commands/batch.py` | 80% | Edge cases de processamento paralelo |
| `commands/export.py` | 86% | Formatos de exportação alternativos |
| `interactive/menu.py` | 83% | Navegação e edge cases do menu |

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

## Concluído

### Sprint 2026-03-17 (saneamento)

- [x] Dividir `api/__init__.py` (694→111 linhas) em deps, schemas, routes/
- [x] Quebrar `core/__init__.py` (902→47 linhas) em 7 módulos
- [x] Integrar DependencyResolver no execute_plugin (field-name→plugin-id, detecção de ciclos)
- [x] Limpar dívidas técnicas (validate_config consistente, wizard stubs, TODOs)
- [x] Pipeline fail-fast com RuntimeError descritivo
- [x] Coverage de 42% → 84% (237→615 testes)
- [x] Remover código morto (run_api.py, módulos vazios, protection morta)
- [x] Migrar setup.py → pyproject.toml
- [x] Organizar docs (mortos → docs/morto/)
- [x] CI com coverage no GitHub Actions
- [x] Dockerfile + docker-compose limpos
- [x] Makefile corrigido
- [x] Instalar pytest-timeout

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
