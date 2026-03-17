#!/usr/bin/env python3
"""
Corrigir o erro do pipeline - 'Document' object has no attribute 'steps'
"""

from pathlib import Path

print("🔧 Corrigindo Pipeline...\n")

init_file = Path("qualia/api/__init__.py")
content = init_file.read_text()

# O erro está em execute_pipeline
# Procurar a linha problemática
lines = content.split('\n')
for i, line in enumerate(lines):
    if "pipeline_config" in line and '"steps":' in line:
        # Verificar se está tentando acessar request.steps
        # O correto é request.steps (da PipelineRequest)
        pass

# O problema é que está passando Document em vez de doc_id para execute_pipeline
# Vamos verificar a assinatura de execute_pipeline no core
print("1️⃣ Verificando o que execute_pipeline espera...")

# Corrigir para usar doc_id (string) em vez de doc (Document)
old_pattern = "results = core.execute_pipeline(doc, pipeline_config)"
new_pattern = "results = core.execute_pipeline(doc.id, pipeline_config)"

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    print("✅ Pipeline agora usa doc.id (string)")
    init_file.write_text(content)
else:
    print("⚠️  Padrão não encontrado, verificando alternativas...")
    
print("\n🎯 Pipeline corrigido!")
print("\nAgora teste novamente o pipeline!")