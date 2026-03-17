#!/usr/bin/env python3
"""
Corrigir o erro 'PipelineConfig' object is not subscriptable
"""

def fix_subscriptable_error():
    file_path = 'qualia/api/__init__.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # O erro está onde tentamos acessar pipeline_config["name"]
    # Deve ser pipeline_config.name
    
    # Procurar e corrigir
    replacements = [
        ('pipeline_config["name"]', 'pipeline_config.name'),
        ("pipeline_config['name']", 'pipeline_config.name'),
    ]
    
    modified = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"✅ Corrigido: {old} → {new}")
            modified = True
    
    # Verificar se há outros acessos incorretos
    import re
    matches = re.findall(r'pipeline_config\[[\'"]\w+[\'"]\]', content)
    if matches:
        print(f"\n⚠️  Encontrados outros acessos que podem precisar correção:")
        for match in matches:
            print(f"   {match}")
    
    if modified:
        with open(file_path, 'w') as f:
            f.write(content)
        print("\n✅ Arquivo salvo!")
    else:
        print("\n🔍 Procurando o erro de outra forma...")
        
        # Mostrar a função execute_pipeline para análise manual
        lines = content.split('\n')
        in_func = False
        for i, line in enumerate(lines):
            if 'async def execute_pipeline' in line:
                in_func = True
            elif in_func and line.strip() and not line.startswith(' '):
                break
            elif in_func and 'pipeline_config' in line:
                print(f"Linha {i+1}: {line}")

if __name__ == "__main__":
    fix_subscriptable_error()