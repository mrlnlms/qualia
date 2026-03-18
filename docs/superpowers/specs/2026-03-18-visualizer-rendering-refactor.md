# Visualizer Rendering Refactor — Design Spec

## Problem

Hoje cada visualizer plugin é responsável por gerar a figura, escolher formato, serializar pra arquivo e lidar com I/O. Isso cria:

- Duplicação: cada plugin reimplementa lógica de formatos (PNG/HTML/SVG), paths, e cleanup
- Dependência frágil: kaleido (100MB, Chromium headless) é necessário pra PNG de plugins plotly, mas falha em ambientes restritos
- Fricção pro plugin author: precisa conhecer libs de serialização, output_path, formatos — quando deveria só pensar em dados → visualização
- Acoplamento: plugin decide formato, mas quem deveria decidir é o consumer

Com cada plugin novo, essa complexidade se multiplica.

## Solution

**Plugin retorna objeto de figura nativo. BaseClass serializa.**

O plugin author implementa uma função: `(data, config) → figure object`. O `BaseVisualizerPlugin` detecta o tipo do objeto retornado e serializa pro formato que o consumer pediu via `output_format` no config.

## Breaking Changes

Este refactor quebra consumers existentes. Dado que o projeto está em dev sem usuários externos, isso é aceitável.

**Response shape do `/visualize/{plugin_id}`:**

Antes:
```json
{"status": "success", "format": "html", "data": "<html>...", "encoding": "utf-8"}
{"status": "success", "data": "base64...", "encoding": "base64", "format": "png"}
```

Depois:
```json
{"status": "success", "plugin_id": "...", "html": "<html>..."}
{"status": "success", "plugin_id": "...", "data": "base64...", "encoding": "base64", "format": "png"}
```

**Plugin IDs renomeados:**
- `wordcloud_viz` → `wordcloud_d3`
- `frequency_chart` → `frequency_chart_plotly`
- `sentiment_viz` → `sentiment_viz_plotly`

**Interface `IVisualizerPlugin.render()`:** remove `output_path`, retorno muda de `Union[str, Path]` → `dict`.

## Design

### Interface

```python
# qualia/core/interfaces.py
class IVisualizerPlugin(IPlugin):
    @abstractmethod
    def render(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Renderiza visualização e retorna dict com resultado serializado."""
        pass
```

Sem `output_path`. Retorno é `dict` (serializado pelo BaseClass).

### BaseVisualizerPlugin

```python
# qualia/core/base_plugins.py
import base64
import importlib.util
import io

class BaseVisualizerPlugin(IVisualizerPlugin):

    # Subclasse declara: "plotly", "matplotlib", ou "html"
    RENDER_LIB = "html"

    def render(self, data, config):
        # Extrai output_format ANTES de validar (não faz parte do schema do plugin)
        config = dict(config)  # cópia — não muta o dict do caller
        output_format = config.pop("output_format", "html")
        validated = self._validate_config(config)
        self._validate_data(data)
        fig = self._render_impl(data, validated)
        return self._serialize(fig, output_format)

    def _render_impl(self, data, config):
        """Plugin implementa: (data, config) → figure object ou HTML str."""
        raise NotImplementedError("Subclasse deve implementar _render_impl()")

    def _serialize(self, fig, fmt):
        """Detecta tipo da figura e serializa pro formato pedido.

        Retorno: dict com "html" ou "data"+"encoding"+"format".
        """
        # HTML string pura
        if isinstance(fig, str):
            if fmt != "html":
                raise ValueError(f"Plugin retorna HTML puro; formato '{fmt}' não suportado")
            return {"html": fig}

        # plotly.Figure (duck-typed via to_html)
        if hasattr(fig, 'to_html'):
            if fmt == "html":
                return {"html": fig.to_html(include_plotlyjs="cdn", full_html=True)}
            elif fmt in ("png", "svg"):
                img_bytes = fig.to_image(format=fmt)
                b64 = base64.b64encode(img_bytes).decode()
                return {"data": b64, "encoding": "base64", "format": fmt}
            else:
                raise ValueError(f"Formato '{fmt}' não suportado para plotly.Figure")

        # matplotlib.Figure (duck-typed via savefig)
        if hasattr(fig, 'savefig'):
            try:
                if fmt == "html":
                    return {"html": self._matplotlib_to_html(fig)}
                elif fmt in ("png", "svg"):
                    buf = io.BytesIO()
                    fig.savefig(buf, format=fmt, bbox_inches='tight', dpi=150)
                    b64 = base64.b64encode(buf.getvalue()).decode()
                    return {"data": b64, "encoding": "base64", "format": fmt}
                else:
                    raise ValueError(f"Formato '{fmt}' não suportado para matplotlib.Figure")
            finally:
                import matplotlib.pyplot as plt
                plt.close(fig)

        raise TypeError(f"Tipo de figura não suportado: {type(fig).__name__}")

    def _matplotlib_to_html(self, fig):
        """Converte matplotlib Figure → HTML com imagem base64 inline.

        Nota: resultado é imagem estática embebida em HTML, não interativo.
        """
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f'<html><body style="margin:0;display:flex;justify-content:center"><img src="data:image/png;base64,{b64}" style="max-width:100%"></body></html>'

    def _validate_config(self, config):
        """Valida e converte tipos dos parâmetros.

        Usa a mesma lógica de conversão do BaseAnalyzerPlugin/BaseDocumentPlugin
        para consistência: int/integer, float, bool/boolean.
        """
        meta = self.meta()
        validated = {}
        for param_name, param_spec in meta.parameters.items():
            if param_name in config:
                value = config[param_name]
                param_type = param_spec.get('type')
                if param_type in ('integer', 'int'):
                    validated[param_name] = int(value)
                elif param_type == 'float':
                    validated[param_name] = float(value)
                elif param_type in ('boolean', 'bool'):
                    if isinstance(value, str):
                        validated[param_name] = value.lower() in ('true', '1', 'yes')
                    else:
                        validated[param_name] = bool(value)
                else:
                    validated[param_name] = value
            else:
                validated[param_name] = param_spec.get('default')
        return validated

    @staticmethod
    def get_supported_formats(render_lib):
        """Retorna formatos disponíveis baseado na lib e no ambiente."""
        if render_lib == "html":
            return ["html"]
        elif render_lib == "matplotlib":
            return ["html", "png", "svg"]
        elif render_lib == "plotly":
            formats = ["html"]
            if importlib.util.find_spec("kaleido") is not None:
                formats.extend(["png", "svg"])
            return formats
        return ["html"]
```

### Detecção dinâmica de formatos

Cada plugin declara `RENDER_LIB` como atributo de classe. O `meta()` do plugin usa `BaseVisualizerPlugin.get_supported_formats(cls.RENDER_LIB)` pra gerar o parâmetro `output_format` dinamicamente:

```python
def meta(self):
    return PluginMetadata(
        id="frequency_chart_plotly",
        name="Frequency Chart (Plotly)",
        version="1.0.0",
        description="Gráfico de frequência de palavras usando Plotly",
        type=PluginType.VISUALIZER,
        requires=["word_frequencies"],
        provides=[],
        parameters={
            "chart_type": {"type": "str", "default": "bar", ...},
            # output_format gerado pela lib
            "output_format": {
                "type": "str",
                "description": "Formato de saída",
                "default": "html",
                "options": self.get_supported_formats(self.RENDER_LIB),
            },
        },
    )
```

Resultado no `/config/consolidated`:
- Plugin plotly + kaleido instalado → `output_format.options: ["html", "png", "svg"]`
- Plugin plotly + kaleido não instalado → `output_format.options: ["html"]`
- Plugin matplotlib → `output_format.options: ["html", "png", "svg"]`
- Plugin D3/HTML puro → `output_format.options: ["html"]`

O frontend `ParamForm` renderiza dropdown com só os formatos que funcionam.

### Plugins — Renomear e Simplificar

| Atual | Novo ID | Novo diretório | Lib | RENDER_LIB | Requires |
|-------|---------|----------------|-----|------------|----------|
| `wordcloud_viz` | `wordcloud_d3` | `plugins/wordcloud_d3/` | D3.js | `"html"` | `word_frequencies` |
| `frequency_chart` | `frequency_chart_plotly` | `plugins/frequency_chart_plotly/` | plotly | `"plotly"` | `word_frequencies` |
| `sentiment_viz` | `sentiment_viz_plotly` | `plugins/sentiment_viz_plotly/` | plotly | `"plotly"` | `polarity`, `subjectivity` |

**sentiment_viz_plotly — caso especial:** hoje o chart_type `distribution` usa matplotlib enquanto os outros 3 (dashboard, gauge, timeline) usam plotly. Na migração, `distribution` será reescrito em plotly pra manter `RENDER_LIB = "plotly"` consistente. Isso simplifica o plugin e elimina a ambiguidade de lib mista.

**wordcloud_d3:** hoje o plugin já tem `_generate_html()` com D3.js cloud layout. Na migração, `_render_impl` retorna o HTML string direto. A branch de matplotlib/PNG é removida.

Exemplo de plugin migrado:

```python
class FrequencyChartPlotly(BaseVisualizerPlugin):
    RENDER_LIB = "plotly"

    def meta(self):
        return PluginMetadata(
            id="frequency_chart_plotly",
            name="Frequency Chart (Plotly)",
            version="2.0.0",
            description="Gráfico de frequência de palavras usando Plotly",
            type=PluginType.VISUALIZER,
            requires=["word_frequencies"],
            provides=[],
            parameters={
                "chart_type": {"type": "str", "default": "bar", "options": ["bar", "horizontal_bar", "line", "area"]},
                "max_items": {"type": "int", "default": 20, "range": [5, 100]},
                "title": {"type": "str", "default": "Word Frequency"},
                "color_scheme": {"type": "str", "default": "viridis", "options": ["viridis", "plasma", "blues", "reds"]},
                "output_format": {
                    "type": "str",
                    "description": "Formato de saída",
                    "default": "html",
                    "options": self.get_supported_formats(self.RENDER_LIB),
                },
            },
        )

    def _render_impl(self, data, config):
        import plotly.graph_objects as go
        frequencies = data["word_frequencies"]
        sorted_items = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)[:config["max_items"]]
        words, counts = zip(*sorted_items) if sorted_items else ([], [])

        fig = go.Figure(go.Bar(x=list(words), y=list(counts)))
        fig.update_layout(title=config["title"])
        return fig  # BaseClass serializa
```

### Rota `/visualize/{plugin_id}`

```python
@router.post("/visualize/{plugin_id}")
async def visualize(plugin_id: str, request: VisualizeRequest):
    core = get_core()
    require_plugin_type(core, plugin_id, "visualizer")
    validate_plugin_config(core, plugin_id, request.config)

    config = {**request.config, "output_format": request.output_format or "html"}
    plugin = core.loader.get_plugin(plugin_id)

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(plugin.render, request.data, config),
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail=f"Plugin '{plugin_id}' timed out (60s)")

    await track(f"/visualize/{plugin_id}", plugin_id)

    return {"status": "success", "plugin_id": plugin_id, **result}
```

Sem temp files. Sem FileResponse. Sem BackgroundTask cleanup.

### Engine `execute_plugin` (branch VISUALIZER)

```python
elif metadata.type == PluginType.VISUALIZER:
    data = {}
    for dep_result in dep_results.values():
        if isinstance(dep_result, dict):
            data.update(dep_result)
    result = plugin.render(data, config)
    # result já é dict com "html" ou "data"+"encoding"+"format"
```

Remove: `output_path`, wrapping em `{"output_path": ...}`.

### CLI `visualize` command

Arquivo: `qualia/cli/commands/visualize.py`

O command recebe o dict de resultado do engine e salva em arquivo:

```python
# Após execute_plugin retornar result dict
if "html" in result:
    output_path = output_path or Path(f"./{plugin_id}_output.html")
    output_path.write_text(result["html"], encoding="utf-8")
elif "data" in result and result.get("encoding") == "base64":
    fmt = result.get("format", "png")
    output_path = output_path or Path(f"./{plugin_id}_output.{fmt}")
    output_path.write_bytes(base64.b64decode(result["data"]))
```

### CLI interactive actions

Arquivo: `qualia/cli/interactive/actions.py`

A função que chama render precisa ser atualizada pra não passar `output_path` e pra lidar com o dict de resultado ao invés de Path.

### Frontend

**`ResultView.svelte` — atualizar `detectType`:**
```javascript
function detectType(r) {
    if (!r) return 'empty';
    if (r.encoding === 'base64') return 'image';
    if (r.html) return 'html';        // MUDOU: checa r.html ao invés de r.format === 'html'
    return 'json';
}
```

**`ResultView.svelte` — atualizar invocação do HtmlResult:**
```svelte
<!-- MUDOU: html={result.html} ao invés de html={result.data} -->
<HtmlResult html={result.html} />
```

**`api.js` — mudar default:**
```javascript
export function visualize(pluginId, data, config = {}, outputFormat = 'html') {
    // MUDOU: default 'png' → 'html'
```

**`Analyze.svelte`:** dropdown de formato vem do schema via ParamForm — sem mudança.

## Arquivos Afetados

**Core:**
- `qualia/core/interfaces.py` — `IVisualizerPlugin.render()` signature
- `qualia/core/base_plugins.py` — rewrite de `BaseVisualizerPlugin`
- `qualia/core/engine.py` — branch VISUALIZER em `execute_plugin()`

**API:**
- `qualia/api/routes/visualize.py` — simplifica rota
- `qualia/api/schemas.py` — `VisualizeRequest` (remover campos desnecessários se houver)

**CLI:**
- `qualia/cli/commands/visualize.py` — salva dict ao invés de Path
- `qualia/cli/interactive/actions.py` — atualiza chamada de render

**Frontend:**
- `qualia/frontend/src/lib/api.js` — default `'png'` → `'html'`
- `qualia/frontend/src/components/ResultView.svelte` — `detectType` + `HtmlResult` prop

**Plugins (deletar e recriar):**
- Deletar: `plugins/wordcloud_viz/`, `plugins/frequency_chart/`, `plugins/sentiment_viz/`
- Criar: `plugins/wordcloud_d3/`, `plugins/frequency_chart_plotly/`, `plugins/sentiment_viz_plotly/`

**Testes (reescrever):**
- `tests/test_api_extended.py` — testes de `/visualize` (novo response shape)
- `tests/test_core.py` — branch VISUALIZER (sem output_path)
- `tests/test_cli.py`, `test_cli_extended.py`, `test_cli_remaining.py`, `test_cli_final.py` — CLI visualize
- `tests/test_pragmatic.py` — testes pragmáticos que usam visualizers

**Docs:**
- `CLAUDE.md` — atualizar nomes de plugins
- `docs/TECHNICAL_STATE.md` — atualizar tabela de plugins
- `README.md` — se menciona plugins específicos

## O Que Sai

- `output_path` em toda a chain (interface, base class, engine, rota, plugins)
- `format` como parâmetro manual em cada plugin schema
- Temp file creation/cleanup na rota `/visualize`
- Base64 encoding na rota (move pro BaseClass)
- FileResponse + BackgroundTask
- matplotlib Agg backend setup no BaseClass (move pra `_serialize`)
- `_ensure_path()` no BaseClass
- Diretórios antigos: `plugins/wordcloud_viz/`, `plugins/frequency_chart/`, `plugins/sentiment_viz/`

## O Que Entra

- `RENDER_LIB` class attribute nos plugins
- `_serialize()` no BaseClass — detecta tipo de figura, serializa
- `_matplotlib_to_html()` helper no BaseClass
- `get_supported_formats()` — detecção dinâmica baseada em libs instaladas
- `_validate_config()` unificada (mesma lógica do BaseAnalyzerPlugin)

## Dependências

- `kaleido` permanece no extra `[viz]` do pyproject.toml
- Não é mais dependência hard de nenhum plugin
- Se ausente: formatos PNG/SVG de plugins plotly ficam indisponíveis (não aparecem no schema)
- matplotlib gera PNG/SVG nativo (não precisa de kaleido)

## Testes

**Unitários (por plugin):**
- `_render_impl()` retorna objeto do tipo esperado (plotly.Figure, matplotlib.Figure, str)
- `render()` com `output_format=html` retorna dict com key `html`
- `render()` com `output_format=png` retorna dict com keys `data`, `encoding`, `format`

**Base class:**
- `_serialize()` com plotly.Figure → HTML dict
- `_serialize()` com matplotlib.Figure → HTML dict (com plt.close)
- `_serialize()` com str → HTML dict
- `_serialize()` com plotly.Figure + png → base64 dict (skip se sem kaleido)
- `_serialize()` com matplotlib.Figure + png → base64 dict
- `_serialize()` com tipo desconhecido → TypeError
- `_serialize()` com formato desconhecido → ValueError
- `_serialize()` com matplotlib + erro → plt.close chamado (via finally)

**Rota:**
- `/visualize/{plugin_id}` retorna JSON (não FileResponse)
- Response contém `html` ou `data`+`encoding`
- Timeout → 504
- Plugin tipo errado → 422

**Engine:**
- Branch VISUALIZER retorna dict (não Path)

**CLI:**
- `visualize` command salva HTML em arquivo .html
- `visualize` command salva PNG quando `output_format=png`

**Detecção de formatos:**
- Plugin plotly sem kaleido → schema mostra só `["html"]`
- Plugin plotly com kaleido → schema mostra `["html", "png", "svg"]`
- Plugin matplotlib → schema mostra `["html", "png", "svg"]`

**Deletar:**
- Todos os testes que verificam FileResponse, temp file cleanup, output_path
