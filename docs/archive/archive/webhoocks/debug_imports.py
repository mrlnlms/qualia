#!/usr/bin/env python3
"""
Debug de importações - descobre por que webhooks e monitor não carregam
"""

import sys
from pathlib import Path

print("🔍 Debug de Importações\n")

# 1. Verificar paths
print("1️⃣ Python paths:")
for p in sys.path[:5]:
    print(f"   {p}")

# 2. Verificar se os arquivos existem
print("\n2️⃣ Arquivos da API:")
api_dir = Path("qualia/api")
for file in ["__init__.py", "webhooks.py", "monitor.py", "run.py"]:
    path = api_dir / file
    exists = "✅" if path.exists() else "❌"
    size = f"({path.stat().st_size} bytes)" if path.exists() else ""
    print(f"   {exists} {file} {size}")

# 3. Tentar importar cada módulo
print("\n3️⃣ Testando imports:")

# Webhooks
print("\n   Tentando: from qualia.api.webhooks import router")
try:
    from qualia.api.webhooks import router as webhook_router
    print("   ✅ webhooks importado com sucesso!")
except ImportError as e:
    print(f"   ❌ Erro ao importar webhooks: {e}")
except Exception as e:
    print(f"   ❌ Outro erro em webhooks: {type(e).__name__}: {e}")

# Monitor
print("\n   Tentando: from qualia.api.monitor import router")
try:
    from qualia.api.monitor import router as monitor_router
    print("   ✅ monitor importado com sucesso!")
except ImportError as e:
    print(f"   ❌ Erro ao importar monitor: {e}")
except Exception as e:
    print(f"   ❌ Outro erro em monitor: {type(e).__name__}: {e}")

# 4. Tentar importar diretamente
print("\n4️⃣ Import direto do módulo:")
try:
    import qualia.api.webhooks
    print("   ✅ qualia.api.webhooks importado")
    print(f"   Conteúdo: {dir(qualia.api.webhooks)[:5]}...")
except Exception as e:
    print(f"   ❌ Erro: {e}")

try:
    import qualia.api.monitor
    print("   ✅ qualia.api.monitor importado")
    print(f"   Conteúdo: {dir(qualia.api.monitor)[:5]}...")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 5. Verificar se há __pycache__ corrompido
print("\n5️⃣ Verificando __pycache__:")
pycache = api_dir / "__pycache__"
if pycache.exists():
    print(f"   ⚠️  __pycache__ existe. Considere deletar: rm -rf {pycache}")

print("\n" + "="*60)
print("\n💡 Soluções comuns:")
print("1. Limpar cache: rm -rf qualia/api/__pycache__")
print("2. Verificar se os arquivos têm a sintaxe correta")
print("3. Verificar se há imports faltando nos módulos")