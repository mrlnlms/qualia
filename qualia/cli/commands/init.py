# qualia/cli/commands/init.py
"""
Comando para inicializar estrutura do projeto Qualia
"""

import click
from pathlib import Path

from .utils import console


@click.command()
def init():
    """Inicializa estrutura do projeto Qualia"""
    console.print("[bold]Inicializando projeto Qualia...[/bold]\n")

    # Criar estrutura de pastas (apenas as essenciais pro engine)
    folders = [
        'plugins',
        'cache',
    ]

    for folder in folders:
        path = Path(folder)
        path.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓[/green] Criado: {folder}/")

    console.print("\n[bold green]Projeto inicializado com sucesso![/bold green]")
    console.print("\nPróximos passos:")
    console.print("  1. Crie plugins em plugins/")
    console.print("  2. Execute: qualia list")