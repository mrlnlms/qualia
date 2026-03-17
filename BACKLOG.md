# Backlog — Qualia Core

Levantamento feito em 2026-03-17 a partir de análise técnica cruzada (Claude + Codex).

## Governança do Repo

- [ ] Remover screenshots soltos da raiz (5 PNGs + `Qulaia screenshots/`)

## Refatoração

- [ ] Quebrar `qualia/core/__init__.py` (902 linhas) — separar em contracts, models, loader, cache, executor, pipeline. Manter re-exports no `__init__.py`
- [ ] Dividir `qualia/api/__init__.py` (694 linhas) — separar em app, schemas, routes, dependencies

## Cobertura de Testes (42% total)

Core e config estão bem cobertos (82% e 98%). O problema está na CLI e em módulos sem teste nenhum.

### Cobertura critica (<25%)

- [ ] `cli/interactive/handlers.py` — 9% (305/336 linhas sem teste)
- [ ] `cli/interactive/utils.py` — 12% (119/135)
- [ ] `cli/commands/visualize.py` — 12% (106/121)
- [ ] `cli/commands/inspect.py` — 16% (36/43)
- [ ] `cli/interactive/wizards.py` — 18% (73/89)
- [ ] `cli/commands/config.py` — 21% (131/166)
- [ ] `cli/commands/process.py` — 22% (47/60)
- [ ] `cli/interactive/__init__.py` — 23% (10/13)

### Cobertura baixa (25-50%)

- [ ] `cli/commands/watch.py` — 26% (68/92)
- [ ] `cli/interactive/menu.py` — 31% (29/42)
- [ ] `cli/formatters.py` — 37% (24/38)
- [ ] `cli/commands/batch.py` — 38% (67/108)
- [ ] `cli/interactive/tutorials.py` — 39% (20/33)
- [ ] `cli/commands/export.py` — 45% (94/170)

### Meta

- [ ] Coverage geral de 42% para pelo menos 70%
- [ ] CLI testável via `CliRunner` do Click — os 21 testes em `test_cli.py` provam que é viável
