# check_execute_plugin.py
"""
Verifica a assinatura de execute_plugin e corrige
"""

import re

print("🔍 Verificando assinatura de execute_plugin...\n")

# 1. Ver a assinatura atual em core/__init__.py
try:
    with open('qualia/core/__init__.py', 'r') as f:
        content = f.read()
    
    # Procurar definição de execute_plugin
    pattern = r'def execute_plugin\([^)]+\):'
    match = re.search(pattern, content)
    
    if match:
        print(f"Assinatura atual: {match.group()}")
        
        # Verificar se tem context como parâmetro
        if 'context' not in match.group():
            print("\n❌ execute_plugin não tem parâmetro context!")
            print("\nOpções de correção:\n")
            
            print("OPÇÃO 1 - Remover context do cli.py:")
            print("  No comando process, mudar:")
            print("  result = core.execute_plugin(plugin, doc, params, {})")
            print("  Para:")
            print("  result = core.execute_plugin(plugin, doc, params)")
            
            print("\nOPÇÃO 2 - Adicionar context ao execute_plugin:")
            print("  Em core/__init__.py, mudar a assinatura para incluir context")
            
except Exception as e:
    print(f"Erro: {e}")

# 2. Ver como process está sendo chamado
print("\n\n🔍 Verificando chamadas em cli.py...")

try:
    with open('qualia/cli.py', 'r') as f:
        cli_content = f.read()
    
    # Procurar por execute_plugin no comando process
    lines = cli_content.split('\n')
    for i, line in enumerate(lines):
        if 'execute_plugin' in line and 'process' in cli_content[max(0, i-50):i]:
            print(f"\nLinha {i+1}: {line.strip()}")
            
            # Contar argumentos
            if 'plugin, doc, params, {}' in line:
                print("  ⚠️  Está passando 4 argumentos (plugin, doc, params, {})")
                print("  Mas execute_plugin espera apenas 3!")

except Exception as e:
    print(f"Erro: {e}")

# 3. Solução automática
print("\n\n🔧 Aplicando correção automática...")

try:
    # Remover o {} extra do cli.py
    pattern = r'(core\.execute_plugin\(plugin, doc, params), \{\}\)'
    replacement = r'\1)'
    
    new_cli = re.sub(pattern, replacement, cli_content)
    
    if new_cli != cli_content:
        with open('qualia/cli.py', 'w') as f:
            f.write(new_cli)
        print("✅ Removido context extra do cli.py!")
    else:
        # Tentar outro padrão
        pattern = r'(core\.execute_plugin\([^,]+,[^,]+,[^,]+), \{\}\)'
        replacement = r'\1)'
        new_cli = re.sub(pattern, replacement, cli_content)
        
        if new_cli != cli_content:
            with open('qualia/cli.py', 'w') as f:
                f.write(new_cli)
            print("✅ Corrigido!")
        else:
            print("❌ Não consegui aplicar correção automática")
            
except Exception as e:
    print(f"Erro: {e}")

print("\n\n📝 Nota sobre o problema:")
print("O BaseDocumentPlugin.process() espera context como parâmetro,")
print("mas QualiaCore.execute_plugin() não está passando context.")
print("\nSolução ideal: fazer execute_plugin passar context para plugins")
print("que precisam (analyzers e document processors).")