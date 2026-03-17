#!/usr/bin/env python3
"""
Teste DIRETO pra descobrir que porra tá acontecendo
"""

from qualia.core import QualiaCore

print("🔍 TESTE DIRETO DO CORE\n")

# Criar core
core = QualiaCore()
core.discover_plugins()

# Testar add_document
print("1️⃣ Testando add_document:")
doc = core.add_document("test123", "Texto de teste")
print(f"   Tipo retornado: {type(doc)}")
print(f"   doc = {doc}")
print(f"   doc.id = {doc.id if hasattr(doc, 'id') else 'NÃO TEM ID'}")

# Testar execute_plugin
print("\n2️⃣ Testando execute_plugin:")

# Tentar com doc_id string
try:
    result = core.execute_plugin("word_frequency", "test123", {}, {})
    print("   ✅ Funcionou com string 'test123'")
except Exception as e:
    print(f"   ❌ Erro com string: {e}")

# Tentar com doc object
try:
    result = core.execute_plugin("word_frequency", doc, {}, {})
    print("   ✅ Funcionou com objeto doc")
except Exception as e:
    print(f"   ❌ Erro com objeto: {e}")

# Tentar com doc.id
try:
    result = core.execute_plugin("word_frequency", doc.id, {}, {})
    print("   ✅ Funcionou com doc.id")
except Exception as e:
    print(f"   ❌ Erro com doc.id: {e}")

print("\n💡 CONCLUSÃO:")
print("execute_plugin espera: ???")