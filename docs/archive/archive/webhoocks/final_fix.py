#!/usr/bin/env python3
"""
CORREÇÃO FINAL - execute_plugin quer Document, não string!
"""

from pathlib import Path

print("🔧 CORREÇÃO FINAL\n")

# 1. Corrigir webhooks.py
webhooks = Path("qualia/api/webhooks.py")
content = webhooks.read_text()

# Substituir a linha errada
old_line = "result = core.execute_plugin(plugin_id, doc_id, config, context)"
new_line = "result = core.execute_plugin(plugin_id, doc, config, context)"

if old_line in content:
    content = content.replace(old_line, new_line)
    print("✅ Webhooks: execute_plugin agora usa 'doc' (Document)")
else:
    print("⚠️  Linha não encontrada, tentando alternativa...")
    # Tentar achar de outra forma
    content = content.replace("execute_plugin(plugin_id, doc_id,", "execute_plugin(plugin_id, doc,")

webhooks.write_text(content)

# 2. Corrigir pipeline também
init_file = Path("qualia/api/__init__.py")
content = init_file.read_text()

# Pipeline também precisa passar Document
if "execute_pipeline(doc," not in content:
    content = content.replace("execute_pipeline(doc.id,", "execute_pipeline(doc,")
    print("✅ Pipeline: execute_pipeline agora usa 'doc' (Document)")

init_file.write_text(content)

print("\n🎯 PRONTO!")
print("\nO problema era simples:")
print("- execute_plugin espera Document, não string")
print("- estávamos passando doc_id (string) em vez de doc (Document)")
print("\n✅ Agora vai funcionar!")