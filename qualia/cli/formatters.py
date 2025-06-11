"""
Formatadores Rich compartilhados entre CLI e menu interativo
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box
from typing import List, Dict, Any

console = Console()


def create_plugin_table(plugins: List[Dict[str, Any]], detailed: bool = False) -> Table:
    """Cria tabela formatada de plugins"""
    table = Table(
        title="Plugins Disponíveis",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    
    # Colunas básicas
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Tipo", style="green")
    table.add_column("Nome", style="white")
    table.add_column("Versão", style="dim")
    
    if detailed:
        table.add_column("Descrição", style="dim")
        table.add_column("Autor", style="dim")
    
    return table


def format_analysis_results(results: Dict[str, Any]) -> Panel:
    """Formata resultados de análise para exibição"""
    content = []
    
    for key, value in results.items():
        if isinstance(value, dict):
            content.append(f"[bold]{key}:[/bold]")
            for k, v in value.items():
                content.append(f"  • {k}: {v}")
        elif isinstance(value, list):
            content.append(f"[bold]{key}:[/bold] ({len(value)} items)")
        else:
            content.append(f"[bold]{key}:[/bold] {value}")
    
    return Panel(
        "\n".join(content),
        title="Resultados da Análise",
        border_style="green"
    )


def format_error(error: Exception) -> Panel:
    """Formata erro para exibição amigável"""
    return Panel(
        f"[red]{type(error).__name__}:[/red] {str(error)}",
        title="Erro",
        border_style="red",
        expand=False
    )


def format_success(message: str) -> str:
    """Formata mensagem de sucesso"""
    return f"[bold green]✓[/bold green] {message}"


def format_warning(message: str) -> str:
    """Formata mensagem de aviso"""
    return f"[bold yellow]⚠[/bold yellow] {message}"


def format_info(message: str) -> str:
    """Formata mensagem informativa"""
    return f"[bold blue]ℹ[/bold blue] {message}"


def show_banner() -> Panel:
    """Retorna o banner do Qualia"""
    return Panel.fit("""
[bold cyan]🔬 QUALIA CORE[/bold cyan]
[dim]Framework para Análise Qualitativa[/dim]

Transforme dados qualitativos em insights quantificados
    """, border_style="cyan")