#!/usr/bin/env python3
"""
Debug detalhado do erro no webhook
"""

import requests
import json

print("🔍 Debug do Webhook Error 500\n")

base_url = "http://localhost:8000"

# 1. Teste simples primeiro
print("1️⃣ Teste webhook mais simples possível:")
response = requests.post(
    f"{base_url}/webhook/custom",
    json={"text": "Teste simples"}
)
print(f"   Status: {response.status_code}")
if response.status_code != 200:
    print(f"   Erro: {response.text}")
else:
    print(f"   Resposta: {json.dumps(response.json(), indent=2)}")

# 2. Verificar se o problema é o plugin
print("\n2️⃣ Teste especificando plugin que existe:")
response = requests.post(
    f"{base_url}/webhook/custom",
    json={
        "text": "Teste com plugin específico",
        "plugin": "word_frequency"  # Plugin que sabemos que existe
    }
)
print(f"   Status: {response.status_code}")
if response.status_code != 200:
    print(f"   Erro: {response.text}")

# 3. Testar webhook de teste
print("\n3️⃣ Teste endpoint de teste do GitHub:")
response = requests.post(f"{base_url}/webhook/test/github")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"   Status: {result.get('status')}")
    print(f"   Plugin usado: {result.get('result', {}).get('plugin_used', 'N/A')}")

# 4. Verificar se plugins estão carregados
print("\n4️⃣ Verificando plugins disponíveis:")
response = requests.get(f"{base_url}/plugins")
if response.status_code == 200:
    plugins = response.json()
    analyzers = [p for p in plugins if p['type'] == 'analyzer']
    print(f"   Total de plugins: {len(plugins)}")
    print(f"   Analyzers disponíveis: {[p['id'] for p in analyzers]}")

# 5. Corrigir teste de pipeline
print("\n5️⃣ Teste de pipeline corrigido:")
response = requests.post(
    f"{base_url}/pipeline",
    json={
        "text": "Este é um teste de pipeline funcionando",
        "steps": [
            {"plugin_id": "word_frequency", "config": {}}
        ]
    }
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print("   ✅ Pipeline funcionando!")
else:
    print(f"   ❌ Erro: {response.text[:200]}")

print("\n" + "="*50)
print("\n💡 Verifique o terminal da API para ver os erros detalhados!")