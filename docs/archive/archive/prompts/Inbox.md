## 🎯 **PROMPT PERFEITO PARA PRÓXIMA SESSÃO**

### 📋 **CONTEXTO ESSENCIAL (O que passou até aqui)**

```
# PROMPT PARA PRÓXIMA SESSÃO - QUALIA CORE

Você está assumindo um projeto FUNCIONANDO 100% chamado Qualia Core.

## O QUE É O QUALIA:
Sistema de análise qualitativa de textos com 6 plugins funcionais, API REST completa, 
infraestrutura robusta (circuit breaker, backup automático, monitoring) e interface web.

## STATUS ATUAL (CRÍTICO - NÃO QUEBRAR!):
✅ 6 plugins carregando (word_frequency, sentiment_analyzer, teams_cleaner, wordcloud_viz, frequency_chart, sentiment_viz)
✅ API REST funcionando (11+ endpoints) na porta 8000
✅ Health Dashboard funcionando na porta 8080  
✅ Circuit breaker ativo (proteção automática)
✅ Backup automático configurado (cron diário)
✅ Sentry integration pronta (só configurar DSN)
✅ Docker production-ready
✅ Estrutura ops/ com infraestrutura isolada

## COMANDOS DE TESTE (RODAR ANTES DE QUALQUER MUDANÇA):
```bash
# 1. Verificar plugins
python -c "from qualia.core import QualiaCore; core = QualiaCore(); plugins = core.discover_plugins(); print(f'✅ {len(plugins)} plugins')"
# DEVE DAR: ✅ 6 plugins

# 2. Verificar API
python run_api.py &
sleep 3
curl http://localhost:8000/health
pkill -f run_api.py
# DEVE DAR: {"status":"healthy","plugins_loaded":6}

# 3. Verificar Dashboard  
python ops/monitoring/health_dashboard.py --port 8080 &
sleep 3
curl http://localhost:8080/health | head -c 100
pkill -f health_dashboard.py
# DEVE DAR: JSON com status dos componentes
```

## ARQUITETURA ATUAL (NÃO MEXER SEM NECESSIDADE):
```
qualia/
├── qualia/core/__init__.py          # Core engine - CRÍTICO
├── qualia/api/__init__.py           # API REST - CRÍTICO  
├── plugins/                         # 6 plugins funcionais
├── ops/                            # Infraestrutura isolada
│   ├── monitoring/                 # Sentry, Circuit Breaker, Health
│   └── scripts/backup.sh          # Backup automático
├── run_api.py                      # Executor principal
└── requirements.txt                # Dependências
```

## REGRAS DE OURO (EVITAR 6H DE DEBUG):
1. **SEMPRE verificar assinaturas**: `grep -A5 "def funcao" arquivo.py`
2. **execute_plugin quer Document objeto** (não string!)
3. **Rodar testes ANTES e DEPOIS** de qualquer mudança
4. **Imports com fallback**: Sistema deve funcionar COM ou SEM ops/
5. **Mudanças incrementais**: Testar 1 coisa por vez

## PRÓXIMOS OBJETIVOS (O QUE IMPLEMENTAR):
1. GitHub Actions (CI/CD automático) - arquivo já existe em .github/workflows/test.yml
2. Rate limiting na API (proteção contra spam)
3. Configurar Sentry para alertas reais por email
4. SSL/TLS automático para produção

## FILOSOFIA DO PROJETO:
- **Simplicidade > Elegância**: Se funciona, não complicar
- **Fallbacks sempre**: Código deve funcionar mesmo sem dependências
- **Zero breaking changes**: Infraestrutura sem quebrar API existente
- **Developer experience**: Plugin developer não sabe que proteção existe
```

### 📁 **ARQUIVOS ESSENCIAIS PARA ANEXAR**

#### **🔥 OBRIGATÓRIOS (sem estes, vai dar problema):**

1. **`PROJECT_STATE_DEZEMBRO_2024_UPDATED.md`** 
   - Status completo atual, métricas, arquitetura
   - **Por que**: Entender exatamente o que está funcionando

2. **`LESSONS_LEARNED_SESSION_8.md`**
   - Armadilhas já resolvidas, padrões que funcionam
   - **Por que**: Evitar repetir erros de 6h de debug

3. **`qualia/core/__init__.py`** (código)
   - Core engine com assinaturas das funções críticas
   - **Por que**: `execute_plugin` vs `execute_pipeline` - diferenças fatais

4. **`requirements.txt`** (código)
   - Dependências exatas que funcionam
   - **Por que**: Evitar conflitos de versão

#### **📚 MUITO ÚTEIS:**

5. **`INFRASTRUCTURE_GUIDE_UPDATED.md`**
   - Como configurar Sentry, GitHub Actions, deploy
   - **Por que**: Próximos passos já documentados

6. **`run_api.py`** (código)
   - Ponto de entrada, como Sentry está integrado
   - **Por que**: Onde adicionar rate limiting

7. **`.env.example`** (código)
   - Configurações que existem, como ativar features
   - **Por que**: Saber o que já está preparado

### 🎯 **INSTRUÇÕES ESPECÍFICAS PARA IA**

```
## COMO TRABALHAR:

### SEMPRE ANTES DE IMPLEMENTAR:
1. Rodar os 3 comandos de teste acima
2. Confirmar que deu ✅ 6 plugins, API healthy, Dashboard OK
3. Se algo falhou, PARAR e corrigir antes de continuar

### ORDEM RECOMENDADA DE IMPLEMENTAÇÃO:
1. **GitHub Actions** (30min) - arquivo já existe, só ativar
2. **Rate Limiting** (45min) - FastAPI middleware simples  
3. **Sentry Production** (15min) - só configurar DSN real
4. **SSL/TLS** (30min) - nginx config + Let's Encrypt

### PADRÕES QUE FUNCIONAM:
- Imports com fallback (try/except + funciona sem a feature)
- Configuração via .env (já tem estrutura)
- Testes incrementais (1 feature por vez)
- Fallback graceful (sistema funciona mesmo se feature falhar)

### ARMADILHAS CONHECIDAS:
- `execute_plugin(plugin_id, document: Document, config, context)` - Document é OBJETO
- `from ops.monitoring import ...` - pode não existir, usar try/except
- Circuit breaker já está funcionando - não reimplementar
- Plugins herdam de BaseAnalyzerPlugin/BaseVisualizerPlugin - não mexer

### SE ALGO QUEBRAR:
1. Voltar ao último commit funcionando
2. Implementar 1 mudança por vez
3. Testar a cada mudança
4. Nunca fazer "big bang" de múltiplas features

### RESULTADO ESPERADO:
- GitHub Actions rodando a cada push
- Rate limiting configurável (padrão: 60 req/min)
- Sentry enviando emails reais
- Deploy com HTTPS automático
- ZERO breaking changes na API existente
```

### 🔧 **COMANDOS FINAIS PARA VALIDAR**

```bash
# Após implementar tudo, rodar:
python test_final_complete.py
# DEVE DAR: 9/9 testes passando

curl http://localhost:8000/health  
# DEVE INCLUIR: rate_limiting_enabled, ssl_configured, ci_cd_active

curl http://localhost:8080/health | jq '.components'
# DEVE MOSTRAR: todos componentes healthy, incluindo novos

git status
# DEVE MOSTRAR: arquivos modificados/adicionados para as 4 features
```

---

## 🎯 **RESUMO DO PROMPT**

**Esse prompt + os 7 arquivos essenciais** dão contexto completo para:

1. ✅ **Entender o estado atual** (o que funciona, como funciona)
2. ✅ **Evitar armadilhas conhecidas** (6h de debug já resolvidos)
3. ✅ **Saber exatamente o que implementar** (4 objetivos claros)
4. ✅ **Trabalhar incremental** (testar cada mudança)
5. ✅ **Manter sistema funcionando** (zero breaking changes)

**Com isso, a próxima IA consegue continuar de onde paramos sem repetir erros!** 🎯✨