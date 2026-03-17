#!/usr/bin/env python3
"""
Encontrar como criar PipelineConfig corretamente
"""

import subprocess

def find_pipeline_config():
    print("🔍 PROCURANDO PipelineConfig NO CORE\n")
    
    # 1. Procurar definição de PipelineConfig
    print("1. Definição de PipelineConfig:")
    result = subprocess.run(
        ['grep', '-B2', '-A10', 'class PipelineConfig', 'qualia/core/__init__.py'],
        capture_output=True, text=True
    )
    if result.stdout:
        print(result.stdout)
    else:
        # Tentar outro padrão
        result = subprocess.run(
            ['grep', '-B2', '-A5', 'PipelineConfig', 'qualia/core/__init__.py'],
            capture_output=True, text=True
        )
        print(result.stdout)
    
    # 2. Ver se é um TypedDict ou dataclass
    print("\n2. Procurando imports relacionados:")
    result = subprocess.run(
        ['grep', '-E', 'from typing|from dataclasses|TypedDict|@dataclass', 'qualia/core/__init__.py'],
        capture_output=True, text=True
    )
    print(result.stdout)
    
    # 3. Ver como criar PipelineConfig
    print("\n3. Procurando exemplos de uso:")
    result = subprocess.run(
        ['grep', '-B2', '-A2', 'PipelineConfig(', 'qualia/core/__init__.py'],
        capture_output=True, text=True
    )
    if result.stdout:
        print(result.stdout)
    else:
        print("   Não encontrado PipelineConfig(")

if __name__ == "__main__":
    find_pipeline_config()