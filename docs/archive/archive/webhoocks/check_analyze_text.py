#!/usr/bin/env python3
"""
Verificar e restaurar analyze_text se necessário
"""

from pathlib import Path

webhooks = Path("qualia/api/webhooks.py")
content = webhooks.read_text()

# Verificar se analyze_text existe
if "def analyze_text" not in content:
    print("❌ Método analyze_text não encontrado! Vamos adicionar...")
    
    # Encontrar onde adicionar (depois de determine_plugin)
    insert_pos = content.find("async def determine_plugin")
    if insert_pos > 0:
        # Encontrar o fim do método determine_plugin
        # Procurar pelo próximo "async def" ou "class"
        next_method = content.find("\n    async def", insert_pos + 1)
        if next_method == -1:
            next_method = content.find("\nclass", insert_pos + 1)
        
        if next_method > 0:
            # Adicionar analyze_text antes do próximo método
            analyze_text_code = '''
    async def analyze_text(self, text: str, plugin_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run analysis on extracted text."""
        if not core:
            raise HTTPException(status_code=500, detail="Core not initialized")
        
        # Create document
        doc_id = f"{self.webhook_type.value}_{datetime.now().timestamp()}"
        doc = core.add_document(doc_id, text)
        
        # Execute plugin
        config = {}  # Could be customized based on webhook type
        result = core.execute_plugin(plugin_id, doc_id, config, context)
        
        return result
'''
            content = content[:next_method] + analyze_text_code + content[next_method:]
            print("✅ Método analyze_text adicionado!")
else:
    print("✅ Método analyze_text encontrado!")
    
    # Verificar se está correto
    # Extrair o método
    start = content.find("async def analyze_text")
    end = content.find("\n    async def", start + 1)
    if end == -1:
        end = content.find("\nclass", start + 1)
    
    if start > 0 and end > 0:
        method_content = content[start:end]
        print("\n📝 Conteúdo atual do analyze_text:")
        print(method_content[:200] + "...")
        
        # Verificar se tem o execute_plugin correto
        if "core.execute_plugin(plugin_id, doc_id" in method_content:
            print("\n✅ execute_plugin está usando doc_id corretamente!")
        else:
            print("\n❌ execute_plugin precisa ser corrigido")

# Salvar se fizemos mudanças
webhooks.write_text(content)

print("\n🔍 Verificando se a classe base tem analyze_text...")
if "class WebhookProcessor:" in content:
    # Encontrar a classe base
    base_start = content.find("class WebhookProcessor:")
    base_end = content.find("\nclass", base_start + 1)
    base_content = content[base_start:base_end] if base_end > 0 else content[base_start:]
    
    if "async def analyze_text" in base_content:
        print("✅ analyze_text está na classe base WebhookProcessor")
    else:
        print("❌ analyze_text NÃO está na classe base")