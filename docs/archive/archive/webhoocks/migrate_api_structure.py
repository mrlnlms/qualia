#!/usr/bin/env python3
"""
Script para migrar a estrutura da API para organização mais limpa.

Este script:
1. Move run_api.py -> qualia/api/run.py
2. Move examples/api_examples.py -> qualia/api/examples/api_examples.py
3. Move examples/webhook_examples.py -> qualia/api/examples/webhook_examples.py
4. Atualiza imports nos arquivos
"""

import os
import shutil
from pathlib import Path

def migrate_api_structure():
    """Reorganiza arquivos da API."""
    
    print("🔄 Migrando estrutura da API...")
    
    # Paths
    root = Path.cwd()
    api_dir = root / "qualia" / "api"
    api_examples_dir = api_dir / "examples"
    
    # Criar diretório examples dentro de api
    api_examples_dir.mkdir(exist_ok=True)
    print(f"✅ Criado diretório: {api_examples_dir}")
    
    # 1. Mover run_api.py
    old_run = root / "run_api.py"
    new_run = api_dir / "run.py"
    
    if old_run.exists():
        # Ler conteúdo e atualizar imports
        content = old_run.read_text()
        # Atualizar import se necessário
        content = content.replace('from qualia.api import app', 'from qualia.api import app')
        
        # Escrever novo arquivo
        new_run.write_text(content)
        print(f"✅ Movido: {old_run} -> {new_run}")
        
        # Remover antigo
        old_run.unlink()
    else:
        print(f"⚠️  Arquivo não encontrado: {old_run}")
    
    # 2. Mover api_examples.py
    old_api_ex = root / "examples" / "api_examples.py"
    new_api_ex = api_examples_dir / "api_examples.py"
    
    if old_api_ex.exists():
        shutil.copy2(old_api_ex, new_api_ex)
        print(f"✅ Movido: {old_api_ex} -> {new_api_ex}")
        old_api_ex.unlink()
    else:
        print(f"⚠️  Arquivo não encontrado: {old_api_ex}")
    
    # 3. Mover webhook_examples.py
    old_webhook_ex = root / "examples" / "webhook_examples.py"
    new_webhook_ex = api_examples_dir / "webhook_examples.py"
    
    if old_webhook_ex.exists():
        shutil.copy2(old_webhook_ex, new_webhook_ex)
        print(f"✅ Movido: {old_webhook_ex} -> {new_webhook_ex}")
        old_webhook_ex.unlink()
    else:
        print(f"⚠️  Arquivo não encontrado: {old_webhook_ex}")
    
    # 4. Criar __init__.py no diretório examples
    init_file = api_examples_dir / "__init__.py"
    init_file.write_text('"""Exemplos de uso da API Qualia Core."""\n')
    print(f"✅ Criado: {init_file}")
    
    # 5. Remover diretório examples se vazio
    old_examples = root / "examples"
    if old_examples.exists() and not any(old_examples.iterdir()):
        old_examples.rmdir()
        print(f"✅ Removido diretório vazio: {old_examples}")
    
    print("\n📁 Nova estrutura:")
    print("qualia/api/")
    print("├── __init__.py")
    print("├── webhooks.py")
    print("├── monitor.py")
    print("├── run.py")
    print("└── examples/")
    print("    ├── __init__.py")
    print("    ├── api_examples.py")
    print("    └── webhook_examples.py")
    
    print("\n✨ Migração concluída!")
    print("\n📝 Novas formas de executar:")
    print("  python -m qualia.api.run")
    print("  python -m qualia.api.run --reload")
    print("  python -m qualia.api.run --port 8080 --workers 4")

if __name__ == "__main__":
    migrate_api_structure()