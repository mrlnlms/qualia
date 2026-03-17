# Backlog — Qualia Core

Levantamento em 2026-03-17 (análise cruzada Claude + Codex), atualizado na mesma sessão.

## Refatoração (prioridade técnica)

1. [x] ~~Dividir `qualia/api/__init__.py` (694→111 linhas) — deps.py, schemas.py, routes/~~
2. [x] ~~Quebrar `qualia/core/__init__.py` (902→47 linhas) — interfaces, models, base_plugins, resolver, cache, loader, engine. Re-exports no `__init__.py`~~

## Infra do Engine (preparar para plugins pesados)

3. [x] ~~Integrar DependencyResolver no execute_plugin — ordenação topológica, detecção de ciclos, resolução field-name→plugin-id via provides_map~~

4. [ ] **Decidir destino do Document stateful (`self.documents`)** — decisão arquitetural deferida.

   **Contexto:** O design original (jun/2025) era inspirado no spaCy — Document como hub central que acumula análises progressivamente. O fluxo imaginado era: criar documento → rodar múltiplos plugins → resultados acumulam em `doc._analyses` → recuperar depois via `get_document()`. Na prática, o Qualia evoluiu pra stateless (API REST, cada request cria Document efêmero, executa, descarta).

   **Estado atual (mar/2026):**
   - `add_document()` chamado em 11 pontos (5 API, 5 CLI, 1 webhook) — todos criam, executam, descartam
   - `get_document()` nunca chamado em produção (só 2 testes)
   - `get_analysis()`, `add_variant()`, `get_variant()` — nunca chamados por ninguém
   - `self.documents` dict cresce sem limite (memory leak lento, inofensivo pro uso local)
   - `Document._analyses` é populado pelo `execute_plugin` mas nunca lido (resultados vão pro cache e pro response direto)

   **Onde faria sentido no futuro:**
   - Sessões de análise interativa no frontend (múltiplas análises no mesmo doc, acumulando)
   - Pipeline stateful onde plugin B lê resultado do plugin A via `doc.get_analysis("A")`
   - Consumers stateful (DeepVoC, Observatório) que mantêm histórico de análises

   **Hoje esses cenários já são cobertos** pelo CacheManager (resultados cacheados por doc_id+plugin_id+config) e pelo DependencyResolver (deps executadas automaticamente). O Document stateful seria uma camada adicional de conveniência.

   **Arquivos envolvidos (não deletar sem decisão):**
   - `qualia/core/models.py` — Document class (campos: `_analyses`, `_variants`, `_cache`; métodos: `add_analysis`, `get_analysis`, `add_variant`, `get_variant`)
   - `qualia/core/engine.py` — `self.documents` dict, `add_document()`, `get_document()`, `self.pipelines`, `save_pipeline()`
   - `qualia/core/engine.py:135` — `document.add_analysis(plugin_id, result)` dentro do `execute_plugin`

   **Decisão pendente:** limpar (remover dict e dead code) ou evoluir (adicionar TTL/LRU e implementar sessões). Deferida até haver use case concreto.

## Comportamento

- [x] Pipeline fail-fast vs fail-soft — definir comportamento claro em falha de step

## Cobertura de Testes

Sessão de 2026-03-17: de 237 testes (42%) para 610 testes (84%).

Módulos ainda abaixo de 90%:
- `core/__init__.py` — 83% (interfaces abstratas + edge cases)
- `api/__init__.py` — 91% (SPA fallback, import errors)
- `commands/batch.py` — 80%
- `commands/export.py` — 86%
- `interactive/wizards.py` — 80%
- `interactive/menu.py` — 83%

## Feito nesta sessão

- [x] Remover código morto (run_api.py, api/run.py, cli/commands.py)
- [x] Remover módulos vazios (document_lab, para_meta, quali_metrics, visual_engine)
- [x] Remover protection morta (auto_protection.py, protected_bases.py)
- [x] Migrar setup.py → pyproject.toml
- [x] Organizar docs (históricos → docs/morto/, ignorado pelo git)
- [x] Adicionar coverage ao CI
- [x] Alinhar Python 3.13 no Dockerfile + corrigir entrypoint
- [x] Arquivar planos finalizados
- [x] Coverage de 42% → 84% (373 testes novos)
- [x] Dividir api/__init__.py (694→111 linhas) em deps, schemas, routes/
- [x] Corrigir Makefile (targets quebrados, referências mortas)
- [x] Remover test_suite.py legado (esperava 6 plugins, usava run_api.py)
- [x] Limpar docker-compose (remover prometheus/grafana/redis fantasma)
- [x] Atualizar README (237→610 testes)
