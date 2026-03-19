# qualia/cli/commands/list.py
"""
Comandos para listar plugins disponíveis
"""

import click
from rich.table import Table

from qualia.core import PluginType
from .utils import get_core, console


def _classify_error(error_msg: str) -> tuple:
    """Classifica erro de discovery por tipo e sugere fix."""
    msg = error_msg.lower()
    if "no module named" in msg or "importerror" in msg:
        module = error_msg.split("'")[-2] if "'" in error_msg else "desconhecido"
        return "ImportError", f"pip install {module}"
    elif "syntaxerror" in msg or "syntax" in msg:
        return "SyntaxError", "Verificar código do plugin"
    elif "oserror" in msg or "no such file" in msg or "filenotfounderror" in msg:
        return "OSError", "Verificar arquivos/modelos necessários"
    elif "valueerror" in msg:
        return "ValueError", "Verificar meta() do plugin (id duplicado?)"
    else:
        return "Error", "Verificar log para detalhes"


def _run_check(core, type_filter: str):
    """Executa diagnóstico de saúde dos plugins."""
    if type_filter == 'all':
        plugins = list(core.registry.values())
    else:
        plugin_type = PluginType(type_filter)
        plugins = [p for p in core.registry.values() if p.type == plugin_type]

    errors = core.discovery_errors

    table = Table(title=f"Diagnóstico de Plugins ({len(plugins)} carregados, {len(errors)} com erro)")
    table.add_column("Plugin", style="cyan", no_wrap=True)
    table.add_column("Tipo", style="magenta")
    table.add_column("Loading", style="yellow")
    table.add_column("Status", style="green")

    for plugin in sorted(plugins, key=lambda p: p.id):
        cls = core.loader._plugin_classes.get(plugin.id)
        is_eager = cls is not None and '__init__' in getattr(cls, '__dict__', {})
        loading = "eager" if is_eager else "lazy"
        table.add_row(plugin.id, plugin.type.value, loading, "✓ saudável")

    console.print(table)

    if errors:
        console.print()
        err_table = Table(title="Plugins com Erro", style="red")
        err_table.add_column("Plugin", style="cyan")
        err_table.add_column("Tipo Erro", style="red")
        err_table.add_column("Mensagem", style="yellow")
        err_table.add_column("Sugestão", style="green")

        for err in errors:
            err_type, suggestion = _classify_error(err["error"])
            err_table.add_row(
                err["plugin"],
                err_type,
                err["error"][:80],
                suggestion,
            )

        console.print(err_table)
    else:
        console.print(f"\n[green]✓ Todos os {len(plugins)} plugins saudáveis — nenhum erro de discovery.[/green]")


@click.command()
@click.option('--type', '-t',
              type=click.Choice(['all', 'analyzer', 'filter', 'visualizer', 'document', 'composer']),
              default='all',
              help='Tipo de plugin para listar')
@click.option('--detailed', '-d', is_flag=True, help='Mostrar informações detalhadas')
@click.option('--check', '-c', is_flag=True, help='Diagnóstico de saúde dos plugins')
def list_plugins(type: str, detailed: bool, check: bool):
    """Lista plugins disponíveis"""
    core = get_core()

    if check:
        _run_check(core, type)
        return
    
    # Filtrar por tipo se necessário
    if type == 'all':
        plugins = core.registry.values()
    else:
        plugin_type = PluginType(type)
        plugins = [p for p in core.registry.values() if p.type == plugin_type]
    
    if not plugins:
        console.print(f"[yellow]Nenhum plugin do tipo '{type}' encontrado.[/yellow]")
        return
    
    # Criar tabela
    table = Table(title=f"Plugins Disponíveis ({len(plugins)} total)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Tipo", style="magenta")
    table.add_column("Nome", style="green")
    table.add_column("Versão", style="yellow")
    
    if detailed:
        table.add_column("Fornece", style="blue")
        table.add_column("Requer", style="red")
    
    # Adicionar plugins à tabela
    for plugin in plugins:
        row = [
            plugin.id,
            plugin.type.value,
            plugin.name,
            plugin.version
        ]
        
        if detailed:
            provides = ", ".join(plugin.provides) if plugin.provides else "-"
            requires = ", ".join(plugin.requires) if plugin.requires else "-"
            row.extend([provides, requires])
        
        table.add_row(*row)
    
    console.print(table)
    
    # Mostrar descrições se detalhado
    if detailed:
        console.print("\n[bold]Descrições:[/bold]")
        for plugin in plugins:
            console.print(f"\n[cyan]{plugin.id}:[/cyan] {plugin.description}")


@click.command(name='list-visualizers')
def list_visualizers():
    """Lista apenas plugins visualizadores disponíveis"""
    core = get_core()
    
    visualizers = [p for p in core.registry.values() if p.type == PluginType.VISUALIZER]
    
    if not visualizers:
        console.print("[yellow]Nenhum visualizador encontrado.[/yellow]")
        return
    
    table = Table(title=f"Visualizadores Disponíveis ({len(visualizers)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Nome", style="green")
    table.add_column("Aceita", style="blue")
    table.add_column("Formatos", style="magenta")
    
    for viz in visualizers:
        accepts = ", ".join(viz.requires) if viz.requires else "qualquer"
        formats = ", ".join(viz.provides) if viz.provides else "png"
        table.add_row(
            viz.id,
            viz.name,
            accepts,
            formats
        )
    
    console.print(table)
    console.print("\n[dim]Use 'qualia inspect <id>' para mais detalhes[/dim]")