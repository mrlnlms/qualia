#!/usr/bin/env python3
"""
Testar individualmente os endpoints que estão falhando
"""

import requests
import json

def test_endpoints():
    print("🧪 TESTE INDIVIDUAL DOS ENDPOINTS\n")
    
    # 1. Teste do Pipeline
    print("1. Testando Pipeline:")
    response = requests.post(
        "http://localhost:8000/pipeline",
        json={
            "text": "Teste do pipeline funcionando",
            "steps": [
                {
                    "plugin_id": "word_frequency",
                    "config": {"min_length": 3}
                }
            ]
        }
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ SUCESSO!")
        print(f"   Steps executados: {result.get('steps_executed', 0)}")
        print(f"   Resultado tem chaves: {list(result.get('results', {}).keys())}")
    else:
        print(f"   ❌ ERRO: {response.text}")
    
    # 2. Teste do Webhook com Sentiment
    print("\n2. Testando Webhook com Sentiment:")
    response = requests.post(
        "http://localhost:8000/webhook/custom",
        json={
            "text": "Estou muito feliz que está funcionando!",
            "plugin": "sentiment_analyzer"
        }
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ SUCESSO!")
        print(f"   Plugin usado: {result.get('plugin', 'N/A')}")
        if 'result' in result and 'sentiment' in result['result']:
            sentiment = result['result']['sentiment']
            print(f"   Sentimento detectado: {sentiment.get('polarity_label', 'N/A')}")
            print(f"   Polaridade: {sentiment.get('polarity', 0):.2f}")
        else:
            print(f"   ⚠️  Resultado não contém sentiment: {result.get('result', {}).keys()}")
    else:
        print(f"   ❌ ERRO: {response.text}")
    
    # 3. Verificar se sentiment_analyzer existe
    print("\n3. Verificando plugins disponíveis:")
    plugins = requests.get("http://localhost:8000/plugins").json()
    
    analyzers = [p for p in plugins if p['type'] == 'analyzer']
    print(f"   Total de analyzers: {len(analyzers)}")
    
    sentiment_exists = any(p['id'] == 'sentiment_analyzer' for p in plugins)
    print(f"   sentiment_analyzer existe: {sentiment_exists}")
    
    if not sentiment_exists:
        print("\n   ⚠️  PROBLEMA: sentiment_analyzer não está disponível!")
        print("   Analyzers disponíveis:")
        for p in analyzers:
            print(f"     - {p['id']}: {p['name']}")

if __name__ == "__main__":
    test_endpoints()