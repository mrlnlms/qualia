# tests/test_visualizer_execution.py
"""Testes de execução real dos visualizer plugins.

Cada teste instancia o plugin, alimenta com dados reais,
e verifica que o resultado é HTML válido.
"""

import pytest
from qualia.core import QualiaCore, Document, PipelineConfig, PipelineStep
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def core():
    tmp = Path(tempfile.mkdtemp())
    c = QualiaCore(plugins_dir=Path(__file__).parent.parent / "plugins", cache_dir=tmp / "cache")
    yield c
    shutil.rmtree(tmp)


@pytest.fixture
def word_freq_data():
    """Dados de word_frequency reais para alimentar visualizers."""
    return {
        "word_frequencies": {
            "análise": 15, "qualitativa": 12, "dados": 10,
            "pesquisa": 8, "entrevista": 7, "texto": 6,
            "resultado": 5, "padrão": 4, "tema": 3, "código": 2,
        }
    }


@pytest.fixture
def sentiment_data():
    """Dados de sentiment_analyzer reais para alimentar visualizers."""
    return {
        "polarity": 0.35,
        "subjectivity": 0.65,
    }


class TestWordCloudD3:
    """Execução real do wordcloud_d3 com dados reais."""

    def test_render_returns_html_dict(self, word_freq_data):
        """render() deve retornar dict com chave 'html'."""
        from plugins.visualizers.wordcloud_d3 import WordCloudD3
        plugin = WordCloudD3()
        result = plugin.render(word_freq_data, {})

        assert isinstance(result, dict)
        assert "html" in result
        assert isinstance(result["html"], str)

    def test_html_contains_d3_script(self, word_freq_data):
        """HTML gerado deve conter referência ao D3.js."""
        from plugins.visualizers.wordcloud_d3 import WordCloudD3
        plugin = WordCloudD3()
        result = plugin.render(word_freq_data, {})

        assert "d3.v7" in result["html"] or "d3js.org" in result["html"]

    def test_html_contains_word_data(self, word_freq_data):
        """HTML gerado deve conter as palavras dos dados."""
        from plugins.visualizers.wordcloud_d3 import WordCloudD3
        plugin = WordCloudD3()
        result = plugin.render(word_freq_data, {})

        # Palavras podem estar unicode-escaped no JSON embutido
        assert "an\\u00e1lise" in result["html"] or "análise" in result["html"]
        assert "qualitativa" in result["html"]

    def test_render_with_custom_config(self, word_freq_data):
        """render() com config customizada deve funcionar."""
        from plugins.visualizers.wordcloud_d3 import WordCloudD3
        plugin = WordCloudD3()
        result = plugin.render(word_freq_data, {"max_words": 5, "width": 600})

        assert isinstance(result, dict)
        assert "html" in result

    def test_render_empty_frequencies(self):
        """render() com dados vazios deve retornar HTML de fallback."""
        from plugins.visualizers.wordcloud_d3 import WordCloudD3
        plugin = WordCloudD3()
        result = plugin.render({"word_frequencies": {}}, {})

        assert isinstance(result, dict)
        assert "html" in result
        assert "Nenhum dado" in result["html"]


class TestFrequencyChartPlotly:
    """Execução real do frequency_chart_plotly com dados reais."""

    def test_render_returns_html_dict(self, word_freq_data):
        """render() deve retornar dict com chave 'html'."""
        from plugins.visualizers.frequency_chart_plotly import FrequencyChartPlotly
        plugin = FrequencyChartPlotly()
        result = plugin.render(word_freq_data, {})

        assert isinstance(result, dict)
        assert "html" in result
        assert isinstance(result["html"], str)

    def test_html_contains_plotly(self, word_freq_data):
        """HTML gerado deve conter Plotly.js."""
        from plugins.visualizers.frequency_chart_plotly import FrequencyChartPlotly
        plugin = FrequencyChartPlotly()
        result = plugin.render(word_freq_data, {})

        assert "plotly" in result["html"].lower()

    @pytest.mark.parametrize("chart_type", ["bar", "horizontal_bar", "line", "area"])
    def test_all_chart_types(self, word_freq_data, chart_type):
        """Todos os tipos de gráfico devem renderizar sem erro."""
        from plugins.visualizers.frequency_chart_plotly import FrequencyChartPlotly
        plugin = FrequencyChartPlotly()
        result = plugin.render(word_freq_data, {"chart_type": chart_type})

        assert isinstance(result, dict)
        assert "html" in result

    def test_render_empty_frequencies(self):
        """render() com dados vazios deve retornar HTML de fallback."""
        from plugins.visualizers.frequency_chart_plotly import FrequencyChartPlotly
        plugin = FrequencyChartPlotly()
        result = plugin.render({"word_frequencies": {}}, {})

        assert isinstance(result, dict)
        assert "html" in result
        assert "Nenhum dado" in result["html"]


class TestSentimentVizPlotly:
    """Execução real do sentiment_viz_plotly com dados reais."""

    def test_render_returns_html_dict(self, sentiment_data):
        """render() deve retornar dict com chave 'html'."""
        from plugins.visualizers.sentiment_viz_plotly import SentimentVizPlotly
        plugin = SentimentVizPlotly()
        result = plugin.render(sentiment_data, {})

        assert isinstance(result, dict)
        assert "html" in result
        assert isinstance(result["html"], str)

    def test_html_contains_plotly(self, sentiment_data):
        """HTML gerado deve conter Plotly.js."""
        from plugins.visualizers.sentiment_viz_plotly import SentimentVizPlotly
        plugin = SentimentVizPlotly()
        result = plugin.render(sentiment_data, {})

        assert "plotly" in result["html"].lower()

    @pytest.mark.parametrize("chart_type", ["dashboard", "gauge", "distribution"])
    def test_chart_types(self, sentiment_data, chart_type):
        """Tipos de gráfico (exceto timeline que precisa de sentence_sentiments) devem renderizar."""
        from plugins.visualizers.sentiment_viz_plotly import SentimentVizPlotly
        plugin = SentimentVizPlotly()
        result = plugin.render(sentiment_data, {"chart_type": chart_type})

        assert isinstance(result, dict)
        assert "html" in result

    def test_timeline_with_sentences(self):
        """Timeline precisa de sentence_sentiments nos dados."""
        from plugins.visualizers.sentiment_viz_plotly import SentimentVizPlotly
        plugin = SentimentVizPlotly()
        data = {
            "polarity": 0.2,
            "subjectivity": 0.5,
            "sentence_sentiments": [
                {"text": "Muito bom", "polarity": 0.8},
                {"text": "Mais ou menos", "polarity": 0.0},
                {"text": "Ruim", "polarity": -0.5},
            ],
        }
        result = plugin.render(data, {"chart_type": "timeline"})

        assert isinstance(result, dict)
        assert "html" in result

    def test_timeline_without_sentences_fallback(self):
        """Timeline sem sentence_sentiments deve retornar HTML de fallback."""
        from plugins.visualizers.sentiment_viz_plotly import SentimentVizPlotly
        plugin = SentimentVizPlotly()
        data = {"polarity": 0.2, "subjectivity": 0.5}
        result = plugin.render(data, {"chart_type": "timeline"})

        assert isinstance(result, dict)
        assert "html" in result
        assert "Sem dados" in result["html"]


class TestVisualizerPipeline:
    """Pipeline completo: analyzer → visualizer via core."""

    def test_word_frequency_to_wordcloud(self, core):
        """Pipeline word_frequency → wordcloud_d3 deve produzir HTML."""
        doc = core.add_document("viz_pipe", "análise qualitativa de dados de pesquisa entrevista texto " * 10)
        pipeline = PipelineConfig(
            name="wf_to_wc",
            steps=[
                PipelineStep("word_frequency"),
                PipelineStep("wordcloud_d3"),
            ],
        )
        results = core.execute_pipeline(pipeline, doc)

        assert "word_frequency" in results
        assert "wordcloud_d3" in results
        assert "html" in results["wordcloud_d3"]
        assert "d3" in results["wordcloud_d3"]["html"].lower() or "análise" in results["wordcloud_d3"]["html"]

    def test_word_frequency_to_frequency_chart(self, core):
        """Pipeline word_frequency → frequency_chart_plotly deve produzir HTML."""
        doc = core.add_document("viz_pipe2", "análise qualitativa de dados de pesquisa " * 10)
        pipeline = PipelineConfig(
            name="wf_to_fc",
            steps=[
                PipelineStep("word_frequency"),
                PipelineStep("frequency_chart_plotly"),
            ],
        )
        results = core.execute_pipeline(pipeline, doc)

        assert "frequency_chart_plotly" in results
        assert "html" in results["frequency_chart_plotly"]
        assert "plotly" in results["frequency_chart_plotly"]["html"].lower()

    def test_sentiment_to_viz(self, core):
        """Pipeline sentiment_analyzer → sentiment_viz_plotly deve produzir HTML."""
        doc = core.add_document("viz_pipe3", "Este produto é excelente e muito bom! Recomendo fortemente. " * 10)
        pipeline = PipelineConfig(
            name="sent_to_viz",
            steps=[
                PipelineStep("sentiment_analyzer", {"language": "pt"}),
                PipelineStep("sentiment_viz_plotly"),
            ],
        )
        results = core.execute_pipeline(pipeline, doc)

        assert "sentiment_viz_plotly" in results
        assert "html" in results["sentiment_viz_plotly"]
