# 🌐 Qualia Core REST API

REST API para o Qualia Core Framework, permitindo análise qualitativa via HTTP.

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
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 📚 Endpoints

### Informações Gerais

#### `GET /`
Retorna informações sobre a API.

#### `GET /health`
Health check do serviço.

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
      "plugin_id": "teams_cleaner",
      "config": {"remove_timestamps": true}
    },
    {
      "plugin_id": "word_frequency",
      "config": {"min_length": 4}
    }
  ]
}
```

**Exemplo:**
```bash
curl -X POST http://localhost:8000/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "text": "[00:00:00] Speaker: Texto importante.",
    "steps": [
      {"plugin_id": "teams_cleaner", "config": {}},
      {"plugin_id": "word_frequency", "config": {}}
    ]
  }'
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

# Uso
client = QualiaAPIClient()

# Listar analyzers
analyzers = client.list_plugins("analyzer")

# Analisar texto
result = client.analyze("word_frequency", "Texto para análise", {"min_length": 4})

# Criar visualização
viz = client.visualize("wordcloud_viz", result['result'])
```

## 🛠️ Configuração Avançada

### Variáveis de Ambiente

```bash
# Host e porta
export QUALIA_API_HOST=0.0.0.0
export QUALIA_API_PORT=8080

# Número de workers (produção)
export QUALIA_API_WORKERS=4
```

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "run_api.py", "--host", "0.0.0.0", "--workers", "4"]
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

## 📊 Monitoramento

### Logs

```python
# Configurar logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Métricas com Prometheus

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

## 📝 Changelog

### v0.1.0 (Inicial)
- ✅ Endpoints básicos de CRUD
- ✅ Análise, processamento e visualização
- ✅ Pipeline support
- ✅ Upload de arquivos
- ✅ Documentação automática com Swagger

## 🤝 Contribuindo

1. Adicione novos endpoints em `qualia/api/__init__.py`
2. Mantenha a documentação atualizada
3. Adicione testes para novos endpoints
4. Use type hints e Pydantic models

---

**Happy API Building!** 🚀