# 🚀 Qualia Core - Guia de Deploy

Este guia cobre diferentes opções de deploy do Qualia Core.

## 📋 Pré-requisitos

- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM mínimo
- 10GB espaço em disco

## 🏃 Quick Start (Desenvolvimento)

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/qualia-core.git
cd qualia-core

# 2. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# 3. Build e execute
docker-compose up -d

# 4. Verifique se está rodando
curl http://localhost:8000/health
```

Acesse:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## 🔧 Configurações

### Variáveis de Ambiente Importantes

```bash
# API
QUALIA_API_PORT=8000
QUALIA_API_WORKERS=4

# Webhooks (opcional)
GITHUB_WEBHOOK_SECRET=seu_secret_aqui
SLACK_SIGNING_SECRET=seu_secret_aqui

# Monitoramento
ENABLE_MONITORING=true
```

### Profiles Docker Compose

```bash
# Básico (apenas API)
docker-compose up -d

# Com Nginx (produção)
docker-compose --profile production up -d

# Com Redis (cache distribuído)
docker-compose --profile scale up -d

# Com monitoramento completo
docker-compose --profile monitoring up -d

# Tudo
docker-compose --profile production --profile scale --profile monitoring up -d
```

## 🌐 Deploy em Produção

### 1. AWS EC2 / DigitalOcean

```bash
# No servidor
sudo apt update
sudo apt install docker.io docker-compose

# Clone e configure
git clone https://github.com/seu-usuario/qualia-core.git
cd qualia-core
cp .env.example .env
nano .env  # Configure production values

# SSL/TLS
mkdir ssl
# Copie seus certificados para ssl/cert.pem e ssl/key.pem
# Ou use Let's Encrypt

# Deploy
docker-compose --profile production up -d
```

### 2. Docker Swarm

```bash
# Inicializar swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml qualia

# Escalar
docker service scale qualia_qualia-api=3
```

### 3. Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qualia-core
spec:
  replicas: 3
  selector:
    matchLabels:
      app: qualia-core
  template:
    metadata:
      labels:
        app: qualia-core
    spec:
      containers:
      - name: api
        image: qualia-core:latest
        ports:
        - containerPort: 8000
        env:
        - name: QUALIA_API_WORKERS
          value: "4"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

```bash
# Deploy
kubectl apply -f k8s/
```

### 4. Heroku

```bash
# Criar app
heroku create meu-qualia-core

# Configurar buildpack
heroku buildpacks:set heroku/python

# Deploy
git push heroku main

# Configurar webhooks
heroku config:set GITHUB_WEBHOOK_SECRET=seu_secret
```

### 5. Google Cloud Run

```bash
# Build imagem
gcloud builds submit --tag gcr.io/PROJECT-ID/qualia-core

# Deploy
gcloud run deploy qualia-core \
  --image gcr.io/PROJECT-ID/qualia-core \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 🔒 Segurança

### 1. HTTPS/TLS

Sempre use HTTPS em produção:

```bash
# Let's Encrypt com Certbot
docker run -it --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  certbot/certbot certonly \
  --standalone \
  -d seu-dominio.com
```

### 2. Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Secrets

```bash
# Gerar secrets seguros
python -c "import secrets; print(secrets.token_hex(32))"

# Usar Docker secrets
docker secret create github_webhook_secret secret.txt
```

## 📊 Monitoramento

### Prometheus + Grafana

```bash
# Deploy com monitoramento
docker-compose --profile monitoring up -d

# Acessar
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### Logs

```bash
# Ver logs da API
docker-compose logs -f qualia-api

# Logs estruturados
docker-compose exec qualia-api tail -f /app/logs/api.log
```

### Health Checks

```bash
# Manual
curl http://localhost:8000/health

# Automatizado (cron)
*/5 * * * * curl -f http://localhost:8000/health || alert
```

## 🔄 CI/CD

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build and push
      run: |
        docker build -t ${{ secrets.REGISTRY }}/qualia-core:latest .
        docker push ${{ secrets.REGISTRY }}/qualia-core:latest
    
    - name: Deploy
      run: |
        ssh ${{ secrets.DEPLOY_HOST }} "
          cd /app/qualia-core
          docker-compose pull
          docker-compose up -d
        "
```

## 🚨 Troubleshooting

### API não responde

```bash
# Verificar containers
docker-compose ps

# Ver logs
docker-compose logs qualia-api

# Reiniciar
docker-compose restart qualia-api
```

### Webhooks não funcionam

1. Verifique secrets no .env
2. Teste com ngrok localmente
3. Verifique logs: `docker-compose logs -f qualia-api | grep webhook`

### Performance ruim

```bash
# Aumentar workers
QUALIA_API_WORKERS=8 docker-compose up -d

# Habilitar cache Redis
docker-compose --profile scale up -d
```

## 📈 Escalabilidade

### Horizontal Scaling

```bash
# Docker Compose
docker-compose up -d --scale qualia-api=4

# Kubernetes
kubectl scale deployment qualia-core --replicas=10
```

### Load Balancer

O Nginx já está configurado para load balancing com `least_conn`.

### Cache

Redis está disponível para cache distribuído:

```bash
docker-compose --profile scale up -d
```

## 🔄 Backup

```bash
# Backup dos dados
docker run --rm \
  -v qualia_cache:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/qualia-backup-$(date +%Y%m%d).tar.gz /data

# Restore
docker run --rm \
  -v qualia_cache:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/qualia-backup-20240101.tar.gz -C /
```

## 📞 Suporte

- Issues: https://github.com/seu-usuario/qualia-core/issues
- Docs: http://localhost:8000/docs
- Email: suporte@qualia-core.com

---

**Happy Deploying!** 🚀