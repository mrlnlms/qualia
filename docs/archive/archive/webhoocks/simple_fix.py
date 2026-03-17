#!/usr/bin/env python3
"""
Correção simples - comenta a linha problemática temporariamente
"""

from pathlib import Path

print("🔧 Aplicando correção simples...\n")

init_file = Path("qualia/api/__init__.py")

if init_file.exists():
    with open(init_file, 'r') as f:
        lines = f.readlines()
    
    # Procurar e comentar a linha problemática
    for i, line in enumerate(lines):
        if "set_tracking_callback(track_webhook)" in line and not line.strip().startswith("#"):
            print(f"Linha {i+1} encontrada: {line.strip()}")
            lines[i] = "# " + line
            print(f"Comentada: # {line.strip()}")
    
    # Salvar
    with open(init_file, 'w') as f:
        f.writelines(lines)
    
    print("\n✅ Correção aplicada!")
    
    # Limpar cache
    import shutil
    pycache = Path("qualia/api/__pycache__")
    if pycache.exists():
        shutil.rmtree(pycache)
        print("✅ Cache limpo!")

print("\n🚀 Tente iniciar a API novamente!")
print("\nNota: O tracking de webhooks ficará desabilitado temporariamente,")
print("mas a API e os webhooks funcionarão normalmente.")