# Recursive Plugin Discovery — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tornar o PluginLoader agnóstico à organização de pastas — descobre plugins em qualquer profundidade dentro de `plugins/`, ignorando pastas que começam com `_`.

**Architecture:** Trocar `iterdir()` por walk recursivo no `PluginLoader.discover()`. Qualquer diretório com `__init__.py` que exporte uma classe `IPlugin` é carregado, não importa a profundidade. Pastas prefixadas com `_` (como `_templates`) são ignoradas explicitamente. Nenhuma mudança em engine, API, CLI, ou qualquer consumer — o loader é a única mudança funcional.

**Tech Stack:** pathlib (rglob), importlib

---

## File Structure

| Arquivo | Responsabilidade | Ação |
|---|---|---|
| `qualia/core/loader.py` | Discovery de plugins | Modify: trocar iterdir por walk recursivo |
| `tests/test_loader_recursive.py` | Testes do discovery recursivo | Create |
| `qualia/cli/commands/create.py` | Comando create | Modify: aceitar `--dir` opcional pra criar em subpasta |
| `tests/test_cli_create.py` | Testes do create | Modify: adicionar teste com --dir |

---

## Chunk 1: Loader recursivo

### Task 1: Testes do discovery recursivo

**Files:**
- Create: `tests/test_loader_recursive.py`

- [ ] **Step 1: Escrever testes para discovery recursivo**

```python
"""Testes do discovery recursivo de plugins."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from qualia.core.loader import PluginLoader


@pytest.fixture
def plugin_tree(tmp_path):
    """Cria árvore de plugins em múltiplos níveis."""
    # Plugin flat (nível 1) — como hoje
    flat = tmp_path / "flat_plugin"
    flat.mkdir()
    (flat / "__init__.py").write_text('''
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document

class FlatAnalyzer(BaseAnalyzerPlugin):
    def meta(self):
        return PluginMetadata(
            id="flat_plugin", name="Flat", type=PluginType.ANALYZER,
            version="0.1.0", description="flat", provides=["flat_result"],
        )
    def _analyze_impl(self, doc, config, ctx):
        return {"flat_result": True}
''')

    # Plugin nested (nível 2) — plugins/analyzers/nested_plugin/
    analyzers = tmp_path / "analyzers"
    analyzers.mkdir()
    nested = analyzers / "nested_plugin"
    nested.mkdir()
    (nested / "__init__.py").write_text('''
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document

class NestedAnalyzer(BaseAnalyzerPlugin):
    def meta(self):
        return PluginMetadata(
            id="nested_plugin", name="Nested", type=PluginType.ANALYZER,
            version="0.1.0", description="nested", provides=["nested_result"],
        )
    def _analyze_impl(self, doc, config, ctx):
        return {"nested_result": True}
''')

    # Plugin deep (nível 3) — plugins/documents/cleaners/deep_plugin/
    cleaners = tmp_path / "documents" / "cleaners"
    cleaners.mkdir(parents=True)
    deep = cleaners / "deep_plugin"
    deep.mkdir()
    (deep / "__init__.py").write_text('''
from qualia.core import BaseDocumentPlugin, PluginMetadata, PluginType, Document

class DeepProcessor(BaseDocumentPlugin):
    def meta(self):
        return PluginMetadata(
            id="deep_plugin", name="Deep", type=PluginType.DOCUMENT,
            version="0.1.0", description="deep",
            provides=["cleaned_document", "quality_report"],
        )
    def _process_impl(self, doc, config, ctx):
        return {"cleaned_document": doc.content, "quality_report": {}}
''')

    # Pasta _templates (deve ser ignorada)
    templates = tmp_path / "_templates"
    templates.mkdir()
    (templates / "analyzer.py").write_text("# template, not a plugin")

    # Pasta organizadora sem __init__.py (deve ser traversada, não carregada)
    # analyzers/ não tem __init__.py — é só agrupamento

    return tmp_path


class TestRecursiveDiscovery:

    def test_discovers_flat_plugin(self, plugin_tree):
        """Plugins no nível 1 continuam funcionando"""
        loader = PluginLoader(plugin_tree)
        discovered = loader.discover()
        assert "flat_plugin" in discovered

    def test_discovers_nested_plugin(self, plugin_tree):
        """Plugins no nível 2 são descobertos"""
        loader = PluginLoader(plugin_tree)
        discovered = loader.discover()
        assert "nested_plugin" in discovered

    def test_discovers_deep_plugin(self, plugin_tree):
        """Plugins no nível 3 são descobertos"""
        loader = PluginLoader(plugin_tree)
        discovered = loader.discover()
        assert "deep_plugin" in discovered

    def test_ignores_underscore_dirs(self, plugin_tree):
        """Pastas com _ no início são ignoradas"""
        loader = PluginLoader(plugin_tree)
        discovered = loader.discover()
        # Nenhum plugin de _templates
        for pid in discovered:
            assert not pid.startswith("_")

    def test_discovers_all_plugins(self, plugin_tree):
        """Descobre todos os 3 plugins em todos os níveis"""
        loader = PluginLoader(plugin_tree)
        discovered = loader.discover()
        assert len(discovered) == 3
        assert set(discovered.keys()) == {"flat_plugin", "nested_plugin", "deep_plugin"}

    def test_empty_dir_no_error(self, tmp_path):
        """Diretório vazio não causa erro"""
        loader = PluginLoader(tmp_path)
        discovered = loader.discover()
        assert discovered == {}

    def test_nonexistent_dir_no_error(self, tmp_path):
        """Diretório inexistente não causa erro"""
        loader = PluginLoader(tmp_path / "nonexistent")
        discovered = loader.discover()
        assert discovered == {}

    def test_duplicate_id_raises(self, plugin_tree):
        """Plugin com ID duplicado em subpasta diferente levanta ValueError"""
        # Cria segundo plugin com mesmo ID
        dup = plugin_tree / "visualizers" / "flat_plugin"
        dup.mkdir(parents=True)
        (dup / "__init__.py").write_text('''
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document

class DupAnalyzer(BaseAnalyzerPlugin):
    def meta(self):
        return PluginMetadata(
            id="flat_plugin", name="Dup", type=PluginType.ANALYZER,
            version="0.1.0", description="dup", provides=["dup_result"],
        )
    def _analyze_impl(self, doc, config, ctx):
        return {"dup_result": True}
''')
        loader = PluginLoader(plugin_tree)
        with pytest.raises(ValueError, match="duplicado"):
            loader.discover()
```

- [ ] **Step 2: Rodar testes pra confirmar que falham**

Run: `pytest tests/test_loader_recursive.py -v`
Expected: FAIL — nested_plugin e deep_plugin não são descobertos (loader só faz 1 nível)

- [ ] **Step 3: Commit testes**

```bash
git add tests/test_loader_recursive.py
~/.claude/scripts/commit.sh "test: testes para discovery recursivo de plugins"
```

---

### Task 2: Implementar discovery recursivo no loader

**Files:**
- Modify: `qualia/core/loader.py:41-117` (método `discover`)

- [ ] **Step 1: Implementar walk recursivo**

Substituir o bloco `for plugin_dir in self.plugins_dir.iterdir()` (linhas 56-110) por walk recursivo. A lógica interna (carregar módulo, detectar IPlugin, eager/lazy) permanece idêntica — só muda como as pastas são encontradas.

Novo método auxiliar `_find_plugin_dirs()` que retorna todas as pastas com `__init__.py`, em qualquer profundidade, ignorando pastas que começam com `_`:

```python
def _find_plugin_dirs(self) -> list[Path]:
    """Encontra todas as pastas com __init__.py recursivamente.

    Ignora pastas cujo nome começa com _ (ex: _templates).
    """
    plugin_dirs = []
    for init_file in self.plugins_dir.rglob("__init__.py"):
        plugin_dir = init_file.parent
        # Ignorar se qualquer componente do path relativo começa com _
        rel = plugin_dir.relative_to(self.plugins_dir)
        if any(part.startswith('_') for part in rel.parts):
            continue
        plugin_dirs.append(plugin_dir)
    return plugin_dirs
```

No `discover()`, trocar:
```python
# ANTES
for plugin_dir in self.plugins_dir.iterdir():
    if plugin_dir.is_dir() and (plugin_dir / "__init__.py").exists():

# DEPOIS
for plugin_dir in self._find_plugin_dirs():
```

O resto do corpo do loop permanece exatamente igual.

- [ ] **Step 2: Rodar testes do loader recursivo**

Run: `pytest tests/test_loader_recursive.py -v`
Expected: 8 PASSED

- [ ] **Step 3: Rodar suite completa**

Run: `pytest tests/ -q`
Expected: 790 passed (782 + 8 novos), 5 skipped

- [ ] **Step 4: Verificar que os 8 plugins reais continuam funcionando**

Run: `source .venv/bin/activate && python -c "from qualia.core import QualiaCore; c = QualiaCore(); print(f'{len(c.registry)} plugins: {sorted(c.registry.keys())}')"`
Expected: `8 plugins: ['frequency_chart_plotly', 'readability_analyzer', 'sentiment_analyzer', 'sentiment_viz_plotly', 'teams_cleaner', 'transcription', 'word_frequency', 'wordcloud_d3']`

- [ ] **Step 5: Commit**

```bash
git add qualia/core/loader.py
~/.claude/scripts/commit.sh "feat: discovery recursivo de plugins — qualquer profundidade, ignora pastas com _"
```

---

## Chunk 2: Atualizar create command e docs

### Task 3: Adicionar opção `--dir` ao comando create

**Files:**
- Modify: `qualia/cli/commands/create.py`
- Modify: `tests/test_cli_create.py`

O comando `qualia create` hoje gera em `plugins/<id>/`. Com discovery recursivo, o dev pode querer gerar em `plugins/analyzers/<id>/`. Adicionar `--dir` opcional:

```
qualia create meu_analyzer analyzer                    → plugins/meu_analyzer/
qualia create meu_analyzer analyzer --dir analyzers    → plugins/analyzers/meu_analyzer/
```

- [ ] **Step 1: Adicionar teste para --dir**

Adicionar ao `tests/test_cli_create.py`:

```python
def test_create_with_dir(self, runner, tmp_path):
    """Cria plugin em subpasta com --dir"""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _setup_templates(tmp_path)
        result = runner.invoke(cli, ["create", "sub_analyzer", "analyzer", "--dir", "analyzers"])
        assert result.exit_code == 0
        init_file = Path("plugins/analyzers/sub_analyzer/__init__.py")
        assert init_file.exists()
        content = init_file.read_text()
        assert "class SubAnalyzerAnalyzer" in content
```

- [ ] **Step 2: Rodar teste pra confirmar que falha**

Run: `pytest tests/test_cli_create.py::TestCreateCommand::test_create_with_dir -v`
Expected: FAIL — `--dir` não existe ainda

- [ ] **Step 3: Implementar --dir no create.py**

Adicionar `@click.option('--dir', '-d', 'subdir', default=None, help='Subpasta dentro de plugins/ (ex: analyzers)')` ao comando.

Atualizar a resolução do `plugin_dir`:

```python
# ANTES
plugin_dir = Path("plugins") / plugin_id

# DEPOIS
if subdir:
    plugin_dir = Path("plugins") / subdir / plugin_id
else:
    plugin_dir = Path("plugins") / plugin_id
```

- [ ] **Step 4: Rodar testes do create**

Run: `pytest tests/test_cli_create.py -v`
Expected: 8 PASSED (7 anteriores + 1 novo)

- [ ] **Step 5: Commit**

```bash
git add qualia/cli/commands/create.py tests/test_cli_create.py
~/.claude/scripts/commit.sh "feat: qualia create --dir — cria plugins em subpastas"
```

---

### Task 4: Atualizar documentação

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/TECHNICAL_STATE.md`

- [ ] **Step 1: Atualizar CLAUDE.md**

Na seção Plugins, adicionar nota sobre organização livre:

Trocar: `O core descobre plugins automaticamente — basta criar pasta em plugins/ com __init__.py que exporte a classe. Sem registro manual.`

Por: `O core descobre plugins automaticamente em qualquer profundidade dentro de plugins/ — basta ter __init__.py que exporte a classe. Organize como quiser (flat, por tipo, por domínio). Pastas com _ no nome são ignoradas. Sem registro manual.`

- [ ] **Step 2: Atualizar TECHNICAL_STATE.md**

Na seção de loading, atualizar a descrição do discovery para mencionar o walk recursivo.

- [ ] **Step 3: Rodar suite completa**

Run: `pytest tests/ -q`
Expected: 790 passed, 5 skipped

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs/TECHNICAL_STATE.md
~/.claude/scripts/commit.sh "docs: discovery recursivo documentado"
```

- [ ] **Step 5: Push**

```bash
git push
```

- [ ] **Step 6: Arquivar plano**

```bash
mv docs/superpowers/plans/2026-03-19-recursive-plugin-discovery.md docs/archive/claude_sources/plans/20260319-recursive-plugin-discovery.md
rm -rf docs/superpowers/
git add -A
~/.claude/scripts/commit.sh "chore: arquiva plano de discovery recursivo"
git push
```
