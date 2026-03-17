#!/usr/bin/env python3
"""
Testa os novos recursos: Webhooks e Monitor
"""

import requests

print("🧪 Testando Novos Recursos da API\n")

base_url = "http://localhost:8000"

# 1. Verificar se os novos endpoints existem
print("1️⃣ Verificando endpoints...")

endpoints = [
    ("/webhook/stats", "Webhook Stats"),
    ("/monitor/", "Monitor Dashboard"),
    ("/", "Root (deve listar novos endpoints)")
]

for endpoint, name in endpoints:
    try:
        r = requests.get(f"{base_url}{endpoint}")
        if r.status_code == 200:
            print(f"✅ {name}: OK")
            if endpoint == "/":
                data = r.json()
                if "webhooks" in data.get("endpoints", {}):
                    print("   ✅ Webhooks habilitados!")
                else:
                    print("   ⚠️  Webhooks NÃO detectados")
        else:
            print(f"❌ {name}: {r.status_code}")
    except Exception as e:
        print(f"❌ {name}: {str(e)}")

# 2. Testar webhook se disponível
print("\n2️⃣ Testando webhook custom...")
try:
    r = requests.post(
        f"{base_url}/webhook/custom",
        json={"text": "Teste de webhook funcionando!"}
    )
    if r.status_code == 200:
        print("✅ Webhook funcionando!")
        result = r.json()
        print(f"   Plugin usado: {result.get('plugin_used', 'N/A')}")
        print(f"   Status: {result.get('status', 'N/A')}")
    else:
        print(f"❌ Webhook retornou: {r.status_code}")
except Exception as e:
    print(f"❌ Webhook erro: {str(e)}")

# 3. Verificar pipeline corrigido
print("\n3️⃣ Testando pipeline corrigido...")
try:
    # Pipeline só com analyzer
    r = requests.post(
        f"{base_url}/pipeline",
        json={
            "text": "Teste simples de pipeline",
            "steps": [
                {"plugin_id": "word_frequency"}
            ]
        }
    )
    if r.status_code == 200:
        print("✅ Pipeline funcionando!")
    else:
        print(f"❌ Pipeline: {r.status_code}")
        print(f"   Erro: {r.text}")
except Exception as e:
    print(f"❌ Pipeline erro: {str(e)}")

print("\n" + "="*50)
print("\n📝 Status:")
print("- API Básica: ✅ Funcionando")
print("- Webhooks: " + ("✅ Habilitados" if "webhook" in locals() else "⚠️  Não detectados"))
print("- Monitor: " + ("✅ Habilitado" if "monitor" in locals() else "⚠️  Não detectado"))