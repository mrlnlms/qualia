#!/usr/bin/env python3
"""
Script para corrigir o bug do pipeline na API do Qualia Core
"""

def fix_pipeline_bug():
    file_path = 'qualia/api/__init__.py'
    
    # Ler o arquivo
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Procurar e corrigir a linha
    fixed = False
    for i, line in enumerate(lines):
        if 'results = core.execute_pipeline(doc, pipeline_config)' in line:
            lines[i] = line.replace('execute_pipeline(doc,', 'execute_pipeline(doc.id,')
            print(f"✅ Bug corrigido na linha {i+1}")
            print(f"   De:   {line.strip()}")
            print(f"   Para: {lines[i].strip()}")
            fixed = True
            break
    
    if fixed:
        # Salvar o arquivo corrigido
        with open(file_path, 'w') as f:
            f.writelines(lines)
        print("\n✅ Arquivo salvo com sucesso!")
    else:
        print("❌ Bug não encontrado. Verificando se já foi corrigido...")
        
        # Verificar se já está corrigido
        for i, line in enumerate(lines):
            if 'execute_pipeline(doc.id,' in line:
                print(f"✅ O bug já foi corrigido! Linha {i+1}: {line.strip()}")
                return
            elif 'execute_pipeline' in line:
                print(f"Linha {i+1}: {line.strip()}")

if __name__ == "__main__":
    fix_pipeline_bug()