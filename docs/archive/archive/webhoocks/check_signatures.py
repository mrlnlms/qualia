#!/usr/bin/env python3
"""
Verificar as assinaturas exatas no core
"""

import subprocess
import re

def check_core_signatures():
    print("🔍 VERIFICANDO ASSINATURAS DO CORE\n")
    
    # 1. Verificar execute_pipeline
    print("1. Assinatura de execute_pipeline:")
    result = subprocess.run(
        ['grep', '-A', '5', 'def execute_pipeline', 'qualia/core/__init__.py'],
        capture_output=True, text=True
    )
    print(result.stdout)
    
    # 2. Verificar como está sendo chamado na API
    print("\n2. Como está sendo chamado na API:")
    result = subprocess.run(
        ['grep', '-n', 'core.execute_pipeline', 'qualia/api/__init__.py'],
        capture_output=True, text=True
    )
    print(result.stdout)
    
    # 3. Verificar a estrutura de PipelineConfig
    print("\n3. Verificando se tem que converter pipeline_config:")
    with open('qualia/core/__init__.py', 'r') as f:
        content = f.read()
        
    # Procurar por PipelineConfig ou algo similar
    if 'from typing' in content:
        print("   Core usa typing...")
        
    # Ver se execute_pipeline espera dict ou alguma classe especial
    lines = content.split('\n')
    in_execute_pipeline = False
    for line in lines:
        if 'def execute_pipeline' in line:
            in_execute_pipeline = True
        elif in_execute_pipeline and ('def ' in line or 'class ' in line):
            break
        elif in_execute_pipeline:
            if 'pipeline' in line.lower() or 'config' in line.lower():
                print(f"   {line.strip()}")

if __name__ == "__main__":
    check_core_signatures()