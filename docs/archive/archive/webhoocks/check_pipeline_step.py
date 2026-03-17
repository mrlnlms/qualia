#!/usr/bin/env python3
"""
Verificar a estrutura REAL do PipelineStep antes de mudar
"""

from qualia.core import PipelineStep
import inspect

def check_pipeline_step():
    print("🔍 ANÁLISE COMPLETA DO PipelineStep\n")
    
    # 1. Ver os campos reais
    print("1. Campos do PipelineStep:")
    print(f"   Annotations: {PipelineStep.__annotations__}")
    
    # 2. Ver o __init__
    print("\n2. Assinatura do __init__:")
    sig = inspect.signature(PipelineStep.__init__)
    print(f"   {sig}")
    
    # 3. Tentar criar um PipelineStep com diferentes combinações
    print("\n3. Testando criação:")
    
    # Teste A: Só os campos básicos
    try:
        step1 = PipelineStep(plugin_id="test", config={})
        print("   ✅ Criado com (plugin_id, config)")
    except Exception as e:
        print(f"   ❌ Erro com campos básicos: {e}")
    
    # Teste B: Com output_name
    try:
        step2 = PipelineStep(plugin_id="test", config={}, output_name="result")
        print("   ✅ Criado com (plugin_id, config, output_name)")
    except Exception as e:
        print(f"   ❌ Erro com output_name: {e}")
    
    # 4. Ver se tem defaults
    print("\n4. Verificando valores padrão:")
    if hasattr(PipelineStep, '__dataclass_fields__'):
        for field_name, field_info in PipelineStep.__dataclass_fields__.items():
            print(f"   {field_name}:")
            print(f"     - tipo: {field_info.type}")
            print(f"     - tem default: {field_info.default != field_info.default_factory}")
    
    # 5. Ver no arquivo fonte
    print("\n5. Buscando definição no arquivo:")
    import subprocess
    result = subprocess.run(
        ['grep', '-A5', 'class PipelineStep', 'qualia/core/__init__.py'],
        capture_output=True, text=True
    )
    print(result.stdout)

if __name__ == "__main__":
    check_pipeline_step()