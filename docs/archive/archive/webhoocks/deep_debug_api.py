#!/usr/bin/env python3
"""
Debug profundo para descobrir por que os módulos não carregam
"""

import sys
from pathlib import Path

print("🔍 Debug Profundo da API\n")

# 1. Tentar importar o __init__.py e ver o que acontece
print("1️⃣ Testando import do __init__.py:")
try:
    # Adicionar path se necessário
    sys.path.insert(0, str(Path.cwd()))
    
    # Tentar importar
    from qualia.api import app, HAS_EXTENSIONS
    print(f"   ✅ API importada")
    print(f"   HAS_EXTENSIONS = {HAS_EXTENSIONS}")
    
    if not HAS_EXTENSIONS:
        print("   ❌ Extensões não foram carregadas!")
except Exception as e:
    print(f"   ❌ Erro ao importar API: {e}")

# 2. Testar imports individuais com mais detalhes
print("\n2️⃣ Testando imports individuais:")

# Webhooks
print("\n   📌 Webhooks:")
try:
    import qualia.api.webhooks as wb
    print(f"   ✅ Módulo webhooks importado")
    print(f"   Conteúdo: {[x for x in dir(wb) if not x.startswith('_')][:5]}")
    
    # Tentar importar específicos
    try:
        from qualia.api.webhooks import router as webhook_router
        print("   ✅ router importado com sucesso")
    except Exception as e:
        print(f"   ❌ Erro ao importar router: {e}")
    
    try:
        from qualia.api.webhooks import init_webhooks
        print("   ✅ init_webhooks importado com sucesso")
    except Exception as e:
        print(f"   ❌ Erro ao importar init_webhooks: {e}")
    
    try:
        from qualia.api.webhooks import set_tracking_callback
        print("   ✅ set_tracking_callback importado com sucesso")
    except Exception as e:
        print(f"   ❌ Erro ao importar set_tracking_callback: {e}")
        
except Exception as e:
    print(f"   ❌ Erro geral em webhooks: {e}")

# Monitor
print("\n   📌 Monitor:")
try:
    import qualia.api.monitor as mon
    print(f"   ✅ Módulo monitor importado")
    print(f"   Conteúdo: {[x for x in dir(mon) if not x.startswith('_')][:5]}")
    
    try:
        from qualia.api.monitor import router as monitor_router
        print("   ✅ router importado com sucesso")
    except Exception as e:
        print(f"   ❌ Erro ao importar router: {e}")
    
    try:
        from qualia.api.monitor import track_request
        print("   ✅ track_request importado com sucesso")
    except Exception as e:
        print(f"   ❌ Erro ao importar track_request: {e}")
    
    try:
        from qualia.api.monitor import track_webhook
        print("   ✅ track_webhook importado com sucesso")
    except Exception as e:
        print(f"   ❌ Erro ao importar track_webhook: {e}")
        
except Exception as e:
    print(f"   ❌ Erro geral em monitor: {e}")

# 3. Simular o que o __init__.py faz
print("\n3️⃣ Simulando import do __init__.py:")
try:
    from qualia.api.webhooks import router as webhook_router, init_webhooks, set_tracking_callback
    from qualia.api.monitor import router as monitor_router, track_request, track_webhook
    print("   ✅ Todos os imports funcionaram!")
    HAS_EXTENSIONS = True
except ImportError as e:
    print(f"   ❌ ImportError: {e}")
    HAS_EXTENSIONS = False
except Exception as e:
    print(f"   ❌ Outro erro: {type(e).__name__}: {e}")
    HAS_EXTENSIONS = False

print(f"\n   HAS_EXTENSIONS seria: {HAS_EXTENSIONS}")

# 4. Verificar se há algum print escondido
print("\n4️⃣ Verificando origem do warning:")
init_file = Path("qualia/api/__init__.py")
if init_file.exists():
    content = init_file.read_text()
    warning_line = 'print("Warning: Webhook and monitor modules not found. Running in basic mode.")'
    if warning_line in content:
        line_num = content[:content.find(warning_line)].count('\n') + 1
        print(f"   ⚠️  Warning está na linha {line_num} do __init__.py")
    else:
        print("   ❓ Warning não encontrado no local esperado")

print("\n" + "="*60)
print("\n💡 Diagnóstico completo concluído!")