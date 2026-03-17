#!/usr/bin/env python3
"""
Teste Básico da API - Testa apenas o essencial sem webhooks/monitor
"""

import requests
import time

print("🧪 Teste Básico da API Qualia Core\n")

print("⚠️  IMPORTANTE: A API precisa estar rodando!")
print("   Execute em outro terminal: python run_api.py --reload\n")

input("Pressione ENTER quando a API estiver rodando...")

base_url = "http://localhost:8000"

tests_passed = 0
tests_total = 0

def test_endpoint(name, method, url, **kwargs):
    global tests_passed, tests_total
    tests_total += 1
    
    try:
        if method == "GET":
            response = requests.get(f"{base_url}{url}", **kwargs)
        else:
            response = requests.post(f"{base_url}{url}", **kwargs)
        
        if response.status_code in [200, 201]:
            print(f"✅ {name}: OK ({response.status_code})")
            tests_passed += 1
            return True
        else:
            print(f"❌ {name}: FALHOU ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ {name}: ERRO - {str(e)}")
        return False

# Testes básicos
print("\n1️⃣ Testando endpoints básicos...")
test_endpoint("Root", "GET", "/")
test_endpoint("Health", "GET", "/health")
test_endpoint("Plugins", "GET", "/plugins")

# Teste de análise
print("\n2️⃣ Testando análise...")
test_endpoint(
    "Word Frequency", 
    "POST", 
    "/analyze/word_frequency",
    json={"text": "Este é um teste básico da API"}
)

# Teste de pipeline
print("\n3️⃣ Testando pipeline...")
test_endpoint(
    "Pipeline",
    "POST",
    "/pipeline",
    json={
        "text": "[00:00:00] Speaker: Teste de pipeline",
        "steps": [
            {"plugin_id": "teams_cleaner"},
            {"plugin_id": "word_frequency"}
        ]
    }
)

# Resumo
print("\n" + "="*50)
print(f"\n📊 Resultado: {tests_passed}/{tests_total} testes passaram")

if tests_passed == tests_total:
    print("✅ Todos os testes básicos passaram!")
else:
    print("❌ Alguns testes falharam")

print("\n💡 Próximos passos:")
print("1. Se os testes básicos passaram, a API está funcionando!")
print("2. Para habilitar webhooks/monitor, copie os arquivos dos artifacts")
print("3. Use test_infrastructure.py para teste completo")