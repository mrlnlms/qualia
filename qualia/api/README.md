# 🌐 Qualia Core API

REST API completa para o Qualia Core Framework.

## 📁 Estrutura

```
qualia/api/
├── __init__.py       # FastAPI app principal
├── webhooks.py       # Handlers de webhooks
├── monitor.py        # Monitor em tempo real
├── run.py           # Script para executar a API
├── __main__.py      # Permite python -m qualia.api
└── examples/        # Exemplos de uso
    ├── api_examples.py
    └── webhook_examples.py
```

## 🚀 Como Executar

### Opção 1: Como módulo Python
```bash
# Básico
python -m qualia.api

# Com reload (desenvolvimento)
python -m qualia.api --reload

# Customizado
python -m qualia.api --port 8080 --workers 4
```

### Opção 2: Script direto
```bash
python qualia/api/run.py --reload
```

### Opção 3: Docker
```bash
docker-compose up -d
```

## 📚 Endpoints Principais

### Core API
- `GET /` - Informações da API
- `GET /health` - Health check
- `GET /plugins` - Lista plugins
- `POST /analyze/{plugin_id}` - Executar análise
- `POST /visualize/{plugin_id}` - Gerar visualização
- `POST /pipeline` - Executar pipeline

### Webhooks
- `POST /webhook/github` - GitHub events
- `POST /webhook/slack` - Slack messages
- `POST /webhook/discord` - Discord messages
- `POST /webhook/custom` - Generic webhook
- `GET /webhook/stats` - Estatísticas

### Monitor
- `GET /monitor/` - Dashboard HTML
- `GET /monitor/stream` - SSE stream

## 🧪 Exemplos

### Teste Rápido
```bash
# Testar API
python -m qualia.api.examples.api_examples

# Testar webhooks
python -m qualia.api.examples.webhook_examples
```

### Análise via cURL
```bash
curl -X POST http://localhost:8000/analyze/word_frequency \
  -H "Content-Type: application/json" \
  -d '{"text": "Teste de análise"}'
```

### Python Client
```python
import requests

# Analisar texto
response = requests.post(
    "http://localhost:8000/analyze/sentiment_analyzer",
    json={"text": "Texto para análise"}
)
print(response.json())
```

## 🔧 Configuração

### Variáveis de Ambiente
```bash
QUALIA_API_HOST=0.0.0.0
QUALIA_API_PORT=8000
QUALIA_API_WORKERS=4
GITHUB_WEBHOOK_SECRET=xxx
ENABLE_MONITORING=true
```

### Desenvolvimento
```bash
# Auto-reload habilitado
python -m qualia.api --reload

# Ver logs detalhados
python -m qualia.api --log-level debug
```

## 📊 Monitoramento

Acesse http://localhost:8000/monitor/ para:
- Métricas em tempo real
- Gráficos de requisições/min
- Uso por plugin
- Atividade de webhooks

## 🐛 Troubleshooting

### ModuleNotFoundError
```bash
# Execute da raiz do projeto
cd /path/to/qualia-core
python -m qualia.api
```

### Porta em uso
```bash
# Use outra porta
python -m qualia.api --port 8080
```

### Webhooks não funcionam
1. Verifique secrets no .env
2. Use ngrok para teste local
3. Veja logs com --log-level debug

---

Para mais informações, veja `/docs` quando a API estiver rodando.