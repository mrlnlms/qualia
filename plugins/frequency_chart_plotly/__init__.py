"""Frequency Chart — visualizador de frequência de palavras usando Plotly."""

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
        import plotly.graph_objects as go

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
