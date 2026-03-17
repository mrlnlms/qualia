#!/usr/bin/env python3
"""
Correção manual direta do problema
"""

from pathlib import Path
import re

print("🔧 Aplicando correção manual...\n")

# 1. Corrigir webhooks.py
webhooks_file = Path("qualia/api/webhooks.py")
print("1️⃣ Corrigindo webhooks.py...")

if webhooks_file.exists():
    content = webhooks_file.read_text()
    
    # Procurar a função analyze_text
    # O problema está aqui: core.add_document retorna Document, mas execute_plugin quer string
    
    # Substituição 1: Na função analyze_text
    old_code = """        # Create document
        doc_id = f"{self.webhook_type.value}_{datetime.now().timestamp()}"
        core.add_document(doc_id, text)
        
        # Execute plugin
        config = {}  # Could be customized based on webhook type
        result = core.execute_plugin(plugin_id, doc_id, config, context)"""
    
    new_code = """        # Create document
        doc_id = f"{self.webhook_type.value}_{datetime.now().timestamp()}"
        doc = core.add_document(doc_id, text)
        
        # Execute plugin (usando doc_id string, não o objeto)
        config = {}  # Could be customized based on webhook type
        result = core.execute_plugin(plugin_id, doc_id, config, context)"""
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("   ✅ Corrigido analyze_text")
    else:
        print("   ⚠️  Padrão não encontrado, tentando correção alternativa...")
        
        # Tentar encontrar e corrigir de outra forma
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "core.add_document(doc_id, text)" in line and "=" not in line:
                lines[i] = "        doc = core.add_document(doc_id, text)"
                print(f"   ✅ Corrigida linha {i+1}")
                break
        content = '\n'.join(lines)
    
    webhooks_file.write_text(content)

# 2. Corrigir pipeline no __init__.py
init_file = Path("qualia/api/__init__.py")
print("\n2️⃣ Corrigindo pipeline no __init__.py...")

if init_file.exists():
    content = init_file.read_text()
    
    # Procurar a função execute_pipeline
    # Mudar de passar 'doc' para 'doc.id'
    
    # Padrão antigo
    old_pattern = r'results = core\.execute_pipeline\(doc, pipeline_config\)'
    # Padrão novo
    new_pattern = 'results = core.execute_pipeline(doc.id, pipeline_config)'
    
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_pattern, content)
        print("   ✅ Corrigido execute_pipeline")
    else:
        print("   ⚠️  Tentando correção alternativa...")
        
        # Verificar se doc.id já está lá
        if "core.execute_pipeline(doc.id" in content:
            print("   ✅ Já está correto!")
        else:
            # Tentar corrigir linha por linha
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "core.execute_pipeline(doc," in line:
                    lines[i] = line.replace("execute_pipeline(doc,", "execute_pipeline(doc.id,")
                    print(f"   ✅ Corrigida linha {i+1}")
                    break
            content = '\n'.join(lines)
    
    init_file.write_text(content)

# 3. Limpar todo o cache
print("\n3️⃣ Limpando cache...")
import shutil
for pycache in Path(".").rglob("__pycache__"):
    if "venv" not in str(pycache):
        shutil.rmtree(pycache)
        print(f"   ✅ Removido: {pycache}")

print("\n✨ Correções manuais aplicadas!")
print("\n⚠️  A API deve recarregar automaticamente.")
print("Aguarde 5 segundos e teste novamente.")