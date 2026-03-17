# final_fixes.py
"""
Correções finais para fazer tudo funcionar
"""

import fileinput
import sys

print("🔧 Aplicando correções finais...\n")

# 1. Corrigir click.Exit -> SystemExit em cli.py
print("1. Corrigindo cli.py (click.Exit -> SystemExit)...")
try:
    with open('qualia/cli.py', 'r') as f:
        content = f.read()
    
    # Substituir todas as ocorrências
    content = content.replace('raise click.Exit(1)', 'raise SystemExit(1)')
    content = content.replace('click.Exit(', 'SystemExit(')
    
    with open('qualia/cli.py', 'w') as f:
        f.write(content)
    
    print("   ✅ cli.py corrigido")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 2. Verificar se os plugins têm validate_config retornando tupla
print("\n2. Verificando validate_config nos plugins...")

plugins_to_check = [
    'plugins/word_frequency/__init__.py',
    'plugins/teams_cleaner/__init__.py',
    'plugins/wordcloud_viz/__init__.py', 
    'plugins/frequency_chart/__init__.py'
]

for plugin_file in plugins_to_check:
    try:
        with open(plugin_file, 'r') as f:
            content = f.read()
        
        # Se tem validate_config mas não retorna tupla
        if 'def validate_config' in content and 'return True, None' not in content:
            print(f"   ⚠️  {plugin_file} precisa retornar tupla")
            
            # Se retorna apenas True
            if 'return True\n' in content:
                content = content.replace('return True\n', 'return True, None\n')
                with open(plugin_file, 'w') as f:
                    f.write(content)
                print(f"   ✅ Corrigido!")
        else:
            print(f"   ✅ {plugin_file} OK")
            
    except Exception as e:
        print(f"   ❌ Erro em {plugin_file}: {e}")

# 3. Verificar se BaseClasses têm validate_config correto
print("\n3. Verificando BaseClasses em core/__init__.py...")
try:
    with open('qualia/core/__init__.py', 'r') as f:
        content = f.read()
    
    # Verificar se validate_config retorna tupla nas base classes
    lines = content.split('\n')
    in_validate_config = False
    found_issue = False
    
    for i, line in enumerate(lines):
        if 'def validate_config' in line and ('BaseAnalyzer' in content[max(0,i-200):i] or 
                                              'BaseVisualizer' in content[max(0,i-200):i] or
                                              'BaseDocument' in content[max(0,i-200):i]):
            in_validate_config = True
            
        if in_validate_config and 'return True' in line and 'return True, None' not in line:
            print(f"   ⚠️  Linha {i+1}: Base class retornando apenas True")
            found_issue = True
            
        if in_validate_config and ('def ' in line and 'validate_config' not in line):
            in_validate_config = False
    
    if not found_issue:
        print("   ✅ Base classes OK")
    else:
        print("   ⚠️  Corrija manualmente: validate_config deve retornar (True, None)")
        
except Exception as e:
    print(f"   ❌ Erro: {e}")

print("\n✨ Correções aplicadas!")
print("\nTeste novamente:")
print("  qualia analyze test_doc.txt -p word_frequency -o test_analysis.json")
print("  qualia visualize test_analysis.json -p wordcloud_viz -o cloud.png")