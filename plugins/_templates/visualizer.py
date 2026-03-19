"""
__PLUGIN_TITLE__ - Visualizer plugin para Qualia Core

Criado em: __DATE__

Arquitetura de rendering:
  - _render_impl(data, config) retorna um objeto de figura ou HTML string
  - O BaseVisualizerPlugin._serialize() detecta o tipo via duck-typing e serializa
  - O consumer escolhe o formato via output_format no config
  - Formatos disponiveis sao detectados automaticamente baseado nas libs instaladas

Tipos de retorno suportados:
  - plotly.Figure  → HTML interativo (sempre) ou PNG/SVG (se kaleido instalado)
  - matplotlib.Figure → HTML (img inline) ou PNG/SVG (nativo)
  - str (HTML) → HTML direto (sem conversao pra imagem)
"""

from typing import Dict, Any
from qualia.core import BaseVisualizerPlugin, PluginMetadata, PluginType

# Escolha UMA lib de rendering e descomente:
# import plotly.graph_objects as go       # RENDER_LIB = "plotly"
# import matplotlib.pyplot as plt         # RENDER_LIB = "matplotlib"
# (ou retorne HTML string puro)           # RENDER_LIB = "html"


class __CLASS_NAME__(BaseVisualizerPlugin):
    """
    TODO: Descreva o que este visualizer faz.

    Exemplo de uso:
        qualia visualize data.json -p __PLUGIN_ID__
        qualia visualize data.json -p __PLUGIN_ID__ -P theme=dark
    """

    # Declare qual lib de rendering este plugin usa.
    # Isso controla quais formatos de saida ficam disponiveis:
    #   "plotly"     → html (sempre), png/svg (se kaleido instalado)
    #   "matplotlib" → html, png, svg (todos nativos)
    #   "html"       → apenas html
    RENDER_LIB = "plotly"

    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="__PLUGIN_ID__",
            name="__PLUGIN_TITLE__",
            type=PluginType.VISUALIZER,
            version="0.1.0",
            description="TODO: descreva o plugin",

            # Dados necessarios (campos que devem existir no input)
            # O engine resolve dependencias automaticamente:
            # se requires=["word_frequencies"], o engine roda word_frequency antes.
            # Exemplos: ["word_frequencies"], ["polarity", "subjectivity"], ["clusters"]
            requires=[
                "data_field",  # TODO: mude para o campo real
            ],

            # Visualizers NAO declaram provides (retornam visualizacao, nao dados).
            provides=[],

            parameters={
                "theme": {
                    "type": "str",
                    "options": ["light", "dark"],
                    "default": "dark",
                    "description": "Tema visual"
                },
            }
        )

    def _render_impl(self, data: Dict[str, Any], config: Dict[str, Any]):
        """
        Gera a visualizacao e retorna o objeto de figura.

        O BaseClass cuida da serializacao — voce so precisa retornar:
          - plotly.Figure (se RENDER_LIB = "plotly")
          - matplotlib.Figure (se RENDER_LIB = "matplotlib")
          - str HTML (se RENDER_LIB = "html")

        Args:
            data: Dados para visualizar (vem de analyzers via requires)
            config: Configuracoes validadas com defaults aplicados

        Returns:
            Objeto de figura nativo da lib escolhida
        """
        import plotly.graph_objects as go

        theme = config.get('theme', 'dark')
        template = 'plotly_dark' if theme == 'dark' else 'plotly_white'

        required_data = data.get('data_field', {})
        if not required_data:
            raise ValueError("Dados necessarios nao encontrados: 'data_field'")

        # TODO: implemente sua visualizacao aqui
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=list(required_data.keys()),
            y=list(required_data.values()),
        ))
        fig.update_layout(
            title=self.meta().name,
            template=template,
        )

        return fig  # BaseClass serializa pro formato que o consumer pediu
