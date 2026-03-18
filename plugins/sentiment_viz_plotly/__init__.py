"""Sentiment Visualizer — dashboards e gráficos de sentimento usando Plotly."""

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
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        polarity = data["polarity"]
        subjectivity = data["subjectivity"]

        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "pie"}, {"type": "scatter"}]],
            subplot_titles=["Polaridade", "Subjetividade", "Distribuição", "Timeline"]
        )

        fig.add_trace(go.Indicator(
            mode="gauge+number", value=polarity,
            gauge=dict(axis=dict(range=[-1, 1]),
                      bar=dict(color=self._get_sentiment_color(polarity)),
                      steps=[
                          dict(range=[-1, -0.1], color="#fadbd8"),
                          dict(range=[-0.1, 0.1], color="#f0f0f0"),
                          dict(range=[0.1, 1], color="#d5f5e3"),
                      ]),
        ), row=1, col=1)

        fig.add_trace(go.Indicator(
            mode="gauge+number", value=subjectivity,
            gauge=dict(axis=dict(range=[0, 1]), bar=dict(color="#3498db")),
        ), row=1, col=2)

        sentiment_stats = data.get("sentiment_stats", {})
        if sentiment_stats:
            labels = list(sentiment_stats.keys())
            values = list(sentiment_stats.values())
            colors = [self._get_sentiment_color(1 if l == "positive" else -1 if l == "negative" else 0) for l in labels]
            fig.add_trace(go.Pie(labels=labels, values=values, marker=dict(colors=colors)), row=2, col=1)

        sentences = data.get("sentence_sentiments", [])
        if sentences:
            polarities = [s.get("polarity", 0) for s in sentences]
            colors = [self._get_sentiment_color(p) for p in polarities]
            fig.add_trace(go.Scatter(
                y=polarities, mode='lines+markers',
                marker=dict(color=colors, size=8), line=dict(color='#636EFA'),
            ), row=2, col=2)

        fig.update_layout(template="plotly_dark", height=700, showlegend=False, margin=dict(l=40, r=40, t=60, b=40))
        return fig

    def _render_gauge(self, data, config):
        import plotly.graph_objects as go

        polarity = data["polarity"]
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=polarity,
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
        import plotly.graph_objects as go

        sentences = data.get("sentence_sentiments", [])
        if not sentences:
            return "<html><body><p>Sem dados de sentimento por frase</p></body></html>"

        polarities = [s.get("polarity", 0) for s in sentences]
        texts = [s.get("text", f"Frase {i+1}")[:50] for i, s in enumerate(sentences)]
        colors = [self._get_sentiment_color(p) for p in polarities]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(1, len(polarities) + 1)),
            y=polarities, mode='lines+markers',
            marker=dict(color=colors, size=10),
            text=texts, hovertemplate="%{text}<br>Polaridade: %{y:.2f}<extra></extra>",
        ))

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
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        polarity = data["polarity"]
        subjectivity = data["subjectivity"]

        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "pie"}, {"type": "bar"}]],
            subplot_titles=["Distribuição", "Métricas"]
        )

        sentiment_stats = data.get("sentiment_stats", {})
        if sentiment_stats:
            labels = list(sentiment_stats.keys())
            values = list(sentiment_stats.values())
        else:
            if polarity > 0.1:
                labels, values = ["Positivo", "Neutro"], [70, 30]
            elif polarity < -0.1:
                labels, values = ["Negativo", "Neutro"], [70, 30]
            else:
                labels, values = ["Neutro", "Positivo", "Negativo"], [60, 20, 20]

        colors = [self._get_sentiment_color(1 if "pos" in l.lower() else -1 if "neg" in l.lower() else 0) for l in labels]
        fig.add_trace(go.Pie(labels=labels, values=values, marker=dict(colors=colors)), row=1, col=1)

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
