"""
Webhook Examples - Como usar webhooks com Qualia Core

Este arquivo demonstra como configurar e testar webhooks.
"""

import requests
import json
import hmac
import hashlib
import os

# Base URL da API
BASE_URL = "http://localhost:8000"

def test_github_webhook():
    """Testa webhook do GitHub com assinatura."""
    print("🔷 Testando GitHub Webhook...")
    
    # Payload de exemplo (PR aberta)
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 42,
            "title": "Adiciona nova funcionalidade de análise",
            "body": "Esta PR implementa melhorias significativas no sistema de análise. É uma mudança fantástica que vai melhorar muito a experiência!",
            "user": {
                "login": "developer"
            }
        },
        "repository": {
            "name": "qualia-core"
        }
    }
    
    # Se houver secret configurado
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    headers = {}
    
    if secret:
        # Calcular assinatura
        raw_payload = json.dumps(payload, separators=(',', ':')).encode()
        signature = "sha256=" + hmac.new(
            secret.encode(),
            raw_payload,
            hashlib.sha256
        ).hexdigest()
        headers["X-Hub-Signature-256"] = signature
    
    # Enviar request
    response = requests.post(
        f"{BASE_URL}/webhook/github",
        json=payload,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_slack_webhook():
    """Testa webhook do Slack."""
    print("🔷 Testando Slack Webhook...")
    
    # Payload de exemplo
    payload = {
        "event": {
            "type": "message",
            "text": "Pessoal, estou muito feliz com o progresso do projeto! O novo sistema está funcionando perfeitamente.",
            "user": "U123456",
            "channel": "C123456"
        }
    }
    
    response = requests.post(f"{BASE_URL}/webhook/slack", json=payload)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_discord_webhook():
    """Testa webhook do Discord."""
    print("🔷 Testando Discord Webhook...")
    
    payload = {
        "content": "Alguém pode me ajudar? Estou com dificuldades para entender este código.",
        "username": "User123",
        "avatar_url": "https://example.com/avatar.png"
    }
    
    response = requests.post(f"{BASE_URL}/webhook/discord", json=payload)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_custom_webhook():
    """Testa webhook genérico."""
    print("🔷 Testando Custom Webhook...")
    
    # Teste 1: Análise de frequência
    payload1 = {
        "text": "Este é um texto de exemplo para análise. O texto contém várias palavras repetidas. Análise é importante!",
        "plugin": "word_frequency"
    }
    
    response = requests.post(f"{BASE_URL}/webhook/custom", json=payload1)
    print("Teste 1 - Word Frequency:")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    
    # Teste 2: Análise de sentimento
    payload2 = {
        "text": "Estou extremamente satisfeito com os resultados! O projeto superou todas as expectativas.",
        "plugin": "sentiment_analyzer"
    }
    
    response = requests.post(f"{BASE_URL}/webhook/custom", json=payload2)
    print("Teste 2 - Sentiment Analysis:")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_webhook_stats():
    """Verifica estatísticas dos webhooks."""
    print("🔷 Verificando estatísticas...")
    
    response = requests.get(f"{BASE_URL}/webhook/stats")
    print(f"Stats: {json.dumps(response.json(), indent=2)}")

def setup_github_webhook():
    """Mostra como configurar webhook no GitHub."""
    print("📝 Como configurar webhook no GitHub:")
    print("1. Vá para Settings > Webhooks no seu repositório")
    print("2. Clique em 'Add webhook'")
    print("3. Configure:")
    print("   - Payload URL: https://seu-dominio.com/webhook/github")
    print("   - Content type: application/json")
    print("   - Secret: (mesmo valor em GITHUB_WEBHOOK_SECRET)")
    print("   - Events: Issues, Pull requests, Push")
    print("4. Salve o webhook")
    print()
    print("Para testar localmente com ngrok:")
    print("   ngrok http 8000")
    print("   Use a URL do ngrok como Payload URL")
    print()

def test_with_ngrok():
    """Instruções para testar com ngrok."""
    print("🌐 Testando com ngrok:")
    print("1. Instale ngrok: https://ngrok.com/download")
    print("2. Execute a API: python run_api.py --reload")
    print("3. Em outro terminal: ngrok http 8000")
    print("4. Copie a URL HTTPS do ngrok")
    print("5. Configure webhooks para usar essa URL")
    print()
    print("Exemplo de URL: https://abc123.ngrok.io/webhook/github")
    print()

if __name__ == "__main__":
    print("=== Qualia Core Webhook Examples ===\n")
    
    # Verificar se API está rodando
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ API não está respondendo. Execute: python run_api.py")
            exit(1)
    except:
        print("❌ API não está rodando. Execute: python run_api.py")
        exit(1)
    
    # Executar testes
    test_github_webhook()
    test_slack_webhook()
    test_discord_webhook()
    test_custom_webhook()
    test_webhook_stats()
    
    print("\n" + "="*50 + "\n")
    
    # Instruções de configuração
    setup_github_webhook()
    test_with_ngrok()