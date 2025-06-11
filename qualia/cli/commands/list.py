# qualia/cli/commands/list.py
"""
Comandos para listar plugins disponíveis
"""

import click
from rich.table import Table

from qualia.core import PluginType
from .utils import get_core, console


@click.command()
@click.option('--type', '-t', 
              type=click.Choice(['all', 'analyzer', 'filter', 'visualizer', 'document', 'composer']),
              default='all',
              help='Tipo de plugin para listar')
@click.option('--detailed', '-d', is_flag=True, help='Mostrar informações detalhadas')
def list_plugins(type: str, detailed: bool):
    """Lista plugins disponíveis"""
    core = get_core()
    
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