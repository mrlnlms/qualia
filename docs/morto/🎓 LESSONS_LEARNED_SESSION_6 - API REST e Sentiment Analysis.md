# 🎓 Lições Aprendidas - Sessão 6: API REST e Sentiment Analysis

## 1. FastAPI: Produtividade Instantânea

### O Que Funcionou
```python
# Em menos de 300 linhas, temos:
- 11 endpoints funcionais
- Documentação automática
- Validação de tipos
- Upload de arquivos
- CORS configurado
```

### Aprendizado Chave
FastAPI + Pydantic = **documentação que se escreve sozinha**. O Swagger UI em `/docs` é gerado automaticamente e permite testar a API direto do browser.

## 2. Plugin Auto-Discovery na API

### O Problema
Como fazer a API descobrir novos plugins automaticamente?

### A Solução
```python
# Na inicialização da API
core = QualiaCore()
core.discover_plugins()  # Mesma mágica da CLI!

# Endpoints genéricos
POST /analyze/{plugin_id}  # Funciona para QUALQUER analyzer
```

**Lição**: Reutilizar a arquitetura bare metal existente = zero código extra.

## 3. Debugging de Import Errors

### O Erro Clássico
```python
ImportError: cannot import name 'SentimentAnalyzer' from 'plugins.sentiment_analyzer'
```

### Script de Debug que Salvou
```python
# debug_sentiment.py
try:
    import plugins.sentiment_analyzer
    print("✓ Módulo importado!")
    print("Conteúdo:", dir(plugins.sentiment_analyzer))
except Exception as e:
    print(f"✗ Erro: {e}")
```

**Lição**: Sempre criar scripts de debug para problemas de import. Economiza horas!

## 4. Cuidado com Copy/Paste

### O Bug
```bash
# sentiment_analyzer/__init__.py continha:
class SentimentVisualizer(BaseVisualizerPlugin):  # ERRADO!
```

### A Descoberta
```bash
grep "class" plugins/sentiment_analyzer/__init__.py
# Revelou o problema imediatamente
```

**Lição**: `grep` e `head` são seus amigos para debug rápido.

## 5. API Attributes vs Registry

### Erro Inicial
```python
# API tentava acessar
core.plugin_registry  # Não existe!

# Correto é
core.plugins  # Dict de plugins
```

### Fix Simples
Buscar e substituir em toda a API: `plugin_registry` → `plugins`

**Lição**: Sempre verificar os nomes exatos dos atributos do Core.

## 6. TextBlob e Português

### Descoberta
TextBlob retorna polaridade 0.0 para muitos textos em português.

### Workarounds
1. Usar textos com palavras mais "carregadas"
2. Considerar `textblob-pt` para melhor suporte
3. Implementar dicionário próprio de sentimentos PT-BR

**Lição**: Bibliotecas de NLP nem sempre são multilíngues de verdade.

## 7. Swagger não Mostra Plugins Individualmente

### Confusão Inicial
"Onde está o endpoint `/analyze/sentiment_analyzer`?"

### Esclarecimento
- Swagger mostra endpoints **genéricos**: `/analyze/{plugin_id}`
- Você passa o ID do plugin como **parâmetro**
- Isso é by design - mantém a API extensível

**Lição**: APIs RESTful favorecem endpoints genéricos com parâmetros.

## 8. Matplotlib vs Plotly em Subplots

### Bug Sutil
```python
# Plotly subplots
fig.add_hline(row=2, col=2)  # Não funciona!

# Solução
fig.add_shape(type="line", row=2, col=2)  # Funciona!
```

**Lição**: Plotly tem quirks em subplots. Sempre checar a documentação.

## 9. Shell Escaping no Terminal

### Problema
```bash
echo "Texto com aspas!" > arquivo.txt
# Shell espera fechamento de aspas
```

### Solução
```bash
echo 'Texto com aspas!' > arquivo.txt  # Aspas simples
# ou
cat > arquivo.txt << EOF
Texto com aspas!
EOF
```

**Lição**: Use heredocs ou aspas simples para textos complexos.

## 10. Desenvolvimento com Hot Reload

### Fluxo Produtivo
```bash
# Terminal 1
python run_api.py --reload  # API recarrega ao salvar

# Terminal 2
# Editar plugins - mudanças aplicadas instantaneamente!
```

**Lição**: `--reload` é essencial para desenvolvimento rápido.

## Métricas da Sessão

- **Tempo total**: ~3 horas
- **Linhas de código**: +2000
- **Novos arquivos**: 6
- **Bugs resolvidos**: 5
- **Funcionalidades novas**: API completa + 2 plugins

## Conclusão

A Sessão 6 transformou o Qualia em uma plataforma completa:
- **CLI** ✅ 
- **Menu Interativo** ✅
- **API REST** ✅ (NOVO!)
- **Documentação Automática** ✅ (NOVO!)

A combinação FastAPI + arquitetura modular do Qualia resultou em uma API que se auto-documenta e auto-descobre plugins. O próximo passo natural são webhooks para integração com ferramentas externas.

## Top 3 Insights

1. **Reutilizar > Reescrever**: A API reutilizou 100% do Core
2. **Debug Scripts Salvam Tempo**: Criar scripts específicos para debug
3. **Documentação Automática é Mágica**: FastAPI + Swagger = ❤️

---

*"The best API is the one that writes its own documentation"* 🚀