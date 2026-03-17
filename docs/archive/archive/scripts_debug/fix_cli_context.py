# fix_cli_context.py
"""
Corrige o problema do context no comando process
"""

import re

print("🔧 Corrigindo problema do context no CLI...\n")

# Ler o arquivo cli.py
try:
    with open('qualia/cli.py', 'r') as f:
        content = f.read()
    
    # Procurar pela linha problemática no comando process
    # Pattern: result = core.execute_plugin(plugin, doc, params)
    pattern = r'(result = core\.execute_plugin\(plugin, doc, params)\)'
    replacement = r'\1, {})'  # Adiciona , {} para o context
    
    # Fazer a substituição
    new_content = re.sub(pattern, replacement, content)
    
    # Verificar se a mudança foi feita
    if new_content != content:
        # Salvar o arquivo
        with open('qualia/cli.py', 'w') as f:
            f.write(new_content)
        print("✅ Arquivo cli.py corrigido!")
        print("   - Adicionado context vazio {} ao execute_plugin no comando process")
    else:
        print("⚠️  Não encontrei a linha exata. Vamos procurar de forma mais ampla...")
        
        # Procurar dentro da função process
        lines = content.split('\n')
        in_process_cmd = False
        fixed = False
        
        for i, line in enumerate(lines):
            # Detectar início do comando process
            if '@cli.command()' in line and i+1 < len(lines):
                # Ver se a próxima função é process
                next_few_lines = '\n'.join(lines[i:i+10])
                if 'def process(' in next_few_lines:
                    in_process_cmd = True
            
            # Se estamos no comando process
            if in_process_cmd and 'core.execute_plugin' in line and 'params)' in line and 'params, {})' not in line:
                print(f"   Encontrado na linha {i+1}: {line.strip()}")
                # Adicionar , {} antes do )
                lines[i] = line.replace('params)', 'params, {})')
                print(f"   Corrigido para: {lines[i].strip()}")
                fixed = True
                in_process_cmd = False
                
        if fixed:
            # Salvar
            with open('qualia/cli.py', 'w') as f:
                f.write('\n'.join(lines))
            print("\n✅ Correção aplicada!")
        else:
            print("\n❌ Não consegui aplicar a correção automaticamente.")
            print("\nCorreção manual:")
            print("1. Abra qualia/cli.py")
            print("2. Procure pela função 'def process'")
            print("3. Encontre a linha: result = core.execute_plugin(plugin, doc, params)")
            print("4. Mude para: result = core.execute_plugin(plugin, doc, params, {})")
            
except Exception as e:
    print(f"❌ Erro: {e}")

print("\n📝 Alternativamente, você pode corrigir o execute_plugin em core/__init__.py")
print("   para tornar context opcional com default {}:")
print("\n   def execute_plugin(self, plugin_id, document, config=None, context=None):")
print("       context = context or {}")
print("\nTeste novamente:")
print("  qualia process transcript_example.txt -p teams_cleaner --save-as cleaned.txt")