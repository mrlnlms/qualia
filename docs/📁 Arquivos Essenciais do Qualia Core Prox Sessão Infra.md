# 📁 Arquivos Essenciais do Qualia Core

## 🎯 Arquivos CRÍTICOS (onde estão as pegadinhas)

### 1. `qualia/core/__init__.py`
**Por que importante**: Define as assinaturas EXATAS das funções
```python
# ATENÇÃO: 
# execute_plugin(plugin_id, document: Document, config, context)
# execute_pipeline(pipeline_config: PipelineConfig, document: Document)
# add_document retorna Document objeto, não string!
```

### 2. `qualia/api/__init__.py` 
**Por que importante**: Onde acontecem as conversões de tipos
```python
# Linha ~336: Pipeline corrigido
# Imports importantes: PipelineConfig, PipelineStep
# Document vs doc.id já resolvido
```

### 3. `test_final_complete.py`
**Por que importante**: Valida se tudo está funcionando
```bash
# SEMPRE rodar antes de mudanças grandes:
python test_final_complete.py
# Deve mostrar 9/9 passando
```

## ⚠️ Armadilhas Já Resolvidas (NÃO MEXER)

### 1. Document vs String
- `execute_plugin` quer Document objeto ✅
- `execute_pipeline` quer doc.id string ❌ ERRADO! Quer Document também!
- Já está corrigido, não mudar

### 2. PipelineConfig não é dict
- Tem que criar objetos PipelineConfig e PipelineStep
- Não pode passar dict direto
- Já está corrigido na API

### 3. Imports condicionais
```python
if HAS_EXTENSIONS:
    # Tudo relacionado deve estar DENTRO do if
    from qualia.api.webhooks import ...
    use_webhook()  # ✅ Dentro do escopo
```

## 📝 Scripts Úteis para Debug

### Ver assinatura de função:
```bash
grep -A5 "def nome_da_funcao" qualia/core/__init__.py
```

### Testar endpoint específico:
```bash
curl -X POST http://localhost:8000/analyze/word_frequency \
  -H "Content-Type: application/json" \
  -d '{"text": "teste"}'
```

### Ver tipos de um objeto:
```python
# test_debug.py
from qualia.core import QualiaCore, Document
doc = core.add_document("test", "texto")
print(f"Type: {type(doc)}")
print(f"Has id: {hasattr(doc, 'id')}")
```

## 🔄 Workflow Recomendado

1. **ANTES de qualquer mudança**:
   ```bash
   python test_final_complete.py  # Garantir 9/9
   git status                     # Ver o que mudou
   ```

2. **Durante desenvolvimento**:
   ```bash
   # Terminal 1: API rodando
   python run_api.py --reload
   
   # Terminal 2: Testes
   python test_individual.py
   ```

3. **Após mudanças**:
   ```bash
   python test_final_complete.py  # Deve continuar 9/9
   git diff                       # Revisar mudanças
   ```

## 🚫 O que NÃO FAZER

1. **NÃO assumir tipos** - Sempre verificar com grep/print
2. **NÃO criar scripts gigantes** - Testar incrementalmente  
3. **NÃO refatorar working code** - Se funciona, não toque
4. **NÃO ignorar erros** - Ler a mensagem completa primeiro

## ✅ Checklist para Nova Feature

- [ ] Rodar testes antes (9/9 passando?)
- [ ] Verificar assinaturas no core
- [ ] Implementar incrementalmente
- [ ] Testar cada parte isolada
- [ ] Rodar testes depois (ainda 9/9?)
- [ ] Commitar com mensagem clara

## 📊 Estado Atual Confirmado

```python
# FUNCIONANDO 100%:
- Core engine ✅
- 6 Plugins ✅
- 13 comandos CLI ✅
- 11+ endpoints API ✅
- Webhooks ✅
- Monitor ✅
- Docker ✅
- Todos os testes ✅
```

## 🎯 Para Próxima Sessão

Se for implementar infraestrutura grátis:
1. Focar em Sentry primeiro (máximo valor, mínimo esforço)
2. GitHub Actions básico (só rodar testes)
3. Testar uma coisa por vez
4. Não overengineer

---

**Lembre-se**: O sistema está 100% funcional. Qualquer adição deve melhorar, não complicar!

