"""
WordCloud Visualizer Plugin

Gera nuvens de palavras a partir de frequências
Outputs: PNG, SVG, HTML interativo
"""

from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path
import json

from qualia.core import (
    IVisualizerPlugin,
    PluginMetadata,
    PluginType
)


class WordCloudVisualizer(IVisualizerPlugin):
    """
    Cria nuvens de palavras bonitas e informativas
    """
    
    def meta(self) -> PluginMetadata:
        """Plugin para visualização de nuvem de palavras"""
        return PluginMetadata(
            id="wordcloud_viz",
            type=PluginType.VISUALIZER,
            name="Word Cloud Visualizer",
            description="Gera nuvens de palavras a partir de frequências",
            version="1.0.0",
            
            # Aceita dados destes tipos
            accepts=[
                "word_frequencies",    # Do word_frequency analyzer
                "top_words",          # Lista de (palavra, freq)
                "vocabulary"          # Dicionário palavra->freq
            ],
            
            # O que produz
            provides=[
                "visualization_path",  # Caminho do arquivo gerado
                "visualization_html"   # HTML embed se formato html
            ],
            
            parameters={
                "max_words": {
                    "type": "integer",
                    "default": 100,
                    "min": 10,
                    "max": 500,
                    "description": "Número máximo de palavras na nuvem"
                },
                "width": {
                    "type": "integer",
                    "default": 800,
                    "min": 400,
                    "max": 2000,
                    "description": "Largura da imagem em pixels"
                },
                "height": {
                    "type": "integer",
                    "default": 600,
                    "min": 300,
                    "max": 1500,
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
                    "options": ["viridis", "plasma", "inferno", "magma", "Blues", "Reds", "Greens", "coolwarm"],
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
                    "min": 0.0,
                    "max": 1.0,
                    "description": "Escala relativa (0=freq absoluta, 1=rank)"
                }
            }
        )
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Valida configuração"""
        meta = self.meta()
        
        for param, value in config.items():
            if param not in meta.parameters:
                return False, f"Parâmetro desconhecido: {param}"
            
            param_schema = meta.parameters[param]
            param_type = param_schema.get("type")
            
            if param_type == "integer" and not isinstance(value, int):
                return False, f"{param} deve ser inteiro"
            elif param_type == "float" and not isinstance(value, (int, float)):
                return False, f"{param} deve ser número"
            elif param_type == "choice" and value not in param_schema.get("options", []):
                return False, f"{param} deve ser uma das opções: {param_schema.get('options')}"
            
            # Validação de ranges
            if param_type in ["integer", "float"]:
                min_val = param_schema.get("min")
                max_val = param_schema.get("max")
                if min_val is not None and value < min_val:
                    return False, f"{param} deve ser >= {min_val}"
                if max_val is not None and value > max_val:
                    return False, f"{param} deve ser <= {max_val}"
        
        return True, None
    
    def render(self, data: Dict[str, Any], config: Dict[str, Any], output_path: Path) -> str:
        """
        Renderiza nuvem de palavras
        
        Args:
            data: Dados de frequência
            config: Configuração de visualização
            output_path: Onde salvar
        
        Returns:
            Caminho do arquivo gerado
        """
        # Aplicar defaults
        params = self._apply_defaults(config)
        
        # Extrair frequências dos dados
        frequencies = self._extract_frequencies(data)
        
        if not frequencies:
            raise ValueError("Nenhuma frequência de palavras encontrada nos dados")
        
        # Limitar número de palavras
        if len(frequencies) > params["max_words"]:
            # Ordenar por frequência e pegar top N
            sorted_freq = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
            frequencies = dict(sorted_freq[:params["max_words"]])
        
        # Garantir diretório existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Renderizar baseado no formato
        if params["format"] == "html":
            return self._render_html(frequencies, params, output_path)
        else:
            return self._render_image(frequencies, params, output_path)
    
    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica valores default"""
        meta = self.meta()
        params = {}
        
        for param_name, param_schema in meta.parameters.items():
            if param_name in config:
                params[param_name] = config[param_name]
            else:
                params[param_name] = param_schema.get("default")
        
        return params
    
    def _extract_frequencies(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extrai frequências dos dados em vários formatos"""
        # Tenta diferentes formatos de dados
        
        # Formato 1: word_frequencies direto
        if "word_frequencies" in data:
            return data["word_frequencies"]
        
        # Formato 2: top_words como lista de tuplas
        if "top_words" in data:
            return dict(data["top_words"])
        
        # Formato 3: vocabulary
        if "vocabulary" in data:
            return data["vocabulary"]
        
        # Formato 4: o próprio data é um dict de frequências
        if all(isinstance(v, (int, float)) for v in data.values()):
            return data
        
        return {}
    
    def _render_image(self, frequencies: Dict[str, float], params: Dict[str, Any], output_path: Path) -> str:
        """Renderiza como imagem (PNG/SVG)"""
        try:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt
            
            # Configurar WordCloud
            wc = WordCloud(
                width=params["width"],
                height=params["height"],
                max_words=params["max_words"],
                background_color=params["background_color"],
                colormap=params["colormap"],
                relative_scaling=params["relative_scaling"],
                font_path=None,  # Usa fonte do sistema
                prefer_horizontal=0.7
            )
            
            # Gerar nuvem
            wc.generate_from_frequencies(frequencies)
            
            # Criar figura
            fig, ax = plt.subplots(figsize=(params["width"]/100, params["height"]/100))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            
            # Ajustar margens
            plt.tight_layout(pad=0)
            
            # Salvar
            if params["format"] == "svg":
                output_file = output_path.with_suffix('.svg')
                plt.savefig(output_file, format='svg', bbox_inches='tight', pad_inches=0)
            else:
                output_file = output_path.with_suffix('.png')
                plt.savefig(output_file, format='png', dpi=150, bbox_inches='tight', pad_inches=0)
            
            plt.close()
            
            return str(output_file)
            
        except ImportError:
            raise ImportError("Instale wordcloud e matplotlib: pip install wordcloud matplotlib")
    
    def _render_html(self, frequencies: Dict[str, float], params: Dict[str, Any], output_path: Path) -> str:
        """Renderiza como HTML interativo usando D3.js"""
        # Template HTML com D3.js word cloud
        html_template = '''
<!DOCTYPE html>
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
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
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
            padding: 8px 12px;
            background: rgba(0,0,0,0.8);
            color: white;
            border-radius: 4px;
            font-size: 14px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
        }}
    </style>
</head>
<body>
    <div id="wordcloud"></div>
    <div id="tooltip"></div>
    
    <script>
        // Dados
        var words = {words_json};
        
        // Configurações
        var width = {width};
        var height = {height};
        var maxWords = {max_words};
        
        // Cores
        var color = d3.scale.category20();
        
        // Preparar dados
        var wordEntries = Object.entries(words)
            .sort((a, b) => b[1] - a[1])
            .slice(0, maxWords)
            .map(([text, size]) => ({{
                text: text,
                size: size,
                originalSize: size
            }}));
        
        // Escala de tamanhos
        var maxSize = Math.max(...wordEntries.map(d => d.size));
        var minSize = Math.min(...wordEntries.map(d => d.size));
        var sizeScale = d3.scale.linear()
            .domain([minSize, maxSize])
            .range([20, 100]);
        
        // Layout
        var layout = d3.layout.cloud()
            .size([width, height])
            .words(wordEntries)
            .padding(5)
            .rotate(() => (Math.random() - 0.5) * 60)
            .font("{font_family}")
            .fontSize(d => sizeScale(d.size))
            .on("end", draw);
        
        layout.start();
        
        // Desenhar
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
                .style("font-size", d => d.size + "px")
                .style("font-family", "{font_family}")
                .style("fill", (d, i) => color(i))
                .attr("text-anchor", "middle")
                .attr("transform", d => "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")")
                .text(d => d.text)
                .on("mouseover", function(d) {{
                    var tooltip = d3.select("#tooltip");
                    tooltip.style("opacity", 1)
                        .html(d.text + ": " + d.originalSize)
                        .style("left", (d3.event.pageX + 10) + "px")
                        .style("top", (d3.event.pageY - 10) + "px");
                }})
                .on("mouseout", function() {{
                    d3.select("#tooltip").style("opacity", 0);
                }});
        }}
    </script>
</body>
</html>
        '''
        
        # Preparar dados
        words_json = json.dumps(frequencies)
        
        # Substituir no template
        html_content = html_template.format(
            words_json=words_json,
            width=params["width"],
            height=params["height"],
            max_words=params["max_words"],
            font_family=params["font_family"],
            bg_color=params["background_color"] if params["background_color"] != "transparent" else "white"
        )
        
        # Salvar
        output_file = output_path.with_suffix('.html')
        output_file.write_text(html_content, encoding='utf-8')
        
        return str(output_file)