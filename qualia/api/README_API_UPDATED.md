# 🌐 Qualia Core REST API

REST API completa para o Qualia Core Framework, com suporte a webhooks e monitoramento em tempo real.

## 🚀 Quick Start

### 1. Instalar Dependências

```bash
pip install fastapi uvicorn python-multipart
```

### 2. Executar a API

```bash
# Modo desenvolvimento (com auto-reload)
python run_api.py --reload

# Modo produção
python run_api.py --workers 4
```

### 3. Acessar

- **API**: http://localhost:8000
- **Documentação Interativa**: http://localhost:8000/docs
- **Monitor em Tempo Real**: http://localhost:8000/monitor/
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 📚 Endpoints

### Informações Gerais

#### `GET /`
Retorna informações sobre a API e lista todos os endpoints disponíveis.

#### `GET /health`
Health check do serviço com contagem de plugins carregados.

### Plugins

#### `GET /plugins`
Lista todos os plugins disponíveis.

**Query Parameters:**
- `plugin_type` (opcional): Filtrar por tipo (analyzer, visualizer, document)

**Exemplo:**
```bash
curl http://localhost:8000/plugins?plugin_type=analyzer
```

#### `GET /plugins/{plugin_id}`
Detalhes de um plugin específico.

**Exemplo:**
```bash
curl http://localhost:8000/plugins/word_frequency
```

### Análise

#### `POST /analyze/{plugin_id}`
Executa um analyzer sobre texto.

**Body:**
```json
{
  "text": "Texto para analisar",
  "config": {
    "min_length": 4,
    "remove_stopwords": true
  },
  "context": {}
}
```

**Exemplo:**
```bash
curl -X POST http://localhost:8000/analyze/word_frequency \
  -H "Content-Type: application/json" \
  -d '{
    "text": "O Qualia é um framework incrível para análise.",
    "config": {"min_length": 4}
  }'
```

#### `POST /analyze/{plugin_id}/file`
Analisa arquivo enviado.

**Form Data:**
- `file`: Arquivo para análise
- `config`: JSON string com configuração
- `context`: JSON string com contexto

**Exemplo:**
```bash
curl -X POST http://localhost:8000/analyze/word_frequency/file \
  -F "file=@document.txt" \
  -F 'config={"min_length": 4}'
```

### Processamento

#### `POST /process/{plugin_id}`
Processa documento com plugin.

**Body:**
```json
{
  "text": "Texto para processar",
  "config": {}
}
```

**Exemplo:**
```bash
curl -X POST http://localhost:8000/process/teams_cleaner \
  -H "Content-Type: application/json" \
  -d '{
    "text": "[00:00:00] João: Olá!",
    "config": {"remove_timestamps": true}
  }'
```

### Visualização

#### `POST /visualize/{plugin_id}`
Gera visualização a partir de dados.

**Body:**
```json
{
  "data": {
    "word_frequencies": {
      "palavra1": 10,
      "palavra2": 8
    }
  },
  "config": {
    "max_words": 50
  },
  "output_format": "png"
}
```

**Formatos Suportados:**
- `png`: Retorna base64
- `svg`: Retorna base64
- `html`: Retorna HTML como texto

**Exemplo:**
```bash
curl -X POST http://localhost:8000/visualize/wordcloud_viz \
  -H "Content-Type: application/json" \
  -d '{
    "data": {"word_frequencies": {"api": 10, "rest": 8}},
    "output_format": "png"
  }'
```

### Pipeline

#### `POST /pipeline`
Executa pipeline de plugins.

**Body:**
```json
{
  "text": "Texto para processar",
  "steps": [
    {
      "plugin_id": "word_frequency",
      "config": {"min_length": 4}
    }
  ]
}
```

**Nota**: Atualmente há um bug conhecido com pipelines mistos. Use apenas analyzers no pipeline.

### 📡 Webhooks (NOVO!)

#### `POST /webhook/custom`
Webhook genérico para processar texto de qualquer fonte.

**Body:**
```json
{
  "text": "Texto para analisar",
  "plugin": "word_frequency"  // opcional, default: word_frequency
}
```

**Exemplo:**
```bash
curl -X POST http://localhost:8000/webhook/custom \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Analisar sentimento deste texto!",
    "plugin": "sentiment_analyzer"
  }'
```

#### `GET /webhook/stats`
Retorna estatísticas de processamento dos webhooks.

**Response:**
```json
{
  "status": "ok",
  "stats": {
    "generic": {
      "total_received": 10,
      "total_processed": 9,
      "total_errors": 1,
      "last_processed": "2024-12-11T20:30:00"
    }
  }
}
```

### 📊 Monitor em Tempo Real (NOVO!)

#### `GET /monitor/`
Dashboard HTML com visualizações em tempo real.

Acesse direto no navegador: http://localhost:8000/monitor/

**Características:**
- Gráficos ao vivo de requests/min
- Contadores de uso por plugin
- Atividade de webhooks
- Últimos erros
- Zero dependências externas

#### `GET /monitor/stream`
Server-Sent Events (SSE) stream com métricas em tempo real.

**Exemplo JavaScript:**
```javascript
const eventSource = new EventSource('http://localhost:8000/monitor/stream');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Métricas:', data.metrics);
};
```

**Response (SSE):**
```
data: {"timestamp":"2024-12-11T20:30:00","metrics":{"requests_total":150,"requests_per_minute":12.5,...}}

data: {"timestamp":"2024-12-11T20:30:01","metrics":{"requests_total":151,"requests_per_minute":12.6,...}}
```

## 🐍 Python Client Example

```python
import requests
import json

class QualiaAPIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def list_plugins(self, plugin_type=None):
        params = {"plugin_type": plugin_type} if plugin_type else {}
        return requests.get(f"{self.base_url}/plugins", params=params).json()
    
    def analyze(self, plugin_id, text, config=None):
        data = {
            "text": text,
            "config": config or {}
        }
        return requests.post(f"{self.base_url}/analyze/{plugin_id}", json=data).json()
    
    def visualize(self, plugin_id, data, config=None, output_format="png"):
        payload = {
            "data": data,
            "config": config or {},
            "output_format": output_format
        }
        return requests.post(f"{self.base_url}/visualize/{plugin_id}", json=payload).json()
    
    def webhook(self, text, plugin="word_frequency"):
        payload = {
            "text": text,
            "plugin": plugin
        }
        return requests.post(f"{self.base_url}/webhook/custom", json=payload).json()
    
    def get_metrics(self):
        """Get current metrics from monitor"""
        response = requests.get(f"{self.base_url}/monitor/stream", stream=True)
        for line in response.iter_lines():
            if line and line.startswith(b'data:'):
                return json.loads(line[6:])
        return None

# Uso
client = QualiaAPIClient()

# Listar analyzers
analyzers = client.list_plugins("analyzer")

# Analisar texto
result = client.analyze("word_frequency", "Texto para análise", {"min_length": 4})

# Webhook
webhook_result = client.webhook("Texto via webhook!", "sentiment_analyzer")

# Obter métricas
metrics = client.get_metrics()
print(f"Total de requests: {metrics['metrics']['requests_total']}")
```

## 🛠️ Configuração Avançada

### Variáveis de Ambiente

```bash
# Host e porta
export QUALIA_API_HOST=0.0.0.0
export QUALIA_API_PORT=8080

# Número de workers (produção)
export QUALIA_API_WORKERS=4

# Webhooks
export GITHUB_WEBHOOK_SECRET=seu_secret_aqui
export SLACK_SIGNING_SECRET=seu_secret_aqui

# Monitoramento
export ENABLE_MONITORING=true
```

### Docker

```bash
# Build
docker build -t qualia-core:latest .

# Run
docker run -p 8000:8000 \
  -e GITHUB_WEBHOOK_SECRET=xxx \
  qualia-core:latest

# Docker Compose
docker-compose up -d
```

### NGINX Proxy

```nginx
server {
    listen 80;
    server_name api.qualia.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # SSE para monitor
    location /monitor/stream {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
    }
}
```

## 🔒 Segurança

### CORS

Por padrão, CORS está habilitado para todos os origins. Em produção, configure:

```python
# Em qualia/api/__init__.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://seu-dominio.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Rate Limiting

Adicione rate limiting com slowapi:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/analyze/{plugin_id}")
@limiter.limit("10/minute")
async def analyze(plugin_id: str, request: AnalyzeRequest):
    # ...
```

### Webhook Security

Para GitHub webhooks:
```bash
export GITHUB_WEBHOOK_SECRET=gere_um_secret_seguro
```

O webhook verificará automaticamente a assinatura HMAC.

## 📊 Monitoramento

### Métricas Disponíveis

O monitor rastreia:
- `requests_total`: Total de requisições
- `requests_per_minute`: Taxa de requisições
- `active_connections`: Conexões SSE ativas
- `plugin_usage`: Uso por plugin
- `webhook_stats`: Estatísticas de webhooks
- `errors_total`: Total de erros
- `last_error`: Último erro registrado
- `uptime_seconds`: Tempo de atividade

### Integração com Prometheus

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
# Métricas disponíveis em /metrics
```

## 🧪 Testes

```python
# test_api.py
from fastapi.testclient import TestClient
from qualia.api import app

client = TestClient(app)

def test_list_plugins():
    response = client.get("/plugins")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_analyze():
    response = client.post("/analyze/word_frequency", json={
        "text": "Test text",
        "config": {}
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_webhook():
    response = client.post("/webhook/custom", json={
        "text": "Webhook test"
    })
    assert response.status_code == 200
    assert "result" in response.json()

def test_monitor():
    response = client.get("/monitor/")
    assert response.status_code == 200
    assert "Qualia Core Monitor" in response.text
```

## 🚨 Troubleshooting

### Problema: "Plugin not found"
**Solução**: Certifique-se de que os plugins estão no diretório correto e que `core.discover_plugins()` foi executado.

### Problema: "CORS error"
**Solução**: Verifique as configurações de CORS e adicione seu domínio à lista de origins permitidos.

### Problema: "File upload failed"
**Solução**: Instale `python-multipart`:
```bash
pip install python-multipart
```

### Problema: Pipeline retorna erro
**Status**: Bug conhecido. Use apenas analyzers no pipeline ou execute steps separadamente.

### Problema: Monitor não atualiza
**Solução**: Verifique se o navegador suporta SSE e se não há proxy bloqueando conexões longas.

## 📝 Changelog

### v0.1.0 (Dezembro 2024)
- ✅ Endpoints básicos de CRUD
- ✅ Análise, processamento e visualização
- ✅ Pipeline support (com bug conhecido)
- ✅ Upload de arquivos
- ✅ Webhooks genéricos (NOVO!)
- ✅ Monitor em tempo real (NOVO!)
- ✅ Docker support (NOVO!)
- ✅ Documentação automática com Swagger

## 🤝 Contribuindo

1. Adicione novos endpoints em `qualia/api/__init__.py`
2. Webhooks em `qualia/api/webhooks.py`
3. Mantenha a documentação atualizada
4. Adicione testes para novos endpoints
5. Use type hints e Pydantic models

---

**Happy API Building!** 🚀