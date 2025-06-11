from qualia.core import QualiaCore
from pathlib import Path

# Teste 1: Core vazio
print("=== TESTE 1: Core Vazio ===")
core = QualiaCore()
print(f"Plugins iniciais: {len(core.plugins)}")
print(f"Registry inicial: {len(core.registry)}")

# Teste 2: Descobrir plugins
print("\n=== TESTE 2: Descoberta de Plugins ===")
discovered = core.discover_plugins()
print(f"Plugins descobertos: {len(discovered)}")
for plugin_id, meta in discovered.items():
    print(f"  - {plugin_id}: {meta.type.value}")

# Teste 3: Criar documento
print("\n=== TESTE 3: Documento de Teste ===")
doc = core.add_document(
    "test_001",
    "Este é um texto de teste. Texto texto texto. Palavra repetida repetida repetida."
)
print(f"Documento criado: {doc.id}")

# Teste 4: Executar análise
if "word_frequency" in core.plugins:
    print("\n=== TESTE 4: Análise de Frequência ===")
    result = core.execute_plugin("word_frequency", doc, {"min_word_length": 4})
    print(f"Vocabulário: {result.get('vocabulary_size')} palavras")
    print(f"Top palavras: {result.get('top_words', [])[:5]}")
