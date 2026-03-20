# Mutation Testing Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rodar mutation testing nos módulos críticos do Qualia, triar sobreviventes, e matar os que indicam gaps reais nos testes.

**Architecture:** mutmut 3.x configurado via `pyproject.toml`. 3 fases por prioridade de retorno. Cada fase: rodar mutmut no módulo, triar sobreviventes com critérios do Codex, escrever testes pra matar os relevantes.

**Tech Stack:** mutmut 3.5, pytest, pyproject.toml

---

## Critérios de triagem dos sobreviventes

Pra cada mutante que sobrevive:

- **kill required** — branch de erro, timeout, validação, contrato provides, cache key, cleanup → escrever teste
- **provável gap** — condição booleana, comparação, ordem de merge, fallback de formato → escrever teste
- **equivalent mutant** — logging, string literal irrelevante, refator sem efeito observável → ignorar

---

## File Structure

- **Modify:** `pyproject.toml` — adicionar `[tool.mutmut]`
- **Modify:** `tests/` — testes novos pra matar sobreviventes
- **No new files** (mutmut gera `mutants/` como dir temporário)

---

### Task 1: Configurar mutmut

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Adicionar seção mutmut ao pyproject.toml**

Adicionar ao final do `pyproject.toml`:

```toml
[tool.mutmut]
runner = "python -m pytest tests/ -x -q --timeout=10 --no-header"
```

- [ ] **Step 2: Validar que mutmut roda num módulo pequeno**

Run: `source .venv/bin/activate && mutmut run "qualia/core/models.py" 2>&1 | tail -5`
Expected: roda sem crash, mostra resultado (killed/survived)

Se der erro de import no mutants dir: ajustar o runner pra incluir `PYTHONPATH=.` ou `pip install -e .` no setup.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
~/.claude/scripts/commit.sh "chore: configura mutmut pra mutation testing"
```

---

### Task 2: Fase 1 — módulos de maior retorno

**Files:**
- Modules: `qualia/core/engine.py`, `qualia/core/cache.py`, `qualia/api/routes/pipeline.py`

- [ ] **Step 1: Rodar mutmut em engine.py**

Run: `source .venv/bin/activate && mutmut run "qualia/core/engine.py"`
Anotar: total de mutantes, killed, survived, timeout

- [ ] **Step 2: Listar sobreviventes de engine.py**

Run: `source .venv/bin/activate && mutmut results`
Para cada sobrevivente: `mutmut show <mutant_name>`

Triar com critérios acima. Anotar os que são "kill required" ou "provável gap".

- [ ] **Step 3: Rodar mutmut em cache.py**

Run: `source .venv/bin/activate && mutmut run "qualia/core/cache.py"`
Mesma triagem.

- [ ] **Step 4: Rodar mutmut em pipeline.py**

Run: `source .venv/bin/activate && mutmut run "qualia/api/routes/pipeline.py"`
Mesma triagem.

- [ ] **Step 5: Escrever testes para matar sobreviventes da Fase 1**

Para cada "kill required"/"provável gap":
1. Entender o que o mutante muda
2. Escrever teste que falha com a mutação e passa sem ela
3. Adicionar ao arquivo de teste existente mais relevante

- [ ] **Step 6: Re-rodar mutmut nos 3 módulos pra confirmar kills**

Run: `source .venv/bin/activate && mutmut run "qualia/core/engine.py" && mutmut run "qualia/core/cache.py" && mutmut run "qualia/api/routes/pipeline.py"`
Expected: todos os "kill required" agora morrem

- [ ] **Step 7: Rodar suite completa**

Run: `source .venv/bin/activate && pytest tests/ --tb=short`
Expected: tudo passa

- [ ] **Step 8: Commit**

```bash
git add tests/
~/.claude/scripts/commit.sh "test: mutation testing fase 1 — mata sobreviventes em engine, cache, pipeline"
```

---

### Task 3: Fase 2 — validação e contratos

**Files:**
- Modules: `qualia/core/base_plugins.py`, `qualia/api/deps.py`, `qualia/api/routes/transcribe.py`, `qualia/api/routes/visualize.py`

- [ ] **Step 1: Rodar mutmut nos 4 módulos**

```bash
source .venv/bin/activate
mutmut run "qualia/core/base_plugins.py"
mutmut run "qualia/api/deps.py"
mutmut run "qualia/api/routes/transcribe.py"
mutmut run "qualia/api/routes/visualize.py"
```

- [ ] **Step 2: Triar sobreviventes**

Mesmos critérios. Anotar "kill required" e "provável gap".

- [ ] **Step 3: Escrever testes para matar sobreviventes da Fase 2**

Adicionar aos arquivos de teste existentes.

- [ ] **Step 4: Rodar suite completa**

Run: `source .venv/bin/activate && pytest tests/ --tb=short`
Expected: tudo passa

- [ ] **Step 5: Commit**

```bash
git add tests/
~/.claude/scripts/commit.sh "test: mutation testing fase 2 — mata sobreviventes em base_plugins, deps, transcribe, visualize"
```

---

### Task 4: Fase 3 — consistência de interface

**Files:**
- Modules: `qualia/api/routes/analyze.py`, `qualia/api/routes/process.py`, `qualia/cli/commands/pipeline.py`, `qualia/cli/commands/process.py`

- [ ] **Step 1: Rodar mutmut nos 4 módulos**

```bash
source .venv/bin/activate
mutmut run "qualia/api/routes/analyze.py"
mutmut run "qualia/api/routes/process.py"
mutmut run "qualia/cli/commands/pipeline.py"
mutmut run "qualia/cli/commands/process.py"
```

- [ ] **Step 2: Triar e matar sobreviventes**

Mesma abordagem das fases anteriores.

- [ ] **Step 3: Rodar suite completa**

Run: `source .venv/bin/activate && pytest tests/ --tb=short`
Expected: tudo passa

- [ ] **Step 4: Commit**

```bash
git add tests/
~/.claude/scripts/commit.sh "test: mutation testing fase 3 — mata sobreviventes em analyze, process, CLI pipeline/process"
```

---

### Task 5: Relatório final e cleanup

- [ ] **Step 1: Rodar mutmut em todos os módulos das 3 fases e anotar score final**

Registrar: total mutantes, killed, survived (equivalent), % kill rate por módulo.

- [ ] **Step 2: Limpar artefatos**

```bash
rm -rf mutants/ .mutmut-cache/
```

- [ ] **Step 3: Atualizar BACKLOG.md com resultado**

Adicionar seção "Mutation testing (2026-03-20)" com o score por módulo.

- [ ] **Step 4: Commit final**

```bash
git add docs/BACKLOG.md
~/.claude/scripts/commit.sh "docs: resultado mutation testing — score por módulo"
```
