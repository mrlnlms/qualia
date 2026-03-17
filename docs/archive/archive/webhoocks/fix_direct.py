#!/usr/bin/env python3
"""
Correção DIRETA - sem complicação
"""

from pathlib import Path

# WEBHOOK - usar doc_id direto, sem .id
webhooks = Path("qualia/api/webhooks.py")
content = webhooks.read_text()
content = content.replace(
    "result = core.execute_plugin(plugin_id, doc_id, config, context)",
    "result = core.execute_plugin(plugin_id, doc.id if hasattr(doc, 'id') else doc, config, context)"
)
webhooks.write_text(content)
print("✅ Webhook corrigido")

# PIPELINE - usar doc direto, sem .id
init = Path("qualia/api/__init__.py")
content = init.read_text()
content = content.replace(
    "results = core.execute_pipeline(doc.id, pipeline_config)",
    "results = core.execute_pipeline(doc, pipeline_config)"
)
init.write_text(content)
print("✅ Pipeline corrigido")

print("\n🚀 Pronto! Teste agora.")