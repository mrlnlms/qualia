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
    return _TEMPLATES_DIR


@click.command()
@click.argument("plugin_id", required=False)
@click.argument("plugin_type", required=False,
                type=click.Choice(["analyzer", "visualizer", "document"], case_sensitive=False))
@click.option("--dir", "-d", "subdir", default=None,
              help="Subpasta dentro de plugins/ (ex: analyzers, documents/cleaners)")
def create(plugin_id: str, plugin_type: str, subdir: str):
    """Cria novo plugin a partir de template.

    Exemplos:
        qualia create meu_analyzer analyzer
        qualia create meu_viz visualizer --dir visualizers
        qualia create meu_cleaner document -d documents/cleaners
        qualia create  (lista templates disponíveis)
    """
    templates_dir = _resolve_templates_dir()

    # Sem argumentos: lista templates disponíveis
    if not plugin_id:
        console.print("[bold]Templates disponíveis:[/bold]\n")
        for tpl_type in _CLASS_SUFFIXES:
            tpl_file = templates_dir / f"{tpl_type}.py"
            exists = tpl_file.exists()
            mark = "✓" if exists else "✗"
            color = "green" if exists else "red"
            console.print(f"  [{color}]{mark}[/] {tpl_type:12} → qualia create <nome> {tpl_type}")
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
        console.print("[dim]Verifique se plugins/_templates/ existe com os arquivos .py[/dim]")
        raise SystemExit(1)

    # Verificar se plugin já existe
    if subdir:
        plugin_dir = Path("plugins") / subdir / plugin_id
    else:
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
    rel_path = plugin_dir
    console.print(f"\n[green]✓ Plugin criado: {rel_path}/[/green]")
    console.print(f"\nPróximos passos:")
    console.print(f"  1. Editar {rel_path}/__init__.py — procurar por TODO")
    console.print(f"  2. Se precisar de deps novas, adicionar no pyproject.toml (extras)")
    console.print(f"  3. Testar: python plugins/{plugin_id}/__init__.py")
    console.print(f"  4. Usar:   qualia {cli_cmd} arquivo.txt -p {plugin_id}")
