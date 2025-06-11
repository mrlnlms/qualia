# qualia/cli/commands/inspect.py
"""
Comando para inspecionar detalhes de plugins
"""

import click
from rich.panel import Panel
from rich.table import Table

from .utils import get_core, console


@click.command()
@click.argument('plugin_id')
def inspect(plugin_id: str):
    """Inspeciona detalhes de um plugin"""
    core = get_core()
    
    if plugin_id not in core.registry:
        console.print(f"[red]Plugin '{plugin_id}' não encontrado![/red]")
        return
    
    meta = core.registry[plugin_id]
    
    # Painel principal
    console.print(Panel(
        f"[bold cyan]{meta.name}[/bold cyan]\n"
        f"[yellow]v{meta.version}[/yellow]\n\n"
        f"{meta.description}",
        title=f"Plugin: {plugin_id}",
        border_style="blue"
    ))
    
    # Informações técnicas
    console.print("\n[bold]Informações Técnicas:[/bold]")
    console.print(f"  Tipo: [magenta]{meta.type.value}[/magenta]")
    console.print(f"  ID: [cyan]{meta.id}[/cyan]")
    
    # O que fornece
    if meta.provides:
        console.print("\n[bold]Fornece:[/bold]")
        for item in meta.provides:
            console.print(f"  • [green]{item}[/green]")
    
    # Dependências
    if meta.requires:
        console.print("\n[bold]Requer:[/bold]")
        for item in meta.requires:
            console.print(f"  • [red]{item}[/red]")
    
    # Pode usar
    if meta.can_use:
        console.print("\n[bold]Pode usar (opcional):[/bold]")
        for item in meta.can_use:
            console.print(f"  • [yellow]{item}[/yellow]")
    
    # Parâmetros
    if meta.parameters:
        console.print("\n[bold]Parâmetros:[/bold]")
        param_table = Table(show_header=True, header_style="bold")
        param_table.add_column("Nome", style="cyan")
        param_table.add_column("Tipo", style="magenta")
        param_table.add_column("Default", style="green")
        param_table.add_column("Descrição")
        
        for param_name, param_info in meta.parameters.items():
            param_type = param_info.get('type', 'string')
            default = str(param_info.get('default', '-'))
            description = param_info.get('description', '')
            
            # Adicionar opções se for choice
            if param_type == 'choice' and 'options' in param_info:
                param_type = f"choice {param_info['options']}"
            
            param_table.add_row(
                param_name,
                param_type,
                default,
                description
            )
        
        console.print(param_table)