#!/usr/bin/env python3
"""
Adiciona a função set_tracking_callback que está faltando em webhooks.py
"""

from pathlib import Path

print("🔧 Adicionando função faltante...\n")

webhooks_file = Path("qualia/api/webhooks.py")

# Adicionar a função no final do arquivo
additional_code = '''

def set_tracking_callback(callback):
    """Set callback for tracking webhook metrics."""
    global track_webhook_callback
    track_webhook_callback = callback
'''

if webhooks_file.exists():
    content = webhooks_file.read_text()
    
    # Verificar se já existe
    if "def set_tracking_callback" not in content:
        # Adicionar antes do final do arquivo
        content = content.rstrip() + additional_code
        webhooks_file.write_text(content)
        print("✅ Função set_tracking_callback adicionada!")
    else:
        print("⚠️  Função já existe!")
else:
    print("❌ webhooks.py não encontrado!")

print("\nReinicie a API para testar!")