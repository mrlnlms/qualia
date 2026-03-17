#!/usr/bin/env python3
"""
Vamos adicionar prints para rastrear onde está o erro
"""

from pathlib import Path

webhooks = Path("qualia/api/webhooks.py")
content = webhooks.read_text()

# Adicionar prints para debug
new_analyze = '''    async def analyze_text(self, text: str, plugin_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run analysis on extracted text."""
        if not core:
            raise HTTPException(status_code=500, detail="Core not initialized")
        
        # Create document
        doc_id = f"{self.webhook_type.value}_{datetime.now().timestamp()}"
        doc = core.add_document(doc_id, text)
        print(f"DEBUG: doc type = {type(doc)}, doc = {doc}")
        print(f"DEBUG: doc_id = {doc_id}")
        
        # Execute plugin
        config = {}  # Could be customized based on webhook type
        try:
            # Tentar ambas as formas
            if hasattr(doc, 'id'):
                result = core.execute_plugin(plugin_id, doc_id, config, context)
            else:
                result = core.execute_plugin(plugin_id, doc, config, context)
        except Exception as e:
            print(f"DEBUG ERROR: {type(e).__name__}: {e}")
            raise'''

# Substituir a função inteira
import re
pattern = r'async def analyze_text\(self.*?\n        return result'
match = re.search(pattern, content, re.DOTALL)
if match:
    content = content[:match.start()] + new_analyze + '\n        return result' + content[match.end():]
    webhooks.write_text(content)
    print("✅ Debug adicionado ao webhook")
else:
    print("❌ Não encontrou a função analyze_text")

print("\nAgora teste e veja o que aparece no terminal da API!")