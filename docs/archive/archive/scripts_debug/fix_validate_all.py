# fix_validate_all.py
"""
Corrige validate_config para retornar tupla em todos os lugares
"""

import re

print("🔧 Corrigindo validate_config em todos os arquivos...\n")

# 1. Primeiro, vamos procurar validate_config de forma mais ampla
files_to_check = [
    'qualia/core/__init__.py',
    'plugins/word_frequency/__init__.py',
    'plugins/teams_cleaner/__init__.py',
    'plugins/wordcloud_viz/__init__.py',
    'plugins/frequency_chart/__init__.py'
]

for file_path in files_to_check:
    print(f"\n📄 Verificando {file_path}:")
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Procurar por validate_config e seus returns
        lines = content.split('\n')
        found_validate = False
        changes_made = False
        
        for i, line in enumerate(lines):
            # Detectar início do método
            if 'validate_config' in line and ('def' in line or 'def' in lines[i-1] if i > 0 else False):
                found_validate = True
                print(f"   Encontrado validate_config na linha {i+1}")
                
            # Se estamos dentro do validate_config
            if found_validate:
                # Procurar por return
                if 'return' in line:
                    stripped = line.strip()
                    print(f"   Linha {i+1}: {stripped}")
                    
                    # Se retorna apenas True ou False
                    if stripped == 'return True' or stripped == 'return False':
                        # Corrigir para retornar tupla
                        indent = len(line) - len(line.lstrip())
                        new_line = ' ' * indent + 'return True, None'
                        lines[i] = new_line
                        print(f"   ✅ Corrigido para: {new_line.strip()}")
                        changes_made = True
                        found_validate = False  # Reset após encontrar return
                    elif 'return True, None' in stripped:
                        print(f"   ✅ Já está correto")
                        found_validate = False
                    
                # Detectar fim do método (nova definição ou dedent)
                if i > 0 and line and not line[0].isspace() and 'def' in line:
                    found_validate = False
        
        # Salvar se houve mudanças
        if changes_made:
            with open(file_path, 'w') as f:
                f.write('\n'.join(lines))
            print(f"   💾 Arquivo salvo com correções")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

# 2. Verificar especificamente as BaseClasses
print("\n\n🔍 Verificando BaseClasses especificamente:")
try:
    with open('qualia/core/__init__.py', 'r') as f:
        content = f.read()
    
    # Usar regex para encontrar validate_config nas base classes
    pattern = r'class Base(Analyzer|Visualizer|Document)Plugin.*?(?=class|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        if 'validate_config' in match:
            print(f"\n   Encontrado em Base{match[0]}Plugin")
            # Extrair o método validate_config
            validate_pattern = r'def validate_config.*?(?=\n    def|\n\n|\Z)'
            validate_match = re.search(validate_pattern, match, re.DOTALL)
            if validate_match:
                method = validate_match.group()
                print("   Método atual:")
                for line in method.split('\n')[:5]:  # Primeiras 5 linhas
                    print(f"     {line}")

except Exception as e:
    print(f"   ❌ Erro: {e}")

print("\n\n✅ Processo concluído!")
print("\nTeste novamente:")
print("  qualia analyze test_doc.txt -p word_frequency -o test_analysis.json")