# Backlog Cleanup Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolver os 8 itens pendentes do backlog — pipeline CLI/API unificado, blocos standalone, eager/lazy explícito, upload size limit, coverage gaps, discovery errors com severidade, e endpoint /plugins/health.

**Architecture:** Tarefas independentes atacadas em sequência do mais simples ao mais complexo. Testes primeiro (TDD), commit após cada tarefa.

**Tech Stack:** Python 3.13+, FastAPI, pytest, Click

---

## Chunk 1: Limpeza rápida (Tasks 1-3)

### Task 1: Remover blocos `if __name__` dos plugins

**Files:**
- Modify: `plugins/analyzers/word_frequency/__init__.py:319-336`
- Modify: `plugins/analyzers/sentiment_analyzer/__init__.py:285-311`
- Modify: `plugins/analyzers/readability_analyzer/__init__.py:169-202`
- Modify: `plugins/documents/teams_cleaner/__init__.py:545-571`

- [ ] **Step 1: Remover bloco standalone do word_frequency**

Deletar tudo a partir da linha com `# ===` e `if __name__` até o final do arquivo em `plugins/analyzers/word_frequency/__init__.py`. O bloco começa com o comentário `# TESTE STANDALONE`.

- [ ] **Step 2: Remover bloco standalone do sentiment_analyzer**

Deletar tudo a partir de `# Para testes diretos` e `if __name__` até o final em `plugins/analyzers/sentiment_analyzer/__init__.py`.

- [ ] **Step 3: Remover bloco standalone do readability_analyzer**

Deletar tudo a partir de `# ===` e `if __name__` até o final em `plugins/analyzers/readability_analyzer/__init__.py`.

- [ ] **Step 4: Remover bloco standalone do teams_cleaner**

Deletar tudo a partir de `# ===` e `if __name__` até o final em `plugins/documents/teams_cleaner/__init__.py`.

- [ ] **Step 5: Rodar testes e verificar**

Run: `pytest tests/ -q --timeout=60`
Expected: 835 passed, 1 skipped (sem mudança — os blocos não eram cobertos por testes)

- [ ] **Step 6: Commit**

```bash
~/.claude/scripts/commit.sh "chore: remove blocos if __name__ dos 4 plugins — dead code standalone"
```

---

### Task 2: Heurística eager/lazy explícita

**Files:**
- Modify: `qualia/core/loader.py:99`
- Modify: `plugins/analyzers/word_frequency/__init__.py` (adicionar atributo)
- Modify: `plugins/analyzers/sentiment_analyzer/__init__.py` (adicionar atributo)
- Test: `tests/test_loader_recursive.py`

- [ ] **Step 1: Escrever teste para detecção por atributo EAGER_LOAD**

Em `tests/test_loader_recursive.py`, adicionar teste:

```python
def test_eager_load_attribute_detection(tmp_path):
    """Plugin com EAGER_LOAD = True é carregado eagerly mesmo sem __init__."""
    plugin_dir = tmp_path / "test_eager"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text('''
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document

class EagerTestPlugin(BaseAnalyzerPlugin):
    EAGER_LOAD = True

    def meta(self):
        return PluginMetadata(
            id="eager_test", name="Eager Test", type=PluginType.ANALYZER,
            version="1.0.0", description="Test", provides=["test_field"],
        )

    def _analyze_impl(self, document, config, context):
        return {"test_field": "ok"}
''')
    from qualia.core.loader import PluginLoader
    loader = PluginLoader(tmp_path)
    loader.discover()
    # Sem __init__ próprio, mas com EAGER_LOAD = True → deve estar em loaded_plugins
    assert "eager_test" in loader.loaded_plugins
```

- [ ] **Step 2: Rodar teste — deve falhar**

Run: `pytest tests/test_loader_recursive.py::test_eager_load_attribute_detection -v`
Expected: FAIL (EAGER_LOAD não é checado ainda)

- [ ] **Step 3: Implementar detecção por EAGER_LOAD no loader**

Em `qualia/core/loader.py`, linha 99, mudar:

```python
# ANTES:
needs_eager = '__init__' in obj.__dict__

# DEPOIS:
needs_eager = getattr(obj, 'EAGER_LOAD', None) is True or '__init__' in obj.__dict__
```

Atualizar docstring da classe (linhas 28-32):

```python
"""Carrega plugins com instanciação lazy ou eager automática.

Plugins com EAGER_LOAD = True ou __init__ próprio (warm-up, modelos, corpora)
são instanciados na main thread durante discover() (eager).
Os demais são instanciados sob demanda no primeiro get_plugin() (lazy).

A detecção prioriza EAGER_LOAD (explícito) sobre __init__ em cls.__dict__ (implícito).
"""
```

- [ ] **Step 4: Rodar teste — deve passar**

Run: `pytest tests/test_loader_recursive.py::test_eager_load_attribute_detection -v`
Expected: PASS

- [ ] **Step 5: Rodar suite completa**

Run: `pytest tests/ -q --timeout=60`
Expected: 836 passed, 1 skipped (1 teste novo)

- [ ] **Step 6: Commit**

```bash
~/.claude/scripts/commit.sh "feat: EAGER_LOAD atributo explícito para plugins — fallback pra __init__ detection"
```

---

### Task 3: Upload file size limit (413)

**Files:**
- Create: `qualia/api/deps.py` (adicionar constante + helper)
- Modify: `qualia/api/routes/transcribe.py:48-51`
- Modify: `qualia/api/routes/pipeline.py:80-84`
- Test: `tests/test_api_extended.py`

- [ ] **Step 1: Escrever teste para 413 em transcribe**

Em `tests/test_api_extended.py`, na classe de transcribe, adicionar:

```python
def test_transcribe_file_too_large_returns_413(self, client):
    """Upload > MAX_UPLOAD_SIZE retorna 413."""
    from qualia.api.deps import MAX_UPLOAD_SIZE
    # Gerar conteúdo maior que o limite
    fake_content = b"\x00" * (MAX_UPLOAD_SIZE + 1)
    import io
    response = client.post(
        "/transcribe/transcription",
        files={"file": ("big.mp3", io.BytesIO(fake_content), "audio/mpeg")},
        data={"config": "{}"},
    )
    assert response.status_code == 413
```

- [ ] **Step 2: Escrever teste para 413 em pipeline**

```python
def test_pipeline_file_too_large_returns_413(self, client):
    """Upload > MAX_UPLOAD_SIZE no pipeline retorna 413."""
    import io, json
    from qualia.api.deps import MAX_UPLOAD_SIZE
    fake_content = b"\x00" * (MAX_UPLOAD_SIZE + 1)
    steps = json.dumps([{"plugin_id": "transcription"}])
    response = client.post(
        "/pipeline",
        files={"file": ("big.mp3", io.BytesIO(fake_content), "audio/mpeg")},
        data={"steps": steps, "text": ""},
    )
    assert response.status_code == 413
```

- [ ] **Step 3: Rodar testes — devem falhar**

Run: `pytest tests/test_api_extended.py -k "too_large_returns_413" -v`
Expected: FAIL (413 não implementado)

- [ ] **Step 4: Adicionar constante e helper em deps.py**

Em `qualia/api/deps.py`, adicionar:

```python
# Limite de upload (25MB — alinhado com Groq API limit)
MAX_UPLOAD_SIZE = 25 * 1024 * 1024  # 25MB


async def check_upload_size(file: UploadFile, max_size: int = MAX_UPLOAD_SIZE):
    """Lê o conteúdo do upload e rejeita com 413 se exceder limite."""
    content = await file.read()
    if len(content) > max_size:
        size_mb = len(content) / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo muito grande: {size_mb:.1f}MB. Limite: {max_size // (1024 * 1024)}MB."
        )
    return content
```

Adicionar imports necessários (`UploadFile` de fastapi, `HTTPException`).

- [ ] **Step 5: Usar helper em transcribe.py**

Substituir em `qualia/api/routes/transcribe.py` (linhas 48-51):

```python
# ANTES:
suffix = Path(file.filename).suffix if file.filename else ""
with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
    content = await file.read()
    tmp.write(content)
    tmp_path = tmp.name

# DEPOIS:
from qualia.api.deps import check_upload_size
content = await check_upload_size(file)
suffix = Path(file.filename).suffix if file.filename else ""
with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
    tmp.write(content)
    tmp_path = tmp.name
```

- [ ] **Step 6: Usar helper em pipeline.py**

Substituir em `qualia/api/routes/pipeline.py` (linhas 80-84):

```python
# ANTES:
suffix = Path(file.filename).suffix if file.filename else ""
with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
    content = await file.read()
    tmp.write(content)
    tmp_path = tmp.name

# DEPOIS:
from qualia.api.deps import check_upload_size
content = await check_upload_size(file)
suffix = Path(file.filename).suffix if file.filename else ""
with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
    tmp.write(content)
    tmp_path = tmp.name
```

- [ ] **Step 7: Rodar testes — devem passar**

Run: `pytest tests/test_api_extended.py -k "too_large_returns_413" -v`
Expected: PASS

- [ ] **Step 8: Rodar suite completa**

Run: `pytest tests/ -q --timeout=60`
Expected: 837+ passed, 1 skipped

- [ ] **Step 9: Commit**

```bash
~/.claude/scripts/commit.sh "fix: upload file size limit 25MB com 413 — transcribe e pipeline protegidos"
```

---

## Chunk 2: Coverage gaps (Tasks 4-5)

### Task 4: Coverage base_plugins.py — type conversion branches

**Files:**
- Test: `tests/test_core.py` ou novo `tests/test_base_plugins.py`

- [ ] **Step 1: Escrever testes para branches de conversão**

Criar testes em `tests/test_core.py` (classe nova `TestValidateAndConvert`):

```python
class TestValidateAndConvert:
    """Testa _validate_and_convert com todas as branches de tipo."""

    def test_int_conversion_from_string(self):
        from qualia.core.base_plugins import _validate_and_convert
        params = {"count": {"type": "int", "default": 0}}
        result = _validate_and_convert({"count": "42"}, params)
        assert result["count"] == 42

    def test_float_conversion_from_string(self):
        from qualia.core.base_plugins import _validate_and_convert
        params = {"threshold": {"type": "float", "default": 0.0}}
        result = _validate_and_convert({"threshold": "0.75"}, params)
        assert result["threshold"] == 0.75

    def test_bool_from_string_true(self):
        from qualia.core.base_plugins import _validate_and_convert
        params = {"enabled": {"type": "bool", "default": False}}
        for truthy in ("true", "True", "1", "yes"):
            result = _validate_and_convert({"enabled": truthy}, params)
            assert result["enabled"] is True, f"Failed for '{truthy}'"

    def test_bool_from_string_false(self):
        from qualia.core.base_plugins import _validate_and_convert
        params = {"enabled": {"type": "bool", "default": True}}
        for falsy in ("false", "0", "no", "anything"):
            result = _validate_and_convert({"enabled": falsy}, params)
            assert result["enabled"] is False, f"Failed for '{falsy}'"

    def test_bool_from_nonstring(self):
        from qualia.core.base_plugins import _validate_and_convert
        params = {"enabled": {"type": "bool", "default": False}}
        assert _validate_and_convert({"enabled": 1}, params)["enabled"] is True
        assert _validate_and_convert({"enabled": 0}, params)["enabled"] is False
        assert _validate_and_convert({"enabled": None}, params)["enabled"] is False

    def test_int_invalid_raises(self):
        from qualia.core.base_plugins import _validate_and_convert
        params = {"count": {"type": "int", "default": 0}}
        with pytest.raises(ValueError):
            _validate_and_convert({"count": "abc"}, params)

    def test_unknown_param_rejected(self):
        from qualia.core.base_plugins import _validate_and_convert
        params = {"known": {"type": "str", "default": ""}}
        with pytest.raises(ValueError, match="desconhecido"):
            _validate_and_convert({"unknown": "x"}, params)

    def test_exclude_skips_params(self):
        from qualia.core.base_plugins import _validate_and_convert
        params = {"keep": {"type": "str", "default": ""}, "skip": {"type": "str", "default": ""}}
        result = _validate_and_convert({"keep": "a", "skip": "b"}, params, exclude={"skip"})
        assert "keep" in result
        assert "skip" not in result

    def test_default_applied_when_missing(self):
        from qualia.core.base_plugins import _validate_and_convert
        params = {"count": {"type": "int", "default": 42}}
        result = _validate_and_convert({}, params)
        assert result["count"] == 42
```

- [ ] **Step 2: Rodar testes — todos devem passar (testando código existente)**

Run: `pytest tests/test_core.py::TestValidateAndConvert -v`
Expected: PASS (9 testes novos)

- [ ] **Step 3: Commit**

```bash
~/.claude/scripts/commit.sh "test: coverage _validate_and_convert — int, float, bool, exclude, defaults, unknown params"
```

---

### Task 5: Coverage pipeline.py — timeout paths

**Files:**
- Test: `tests/test_api_extended.py`

- [ ] **Step 1: Escrever teste para timeout no step 0 (file+document)**

Na classe `TestPipelineEndpoint` em `tests/test_api_extended.py`:

```python
def test_pipeline_file_step0_timeout_returns_504(self, client):
    """Timeout no step 0 (file+document) retorna 504."""
    import io
    from unittest.mock import patch, MagicMock, AsyncMock
    import asyncio as _asyncio

    with patch("qualia.api.routes.pipeline.get_core") as mock_get_core:
        mock_core = MagicMock()
        mock_get_core.return_value = mock_core
        doc_meta = MagicMock(type=MagicMock(value="document"), provides=["transcription"])
        mock_core.registry.get.return_value = doc_meta
        mock_core.registry.__contains__ = MagicMock(return_value=True)
        mock_core.get_config_registry.return_value = None
        mock_core.add_document.return_value = MagicMock()

    with patch("qualia.api.routes.pipeline.asyncio.wait_for", side_effect=_asyncio.TimeoutError):
        with patch("qualia.api.routes.pipeline.get_core", return_value=mock_core):
            steps = json.dumps([{"plugin_id": "transcription"}])
            fake_audio = io.BytesIO(b"\x00" * 100)
            response = client.post(
                "/pipeline",
                files={"file": ("audio.mp3", fake_audio, "audio/mpeg")},
                data={"steps": steps},
            )
    assert response.status_code == 504
```

- [ ] **Step 2: Escrever teste para timeout no visualizer step**

```python
def test_pipeline_visualizer_timeout_returns_504(self, client):
    """Timeout num step visualizer retorna 504."""
    import asyncio as _asyncio

    with patch("qualia.api.routes.pipeline.asyncio.wait_for") as mock_wait:
        # Primeira chamada OK (analyzer), segunda timeout (visualizer)
        mock_wait.side_effect = [
            {"word_frequencies": {"a": 1}, "total_words": 1},  # analyzer ok
            _asyncio.TimeoutError(),  # visualizer timeout
        ]
        steps = json.dumps([
            {"plugin_id": "word_frequency"},
            {"plugin_id": "frequency_chart_plotly"},
        ])
        response = client.post(
            "/pipeline",
            data={"text": "palavra teste", "steps": steps},
        )
    assert response.status_code == 504
```

- [ ] **Step 3: Rodar testes**

Run: `pytest tests/test_api_extended.py -k "pipeline" -v --timeout=60`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
~/.claude/scripts/commit.sh "test: coverage pipeline timeout — step0 file+document e visualizer step"
```

---

## Chunk 3: Discovery errors com severidade + endpoint (Tasks 6-7)

### Task 6: Enriquecer discovery errors com severidade e tipo

**Files:**
- Modify: `qualia/core/loader.py:129-135`
- Modify: `qualia/cli/commands/list.py:13-26`
- Test: `tests/test_loader_errors.py`

- [ ] **Step 1: Escrever teste para campos enriquecidos**

Em `tests/test_loader_errors.py`, adicionar:

```python
def test_discovery_errors_have_severity_and_type(tmp_path):
    """Erros de discovery incluem severity e type."""
    plugin_dir = tmp_path / "broken_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text("import nao_existe_xyz")

    loader = PluginLoader(tmp_path)
    loader.discover()

    assert len(loader.discovery_errors) == 1
    err = loader.discovery_errors[0]
    assert "severity" in err
    assert "type" in err
    assert err["severity"] in ("critical", "warning")
    assert err["type"] == "import_error"
```

- [ ] **Step 2: Rodar teste — deve falhar**

Run: `pytest tests/test_loader_errors.py::test_discovery_errors_have_severity_and_type -v`
Expected: FAIL (campos severity/type não existem)

- [ ] **Step 3: Implementar classificação no loader**

Em `qualia/core/loader.py`, substituir o bloco except (linhas 129-135):

```python
except Exception as e:
    logger.error(f"Erro ao carregar plugin {plugin_dir.name}: {e}")
    error_type, severity = self._classify_error(e)
    self.discovery_errors.append({
        "plugin": plugin_dir.name,
        "error": str(e),
        "path": str(plugin_dir),
        "type": error_type,
        "severity": severity,
    })
```

Adicionar método `_classify_error` à classe `PluginLoader`:

```python
@staticmethod
def _classify_error(exc: Exception) -> tuple:
    """Classifica exceção por tipo e severidade.

    Returns:
        (type_str, severity_str) — severity é 'critical' ou 'warning'
    """
    if isinstance(exc, ImportError):
        return "import_error", "critical"
    elif isinstance(exc, SyntaxError):
        return "syntax_error", "critical"
    elif isinstance(exc, (OSError, FileNotFoundError)):
        return "os_error", "critical"
    elif isinstance(exc, ValueError):
        return "value_error", "critical"
    else:
        return "unknown_error", "warning"
```

- [ ] **Step 4: Rodar teste — deve passar**

Run: `pytest tests/test_loader_errors.py -v`
Expected: PASS

- [ ] **Step 5: Simplificar _classify_error na CLI (usa campos do loader)**

Em `qualia/cli/commands/list.py`, simplificar `_classify_error` para usar os novos campos:

```python
def _classify_error(error_dict: dict) -> tuple:
    """Extrai tipo e sugestão de fix do error dict."""
    err_type = error_dict.get("type", "unknown_error")
    suggestions = {
        "import_error": "pip install <módulo>",
        "syntax_error": "Verificar código do plugin",
        "os_error": "Verificar arquivos/modelos necessários",
        "value_error": "Verificar meta() do plugin (id duplicado?)",
    }
    return err_type.replace("_", " ").title(), suggestions.get(err_type, "Verificar log para detalhes")
```

Atualizar chamada em `_run_check` para passar o dict inteiro em vez de só o error string.

- [ ] **Step 6: Rodar suite completa**

Run: `pytest tests/ -q --timeout=60`
Expected: all passed

- [ ] **Step 7: Commit**

```bash
~/.claude/scripts/commit.sh "feat: discovery errors com severity e type — classificação na fonte (loader)"
```

---

### Task 7: Endpoint /plugins/health

**Files:**
- Modify: `qualia/api/routes/plugins.py`
- Test: `tests/test_api_extended.py`

- [ ] **Step 1: Escrever teste para /plugins/health**

```python
class TestPluginsHealth:
    def test_plugins_health_returns_per_plugin_status(self, client):
        """GET /plugins/health retorna status individual por plugin."""
        response = client.get("/plugins/health")
        assert response.status_code == 200
        data = response.json()
        assert "plugins" in data
        assert len(data["plugins"]) >= 8
        # Cada plugin tem campos obrigatórios
        for p in data["plugins"]:
            assert "id" in p
            assert "status" in p
            assert p["status"] in ("loaded", "failed")
            assert "loading" in p
            assert p["loading"] in ("eager", "lazy")

    def test_plugins_health_no_errors(self, client):
        """Sem erros de discovery → errors vazio."""
        response = client.get("/plugins/health")
        data = response.json()
        assert data.get("errors", []) == [] or "errors" not in data
```

- [ ] **Step 2: Rodar testes — devem falhar**

Run: `pytest tests/test_api_extended.py::TestPluginsHealth -v`
Expected: FAIL (endpoint não existe)

- [ ] **Step 3: Implementar endpoint**

Em `qualia/api/routes/plugins.py`, adicionar:

```python
@router.get("/plugins/health")
def plugins_health():
    """Status individual por plugin — loaded/failed, eager/lazy."""
    core = get_core()
    plugins_status = []
    for plugin_id, meta in core.registry.items():
        is_loaded = plugin_id in core.loader.loaded_plugins
        needs_eager = getattr(core.loader._plugin_classes.get(plugin_id), 'EAGER_LOAD', None) is True \
            or '__init__' in (core.loader._plugin_classes.get(plugin_id, type).__dict__)
        plugins_status.append({
            "id": plugin_id,
            "name": meta.name,
            "type": meta.type.value,
            "status": "loaded" if is_loaded else "pending",
            "loading": "eager" if needs_eager else "lazy",
        })

    response = {
        "status": "healthy",
        "total": len(core.registry),
        "plugins": plugins_status,
    }
    if core.discovery_errors:
        response["errors"] = core.discovery_errors
        response["status"] = "degraded"
    return response
```

Nota: o endpoint deve ser registrado ANTES do `/{plugin_id}` catch-all para não conflitar.

- [ ] **Step 4: Rodar testes — devem passar**

Run: `pytest tests/test_api_extended.py::TestPluginsHealth -v`
Expected: PASS

- [ ] **Step 5: Rodar suite completa**

Run: `pytest tests/ -q --timeout=60`
Expected: all passed

- [ ] **Step 6: Commit**

```bash
~/.claude/scripts/commit.sh "feat: endpoint /plugins/health — status individual por plugin com loading mode"
```

---

## Chunk 4: Pipeline CLI unificado (Task 8)

### Task 8: Unificar pipeline CLI com API

A CLI pipeline diverge da API em 3 pontos:
1. Config key `plugin` vs `plugin_id`
2. Sem text chaining entre steps
3. Visualizer busca `word_frequencies` específico em vez de usar último resultado

**Files:**
- Modify: `qualia/cli/commands/pipeline.py`
- Test: `tests/test_cli.py` ou `tests/test_cli_extended.py`

- [ ] **Step 1: Escrever teste para config com `plugin_id` key**

Em `tests/test_cli_extended.py`, adicionar:

```python
def test_pipeline_accepts_plugin_id_key(self, runner, tmp_path):
    """Pipeline config com 'plugin_id' funciona (alinhado com API)."""
    doc = tmp_path / "doc.txt"
    doc.write_text("Texto de teste para pipeline com várias palavras repetidas.")
    config = tmp_path / "pipe.yaml"
    config.write_text(yaml.dump({
        "name": "test_pipe",
        "steps": [{"plugin_id": "word_frequency", "config": {}}]
    }))
    result = runner.invoke(cli, ["pipeline", str(doc), "-c", str(config)])
    assert result.exit_code == 0
    assert "Pipeline completo" in result.output
```

- [ ] **Step 2: Escrever teste para text chaining**

```python
def test_pipeline_chains_text_between_steps(self, runner, tmp_path):
    """Pipeline CLI encadeia texto entre steps (como API faz)."""
    doc = tmp_path / "doc.txt"
    doc.write_text("Texto para análise de frequência e sentimento.")
    config = tmp_path / "pipe.yaml"
    config.write_text(yaml.dump({
        "name": "chain_test",
        "steps": [
            {"plugin_id": "word_frequency"},
            {"plugin_id": "readability_analyzer"},
        ]
    }))
    result = runner.invoke(cli, ["pipeline", str(doc), "-c", str(config)])
    assert result.exit_code == 0
    assert "Pipeline completo" in result.output
```

- [ ] **Step 3: Rodar testes — verificar estado atual**

Run: `pytest tests/test_cli_extended.py -k "pipeline" -v`
Note: O primeiro teste pode falhar se a CLI não aceita `plugin_id` key.

- [ ] **Step 4: Unificar config key (aceitar `plugin_id` e `plugin`)**

Em `qualia/cli/commands/pipeline.py`, linhas 36-42:

```python
# ANTES:
step = PipelineStep(
    plugin_id=step_data['plugin'],
    ...
)

# DEPOIS:
step = PipelineStep(
    plugin_id=step_data.get('plugin_id', step_data.get('plugin', '')),
    config=step_data.get('config', {}),
    output_name=step_data.get('output_name')
)
```

- [ ] **Step 5: Unificar visualizer — usar último resultado em vez de buscar word_frequencies**

Substituir o bloco de visualizer (linhas 93-116):

```python
if plugin_meta.type == PluginType.VISUALIZER:
    if results:
        # Usar último resultado como dados (como API faz)
        last_result = list(results.values())[-1]
        if isinstance(last_result, dict):
            plugin_instance = core.get_plugin(step.plugin_id)
            viz_config = {**(step.config or {}), "output_format": "html"}
            viz_result = plugin_instance.render(last_result, viz_config)
            if output_dir and "html" in viz_result:
                viz_output = output_path / f"{step.output_name or step.plugin_id}.html"
                viz_output.write_text(viz_result["html"], encoding="utf-8")
                viz_result["output"] = str(viz_output)
            results[step.output_name or step.plugin_id] = viz_result
        else:
            raise ValueError(f"Resultado anterior não é dict para {step.plugin_id}")
    else:
        raise ValueError(f"Visualizador {step.plugin_id} precisa de dados anteriores")
```

- [ ] **Step 6: Rodar testes**

Run: `pytest tests/ -k "pipeline" -v --timeout=60`
Expected: PASS

- [ ] **Step 7: Rodar suite completa**

Run: `pytest tests/ -q --timeout=60`
Expected: all passed

- [ ] **Step 8: Commit**

```bash
~/.claude/scripts/commit.sh "fix: pipeline CLI unificado com API — plugin_id key, último resultado pra visualizer"
```

---

## Final: Atualizar docs

### Task 9: Atualizar BACKLOG.md e TECHNICAL_STATE.md

- [ ] **Step 1: Marcar todos os 8 itens como concluídos no BACKLOG.md**

- [ ] **Step 2: Atualizar contagem de testes no TECHNICAL_STATE.md e BACKLOG.md**

- [ ] **Step 3: Atualizar MEMORY.md com resumo**

- [ ] **Step 4: Commit**

```bash
~/.claude/scripts/commit.sh "docs: backlog zerado — 8 itens pendentes resolvidos, contagem de testes atualizada"
```
