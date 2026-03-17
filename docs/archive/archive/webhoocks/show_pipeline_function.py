#!/usr/bin/env python3
"""
Mostrar a função execute_pipeline completa da API
"""

def show_pipeline_function():
    with open('qualia/api/__init__.py', 'r') as f:
        lines = f.readlines()
    
    # Encontrar a função execute_pipeline
    start = None
    end = None
    indent_level = None
    
    for i, line in enumerate(lines):
        if 'async def execute_pipeline' in line:
            start = i
            # Detectar nível de indentação
            indent_level = len(line) - len(line.lstrip())
        elif start is not None and line.strip() and len(line) - len(line.lstrip()) <= indent_level:
            # Próxima função ou fim do bloco
            end = i
            break
    
    if start:
        print(f"📍 Função execute_pipeline (linhas {start+1} a {end or len(lines)}):\n")
        print("".join(lines[start:end or len(lines)]))
        
        # Destacar a linha problemática
        print("\n⚠️  LINHA PROBLEMÁTICA:")
        for i in range(start, end or len(lines)):
            if 'core.execute_pipeline' in lines[i]:
                print(f"   Linha {i+1}: {lines[i].strip()}")

if __name__ == "__main__":
    show_pipeline_function()