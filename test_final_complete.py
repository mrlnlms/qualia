#!/usr/bin/env python3
"""
Teste FINAL - Verificar se TUDO está funcionando
"""

import requests
import json

print("🎯 TESTE FINAL DA INFRAESTRUTURA\n")

base_url = "http://localhost:8000"
passed = 0
total = 0

def test(name, func):
    global passed, total
    total += 1
    try:
        result = func()
        if result:
            print(f"✅ {name}")
            passed += 1
        else:
            print(f"❌ {name}")
    except Exception as e:
        print(f"❌ {name}: {e}")

# 1. API Básica
test("API Health", lambda: requests.get(f"{base_url}/health").status_code == 200)
test("API Plugins", lambda: len(requests.get(f"{base_url}/plugins").json()) > 0)

# 2. Webhooks
def test_webhook():
    r = requests.post(f"{base_url}/webhook/custom", json={"text": "Teste completo!"})
    return r.status_code == 200 and r.json()["status"] == "success"

test("Webhook Custom", test_webhook)
test("Webhook Stats", lambda: requests.get(f"{base_url}/webhook/stats").status_code == 200)

# 3. Monitor
test("Monitor Dashboard", lambda: requests.get(f"{base_url}/monitor/").status_code == 200)
test("Monitor Stream", lambda: requests.get(f"{base_url}/monitor/stream", stream=True, timeout=1).status_code == 200)

# 4. Análise
def test_analysis():
    r = requests.post(f"{base_url}/analyze/word_frequency", json={"text": "Infraestrutura completa e funcionando!"})
    return r.status_code == 200

test("Análise Word Frequency", test_analysis)

# 5. Pipeline (corrigido)
def test_pipeline():
    r = requests.post(f"{base_url}/pipeline", json={
        "text": "Pipeline também funcionando!",
        "steps": [{"plugin_id": "word_frequency"}]
    })
    return r.status_code == 200

test("Pipeline", test_pipeline)

# 6. Teste com sentiment analyzer
def test_sentiment():
    r = requests.post(f"{base_url}/webhook/custom", json={
        "text": "Estou muito feliz que finalmente está tudo funcionando!",
        "plugin": "sentiment_analyzer"
    })
    return r.status_code == 200 and "sentiment" in r.json().get("result", {})

test("Webhook com Sentiment", test_sentiment)

print("\n" + "="*50)
print(f"\n📊 RESULTADO FINAL: {passed}/{total} testes passaram")

if passed == total:
    print("\n🎉 PARABÉNS! INFRAESTRUTURA 100% FUNCIONAL!")
    print("\n✅ O que está funcionando:")
    print("- API REST com documentação automática")
    print("- Webhooks para integrações externas")
    print("- Monitor em tempo real")
    print("- Análise e pipelines")
    print("\n🌐 Acesse:")
    print(f"- Monitor: {base_url}/monitor/")
    print(f"- API Docs: {base_url}/docs")
    print("\n🚀 Sprint de infraestrutura CONCLUÍDA!")
else:
    print(f"\n⚠️  Alguns testes falharam ({total-passed})")