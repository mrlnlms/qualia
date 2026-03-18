# Ecosystem Readiness — Design Spec

## Problem

O Qualia é o engine central de um ecossistema com 4 consumers (DeepVoC, Observatório VoC, whats-le, transcript-analyser). Cada um tem peças de análise que deveriam ser plugins genéricos do Qualia — embeddings, clustering, sentimento com transformers, topic modeling, parsing de WhatsApp, etc.

Dois blockers impedem a migração orgânica:

1. **Colisão de `provides`** — Dois plugins que declaram o mesmo campo (ex: `sentiment_textblob` e `sentiment_roberta` ambos com `provides=["sentiment_score"]`) causam `ValueError` no startup. Isso impede ter plugins alternativos pro mesmo tipo de análise.

2. **Sem extra `[ml]`** — Não existe grupo de dependências pra PyTorch, transformers, sentence-transformers. Plugins de ML pesado não têm como declarar deps.

## Contexto

O cenário de uso real: no Workflow do frontend, o usuário arrasta 5 blocos de sentiment analyzer (TextBlob, RoBERTa, DeBERTa, etc.) conectados ao mesmo texto, cada um gera `sentiment_score`, e depois conecta todos a um único visualizer que plota os 5 resultados comparativamente.

**O consumer sempre escolhe explicitamente qual plugin rodar.** Não existe cenário de resolução automática ambígua na prática — o pipeline é montado pelo usuário, não inferido pelo engine.

## Mudanças

### 1. Relaxar colisão de `provides` no DependencyResolver

**Arquivo:** `qualia/core/resolver.py:36-42`

**Antes:**
```python
for field_name in metadata.provides:
    if field_name in self._provides_map:
        existing = self._provides_map[field_name]
        raise ValueError(
            f"Colisão de provides: campo '{field_name}' fornecido por "
            f"'{existing}' e '{plugin_id}'. Renomeie um deles."
        )
    self._provides_map[field_name] = plugin_id
```

**Depois — `_provides_map` sempre armazena `List[str]`** (elimina isinstance guards):

Tipo muda de `Dict[str, str]` pra `Dict[str, List[str]]`.

**`__init__` (linha 29):**
```python
self._provides_map: Dict[str, List[str]] = {}  # field_name -> [plugin_ids]
```

**`add_plugin()` — substituir linhas 35-42:**
```python
for field_name in metadata.provides:
    if field_name not in self._provides_map:
        self._provides_map[field_name] = []
    self._provides_map[field_name].append(plugin_id)
    if len(self._provides_map[field_name]) > 1:
        logger.info(
            "Campo '%s' fornecido por múltiplos plugins: %s",
            field_name, self._provides_map[field_name],
        )
```

**`build_graph()` — substituir linhas 57-58:**
```python
elif req in self._provides_map:
    providers = self._provides_map[req]
    if len(providers) == 1:
        resolved_deps.add(providers[0])
    else:
        # Múltiplos providers — consumer deve escolher explicitamente
        logger.warning(
            "Plugin '%s' requires '%s' que é provido por %s. "
            "Use o plugin ID diretamente no requires ou especifique no pipeline.",
            plugin_id, req, providers,
        )
```

**`resolve_provider()` — substituir linhas 66-68:**
```python
def resolve_provider(self, field_name: str) -> Optional[str]:
    """Retorna o plugin_id que provê um campo, ou None se ambíguo/inexistente."""
    providers = self._provides_map.get(field_name, [])
    return providers[0] if len(providers) == 1 else None

def list_providers(self, field_name: str) -> List[str]:
    """Retorna todos os plugin_ids que provêm um campo."""
    return self._provides_map.get(field_name, [])
```

### 2. Adicionar extra `[ml]` no pyproject.toml

**Arquivo:** `pyproject.toml` (seção `[project.optional-dependencies]`)

Adicionar entre `nlp` e `transcription`:

```toml
ml = [
    "torch>=2.0.0",
    "transformers>=4.30.0",
    "sentence-transformers>=2.2.0",
    "scikit-learn>=1.3.0",
    "umap-learn>=0.5.0",
    "hdbscan>=0.8.30",
]
```

Notas:
- `scikit-learn>=1.3.0` inclui `sklearn.cluster.HDBSCAN` nativo — `hdbscan` como pacote separado pode ser removido se consumers usarem o wrapper do sklearn
- `umap-learn` puxa `numba` (compilador JIT, ~100MB) — aceitável pra extra `[ml]` mas worth notar
- Plugins que dependem dessas libs fazem `import` dentro do `_analyze_impl` (lazy), não no top-level — quem não instala `[ml]` não vê ImportError

Atualizar `all`:

```toml
all = [
    "qualia-core[api,viz,nlp,ml,transcription]",
]
```

### 3. Nenhum plugin novo

Os plugins vêm organicamente quando cada projeto do ecossistema precisar. O `docs/ECOSYSTEM_MAP.md` serve como catálogo de referência.

## Arquivos Afetados

- `qualia/core/resolver.py:36-42, 57-58, 66-68` — relaxar colisão, lidar com lista de providers
- `pyproject.toml:52` — adicionar extra `[ml]`
- `tests/test_core.py` — atualizar teste de colisão (era ValueError, agora é startup ok + lista)
- `tests/test_cache_deps.py` — atualizar: `_provides_map` agora é `Dict[str, List[str]]`, ajustar assertivas
- `CLAUDE.md` — documentar extra `[ml]` e nova regra de provides
- `docs/TECHNICAL_STATE.md` — atualizar seção de provides

## Testes

**Resolver unitários:**
- Dois plugins com mesmo provides → startup ok, `_provides_map[field]` é lista de 2
- Três plugins com mesmo provides → lista de 3
- `build_graph()` com requires ambíguo (2 providers) → warning no log, dep não adicionada ao grafo
- `build_graph()` com requires para provider único → funciona como antes (sem regressão)
- `resolve_provider()` com campo ambíguo → retorna None
- `resolve_provider()` com campo único → retorna plugin_id
- `list_providers()` com campo ambíguo → retorna lista completa
- `list_providers()` com campo inexistente → retorna []

**Integração engine:**
- `discover_plugins()` com dois plugins reais que declaram mesmo provides → engine carrega ambos sem erro
- Chamar cada um via API → ambos respondem independentemente
- Pipeline com step explícito → funciona sem ambiguidade

**Regressão:**
- Todos os testes existentes de resolver continuam passando
- Testes de provides validation no engine (warning se resultado não contém campo) inalterados

## O Que NÃO Muda

- Interface dos plugins (IPlugin, IAnalyzerPlugin, IVisualizerPlugin, IDocumentPlugin)
- BaseClass de nenhum tipo
- API routes
- Frontend
- CLI
- Contrato de provides (engine ainda valida que resultado contém campos declarados)
- Resolução automática quando provider é único (sem regressão)
