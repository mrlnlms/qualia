# plugins/wordcloud_viz/__init__.py
"""
Plugin de visualização que gera nuvens de palavras
"""

from typing import Dict, Any
from pathlib import Path
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import json

# Importar a base class em vez da interface
from qualia.core import BaseVisualizerPlugin, PluginMetadata, PluginType


class WordCloudVisualizer(BaseVisualizerPlugin):
    """Gera nuvens de palavras a partir de frequências"""
    
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="wordcloud_viz",
            name="Word Cloud Visualizer",
            type=PluginType.VISUALIZER,
            version="1.0.0",
            description="Gera nuvens de palavras a partir de frequências",
            requires=["word_frequencies"],  # Precisa deste campo nos dados
            provides=["visualization_path", "visualization_html"],
            parameters={
                "max_words": {
                    "type": "integer",
                    "default": 100,
                    "description": "Número máximo de palavras na nuvem"
                },
                "width": {
                    "type": "integer", 
                    "default": 800,
                    "description": "Largura da imagem em pixels"
                },
                "height": {
                    "type": "integer",
                    "default": 600,
                    "description": "Altura da imagem em pixels"
                },
                "background_color": {
                    "type": "choice",
                    "options": ["white", "black", "transparent"],
                    "default": "white",
                    "description": "Cor de fundo"
                },
                "colormap": {
                    "type": "choice",
                    "options": ["viridis", "plasma", "inferno", "magma", 
                               "Blues", "Reds", "Greens", "coolwarm"],
                    "default": "viridis",
                    "description": "Esquema de cores"
                },
                "format": {
                    "type": "choice",
                    "options": ["png", "svg", "html"],
                    "default": "png",
                    "description": "Formato de saída"
                },
                "font_family": {
                    "type": "choice",
                    "options": ["sans-serif", "serif", "monospace"],
                    "default": "sans-serif",
                    "description": "Família da fonte"
                },
                "relative_scaling": {
                    "type": "float",
                    "default": 0.5,
                    "description": "Escala relativa (0=freq absoluta, 1=rank)"
                }
            }
        )
    
    def _render_impl(self, data: Dict[str, Any], config: Dict[str, Any], 
                     output_path: Path) -> Path:
        """
        Implementação real da renderização
        
        Nota: Toda validação já foi feita pela BaseVisualizerPlugin:
        - output_path é garantidamente um Path
        - diretório pai já existe
        - config tem todos os defaults aplicados
        - campos obrigatórios nos dados foram validados
        """
        
        # Extrair frequências (já validado que existe)
        frequencies = data['word_frequencies']
        
        # Gerar wordcloud com configurações
        wordcloud = WordCloud(
            width=config['width'],
            height=config['height'],
            max_words=config['max_words'],
            background_color=config['background_color'],
            colormap=config['colormap'],
            relative_scaling=config['relative_scaling'],
            font_path=None  # Usa fonte do sistema
        ).generate_from_frequencies(frequencies)
        
        # Renderizar baseado no formato
        format_type = config['format']
        
        if format_type in ['png', 'svg']:
            # Criar figura matplotlib
            fig, ax = plt.subplots(figsize=(config['width']/100, config['height']/100))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            
            # Ajustar margens
            plt.tight_layout(pad=0)
            
            # Salvar no formato apropriado
            plt.savefig(output_path, format=format_type, 
                       bbox_inches='tight', pad_inches=0,
                       dpi=100 if format_type == 'png' else None)
            plt.close()
            
        elif format_type == 'html':
            # Gerar versão interativa em HTML
            html_content = self._generate_html(frequencies, config)
            output_path.write_text(html_content, encoding='utf-8')
        
        return output_path
    
    def _generate_html(self, frequencies: Dict[str, int], config: Dict[str, Any]) -> str:
        """Gera versão HTML interativa usando D3.js"""
        
        # Preparar dados para JavaScript
        words = [
            {"text": word, "size": count} 
            for word, count in frequencies.items()
        ][:config['max_words']]
        
        # Template HTML com D3.js cloud layout
        template = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Word Cloud - Qualia</title>
    <script src="https://d3js.org/d3.v3.min.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/jasondavies/d3-cloud/build/d3.layout.cloud.js"></script>
    <style>
        body {{
            font-family: {font_family};
            background-color: {bg_color};
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        #wordcloud {{
            background: {bg_color};
            border: 1px solid #ddd;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .word {{
            cursor: pointer;
            transition: opacity 0.3s;
        }}
        .word:hover {{
            opacity: 0.7;
        }}
        #tooltip {{
            position: absolute;
            padding: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border-radius: 5px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div id="wordcloud"></div>
    <div id="tooltip"></div>
    
    <script>
        var words = {words_json};
        
        var width = {width};
        var height = {height};
        
        // Escalas
        var maxSize = Math.max(...words.map(d => d.size));
        var minSize = Math.min(...words.map(d => d.size));
        var sizeScale = d3.scale.linear()
            .domain([minSize, maxSize])
            .range([15, 80]);
        
        // Cores
        var color = d3.scale.category20();
        
        // Layout
        var layout = d3.layout.cloud()
            .size([width, height])
            .words(words)
            .padding(5)
            .rotate(function() {{ return ~~(Math.random() * 2) * 90; }})
            .font("{font_family}")
            .fontSize(function(d) {{ return sizeScale(d.size); }})
            .on("end", draw);
        
        layout.start();
        
        function draw(words) {{
            d3.select("#wordcloud").append("svg")
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", "translate(" + width/2 + "," + height/2 + ")")
                .selectAll("text")
                .data(words)
                .enter().append("text")
                .attr("class", "word")
                .style("font-size", function(d) {{ return d.size + "px"; }})
                .style("font-family", "{font_family}")
                .style("fill", function(d, i) {{ return color(i); }})
                .attr("text-anchor", "middle")
                .attr("transform", function(d) {{
                    return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
                }})
                .text(function(d) {{ return d.text; }})
                .on("mouseover", function(d) {{
                    var tooltip = d3.select("#tooltip");
                    tooltip.html(d.text + ": " + d.size)
                        .style("opacity", 1)
                        .style("left", (d3.event.pageX + 10) + "px")
                        .style("top", (d3.event.pageY - 10) + "px");
                }})
                .on("mouseout", function() {{
                    d3.select("#tooltip").style("opacity", 0);
                }});
        }}
    </script>
</body>
</html>'''
        
        # Preencher template
        return template.format(
            words_json=json.dumps(words),
            width=config['width'],
            height=config['height'],
            font_family=config['font_family'],
            bg_color=config['background_color'] if config['background_color'] != 'transparent' else 'white'
        )


# Exportar plugin
__all__ = ['WordCloudVisualizer']