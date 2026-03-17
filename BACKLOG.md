# Backlog — Qualia Core

Levantamento em 2026-03-17 (análise cruzada Claude + Codex), atualizado na mesma sessão.

## Refatoração (prioridade técnica)

1. [ ] Quebrar `qualia/core/__init__.py` (902 linhas) — separar em contracts, models, loader, cache, executor, pipeline. Manter re-exports no `__init__.py` pra não quebrar imports
2. [ ] Dividir `qualia/api/__init__.py` (694 linhas) — separar bootstrap, schemas e rotas

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
