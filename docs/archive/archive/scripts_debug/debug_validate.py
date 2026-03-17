# debug_validate.py
"""
Debug para encontrar onde validate_config está retornando apenas bool
"""

print("🔍 Debugando validate_config...\n")

# 1. Testar diretamente o plugin
print("1. Testando WordFrequencyAnalyzer diretamente:")
try:
    from plugins.word_frequency import WordFrequencyAnalyzer
    from qualia.core import Document
    
    analyzer = WordFrequencyAnalyzer()
    result = analyzer.validate_config({})
    print(f"   validate_config retornou: {result}")
    print(f"   Tipo: {type(result)}")
    
    if isinstance(result, tuple):
        print("   ✅ Retorna tupla corretamente")
    else:
        print("   ❌ NÃO retorna tupla!")
        
except Exception as e:
    print(f"   ❌ Erro: {e}")
    import traceback
    traceback.print_exc()

# 2. Verificar a herança
print("\n2. Verificando herança:")
try:
    from plugins.word_frequency import WordFrequencyAnalyzer
    from qualia.core import BaseAnalyzerPlugin
    
    print(f"   WordFrequencyAnalyzer herda de: {WordFrequencyAnalyzer.__bases__}")
    print(f"   MRO: {[c.__name__ for c in WordFrequencyAnalyzer.__mro__]}")
    
    # Verificar qual validate_config está sendo usado
    print("\n   Métodos validate_config na hierarquia:")
    for cls in WordFrequencyAnalyzer.__mro__:
        if hasattr(cls, 'validate_config'):
            print(f"   - {cls.__name__}.validate_config")
            # Tentar ver o código
            import inspect
            try:
                source = inspect.getsource(cls.validate_config)
                # Pegar apenas a linha do return
                for line in source.split('\n'):
                    if 'return' in line:
                        print(f"     {line.strip()}")
                        break
            except:
                pass
                
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 3. Ver o que está em core/__init__.py
print("\n3. Verificando QualiaCore.execute_plugin:")
try:
    with open('qualia/core/__init__.py', 'r') as f:
        lines = f.readlines()
    
    # Procurar a linha que faz: valid, error = plugin.validate_config(config)
    for i, line in enumerate(lines):
        if 'valid, error = plugin.validate_config' in line:
            print(f"   Linha {i+1}: {line.strip()}")
            # Mostrar contexto
            print("   Contexto:")
            for j in range(max(0, i-3), min(len(lines), i+4)):
                print(f"   {j+1}: {lines[j].rstrip()}")
            break
            
except Exception as e:
    print(f"   ❌ Erro: {e}")

print("\n4. Solução sugerida:")
print("   O problema pode estar em:")
print("   a) O plugin tem um validate_config próprio que retorna bool")
print("   b) A BaseClass não está implementando corretamente")
print("   c) Há outro validate_config na hierarquia")
print("\n   Execute: grep -n 'def validate_config' plugins/word_frequency/__init__.py")