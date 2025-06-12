# 🚀 Setup da Infraestrutura Gratuita - Qualia Core

Guia passo-a-passo para implementar monitoramento, alertas e automação **100% grátis**.

## ⏱️ Tempo estimado: 2-3 horas

## 📋 **Pré-requisitos**

✅ Sistema Qualia funcionando (9/9 testes passando)  
✅ Git configurado  
✅ Conta GitHub  
✅ Email válido  

## 🎯 **O que vamos implementar**

1. **Sentry** - Erros por email em 30 segundos
2. **Circuit Breaker** - Proteção automática contra plugins com falha
3. **GitHub Actions** - Testes automáticos a cada push
4. **Backup Automático** - Backup diário às 2AM
5. **Health Dashboard** - Monitoramento visual unificado

---

## 🔥 **1. SENTRY - Monitoramento de Erros (30min)**

### 1.1 Criar conta no Sentry (5min)

```bash
# 1. Acesse https://sentry.io
# 2. Clique "Get Started"
# 3. Crie conta (GitHub login é mais rápido)
# 4. Escolha "Python" como plataforma
# 5. Copie o DSN (algo como: https://abc123@o123.ingest.sentry.io/456)
```

### 1.2 Configurar no projeto (10min)

```bash
# 1. Adicionar dependência
pip install sentry-sdk[fastapi]

# 2. Copiar configuração
cp .env.example .env

# 3. Editar .env e adicionar seu DSN:
# SENTRY_DSN=https://seu-dsn-aqui@sentry.io/projeto
```

### 1.3 Integrar no código (15min)

**⚠️ PERGUNTA**: Preciso mexer no `run_api.py` para adicionar estas 3 linhas?

```python
# No início do run_api.py:
from sentry_config import init_sentry
init_sentry()  # Só isso!
```

Se sim, me mande o arquivo atual ou me diga onde exatamente adicionar.

### 1.4 Testar

```bash
# Executar teste
python sentry_config.py

# Verificar email em 1-2 minutos
# Acessar dashboard: https://sentry.io
```

---

## ⚡ **2. CIRCUIT BREAKER - Proteção Automática (45min)**

### 2.1 Backup dos plugins atuais (5min)

```bash
# Fazer backup antes de mexer nos plugins
cp -r plugins plugins_backup
```

### 2.2 Aplicar nos plugins existentes (40min)

**⚠️ PERGUNTA**: Quais plugins você tem exatamente? Preciso ver a estrutura para aplicar o decorator sem quebrar.

Exemplo de como seria em um plugin:
```python
# plugins/sentiment_analyzer/__init__.py
from circuit_breaker import circuit_breaker

class SentimentAnalyzer(BaseAnalyzerPlugin):
    
    @circuit_breaker(max_failures=5, timeout_seconds=300)
    def _analyze_impl(self, document, config, context):
        # Código original não muda!
        return resultado
```

Me confirme os plugins que tem e eu gero o código exato.

---

## 🔄 **3. GITHUB ACTIONS - CI/CD (30min)**

### 3.1 Criar estrutura (5min)

```bash
# Criar diretório
mkdir -p .github/workflows

# Copiar workflow
# (arquivo test.yml já está pronto!)
```

### 3.2 Adaptar requirements.txt (10min)

**⚠️ PERGUNTA**: Pode me mostrar seu `requirements.txt` atual? Preciso adicionar as dependências dos testes:

```txt
# Dependências novas para testes:
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
httpx>=0.24.0
```

### 3.3 Commit e push (15min)

```bash
git add .
git commit -m "feat: adiciona infraestrutura de monitoramento"
git push

# Em 2-3 minutos, verificar:
# https://github.com/seu-repo/actions
# Deve mostrar testes rodando automaticamente
```

---

## 💾 **4. BACKUP AUTOMÁTICO (30min)**

### 4.1 Configurar script (5min)

```bash
# Dar permissão de execução
chmod +x scripts/backup.sh

# Testar backup manual
./scripts/backup.sh
```

### 4.2 Configurar cron (25min)

```bash
# Editar crontab
crontab -e

# Adicionar linha (backup todo dia às 2AM):
0 2 * * * /caminho/completo/para/scripts/backup.sh cron

# Verificar
crontab -l
```

### 4.3 Testar

```bash
# Forçar backup agora
./scripts/backup.sh

# Verificar se criou arquivo em ./backups/
ls -la backups/
```

---

## 📊 **5. HEALTH DASHBOARD (20min)**

### 5.1 Instalar dependência adicional (5min)

```bash
pip install psutil  # Para monitorar recursos do sistema
```

### 5.2 Executar dashboard (5min)

```bash
# Executar em terminal separado
python health_dashboard.py --port 8080

# Acessar: http://localhost:8080
```

### 5.3 Integrar com API principal (10min)

**⚠️ PERGUNTA**: Quer que o dashboard rode junto com a API principal na porta 8000, ou separado na 8080?

Se junto, preciso mexer no código da API principal.

---

## ✅ **VERIFICAÇÃO FINAL**

Execute cada teste para confirmar que está tudo funcionando:

```bash
# 1. Sentry funcionando?
python -c "from sentry_config import test_sentry; test_sentry()"

# 2. Circuit breaker ativo?
python -c "from circuit_breaker import get_circuit_stats; print(get_circuit_stats())"

# 3. API respondendo?
curl http://localhost:8000/health

# 4. Backup funcionando?
./scripts/backup.sh list

# 5. Dashboard funcionando?
curl http://localhost:8080/health

# 6. Testes passando?
python test_final_complete.py
```

---

## 🎉 **RESULTADO FINAL**

Após setup completo, você terá:

- ✅ **Erro em plugin** → Email em 30 segundos
- ✅ **Plugin falha 5x** → Desabilita automaticamente  
- ✅ **Push no git** → Testes automáticos
- ✅ **Todo dia 2AM** → Backup automático
- ✅ **Dashboard visual** → Status de tudo em tempo real

**Custo total**: R$ 0,00 🎯

---

## 🚨 **PERGUNTAS PARA VOCÊ**

Antes de implementar, preciso saber:

1. **Posso mexer no `run_api.py`** para adicionar 3 linhas do Sentry?
2. **Quais plugins você tem** para aplicar circuit breaker corretamente?
3. **Tem `requirements.txt` atual** para eu adicionar as dependências?
4. **Dashboard junto com API** (porta 8000) ou separado (porta 8080)?

Responda isso e em 2-3 horas está tudo funcionando! 🚀