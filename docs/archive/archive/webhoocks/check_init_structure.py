#!/usr/bin/env python3
"""
Verifica a estrutura do __init__.py para encontrar o problema
"""

from pathlib import Path

print("🔍 Verificando estrutura do __init__.py\n")

init_file = Path("qualia/api/__init__.py")

if init_file.exists():
    content = init_file.read_text()
    lines = content.split('\n')
    
    # Procurar onde está o problema
    print("1️⃣ Procurando imports e uso de set_tracking_callback:")
    
    import_line = -1
    usage_line = -1
    has_extensions_block = -1
    
    for i, line in enumerate(lines, 1):
        if "from qualia.api.webhooks import" in line and "set_tracking_callback" in line:
            print(f"   Linha {i}: {line.strip()}")
            import_line = i
            
        if "set_tracking_callback(track_webhook)" in line and not line.strip().startswith("#"):
            print(f"   Linha {i}: {line.strip()}")
            usage_line = i
            
        if "if HAS_EXTENSIONS:" in line:
            has_extensions_block = i
    
    print(f"\n2️⃣ Análise:")
    print(f"   Import na linha: {import_line}")
    print(f"   Uso na linha: {usage_line}")
    print(f"   Bloco HAS_EXTENSIONS na linha: {has_extensions_block}")
    
    if usage_line > 0 and has_extensions_block > 0:
        if usage_line < has_extensions_block or usage_line > has_extensions_block + 10:
            print("   ❌ PROBLEMA: set_tracking_callback está FORA do bloco if HAS_EXTENSIONS!")
            print("   Isso causa o erro porque a função só existe quando HAS_EXTENSIONS=True")
    
    # Mostrar contexto ao redor da linha 53
    print("\n3️⃣ Contexto ao redor da linha 53:")
    start = max(0, 50)
    end = min(len(lines), 56)
    for i in range(start, end):
        prefix = ">>>" if i == 52 else "   "
        print(f"{prefix} {i+1}: {lines[i]}")

print("\n💡 O problema é que set_tracking_callback está sendo chamado fora do bloco if HAS_EXTENSIONS!")