#!/usr/bin/env python3
"""
Entry point para execução direta do módulo qualia

Permite executar:
    python -m qualia
    
Em vez de precisar chamar:
    python -m qualia.cli
"""

# Com a nova estrutura, importamos do submódulo cli
from .cli import cli

if __name__ == '__main__':
    cli()