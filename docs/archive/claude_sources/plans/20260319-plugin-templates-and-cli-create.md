# Plugin Templates + CLI Create — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extrair templates de plugin para arquivos copiáveis em `plugins/_templates/` e criar comando CLI `qualia create` que gera plugins a partir desses templates.

**Architecture:** Os 3 templates (analyzer, visualizer, document) viram arquivos `.py` reais em `plugins/_templates/`. O loader ignora essa pasta (sem `__init__.py`). O novo comando CLI `qualia create` lê os templates, substitui placeholders, e gera o plugin em `plugins/`. O script `tools/create_plugin.py` é removido.

**Tech Stack:** Click (CLI), Rich (output), pathlib, string.Template ou str.format

---

## Chunk 1: Templates como arquivos copiáveis

### Task 1: Criar os 3 arquivos de template em `plugins/_templates/`

**Files:**
- Create: `plugins/_templates/analyzer.py`
- Create: `plugins/_templates/visualizer.py`
- Create: `plugins/_templates/document.py`

Os templates são extraídos do `TEMPLATES` dict em `tools/create_plugin.py`. A diferença: como agora são arquivos `.py` reais (copiáveis), os placeholders usam o padrão `__PLUGIN_ID__`, `__CLASS_NAME__`, `__PLUGIN_TITLE__`, `__DATE__` em vez de `{plugin_id}` (que conflita com dicts Python). As double-braces `{{` `}}` dos templates atuais voltam a ser `{` `}` normais.

- [ ] **Step 1: Criar `plugins/_templates/analyzer.py`**

Converter o template `TEMPLATES["analyzer"]` de `tools/create_plugin.py` para arquivo real:
- Trocar `{plugin_id}` → `__PLUGIN_ID__`
- Trocar `{class_name}` → `__CLASS_NAME__`
- Trocar `{plugin_title}` → `__PLUGIN_TITLE__`
- Trocar `{date}` → `__DATE__`
- Trocar `{{` → `{` e `}}` → `}` (dicts Python normais)
- Remover bloco `if __name__ == "__main__"` (não faz sentido com placeholders)

- [ ] **Step 2: Criar `plugins/_templates/visualizer.py`**

Mesmo processo para o template `TEMPLATES["visualizer"]`.

- [ ] **Step 3: Criar `plugins/_templates/document.py`**

Mesmo processo para o template `TEMPLATES["document"]`.

- [ ] **Step 4: Verificar que o loader ignora `_templates/`**

Run: `source .venv/bin/activate && python -c "from qualia.core import QualiaCore; c = QualiaCore(); c.discover_plugins(); print([p for p in c.registry])"`

Expected: Lista dos 8 plugins existentes, sem nenhum `_templates` ou erro.

- [ ] **Step 5: Verificar que os templates são Python válido (com placeholders)**

Run: `python -c "content = open('plugins/_templates/analyzer.py').read(); print('OK' if '__PLUGIN_ID__' in content and 'class __CLASS_NAME__' in content else 'FAIL')"`

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add plugins/_templates/
~/.claude/scripts/commit.sh "feat: templates de plugin como arquivos copiáveis em plugins/_templates/"
```

---

### Task 2: Criar comando CLI `qualia create`

**Files:**
- Create: `qualia/cli/commands/create.py`
- Modify: `qualia/cli/commands/__init__.py` (adicionar import + registro)

- [ ] **Step 1: Escrever teste para o comando create — happy path analyzer**

Create: `tests/test_cli_create.py`

```python
"""Testes do comando qualia create"""

import pytest
from pathlib import Path
from click.testing import CliRunner

from qualia.cli.commands import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestCreateCommand:
    """Testes do comando create"""

    def test_create_analyzer(self, runner, tmp_path):
        """Cria analyzer com sucesso"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Precisa da pasta _templates no lugar certo
            templates_dir = Path("plugins/_templates")
            templates_dir.mkdir(parents=True)
            # Copia template real
            import shutil
            real_templates = Path(__file__).parent.parent / "plugins" / "_templates"
            for f in real_templates.glob("*.py"):
                shutil.copy(f, templates_dir / f.name)

            result = runner.invoke(cli, ["create", "test_analyzer", "analyzer"])
            assert result.exit_code == 0
            init_file = Path("plugins/test_analyzer/__init__.py")
            assert init_file.exists()
            content = init_file.read_text()
            assert "class TestAnalyzerAnalyzer" in content
            assert "test_analyzer" in content
            assert "__PLUGIN_ID__" not in content

    def test_create_visualizer(self, runner, tmp_path):
        """Cria visualizer com sucesso"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            templates_dir = Path("plugins/_templates")
            templates_dir.mkdir(parents=True)
            import shutil
            real_templates = Path(__file__).parent.parent / "plugins" / "_templates"
            for f in real_templates.glob("*.py"):
                shutil.copy(f, templates_dir / f.name)

            result = runner.invoke(cli, ["create", "test_viz", "visualizer"])
            assert result.exit_code == 0
            content = Path("plugins/test_viz/__init__.py").read_text()
            assert "class TestVizVisualizer" in content

    def test_create_document(self, runner, tmp_path):
        """Cria document processor com sucesso"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            templates_dir = Path("plugins/_templates")
            templates_dir.mkdir(parents=True)
            import shutil
            real_templates = Path(__file__).parent.parent / "plugins" / "_templates"
            for f in real_templates.glob("*.py"):
                shutil.copy(f, templates_dir / f.name)

            result = runner.invoke(cli, ["create", "test_cleaner", "document"])
            assert result.exit_code == 0
            content = Path("plugins/test_cleaner/__init__.py").read_text()
            assert "class TestCleanerProcessor" in content

    def test_create_invalid_type(self, runner, tmp_path):
        """Tipo inválido mostra erro"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["create", "test_plugin", "invalid"])
            assert result.exit_code != 0

    def test_create_existing_plugin(self, runner, tmp_path):
        """Plugin que já existe mostra erro"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            templates_dir = Path("plugins/_templates")
            templates_dir.mkdir(parents=True)
            import shutil
            real_templates = Path(__file__).parent.parent / "plugins" / "_templates"
            for f in real_templates.glob("*.py"):
                shutil.copy(f, templates_dir / f.name)

            # Cria plugin
            Path("plugins/existing").mkdir(parents=True)
            result = runner.invoke(cli, ["create", "existing", "analyzer"])
            assert result.exit_code == 1
            assert "existe" in result.output.lower()

    def test_create_lists_templates(self, runner, tmp_path):
        """Sem argumentos lista templates disponíveis"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["create"])
            assert result.exit_code == 0
            assert "analyzer" in result.output
            assert "visualizer" in result.output
            assert "document" in result.output
```

- [ ] **Step 2: Rodar teste pra confirmar que falha**

Run: `pytest tests/test_cli_create.py -v`
Expected: FAIL — módulo `create` não existe ainda

- [ ] **Step 3: Implementar `qualia/cli/commands/create.py`**

```python
# qualia/cli/commands/create.py
"""
Comando para criar plugins a partir dos templates.
"""

import click
from pathlib import Path
from datetime import datetime

from .utils import console


# Resolve pasta de templates relativa ao pacote (não ao cwd)
_TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "plugins" / "_templates"

# Mapa tipo → sufixo da classe
_CLASS_SUFFIXES = {
    "analyzer": "Analyzer",
    "visualizer": "Visualizer",
    "document": "Processor",
}

# Mapa tipo → comando CLI correspondente
_CLI_COMMANDS = {
    "analyzer": "analyze",
    "visualizer": "visualize",
    "document": "process",
}


def _resolve_templates_dir() -> Path:
    """Tenta achar _templates/ — primeiro relativo ao pacote, depois relativo ao cwd."""
    if _TEMPLATES_DIR.exists():
        return _TEMPLATES_DIR
    local = Path("plugins/_templates")
    if local.exists():
        return local
    return _TEMPLATES_DIR  # retorna o padrão (vai dar erro descritivo depois)


@click.command()
@click.argument("plugin_id", required=False)
@click.argument("plugin_type", required=False,
                type=click.Choice(["analyzer", "visualizer", "document"], case_sensitive=False))
def create(plugin_id: str, plugin_type: str):
    """Cria novo plugin a partir de template.

    Exemplos:
        qualia create meu_analyzer analyzer
        qualia create meu_viz visualizer
        qualia create meu_cleaner document
        qualia create  (lista templates disponíveis)
    """
    templates_dir = _resolve_templates_dir()

    # Sem argumentos: lista templates disponíveis
    if not plugin_id:
        console.print("[bold]Templates disponíveis:[/bold]\n")
        for tpl_type in _CLASS_SUFFIXES:
            tpl_file = templates_dir / f"{tpl_type}.py"
            exists = "✓" if tpl_file.exists() else "✗"
            console.print(f"  [{('green' if tpl_file.exists() else 'red')}]{exists}[/] {tpl_type:12} → qualia create <nome> {tpl_type}")
        console.print(f"\n[dim]Templates em: {templates_dir}[/dim]")
        console.print("[dim]Ou copie manualmente: cp plugins/_templates/analyzer.py plugins/meu_plugin/__init__.py[/dim]")
        return

    if not plugin_type:
        console.print("[red]Especifique o tipo: qualia create <nome> <tipo>[/red]")
        console.print("Tipos: analyzer, visualizer, document")
        raise SystemExit(1)

    # Verificar template existe
    template_file = templates_dir / f"{plugin_type}.py"
    if not template_file.exists():
        console.print(f"[red]Template não encontrado: {template_file}[/red]")
        console.print(f"[dim]Verifique se plugins/_templates/ existe com os arquivos .py[/dim]")
        raise SystemExit(1)

    # Verificar se plugin já existe
    plugin_dir = Path("plugins") / plugin_id
    if plugin_dir.exists():
        console.print(f"[red]Plugin '{plugin_id}' já existe em {plugin_dir}/[/red]")
        raise SystemExit(1)

    # Preparar variáveis
    class_name = ''.join(word.capitalize() for word in plugin_id.split('_'))
    class_name += _CLASS_SUFFIXES[plugin_type]
    plugin_title = ' '.join(word.capitalize() for word in plugin_id.split('_'))
    date = datetime.now().strftime("%Y-%m-%d")

    # Ler template e substituir placeholders
    content = template_file.read_text()
    content = content.replace("__PLUGIN_ID__", plugin_id)
    content = content.replace("__CLASS_NAME__", class_name)
    content = content.replace("__PLUGIN_TITLE__", plugin_title)
    content = content.replace("__DATE__", date)

    # Criar plugin
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "__init__.py").write_text(content)

    cli_cmd = _CLI_COMMANDS[plugin_type]
    console.print(f"\n[green]✓ Plugin criado: plugins/{plugin_id}/[/green]")
    console.print(f"\nPróximos passos:")
    console.print(f"  1. Editar plugins/{plugin_id}/__init__.py — procurar por TODO")
    console.print(f"  2. Se precisar de deps novas, adicionar no pyproject.toml (extras)")
    console.print(f"  3. Testar: python plugins/{plugin_id}/__init__.py")
    console.print(f"  4. Usar:   qualia {cli_cmd} arquivo.txt -p {plugin_id}")
```

- [ ] **Step 4: Registrar comando no `__init__.py`**

Em `qualia/cli/commands/__init__.py`, adicionar:

```python
from .create import create
```

E no bloco de registro:

```python
cli.add_command(create)
```

- [ ] **Step 5: Rodar testes pra confirmar que passam**

Run: `pytest tests/test_cli_create.py -v`
Expected: 6 PASSED

- [ ] **Step 6: Rodar suite completa**

Run: `pytest tests/ -v`
Expected: 781 passed (775 + 6 novos), 5 skipped

- [ ] **Step 7: Commit**

```bash
git add qualia/cli/commands/create.py qualia/cli/commands/__init__.py tests/test_cli_create.py
~/.claude/scripts/commit.sh "feat: comando qualia create — gera plugins a partir dos templates"
```

---

### Task 3: Remover `tools/` e atualizar referências

**Files:**
- Delete: `tools/create_plugin.py`
- Delete: `tools/` (pasta inteira)
- Modify: `CLAUDE.md` (remover referência a tools/)
- Modify: `docs/TECHNICAL_STATE.md` (remover referência a tools/)

- [ ] **Step 1: Verificar referências a `tools/` no projeto**

Run: `grep -r "tools/" --include="*.py" --include="*.md" . | grep -v docs/morto | grep -v .git`

Corrigir cada referência encontrada.

- [ ] **Step 2: Atualizar CLAUDE.md**

Na seção de Arquitetura, remover a linha `tools/` e atualizar a referência ao template:
- Trocar `Template: tools/create_plugin.py` → `Template: plugins/_templates/ ou qualia create`

- [ ] **Step 3: Atualizar TECHNICAL_STATE.md**

Na seção de thread-safety, trocar referência a `tools/create_plugin.py` → `plugins/_templates/`

- [ ] **Step 4: Deletar `tools/`**

```bash
rm -rf tools/
```

- [ ] **Step 5: Rodar suite completa pra confirmar nada quebrou**

Run: `pytest tests/ -v`
Expected: 781 passed, 5 skipped

- [ ] **Step 6: Commit**

```bash
git add -A
~/.claude/scripts/commit.sh "chore: remove tools/ — templates migrados pra plugins/_templates/, criação via qualia create"
```

- [ ] **Step 7: Push**

```bash
git push
```
