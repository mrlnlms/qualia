#!/usr/bin/env python3
"""
Descobrir o tipo correto para PipelineConfig
"""

from qualia.core import QualiaCore
import inspect

def test_pipeline_types():
    print("🔍 INVESTIGANDO TIPOS DO PIPELINE\n")
    
    core = QualiaCore()
    
    # 1. Ver a assinatura de execute_pipeline
    print("1. Assinatura de execute_pipeline:")
    sig = inspect.signature(core.execute_pipeline)
    print(f"   {sig}")
    
    # 2. Ver anotações de tipo
    print("\n2. Anotações de tipo:")
    for param_name, param in sig.parameters.items():
        if param_name != 'self':
            print(f"   {param_name}: {param.annotation}")
    
    # 3. Procurar PipelineConfig no módulo
    print("\n3. Procurando PipelineConfig no módulo core:")
    import qualia.core
    
    # Listar todos os atributos do módulo
    for attr in dir(qualia.core):
        if 'Pipeline' in attr:
            print(f"   Encontrado: {attr}")
            obj = getattr(qualia.core, attr)
            print(f"   Tipo: {type(obj)}")
            if hasattr(obj, '__annotations__'):
                print(f"   Annotations: {obj.__annotations__}")
    
    # 4. Tentar importar diretamente
    print("\n4. Tentando imports diretos:")
    try:
        from qualia.core import PipelineConfig
        print("   ✅ PipelineConfig importado!")
        print(f"   Tipo: {type(PipelineConfig)}")
        
        # Se for TypedDict, mostrar os campos
        if hasattr(PipelineConfig, '__annotations__'):
            print(f"   Campos: {PipelineConfig.__annotations__}")
            
        # Se for classe, mostrar __init__
        if hasattr(PipelineConfig, '__init__'):
            init_sig = inspect.signature(PipelineConfig.__init__)
            print(f"   __init__: {init_sig}")
            
    except ImportError as e:
        print(f"   ❌ Não foi possível importar: {e}")
    
    # 5. Verificar se é apenas um tipo (TypeAlias)
    print("\n5. Verificando se é um TypeAlias:")
    with open('qualia/core/__init__.py', 'r') as f:
        content = f.read()
        
    # Procurar por PipelineConfig =
    for line in content.split('\n'):
        if 'PipelineConfig' in line and '=' in line and 'class' not in line:
            print(f"   Encontrado: {line.strip()}")

if __name__ == "__main__":
    test_pipeline_types()