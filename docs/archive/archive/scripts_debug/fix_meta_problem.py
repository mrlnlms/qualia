# fix_meta_problem.py
"""
O problema é que as base classes herdam de interfaces que têm meta() como @abstractmethod.
Precisamos garantir que as base classes não sejam instanciadas diretamente.
"""

print("=== DIAGNÓSTICO DO PROBLEMA ===\n")

# Verificar o problema
from abc import ABC, abstractmethod
import inspect

try:
    from qualia.core import IAnalyzerPlugin, BaseAnalyzerPlugin
    
    print("Métodos abstratos em IAnalyzerPlugin:")
    for name, method in inspect.getmembers(IAnalyzerPlugin):
        if getattr(method, '__isabstractmethod__', False):
            print(f"  - {name}")
    
    print("\nMétodos em BaseAnalyzerPlugin:")
    for name in ['meta', 'analyze', 'validate_config', '_analyze_impl']:
        if hasattr(BaseAnalyzerPlugin, name):
            method = getattr(BaseAnalyzerPlugin, name)
            is_abstract = getattr(method, '__isabstractmethod__', False)
            print(f"  - {name}: {'abstract' if is_abstract else 'concrete'}")
    
except Exception as e:
    print(f"Erro: {e}")

print("\n=== SOLUÇÃO ===")
print("""
O problema é que o PluginLoader está tentando instanciar as BaseClasses.
Precisamos fazer o PluginLoader ignorar classes que começam com 'Base'.

Em core/__init__.py, no método load_plugin da classe PluginLoader,
adicione esta verificação:

# Ignorar base classes
if class_name.startswith('Base'):
    continue

Ou melhor ainda, verificar se a classe é abstrata:

# Importar no topo
from abc import ABC

# No loop de classes:
if inspect.isabstract(plugin_class):
    continue
""")

# Vamos também corrigir o erro de indentação no word_frequency
print("\n=== CORRIGINDO WORD_FREQUENCY ===")

try:
    with open('plugins/word_frequency/__init__.py', 'r') as f:
        lines = f.readlines()
    
    # Procurar por problemas de indentação após validate_config
    for i, line in enumerate(lines):
        if 'def validate_config' in line:
            print(f"Linha {i+1}: {line.rstrip()}")
            # Ver as próximas linhas
            for j in range(1, 5):
                if i+j < len(lines):
                    print(f"Linha {i+j+1}: {lines[i+j].rstrip()}")
            break
            
except Exception as e:
    print(f"Erro ao ler arquivo: {e}")

print("\n=== CORREÇÃO MANUAL NECESSÁRIA ===")
print("""
1. Em plugins/word_frequency/__init__.py:
   - Verificar a indentação após o método validate_config
   - Garantir que o próximo método esteja alinhado corretamente

2. Em core/__init__.py, classe PluginLoader:
   - Adicionar verificação para ignorar classes abstratas ou Base*
   
Exemplo:
```python
# Em PluginLoader.load_plugin()
for item_name in dir(module):
    if item_name.startswith('Base'):  # Ignorar base classes
        continue
        
    item = getattr(module, item_name)
    if inspect.isclass(item) and issubclass(item, IPlugin):
        if inspect.isabstract(item):  # Ignorar classes abstratas
            continue
        # ... resto do código
```
""")