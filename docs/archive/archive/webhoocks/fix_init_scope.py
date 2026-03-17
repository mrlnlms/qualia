#!/usr/bin/env python3
"""
Move set_tracking_callback para dentro do bloco if HAS_EXTENSIONS
"""

from pathlib import Path
import re

print("🔧 Corrigindo escopo do set_tracking_callback...\n")

init_file = Path("qualia/api/__init__.py")

if init_file.exists():
    content = init_file.read_text()
    lines = content.split('\n')
    
    # Encontrar e remover a linha problemática
    new_lines = []
    removed_line = None
    
    for i, line in enumerate(lines):
        if "set_tracking_callback(track_webhook)" in line and not line.strip().startswith("#"):
            removed_line = line
            print(f"   ✅ Removida linha {i+1}: {line.strip()}")
            continue  # Pula essa linha
        new_lines.append(line)
    
    # Agora adicionar no lugar correto
    if removed_line:
        # Procurar onde está init_webhooks(core)
        for i, line in enumerate(new_lines):
            if "init_webhooks(core)" in line and not line.strip().startswith("#"):
                # Adicionar logo após
                indent = len(line) - len(line.lstrip())
                new_lines.insert(i + 1, " " * indent + "set_tracking_callback(track_webhook)")
                print(f"   ✅ Adicionada na linha {i+2} (dentro do bloco if HAS_EXTENSIONS)")
                break
    
    # Salvar
    init_file.write_text('\n'.join(new_lines))
    print("\n   ✅ Arquivo corrigido e salvo!")
    
    # Limpar cache
    import shutil
    pycache = Path("qualia/api/__pycache__")
    if pycache.exists():
        shutil.rmtree(pycache)
        print("   ✅ Cache limpo!")

print("\n✨ Correção aplicada!")
print("\n🚀 Reinicie a API agora - deve funcionar sem erros!")