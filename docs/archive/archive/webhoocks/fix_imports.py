#!/usr/bin/env python3
"""
Corrige os imports no __init__.py da API
"""

from pathlib import Path

print("🔧 Corrigindo imports da API...\n")

# 1. Verificar o que realmente existe em webhooks.py
print("1️⃣ Verificando funções disponíveis em webhooks.py:")
try:
    import qualia.api.webhooks as wb
    functions = [x for x in dir(wb) if not x.startswith('_') and callable(getattr(wb, x))]
    print(f"   Funções encontradas: {functions}")
    
    # Verificar se set_tracking_callback existe
    if 'set_tracking_callback' not in functions:
        print("   ❌ set_tracking_callback NÃO existe!")
        print("   ✅ init_webhooks existe!" if 'init_webhooks' in functions else "   ❌ init_webhooks não existe!")
except Exception as e:
    print(f"   Erro: {e}")

# 2. Corrigir o __init__.py
print("\n2️⃣ Corrigindo __init__.py...")

init_file = Path("qualia/api/__init__.py")
if init_file.exists():
    content = init_file.read_text()
    
    # Correção 1: Remover set_tracking_callback do import
    old_line = "from qualia.api.webhooks import router as webhook_router, init_webhooks, set_tracking_callback"
    new_line = "from qualia.api.webhooks import router as webhook_router, init_webhooks"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        print("   ✅ Removido set_tracking_callback do import")
    
    # Correção 2: Remover a chamada para set_tracking_callback
    old_call = "set_tracking_callback(track_webhook)"
    if old_call in content:
        content = content.replace(old_call, "# set_tracking_callback(track_webhook)  # Função não existe")
        print("   ✅ Comentada chamada para set_tracking_callback")
    
    # Salvar
    init_file.write_text(content)
    print("   ✅ Arquivo salvo!")
else:
    print("   ❌ __init__.py não encontrado!")

# 3. Limpar cache
print("\n3️⃣ Limpando cache...")
import shutil
import os

# Limpar todos os pycaches
for root, dirs, files in os.walk("qualia"):
    if "__pycache__" in dirs:
        pycache_path = Path(root) / "__pycache__"
        shutil.rmtree(pycache_path)
        print(f"   ✅ Removido: {pycache_path}")

print("\n✨ Correções aplicadas!")
print("\n🎯 Próximos passos:")
print("1. Reinicie a API (Ctrl+C e rode novamente)")
print("2. O warning deve desaparecer!")
print("3. Execute: python test_new_features.py")