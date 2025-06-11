# qualia/cli/commands/__init__.py
"""
Grupo principal de comandos CLI do Qualia
"""

import click
from .list import list_plugins, list_visualizers
from .inspect import inspect
from .analyze import analyze
from .process import process
from .visualize import visualize
from .pipeline import pipeline
from .init import init
from .watch import watch
from .batch import batch
from .export import export
from .config import config
from ..interactive import start_menu


@click.group()
@click.version_option(version="0.1.0", prog_name="Qualia Core")
def cli():
    """
    🔬 Qualia Core - Framework bare metal para análise qualitativa
    
    Transforma dados qualitativos em insights quantificados através de plugins.
    """
    pass


# Registrar comandos básicos
cli.add_command(list_plugins, name='list')
cli.add_command(list_visualizers)
cli.add_command(inspect)
cli.add_command(analyze)
cli.add_command(process)
cli.add_command(visualize)
cli.add_command(pipeline)
cli.add_command(init)

# Registrar novos comandos
cli.add_command(watch)
cli.add_command(batch)
cli.add_command(export)
cli.add_command(config)  # Este é um grupo com subcomandos (create, validate, list)


@cli.command()
def menu():
    """Abre menu interativo para facilitar o uso do Qualia"""
    try:
        start_menu()
    except KeyboardInterrupt:
        from ..formatters import console
        console.print("\n[yellow]Menu interrompido pelo usuário[/yellow]")
    except Exception as e:
        from ..formatters import console, format_error
        console.print(format_error(e))
        raise


# Entry point
if __name__ == '__main__':
    cli()