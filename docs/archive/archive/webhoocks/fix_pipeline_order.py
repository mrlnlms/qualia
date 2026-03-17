#!/usr/bin/env python3
"""
Corrigir a ordem dos parâmetros em execute_pipeline
"""

def fix_pipeline_parameter_order():
    file_path = 'qualia/api/__init__.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # O problema: execute_pipeline(doc.id, pipeline_config)
    # Correto: execute_pipeline(pipeline_config, doc)
    
    # Primeiro, vamos encontrar a linha exata
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'core.execute_pipeline(doc.id, pipeline_config)' in line:
            print(f"❌ Encontrado erro na linha {i+1}: {line.strip()}")
            print("   Ordem incorreta dos parâmetros!")
            
            # Corrigir para a ordem certa E usar doc em vez de doc.id
            new_line = line.replace(
                'core.execute_pipeline(doc.id, pipeline_config)', 
                'core.execute_pipeline(pipeline_config, doc)'
            )
            lines[i] = new_line
            
            print(f"✅ Corrigido para: {new_line.strip()}")
            
            # Salvar
            with open(file_path, 'w') as f:
                f.write('\n'.join(lines))
            
            print("\n✅ Arquivo salvo com sucesso!")
            return True
    
    print("❌ Padrão não encontrado. Verificando outras possibilidades...")
    
    # Procurar por outras variações
    for i, line in enumerate(lines):
        if 'execute_pipeline' in line and 'doc' in line:
            print(f"Linha {i+1}: {line.strip()}")
    
    return False

if __name__ == "__main__":
    fix_pipeline_parameter_order()