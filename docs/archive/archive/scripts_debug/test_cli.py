#!/usr/bin/env python
import sys
import os

# Adicionar o diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from qualia.cli import cli
    print("✓ CLI importada com sucesso!")
    cli()
except ImportError as e:
    print(f"✗ Erro ao importar CLI: {e}")
    print("\nInstalando dependências...")
    os.system("pip install rich click pyyaml")
    print("\nTente novamente!")
