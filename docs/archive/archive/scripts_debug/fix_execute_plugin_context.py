# fix_execute_plugin_context.py
"""
Atualiza execute_plugin para passar context corretamente
"""

print("🔧 Corrigindo execute_plugin para suportar context...\n")

# Procurar onde execute_plugin chama os plugins
search_text = """
Em core/__init__.py, procure o método execute_plugin e encontre onde ele chama:

1. Para ANALYZER:
   result = plugin.analyze(document, config)
   Mude para:
   result = plugin.analyze(document, config, context)

2. Para DOCUMENT:
   result = plugin.process(document, config)
   Mude para:
   result = plugin.process(document, config, context)

3. No início do método, adicione context como parâmetro:
   def execute_plugin(self, plugin_id: str, document: Document, 
                     config: Dict[str, Any] = None) -> Dict[str, Any]:
   
   Mude para:
   def execute_plugin(self, plugin_id: str, document: Document, 
                     config: Dict[str, Any] = None,
                     context: Dict[str, Any] = None) -> Dict[str, Any]:
       config = config or {}
       context = context or {}

Isso garantirá que context seja passado corretamente para todos os plugins.
"""

print(search_text)

print("\n📝 Correção completa:\n")

print("1. Em cli.py, mantenha:")
print("   result = core.execute_plugin(plugin, doc, params, {})")
print("")
print("2. Em core/__init__.py, atualize execute_plugin para aceitar e passar context")
print("")
print("3. Teste novamente:")
print("   qualia process transcript_example.txt -p teams_cleaner --save-as cleaned.txt")