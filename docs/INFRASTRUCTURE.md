# 🏗️ Qualia Core - Infrastructure Features

Este documento descreve os recursos de infraestrutura implementados.

## 🚀 Quick Start

```bash
# 1. Configurar ambiente
cp .env.example .env

# 2. Build e executar com Docker
docker-compose up -d

# 3. Verificar que está rodando
curl http://localhost:8000/health

# 4. Acessar monitor
open http://localhost:8000/monitor/
```

## 📡 Webhooks

### Configuração

1. **GitHub Webhook**
   ```bash
   # Defina o secret no .env
   GITHUB_WEBHOOK_SECRET=seu_secret_seguro_aqui
   
   # Configure no GitHub:
   # Settings > Webhooks > Add webhook
   # URL: https://seu-dominio.com/webhook/github
   # Content-Type: application/json
   # Secret: mesmo valor do .env
   ```

2. **Teste Local com ngrok**
   ```bash
   # Terminal 1: API
   python run_api.py --reload
   
   # Terminal 2: ngrok
   ngrok http 8000
   
   # Use a URL HTTPS do ngrok no GitHub
   ```

### Endpoints Disponíveis

- `POST /webhook/github` - GitHub events (PRs, Issues, Commits)
- `POST /webhook/slack` - Slack messages
- `POST /webhook/discord` - Discord messages
- `POST /webhook/custom` - Generic webhook

### Exemplo de Uso

```python
# GitHub PR
curl -X POST http://localhost:8000/webhook/github \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=..." \
  -d '{
    "action": "opened",
    "pull_request": {
      "title": "New feature",
      "body": "This PR adds..."
    }
  }'

# Custom webhook
curl -X POST http://localhost:8000/webhook/custom \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Analyze this text",
    "plugin": "sentiment_analyzer"
  }'
```

## 🐳 Docker

### Dockerfile Multi-stage

- **Stage 1**: Builder com dependências de compilação
- **Stage 2**: Runtime otimizado (~200MB)
- **Segurança**: Usuário não-root
- **Health check**: Integrado

### Docker Compose Profiles

```bash
# Básico (apenas API)
docker-compose up -d

# Com Nginx (produção)
docker-compose --profile production up -d

# Com Redis (cache distribuído)
docker-compose --profile scale up -d

# Com monitoramento completo
docker-compose --profile monitoring up -d
```

### Volumes

- `./cache:/app/cache` - Cache persistente
- `./output:/app/output` - Arquivos gerados
- `./plugins:/app/plugins:ro` - Plugins (read-only)

## 📊 Monitor em Tempo Real

### Características

- **Zero dependências**: HTML/CSS/JS puro
- **Server-Sent Events**: Atualizações em tempo real
- **Gráficos ao vivo**: Canvas API nativo
- **Métricas completas**: RPM, erros, webhooks, etc.

### Acessar

```bash
# Dashboard visual
open http://localhost:8000/monitor/

# Stream de eventos (SSE)
curl http://localhost:8000/monitor/stream
```

### Métricas Disponíveis

- Total de requests
- Requests por minuto (gráfico ao vivo)
- Conexões ativas
- Uptime do servidor
- Uso por plugin
- Atividade de webhooks
- Erros (com último erro)

## 🔧 Nginx (Produção)

### Recursos

- **SSL/TLS**: Configurado para HTTPS
- **Rate limiting**: APIs e webhooks
- **Load balancing**: Least connections
- **Compressão**: Gzip habilitado
- **Headers de segurança**: CSP, X-Frame-Options, etc.
- **SSE Support**: Para monitor em tempo real

### Configurar SSL

```bash
# Certificados em ssl/
mkdir ssl
cp seu-certificado.pem ssl/cert.pem
cp sua-chave.pem ssl/key.pem

# Ou com Let's Encrypt
docker run -it --rm \
  -v $(pwd)/ssl:/etc/letsencrypt \
  certbot/certbot certonly \
  --standalone \
  -d seu-dominio.com
```

## 🧪 Testes de Infraestrutura

### Executar Todos os Testes

```bash
python test_infrastructure.py
```

### Opções

```bash
# Pular testes Docker (mais rápido)
python test_infrastructure.py --skip-docker

# Não limpar recursos após testes
python test_infrastructure.py --no-cleanup
```

### O que é Testado

1. ✅ Docker build funciona
2. ✅ Docker compose sobe serviços
3. ✅ Todos os endpoints respondem
4. ✅ Webhooks processam corretamente
5. ✅ Monitor stream funciona
6. ✅ Upload de arquivos
7. ✅ Pipelines executam

## 📈 Monitoramento Avançado

### Prometheus + Grafana (Opcional)

```bash
# Ativar stack de monitoramento
docker-compose --profile monitoring up -d

# Acessar
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### Métricas Prometheus

- `qualia_requests_total`
- `qualia_request_duration_seconds`
- `qualia_active_connections`
- `qualia_plugin_usage`

## 🚀 Deploy Rápido

### AWS EC2

```bash
# No servidor EC2
sudo yum install docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Deploy
git clone <repo>
cd qualia-core
docker-compose --profile production up -d
```

### Heroku

```bash
heroku create meu-qualia
heroku config:set GITHUB_WEBHOOK_SECRET=xxx
git push heroku main
```

### Google Cloud Run

```bash
gcloud builds submit --tag gcr.io/PROJECT/qualia
gcloud run deploy --image gcr.io/PROJECT/qualia
```

## 🔐 Segurança

### Checklist

- [ ] Secrets configurados no .env
- [ ] HTTPS habilitado em produção
- [ ] Rate limiting configurado
- [ ] CORS restrito a origins específicos
- [ ] Headers de segurança no Nginx
- [ ] Usuário não-root no Docker

### Variáveis Sensíveis

```bash
# Nunca commitar!
GITHUB_WEBHOOK_SECRET=...
SLACK_SIGNING_SECRET=...
GRAFANA_PASSWORD=...
```

## 📝 Troubleshooting

### Webhook não funciona

1. Verificar secret está correto
2. Testar com ngrok primeiro
3. Ver logs: `docker-compose logs -f qualia-api | grep webhook`

### Monitor não atualiza

1. Verificar SSE não está sendo bloqueado
2. Nginx precisa de headers especiais para SSE
3. Firewall/proxy pode bloquear conexões longas

### Docker build falha

1. Verificar espaço em disco
2. Limpar cache: `docker system prune -a`
3. Build sem cache: `docker build --no-cache .`

---

**Status**: ✅ Infraestrutura completa e testada!

Agora o Qualia Core tem:
- 🔄 Webhooks para integrações
- 🐳 Docker para deploy fácil  
- 📊 Monitor em tempo real
- 🚀 Pronto para produção!