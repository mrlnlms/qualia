# qualia/__main__.py
"""
Entry point para execução direta do módulo qualia

Permite executar:
    python -m qualia
    
Em vez de precisar chamar:
    python -m qualia.cli
"""

# Como cli.py está no mesmo diretório, importamos assim:
from .cli import cli

if __name__ == '__main__':
    cli()