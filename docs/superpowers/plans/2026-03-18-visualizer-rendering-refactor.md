# Visualizer Rendering Refactor — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mover serialização de visualizações dos plugins individuais pro BaseVisualizerPlugin, com detecção dinâmica de formatos disponíveis no ambiente.

**Architecture:** Plugin retorna objeto de figura nativo (plotly.Figure, matplotlib.Figure, ou HTML str). O BaseClass detecta o tipo via duck-typing e serializa pro formato pedido pelo consumer. Formatos disponíveis no schema são gerados dinamicamente baseado nas libs instaladas.

**Tech Stack:** Python 3.13, FastAPI, plotly, matplotlib, D3.js, Svelte 5

**Spec:** `docs/superpowers/specs/2026-03-18-visualizer-rendering-refactor.md`

---

## Chunk 1: Core — Interface, BaseClass, Engine

### Task 1: Atualizar IVisualizerPlugin interface

**Files:**
- Modify: `qualia/core/interfaces.py:76-82`

- [ ] **Step 1: Atualizar signature do render()**

```python
# qualia/core/interfaces.py — substituir linhas 76-82
class IVisualizerPlugin(IPlugin):
    """Renderiza dados em visualizações"""

    @abstractmethod
    def render(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Renderiza visualização e retorna dict serializado.

        Retorno: {"html": str} ou {"data": str, "encoding": "base64", "format": str}
        """
        pass
```

Nota: remover `output_path: Path` do parâmetro e mudar retorno de `Union[str, Path]` pra `Dict[str, Any]`. Precisa adicionar `Dict` ao import do typing se não estiver.

- [ ] **Step 2: Verificar que o import de Path e Union podem ser removidos se não usados em outro lugar**

Run: `grep -n "Path\|Union" qualia/core/interfaces.py`

Remover imports não utilizados.

- [ ] **Step 3: Commit**

```bash
~/.claude/scripts/commit.sh "refactor: IVisualizerPlugin.render() remove output_path, retorna dict"
```

### Task 2: Reescrever BaseVisualizerPlugin

**Files:**
- Modify: `qualia/core/base_plugins.py:73-162`

- [ ] **Step 1: Reescrever a classe BaseVisualizerPlugin inteira**

Substituir linhas 73-162 de `qualia/core/base_plugins.py` por:

```python
class BaseVisualizerPlugin(IVisualizerPlugin):
    """Base class com funcionalidades comuns para visualizers.

    Plugin author implementa _render_impl(data, config) retornando:
    - plotly.Figure → BaseClass serializa pra HTML ou PNG/SVG
    - matplotlib.Figure → BaseClass serializa pra HTML ou PNG/SVG
    - str (HTML) → BaseClass envolve em dict

    O formato de saída é controlado pelo consumer via output_format no config.
    Formatos disponíveis são detectados dinamicamente baseado nas libs instaladas.
    """

    # Subclasse declara: "plotly", "matplotlib", ou "html"
    RENDER_LIB = "html"

    def render(self, data, config):
        """Valida, renderiza e serializa visualização."""
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
        """Detecta tipo da figura via duck-typing e serializa pro formato pedido."""
        import base64 as b64_mod
        import io

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
                return {"data": b64_mod.b64encode(img_bytes).decode(), "encoding": "base64", "format": fmt}
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
                    return {"data": b64_mod.b64encode(buf.getvalue()).decode(), "encoding": "base64", "format": fmt}
                else:
                    raise ValueError(f"Formato '{fmt}' não suportado para matplotlib.Figure")
            finally:
                import matplotlib.pyplot as plt
                plt.close(fig)

        raise TypeError(f"Tipo de figura não suportado: {type(fig).__name__}")

    @staticmethod
    def _matplotlib_to_html(fig):
        """Converte matplotlib Figure → HTML com imagem base64 inline."""
        import base64 as b64_mod
        import io
        import matplotlib.pyplot as plt

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        b64 = b64_mod.b64encode(buf.getvalue()).decode()
        return (
            '<html><body style="margin:0;display:flex;justify-content:center">'
            f'<img src="data:image/png;base64,{b64}" style="max-width:100%">'
            '</body></html>'
        )

    @staticmethod
    def get_supported_formats(render_lib):
        """Retorna formatos disponíveis baseado na lib e nas deps instaladas."""
        import importlib.util

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

    def _validate_config(self, config):
        """Valida e converte tipos dos parâmetros.

        Unificado com BaseAnalyzerPlugin/BaseDocumentPlugin.
        """
        meta = self.meta()
        validated = {}
        for param_name, param_spec in meta.parameters.items():
            if param_name == "output_format":
                continue  # já extraído no render()
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

    def validate_config(self, config):
        """Valida config e retorna (ok, error_msg)."""
        try:
            self._validate_config(config)
            return True, None
        except Exception as e:
            return False, str(e)

    def _validate_data(self, data):
        """Verifica que campos requeridos existem nos dados."""
        meta = self.meta()
        if meta.requires:
            for field in meta.requires:
                if field not in data:
                    raise ValueError(
                        f"Visualizador '{meta.id}' requer campo '{field}' nos dados. "
                        f"Campos disponíveis: {list(data.keys())}"
                    )
```

- [ ] **Step 2: Rodar testes existentes pra ver o que quebra (esperado: muitos falham)**

Run: `source .venv/bin/activate && pytest tests/test_core.py -x -q 2>&1 | tail -10`
Expected: falhas por signature mismatch — isso é esperado, vamos corrigir nos próximos tasks.

- [ ] **Step 3: Commit**

```bash
~/.claude/scripts/commit.sh "refactor: BaseVisualizerPlugin — plugin retorna figura, BaseClass serializa"
```

### Task 3: Atualizar engine.py branch VISUALIZER

**Files:**
- Modify: `qualia/core/engine.py:129-141`

- [ ] **Step 1: Substituir branch VISUALIZER**

Substituir linhas 129-141 de `qualia/core/engine.py` por:

```python
        elif metadata.type == PluginType.VISUALIZER:
            # Monta dados combinados de todas as dependências
            data = {}
            for dep_result in dep_results.values():
                if isinstance(dep_result, dict):
                    data.update(dep_result)
            result = plugin.render(data, config)
            # result já é dict com "html" ou "data"+"encoding"+"format"
```

Removido: `output_path`, wrapping em `{"output_path": ...}`, isinstance check de Path.

- [ ] **Step 2: Verificar que import de Path pode ser removido se não usado em outro lugar do engine**

Run: `grep -n "Path" qualia/core/engine.py`

Se Path ainda é usado (provavelmente sim, em outros branches), manter o import.

- [ ] **Step 3: Commit**

```bash
~/.claude/scripts/commit.sh "refactor: engine VISUALIZER branch — remove output_path, recebe dict direto"
```

---

## Chunk 2: Plugins — Reescrever os 3 Visualizers

### Task 4: Criar frequency_chart_plotly (substituir frequency_chart)

**Files:**
- Delete: `plugins/frequency_chart/`
- Create: `plugins/frequency_chart_plotly/__init__.py`

- [ ] **Step 1: Deletar plugin antigo**

```bash
rm -rf plugins/frequency_chart/
```

- [ ] **Step 2: Criar novo plugin**

Criar `plugins/frequency_chart_plotly/__init__.py`:

```python
"""Frequency Chart — visualizador de frequência de palavras usando Plotly."""

import plotly.graph_objects as go

from qualia.core import BaseVisualizerPlugin, PluginMetadata, PluginType


class FrequencyChartPlotly(BaseVisualizerPlugin):
    """Gráfico de frequência de palavras com múltiplos estilos via Plotly."""

    RENDER_LIB = "plotly"

    def meta(self):
        return PluginMetadata(
            id="frequency_chart_plotly",
            name="Frequency Chart (Plotly)",
            version="2.0.0",
            description="Gráfico de frequência de palavras usando Plotly — bar, horizontal, line ou area",
            type=PluginType.VISUALIZER,
            requires=["word_frequencies"],
            provides=[],
            parameters={
                "chart_type": {
                    "type": "str", "default": "bar",
                    "options": ["bar", "horizontal_bar", "line", "area"],
                    "description": "Tipo de gráfico",
                },
                "max_items": {
                    "type": "int", "default": 20, "range": [5, 100],
                    "description": "Número máximo de palavras",
                },
                "title": {
                    "type": "str", "default": "Word Frequency",
                    "description": "Título do gráfico",
                },
                "color_scheme": {
                    "type": "str", "default": "Viridis",
                    "options": ["Viridis", "Plasma", "Blues", "Reds", "YlOrRd", "Cividis"],
                    "description": "Esquema de cores",
                },
                "output_format": {
                    "type": "str", "default": "html",
                    "options": self.get_supported_formats("plotly"),
                    "description": "Formato de saída",
                },
            },
        )

    def _render_impl(self, data, config):
        frequencies = data["word_frequencies"]
        sorted_items = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
        sorted_items = sorted_items[:config.get("max_items", 20)]

        if not sorted_items:
            return "<html><body><p>Nenhum dado para visualizar</p></body></html>"

        words, counts = zip(*sorted_items)
        words, counts = list(words), list(counts)
        chart_type = config.get("chart_type", "bar")
        color_scheme = config.get("color_scheme", "Viridis")
        title = config.get("title", "Word Frequency")

        if chart_type == "horizontal_bar":
            fig = go.Figure(go.Bar(
                y=words[::-1], x=counts[::-1],
                orientation='h',
                marker=dict(color=counts[::-1], colorscale=color_scheme),
            ))
        elif chart_type in ("line", "area"):
            fill = 'tozeroy' if chart_type == "area" else None
            fig = go.Figure(go.Scatter(
                x=words, y=counts,
                mode='lines+markers', fill=fill,
                line=dict(color='#636EFA'),
            ))
        else:  # bar (default)
            fig = go.Figure(go.Bar(
                x=words, y=counts,
                marker=dict(color=counts, colorscale=color_scheme),
            ))

        fig.update_layout(
            title=title,
            template="plotly_dark",
            margin=dict(l=60, r=40, t=60, b=100),
            xaxis=dict(tickangle=-45) if chart_type != "horizontal_bar" else {},
        )
        return fig
```

- [ ] **Step 3: Verificar que o plugin é descoberto**

Run: `source .venv/bin/activate && python -c "from qualia.core.engine import QualiaCore; c = QualiaCore(); print([p for p in c.registry if 'frequency' in p])"`
Expected: `['frequency_chart_plotly']`

- [ ] **Step 4: Commit**

```bash
~/.claude/scripts/commit.sh "refactor: frequency_chart → frequency_chart_plotly — retorna plotly.Figure"
```

### Task 5: Criar wordcloud_d3 (substituir wordcloud_viz)

**Files:**
- Delete: `plugins/wordcloud_viz/`
- Create: `plugins/wordcloud_d3/__init__.py`

- [ ] **Step 1: Deletar plugin antigo**

```bash
rm -rf plugins/wordcloud_viz/
```

- [ ] **Step 2: Criar novo plugin**

Criar `plugins/wordcloud_d3/__init__.py`. Este plugin retorna HTML string com D3.js cloud layout — é o mais simples pois já era HTML no plugin anterior. Copiar a lógica do `_generate_html()` do plugin antigo, adaptando pra retornar string ao invés de escrever em arquivo.

Ler `plugins/wordcloud_viz/__init__.py` (já deletado — mas o conteúdo está no git: `git show HEAD:plugins/wordcloud_viz/__init__.py`) pra extrair o HTML template D3.js.

```python
"""Word Cloud D3 — nuvem de palavras interativa usando D3.js."""

from qualia.core import BaseVisualizerPlugin, PluginMetadata, PluginType


class WordCloudD3(BaseVisualizerPlugin):
    """Nuvem de palavras interativa com D3.js cloud layout."""

    RENDER_LIB = "html"

    def meta(self):
        return PluginMetadata(
            id="wordcloud_d3",
            name="Word Cloud (D3.js)",
            version="2.0.0",
            description="Nuvem de palavras interativa usando D3.js — gera HTML",
            type=PluginType.VISUALIZER,
            requires=["word_frequencies"],
            provides=[],
            parameters={
                "max_words": {
                    "type": "int", "default": 100, "range": [10, 500],
                    "description": "Número máximo de palavras",
                },
                "width": {
                    "type": "int", "default": 800, "range": [400, 2000],
                    "description": "Largura em pixels",
                },
                "height": {
                    "type": "int", "default": 400, "range": [200, 1200],
                    "description": "Altura em pixels",
                },
                "colormap": {
                    "type": "str", "default": "category10",
                    "options": ["category10", "set1", "set2", "set3", "paired"],
                    "description": "Paleta de cores D3",
                },
                "output_format": {
                    "type": "str", "default": "html",
                    "options": self.get_supported_formats("html"),
                    "description": "Formato de saída",
                },
            },
        )

    def _render_impl(self, data, config):
        """Gera HTML com D3.js word cloud."""
        frequencies = data["word_frequencies"]
        max_words = config.get("max_words", 100)
        width = config.get("width", 800)
        height = config.get("height", 400)
        colormap = config.get("colormap", "category10")

        sorted_words = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)[:max_words]
        if not sorted_words:
            return "<html><body><p>Nenhum dado para visualizar</p></body></html>"

        max_freq = sorted_words[0][1] if sorted_words else 1
        # Gerar JSON de words pra D3 (json.dumps escapa aspas e caracteres especiais)
        import json
        words_json = ", ".join(
            f'{{"text": {json.dumps(w)}, "size": {max(12, int(60 * c / max_freq))}, "count": {c}}}'
            for w, c in sorted_words
        )

        # Template HTML com D3.js cloud layout inline
        return f'''<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<script src="https://d3js.org/d3.v7.min.js"></script>
<script src="https://cdn.jsdelivr.net/gh/jasondavies/d3-cloud/build/d3.layout.cloud.js"></script>
<style>
  body {{ margin: 0; background: #1a1a2e; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
  .tooltip {{ position: absolute; background: rgba(0,0,0,0.8); color: #fff; padding: 6px 10px; border-radius: 4px; font-size: 13px; pointer-events: none; }}
</style>
</head><body>
<script>
var words = [{words_json}];
var schemes = {{"category10": d3.schemeCategory10, "set1": d3.schemeSet1, "set2": d3.schemeSet2, "set3": d3.schemeSet3, "paired": d3.schemePaired}};
var color = d3.scaleOrdinal(schemes["{colormap}"] || d3.schemeCategory10);
var tooltip = d3.select("body").append("div").attr("class", "tooltip").style("opacity", 0);

d3.layout.cloud().size([{width}, {height}])
  .words(words)
  .padding(3)
  .rotate(function() {{ return ~~(Math.random() * 2) * 90; }})
  .font("Arial")
  .fontSize(function(d) {{ return d.size; }})
  .on("end", draw)
  .start();

function draw(words) {{
  d3.select("body").append("svg")
    .attr("width", {width}).attr("height", {height})
    .append("g").attr("transform", "translate({width/2},{height/2})")
    .selectAll("text").data(words).enter().append("text")
    .style("font-size", function(d) {{ return d.size + "px"; }})
    .style("font-family", "Arial")
    .style("fill", function(d, i) {{ return color(i); }})
    .style("cursor", "pointer")
    .attr("text-anchor", "middle")
    .attr("transform", function(d) {{ return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")"; }})
    .text(function(d) {{ return d.text; }})
    .on("mouseover", function(event, d) {{
      tooltip.transition().duration(200).style("opacity", .9);
      tooltip.html(d.text + ": " + d.count).style("left", (event.pageX + 10) + "px").style("top", (event.pageY - 28) + "px");
    }})
    .on("mouseout", function() {{ tooltip.transition().duration(500).style("opacity", 0); }});
}}
</script>
</body></html>'''
```

- [ ] **Step 3: Verificar descoberta**

Run: `source .venv/bin/activate && python -c "from qualia.core.engine import QualiaCore; c = QualiaCore(); print([p for p in c.registry if 'cloud' in p or 'wordcloud' in p or 'word' in p.lower()])"`
Expected: `['wordcloud_d3']`

- [ ] **Step 4: Commit**

```bash
~/.claude/scripts/commit.sh "refactor: wordcloud_viz → wordcloud_d3 — retorna HTML D3.js direto"
```

### Task 6: Criar sentiment_viz_plotly (substituir sentiment_viz)

**Files:**
- Delete: `plugins/sentiment_viz/`
- Create: `plugins/sentiment_viz_plotly/__init__.py`

- [ ] **Step 1: Deletar plugin antigo**

```bash
rm -rf plugins/sentiment_viz/
```

- [ ] **Step 2: Criar novo plugin**

Este é o mais complexo — 4 chart types. O antigo usava matplotlib pro `distribution`; no novo, tudo é plotly.

Ler o antigo via `git show HEAD:plugins/sentiment_viz/__init__.py` pra preservar a lógica dos 4 renderers, convertendo `distribution` de matplotlib pra plotly.

Criar `plugins/sentiment_viz_plotly/__init__.py`:

```python
"""Sentiment Visualizer — dashboards e gráficos de sentimento usando Plotly."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from qualia.core import BaseVisualizerPlugin, PluginMetadata, PluginType


class SentimentVizPlotly(BaseVisualizerPlugin):
    """Visualizações de sentimento com múltiplos estilos via Plotly."""

    RENDER_LIB = "plotly"

    def meta(self):
        return PluginMetadata(
            id="sentiment_viz_plotly",
            name="Sentiment Visualizer (Plotly)",
            version="2.0.0",
            description="Dashboard, gauge, timeline e distribuição de sentimento via Plotly",
            type=PluginType.VISUALIZER,
            requires=["polarity", "subjectivity"],
            provides=[],
            parameters={
                "chart_type": {
                    "type": "str", "default": "dashboard",
                    "options": ["dashboard", "gauge", "timeline", "distribution"],
                    "description": "Tipo de visualização",
                },
                "color_scheme": {
                    "type": "str", "default": "default",
                    "options": ["default", "colorblind", "pastel"],
                    "description": "Esquema de cores",
                },
                "show_examples": {
                    "type": "bool", "default": True,
                    "description": "Mostrar exemplos de frases",
                },
                "output_format": {
                    "type": "str", "default": "html",
                    "options": self.get_supported_formats("plotly"),
                    "description": "Formato de saída",
                },
            },
        )

    def _render_impl(self, data, config):
        chart_type = config.get("chart_type", "dashboard")
        if chart_type == "dashboard":
            return self._render_dashboard(data, config)
        elif chart_type == "gauge":
            return self._render_gauge(data, config)
        elif chart_type == "timeline":
            return self._render_timeline(data, config)
        elif chart_type == "distribution":
            return self._render_distribution(data, config)
        else:
            raise ValueError(f"chart_type desconhecido: {chart_type}")

    def _get_sentiment_color(self, polarity):
        if polarity > 0.1:
            return "#2ecc71"
        elif polarity < -0.1:
            return "#e74c3c"
        return "#95a5a6"

    def _render_dashboard(self, data, config):
        """Dashboard com gauges de polaridade e subjetividade + extras."""
        polarity = data["polarity"]
        subjectivity = data["subjectivity"]

        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "pie"}, {"type": "scatter"}]],
            subplot_titles=["Polaridade", "Subjetividade", "Distribuição", "Timeline"]
        )

        # Gauge de polaridade
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=polarity,
            gauge=dict(axis=dict(range=[-1, 1]),
                      bar=dict(color=self._get_sentiment_color(polarity)),
                      steps=[
                          dict(range=[-1, -0.1], color="#fadbd8"),
                          dict(range=[-0.1, 0.1], color="#f0f0f0"),
                          dict(range=[0.1, 1], color="#d5f5e3"),
                      ]),
        ), row=1, col=1)

        # Gauge de subjetividade
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=subjectivity,
            gauge=dict(axis=dict(range=[0, 1]),
                      bar=dict(color="#3498db")),
        ), row=1, col=2)

        # Distribuição de sentimento (se disponível)
        sentiment_stats = data.get("sentiment_stats", {})
        if sentiment_stats:
            labels = list(sentiment_stats.keys())
            values = list(sentiment_stats.values())
            colors = [self._get_sentiment_color(1 if l == "positive" else -1 if l == "negative" else 0) for l in labels]
            fig.add_trace(go.Pie(labels=labels, values=values, marker=dict(colors=colors)), row=2, col=1)

        # Timeline (se disponível)
        sentences = data.get("sentence_sentiments", [])
        if sentences:
            polarities = [s.get("polarity", 0) for s in sentences]
            colors = [self._get_sentiment_color(p) for p in polarities]
            fig.add_trace(go.Scatter(
                y=polarities, mode='lines+markers',
                marker=dict(color=colors, size=8),
                line=dict(color='#636EFA'),
            ), row=2, col=2)

        fig.update_layout(
            template="plotly_dark", height=700,
            showlegend=False, margin=dict(l=40, r=40, t=60, b=40),
        )
        return fig

    def _render_gauge(self, data, config):
        """Gauge simples de polaridade."""
        polarity = data["polarity"]
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=polarity,
            delta=dict(reference=0),
            gauge=dict(
                axis=dict(range=[-1, 1]),
                bar=dict(color=self._get_sentiment_color(polarity)),
                steps=[
                    dict(range=[-1, -0.1], color="#fadbd8"),
                    dict(range=[-0.1, 0.1], color="#f0f0f0"),
                    dict(range=[0.1, 1], color="#d5f5e3"),
                ],
            ),
            title=dict(text="Polaridade do Sentimento"),
        ))
        fig.update_layout(template="plotly_dark", height=400)
        return fig

    def _render_timeline(self, data, config):
        """Timeline de sentimento por frase."""
        sentences = data.get("sentence_sentiments", [])
        if not sentences:
            return "<html><body><p>Sem dados de sentimento por frase</p></body></html>"

        polarities = [s.get("polarity", 0) for s in sentences]
        texts = [s.get("text", f"Frase {i+1}")[:50] for i, s in enumerate(sentences)]
        colors = [self._get_sentiment_color(p) for p in polarities]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(1, len(polarities) + 1)),
            y=polarities,
            mode='lines+markers',
            marker=dict(color=colors, size=10),
            text=texts, hovertemplate="%{text}<br>Polaridade: %{y:.2f}<extra></extra>",
        ))

        # Bandas de referência
        fig.add_hrect(y0=0.1, y1=1, fillcolor="#2ecc71", opacity=0.1, line_width=0)
        fig.add_hrect(y0=-0.1, y1=0.1, fillcolor="#95a5a6", opacity=0.1, line_width=0)
        fig.add_hrect(y0=-1, y1=-0.1, fillcolor="#e74c3c", opacity=0.1, line_width=0)

        fig.update_layout(
            title="Sentimento por Frase",
            xaxis_title="Frase", yaxis_title="Polaridade",
            yaxis=dict(range=[-1.1, 1.1]),
            template="plotly_dark", height=450,
        )
        return fig

    def _render_distribution(self, data, config):
        """Distribuição de sentimento — reescrito em Plotly (era matplotlib)."""
        polarity = data["polarity"]
        subjectivity = data["subjectivity"]

        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "pie"}, {"type": "bar"}]],
            subplot_titles=["Distribuição", "Métricas"]
        )

        # Pie chart de distribuição
        sentiment_stats = data.get("sentiment_stats", {})
        if sentiment_stats:
            labels = list(sentiment_stats.keys())
            values = list(sentiment_stats.values())
        else:
            # Inferir da polaridade
            if polarity > 0.1:
                labels, values = ["Positivo", "Neutro"], [70, 30]
            elif polarity < -0.1:
                labels, values = ["Negativo", "Neutro"], [70, 30]
            else:
                labels, values = ["Neutro", "Positivo", "Negativo"], [60, 20, 20]

        colors = [self._get_sentiment_color(1 if "pos" in l.lower() else -1 if "neg" in l.lower() else 0) for l in labels]
        fig.add_trace(go.Pie(labels=labels, values=values, marker=dict(colors=colors)), row=1, col=1)

        # Métricas em bar chart
        metrics = {"Polaridade": polarity, "Subjetividade": subjectivity}
        avg_polarity = data.get("avg_polarity")
        if avg_polarity is not None:
            metrics["Média"] = avg_polarity

        fig.add_trace(go.Bar(
            x=list(metrics.keys()), y=list(metrics.values()),
            marker=dict(color=[self._get_sentiment_color(v) for v in metrics.values()]),
        ), row=1, col=2)

        fig.update_layout(template="plotly_dark", height=400, showlegend=True)
        return fig
```

- [ ] **Step 3: Verificar descoberta**

Run: `source .venv/bin/activate && python -c "from qualia.core.engine import QualiaCore; c = QualiaCore(); print([p for p in c.registry if 'sentiment' in p])"`
Expected: `['sentiment_viz_plotly']`

- [ ] **Step 4: Commit**

```bash
~/.claude/scripts/commit.sh "refactor: sentiment_viz → sentiment_viz_plotly — 4 chart types, tudo plotly"
```

---

## Chunk 3: API, CLI, Frontend

### Task 7: Simplificar rota /visualize

**Files:**
- Modify: `qualia/api/routes/visualize.py`
- Modify: `qualia/api/schemas.py:22` (mudar default de output_format de "png" pra "html")

- [ ] **Step 1: Reescrever visualize.py**

Substituir o conteúdo inteiro de `qualia/api/routes/visualize.py`:

```python
"""Rota de visualização — plugin renderiza, BaseClass serializa."""

import asyncio

from fastapi import APIRouter, HTTPException

from qualia.api.deps import get_core, track, validate_plugin_config, require_plugin_type
from qualia.api.schemas import VisualizeRequest

router = APIRouter()


@router.post("/visualize/{plugin_id}")
async def visualize(plugin_id: str, request: VisualizeRequest):
    """Gera visualização usando plugin especificado.

    Retorna dict com "html" (string HTML) ou "data"+"encoding"+"format" (base64 imagem).
    """
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
        await track(f"/visualize/{plugin_id}", plugin_id, "timeout")
        raise HTTPException(status_code=504, detail=f"Plugin '{plugin_id}' timed out (60s)")
    except HTTPException:
        raise
    except Exception as e:
        await track(f"/visualize/{plugin_id}", plugin_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))

    await track(f"/visualize/{plugin_id}", plugin_id)

    return {"status": "success", "plugin_id": plugin_id, **result}
```

- [ ] **Step 2: Atualizar default em schemas.py**

Em `qualia/api/schemas.py`, linha 22, mudar default de `"png"` pra `"html"`:

```python
    output_format: str = Field("html", description="Output format: html, png, svg")
```

- [ ] **Step 3: Commit**

```bash
~/.claude/scripts/commit.sh "refactor: rota /visualize simplificada — sem temp files, sem FileResponse"
```

### Task 8: Atualizar CLI visualize command

**Files:**
- Modify: `qualia/cli/commands/visualize.py`

- [ ] **Step 1: Ler arquivo atual**

Run: `cat qualia/cli/commands/visualize.py` pra entender a estrutura atual completa.

- [ ] **Step 2: Atualizar a seção de execução**

A mudança principal: `plugin_instance.render(data, params, output_path)` → `plugin_instance.render(data, params_with_format)` que retorna dict. Depois salvar baseado no dict.

Encontrar a chamada `plugin_instance.render(data, params, output_path)` (por volta da linha 146) e substituir o bloco de execução + salvamento:

```python
        # Adicionar output_format ao config
        params_with_format = {**params, "output_format": format_ext}
        result = plugin_instance.render(data, params_with_format)

        # Salvar resultado
        if "html" in result:
            output_path = output_path.with_suffix(".html") if output_path.suffix not in (".html",) else output_path
            output_path.write_text(result["html"], encoding="utf-8")
        elif "data" in result and result.get("encoding") == "base64":
            import base64 as b64_mod
            fmt = result.get("format", "png")
            output_path = output_path.with_suffix(f".{fmt}") if output_path.suffix != f".{fmt}" else output_path
            output_path.write_bytes(b64_mod.b64decode(result["data"]))
        else:
            click.echo(f"Resultado inesperado do plugin: {list(result.keys())}", err=True)
            raise SystemExit(1)
```

Remover a lógica antiga de output_path pré-render e format auto-detection complexa. O format agora vai direto pro plugin via config.

- [ ] **Step 3: Atualizar feedback pós-render**

Ajustar as mensagens de sucesso pra usar o output_path atualizado (que agora pode ter mudado de sufixo).

- [ ] **Step 4: Commit**

```bash
~/.claude/scripts/commit.sh "refactor: CLI visualize — salva dict do plugin ao invés de Path"
```

### Task 9: Atualizar CLI interactive actions

**Files:**
- Modify: `qualia/cli/interactive/actions.py`

- [ ] **Step 1: Ler e entender a função execute_visualization**

A função chama o CLI command como subprocess, então pode não precisar de mudança direta — ela invoca `visualize` como command Click, que já foi atualizado no Task 8. Verificar se há chamada direta a `plugin.render()`.

Run: `grep -n "render\|output_path\|visualiz" qualia/cli/interactive/actions.py`

A função delega pra `run_qualia_command(["visualize", ...])`, ou seja, invoca o CLI command (já atualizado no Task 8). **Nenhuma mudança necessária em actions.py.**

Nota: os testes em `tests/test_cli_interactive.py` referenciam `wordcloud_viz` — serão atualizados no Task 11.

### Task 10: Atualizar frontend

**Files:**
- Modify: `qualia/frontend/src/components/ResultView.svelte`
- Modify: `qualia/frontend/src/lib/api.js`

- [ ] **Step 1: Atualizar detectType em ResultView.svelte**

Encontrar a função `detectType` (por volta da linha 8-15) e substituir:

```javascript
function detectType(r) {
    if (!r) return 'empty';
    if (r.encoding === 'base64') return 'image';
    if (r.html) return 'html';
    return 'json';
}
```

Mudança: `r.format === 'html'` → `r.html` (checa a key diretamente).

- [ ] **Step 2: Atualizar invocação do HtmlResult**

Encontrar onde `HtmlResult` é invocado e mudar prop de `html={result.data}` pra `html={result.html}`:

```svelte
<HtmlResult html={result.html} />
```

- [ ] **Step 3: Atualizar api.js default**

Em `qualia/frontend/src/lib/api.js`, encontrar a função `visualize` e mudar default de `'png'` pra `'html'`:

```javascript
export function visualize(pluginId, data, config = {}, outputFormat = 'html') {
```

- [ ] **Step 4: Commit**

```bash
~/.claude/scripts/commit.sh "refactor: frontend — detectType checa r.html, default output_format html"
```

---

## Chunk 4: Testes + Docs

### Task 11: Reescrever testes de visualização

**Files:**
- Modify: `tests/test_api_extended.py` (TestVisualizeEndpoint, TestVisualizeEdgeCases, TestPipelineEndpoint)
- Modify: `tests/test_core.py` (testes de VISUALIZER branch — output_path, render signature)
- Modify: `tests/test_cli.py` (referências a wordcloud_viz, frequency_chart)
- Modify: `tests/test_cli_extended.py` (TestVisualizeCommand — IDs, render mocks, output)
- Modify: `tests/test_cli_remaining.py` (40+ testes com render(data, params, output_path) mockado)
- Modify: `tests/test_cli_final.py` (pipeline tests com wordcloud_viz)
- Modify: `tests/test_cli_interactive.py` (15+ referências a wordcloud_viz em menu tests)
- Modify: `tests/test_pragmatic.py` (testes que usam visualizers)
- Modify: `tests/test_async.py` (referências a wordcloud_viz)
- Modify: `tests/test_cache_deps.py` (referências a wordcloud_viz, sentiment_viz no resolver)

- [ ] **Step 1: Atualizar testes da API**

Os testes em `TestVisualizeEndpoint` e `TestVisualizeEdgeCases` precisam:
- Mudar plugin IDs: `frequency_chart` → `frequency_chart_plotly`, `wordcloud_viz` → `wordcloud_d3`, `sentiment_viz` → `sentiment_viz_plotly`
- Mudar assertivas de response shape: verificar `result["html"]` ou `result["data"]` ao invés de base64/format antigo
- Remover testes de FileResponse e temp file cleanup
- Atualizar `output_format` default de `"png"` pra `"html"`

- [ ] **Step 2: Atualizar testes do core**

Os testes em `test_core.py` que testam branch VISUALIZER precisam:
- Remover assertivas de `output_path` no resultado
- Verificar que resultado é dict com `html` ou `data`+`encoding`
- Atualizar mocks que passam `output_path` pro render

- [ ] **Step 3: Atualizar testes da CLI (todos os arquivos)**

Múltiplos test files referenciam plugins antigos e a signature `render(data, params, output_path)`:

**`test_cli.py`:** replace `wordcloud_viz` → `wordcloud_d3`, `frequency_chart` → `frequency_chart_plotly`

**`test_cli_extended.py` (TestVisualizeCommand):** mudar IDs, atualizar mocks de `render()` pra 2 args (sem output_path), atualizar assertivas de output (.html default)

**`test_cli_remaining.py` (40+ testes):** Este é o mais trabalhoso. Todos os mocks de `plugin.render(data, params, output_path)` precisam mudar pra `plugin.render(data, params)` retornando dict. O return_value muda de `Path("fake.png")` pra `{"html": "<html>...</html>"}`.

**`test_cli_final.py`:** pipeline tests com `wordcloud_viz` → `wordcloud_d3`

**`test_cli_interactive.py`:** referências a `wordcloud_viz` em menu tests → `wordcloud_d3`

**`test_async.py`:** referência a `wordcloud_viz` → `wordcloud_d3`

**`test_cache_deps.py`:** referências a `wordcloud_viz`, `sentiment_viz` no resolver → novos IDs

Estratégia: usar search-and-replace global nos IDs (`wordcloud_viz` → `wordcloud_d3`, `frequency_chart` → `frequency_chart_plotly`, `sentiment_viz` → `sentiment_viz_plotly`), depois corrigir manualmente os mocks de `render()` e assertivas de output.

- [ ] **Step 4: Atualizar testes pragmáticos**

Testes em `test_pragmatic.py` que usam visualizers — mudar IDs.

- [ ] **Step 5: Rodar suite completa**

Run: `source .venv/bin/activate && pytest tests/ -q 2>&1 | tail -10`
Expected: todos passando (pode precisar de ajustes iterativos)

- [ ] **Step 6: Commit**

```bash
~/.claude/scripts/commit.sh "test: reescreve testes de visualização — novos IDs, response shape, sem output_path"
```

### Task 12: Atualizar documentação

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/TECHNICAL_STATE.md`
- Modify: `README.md`

- [ ] **Step 1: Atualizar CLAUDE.md**

Mudar nomes dos plugins na lista de existentes:
```
wordcloud_viz → wordcloud_d3
frequency_chart → frequency_chart_plotly
sentiment_viz → sentiment_viz_plotly
```

Atualizar qualquer menção a output_path ou formatos na seção de plugins.

- [ ] **Step 2: Atualizar TECHNICAL_STATE.md**

Atualizar tabela de plugins com novos nomes e notas sobre rendering.

- [ ] **Step 3: Atualizar README.md**

Se menciona plugins específicos, atualizar nomes.

- [ ] **Step 4: Rodar suite final**

Run: `source .venv/bin/activate && pytest tests/ --cov=qualia --cov-report=term-missing -q 2>&1 | tail -20`
Verificar coverage e total de testes.

- [ ] **Step 5: Commit**

```bash
~/.claude/scripts/commit.sh "docs: atualiza nomes dos visualizers e arquitetura de rendering"
```
