"""Word Cloud D3 — nuvem de palavras interativa usando D3.js."""

import json

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
        if not isinstance(frequencies, dict):
            raise ValueError(f"word_frequencies deve ser dict, recebeu {type(frequencies).__name__}")
        max_words = config.get("max_words", 100)
        width = config.get("width", 800)
        height = config.get("height", 400)
        colormap = config.get("colormap", "category10")

        sorted_words = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)[:max_words]
        if not sorted_words:
            return "<html><body><p>Nenhum dado para visualizar</p></body></html>"

        max_freq = sorted_words[0][1] if sorted_words else 1
        words_json = ", ".join(
            f'{{"text": {json.dumps(w)}, "size": {max(12, int(60 * c / max_freq))}, "count": {c}}}'
            for w, c in sorted_words
        )

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
    .append("g").attr("transform", "translate({width//2},{height//2})")
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
      tooltip.text(d.text + ": " + d.count).style("left", (event.pageX + 10) + "px").style("top", (event.pageY - 28) + "px");
    }})
    .on("mouseout", function() {{ tooltip.transition().duration(500).style("opacity", 0); }});
}}
</script>
</body></html>'''
