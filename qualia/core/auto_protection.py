"""
Proteção automática SIMPLES - Funciona em qualquer core existente
"""

def add_simple_protection(core):
    """Adiciona proteção simples sem quebrar nada"""
    
    # Salvar método original
    original_execute = core.execute_plugin
    
    def protected_execute(plugin_id, document, config=None, context=None):
        """Wrapper com proteção básica"""
        try:
            # Executar método original
            return original_execute(plugin_id, document, config, context)
        except Exception as e:
            print(f"⚠️ Plugin '{plugin_id}' falhou: {e}")
            # Log do erro sem quebrar sistema
            return {"error": str(e), "plugin_id": plugin_id}
    
    # Substituir método
    core.execute_plugin = protected_execute
    return core