# 🏗️ Qualia Core - Infrastructure Guide

Este documento descreve a infraestrutura implementada e como usar cada componente.

## 📊 Status da Infraestrutura

| Componente | Status | Custo | Complexidade |
|------------|--------|-------|--------------|
| API REST | ✅ 100% Funcional | Grátis | Baixa |
| Webhooks | ✅ Funcionando | Grátis | Baixa |
| Monitor | ✅ Implementado | Grátis | Baixa |
| Docker | ✅ Pronto | Grátis | Média |
| Deploy | ✅ Configurado | $5-10/mês* | Média |

*Somente se publicar online

## 🚀 Quick Start Local

```bash
# 1. Clonar e instalar
git clone <repo>
cd qualia
pip install -r requirements.txt
pip install -e .

# 2. Rodar API com monitor
python run_api.py --reload

# 3. Acessar
# API: http://localhost:8000/docs
# Monitor: http://localhost:8000/monitor/
```

## 📡 Webhooks - Integração Externa

### Webhook Genérico (Funcionando!)

```bash
# Recebe qualquer texto para análise
curl -X POST http://localhost:8000/webhook/custom \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Analisar este texto!",
    "plugin": "sentiment_analyzer"
  }'

# Resposta
{
  "status": "success",
  "plugin": "sentiment_analyzer",
  "result": {
    "sentiment_label": "positivo",
    "polarity": 0.8
  }
}
```

### Estatísticas de Webhooks

```bash
# Ver quantos webhooks foram processados
curl http://localhost:8000/webhook/stats

# Resposta
{
  "status": "ok",
  "stats": {
    "generic": {
      "total_received": 42,
      "total_processed": 41,
      "total_errors": 1,
      "last_processed": "2024-12-11T20:30:00"
    }
  }
}
```

### Estrutura para Futuros Webhooks

```python
# Já preparado para:
- GitHub (PRs, Issues, Commits)
- Slack (Mensagens)
- Discord (Comandos)
# Implementação básica existe, falta apenas handlers específicos
```

## 📊 Monitor em Tempo Real

### Características
- **Zero dependências**: HTML puro + JavaScript vanilla
- **Atualização ao vivo**: Server-Sent Events (SSE)
- **Gráficos nativos**: Canvas API (sem bibliotecas)
- **Métricas úteis**: Requests/min, plugins mais usados, erros

### Acessar Monitor

```bash
# Dashboard visual
http://localhost:8000/monitor/

# Stream de dados (para integração)
curl http://localhost:8000/monitor/stream
```

### Métricas Disponíveis
```javascript
{
  "timestamp": "2024-12-11T20:30:00",
  "metrics": {
    "requests_total": 1547,
    "requests_per_minute": 12.5,
    "active_connections": 3,
    "plugin_usage": {
      "sentiment_analyzer": 847,
      "word_frequency": 512,
      "teams_cleaner": 188
    },
    "webhook_stats": {
      "total": 42,
      "success": 41,
      "errors": 1
    },
    "errors_total": 7,
    "last_error": "TextBlob initialization failed",
    "uptime_seconds": 3600
  }
}
```

## 🐳 Docker - Deploy Simplificado

### Desenvolvimento Local
```bash
# Build e rodar
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar
docker-compose down
```

### Produção (Quando decidir publicar)
```bash
# Com Nginx e SSL
docker-compose --profile production up -d

# Escalar para múltiplos workers
docker-compose up -d --scale qualia-api=4
```

### Estrutura Docker
```yaml
# docker-compose.yml simplificado
services:
  qualia-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - WORKERS=4
    volumes:
      - ./output:/app/output
      - ./cache:/app/cache
```

## 🚀 Deploy (Quando Estiver Pronto)

### Opção 1: VPS Simples ($5/mês)
```bash
# DigitalOcean, Hetzner, Linode, etc
ssh root@seu-servidor
git clone <repo>
cd qualia
docker-compose up -d
```

### Opção 2: AWS Free Tier (1 ano grátis)
```bash
# EC2 t2.micro
# Mesmo processo do VPS
```

### Opção 3: Heroku (Grátis com limitações)
```bash
heroku create meu-qualia
git push heroku main
```

## 🔧 Configuração (.env)

```bash
# Copiar template
cp .env.example .env

# Variáveis principais
QUALIA_API_WORKERS=4           # Número de workers
QUALIA_API_HOST=0.0.0.0       # Host (não mudar)
QUALIA_API_PORT=8000          # Porta

# Webhooks (opcional)
GITHUB_WEBHOOK_SECRET=xxx      # Se usar GitHub
SLACK_SIGNING_SECRET=xxx       # Se usar Slack

# Produção (quando publicar)
CORS_ORIGINS=["https://seu-site.com"]
LOG_LEVEL=INFO
```

## 🧪 Testes de Infraestrutura

### Teste Completo (9/9 passando!)
```bash
python test_final_complete.py

# Saída esperada:
✅ API Health
✅ API Plugins
✅ Webhook Custom
✅ Webhook Stats
✅ Monitor Dashboard
✅ Monitor Stream
✅ Análise Word Frequency
✅ Pipeline
✅ Webhook com Sentiment
```

### Teste Individual
```bash
# Testar só webhooks
python test_individual.py

# Testar só pipeline
curl -X POST http://localhost:8000/pipeline \
  -d '{"text": "teste", "steps": [{"plugin_id": "word_frequency"}]}'
```

## 🛡️ Segurança Básica

### Já Implementado
- ✅ Validação de entrada (Pydantic)
- ✅ CORS configurável
- ✅ Error handling sem exposição
- ✅ Webhook signature (HMAC)
- ✅ Headers de segurança básicos

### Para Adicionar (Quando Publicar)
- [ ] HTTPS (certificado SSL)
- [ ] Rate limiting
- [ ] API keys
- [ ] Firewall básico

## 📈 Próximos Passos de Infra

### 1. Agora (Grátis, 2h)
- [ ] Sentry.io - Alertas de erro por email
- [ ] GitHub Actions - Testes automáticos
- [ ] Backup local - Script cron

### 2. Quando Publicar ($5-10/mês)
- [ ] VPS básico
- [ ] Domínio + SSL
- [ ] Backup S3/B2

### 3. Se Escalar (Depois)
- [ ] Redis cache
- [ ] Load balancer
- [ ] Monitoring completo

## 🔍 Troubleshooting

### "Webhook não funciona"
```bash
# 1. Verificar que API está rodando
curl http://localhost:8000/health

# 2. Testar webhook direto
curl -X POST http://localhost:8000/webhook/custom \
  -d '{"text": "teste"}'

# 3. Ver logs
docker-compose logs | grep webhook
```

### "Monitor não atualiza"
- Verificar se navegador suporta SSE
- Tentar outro navegador
- Ver console do browser (F12)

### "Docker não builda"
```bash
# Limpar cache
docker system prune -a

# Build sem cache
docker build --no-cache .
```

---

**Status Final**: Infraestrutura 100% funcional, testada e documentada!

O sistema está pronto para:
- ✅ Uso local imediato
- ✅ Integrações via webhooks
- ✅ Monitoramento em tempo real
- ✅ Deploy quando decidir publicar