# debug_context.py
"""
Debug do erro de context
"""

print("🔍 Debugando erro de context...\n")

# Vamos criar um teste direto
print("1. Testando teams_cleaner diretamente:")

try:
    from plugins.teams_cleaner import TeamsTranscriptCleaner
    from qualia.core import Document
    
    cleaner = TeamsTranscriptCleaner()
    doc = Document(id="test", content="[00:00:00] Test: Hello")
    
    # Testar com context vazio
    result = cleaner.process(doc, {}, {})
    print("✅ Plugin funciona quando chamado diretamente!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Verificando o execute_plugin...")
print("\nO erro 'cannot access local variable context' sugere que:")
print("- context está sendo usado antes de ser definido")
print("- ou há um problema de escopo")

print("\n📝 Correção sugerida para core/__init__.py:")
print("""
No método execute_plugin, certifique-se de que está assim:

def execute_plugin(self, plugin_id: str, document: Document, 
                  config: Dict[str, Any] = None,
                  context: Dict[str, Any] = None) -> Dict[str, Any]:
    # IMPORTANTE: Definir defaults no INÍCIO do método
    config = config or {}
    context = context or {}
    
    # ... resto do código ...
    
    # E quando chamar o plugin:
    if metadata.type == PluginType.DOCUMENT:
        result = plugin.process(document, config, context)
""")

print("\n3. Teste alternativo - usar Python diretamente:")
print("""
python -c "
from qualia.core import QualiaCore, Document
core = QualiaCore()
core.discover_plugins()
doc = core.add_document('test', open('transcript_example.txt').read())
result = core.execute_plugin('teams_cleaner', doc, {}, {})
print('Funcionou!', len(result.get('cleaned_document', '')), 'chars')
"
""")