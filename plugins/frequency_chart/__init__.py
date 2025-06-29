# plugins/frequency_chart/__init__.py
"""
Plugin de visualização que gera gráficos de frequência
"""

from typing import Dict, Any
from pathlib import Path
import json

# Importar a base class
from qualia.core import BaseVisualizerPlugin, PluginMetadata, PluginType


class FrequencyChartVisualizer(BaseVisualizerPlugin):
    """Gera gráficos de frequência em vários formatos"""
    
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="frequency_chart",
            name="Frequency Chart Visualizer",
            type=PluginType.VISUALIZER,
            version="1.0.0",
            description="Gera gráficos de frequência (barras, linha, área)",
            requires=["word_frequencies"],  # ou ["frequencies"] genérico
            provides=["chart_path", "chart_html"],
            parameters={
                "chart_type": {
                    "type": "choice",
                    "options": ["bar", "horizontal_bar", "line", "area"],
                    "default": "bar",
                    "description": "Tipo de gráfico"
                },
                "max_items": {
                    "type": "integer",
                    "default": 20,
                    "description": "Número máximo de itens a mostrar"
                },
                "width": {
                    "type": "integer",
                    "default": 800,
                    "description": "Largura do gráfico em pixels"
                },
                "height": {
                    "type": "integer",
                    "default": 600,
                    "description": "Altura do gráfico em pixels"
                },
                "title": {
                    "type": "string",
                    "default": "Análise de Frequência",
                    "description": "Título do gráfico"
                },
                "color_scheme": {
                    "type": "choice",
                    "options": ["blues", "reds", "greens", "viridis", "rainbow"],
                    "default": "blues",
                    "description": "Esquema de cores"
                },
                "format": {
                    "type": "choice",
                    "options": ["png", "html", "svg"],
                    "default": "html",
                    "description": "Formato de saída"
                },
                "interactive": {
                    "type": "boolean",
                    "default": True,
                    "description": "Gerar versão interativa (apenas HTML)"
                }
            }
        )
    
    def _render_impl(self, data: Dict[str, Any], config: Dict[str, Any], 
                     output_path: Path) -> Path:
        """
        Implementação real da renderização
        
        Todas as validações já foram feitas pela BaseVisualizerPlugin
        """
        
        # Extrair e preparar dados
        frequencies = data['word_frequencies']
        
        # Ordenar e limitar itens
        sorted_items = sorted(
            frequencies.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:config['max_items']]
        
        # Renderizar baseado no formato
        if config['format'] == 'html' and config['interactive']:
            self._render_plotly(sorted_items, config, output_path)
        else:
            self._render_matplotlib(sorted_items, config, output_path)
        
        return output_path
    
    def _render_plotly(self, items: list, config: Dict[str, Any], 
                       output_path: Path):
        """Renderiza gráfico interativo com Plotly"""
        try:
            import plotly.graph_objects as go
            import plotly.express as px
        except ImportError:
            raise ImportError("Plotly não instalado. Use: pip install plotly")
        
        words, counts = zip(*items) if items else ([], [])
        
        # Criar figura baseada no tipo
        if config['chart_type'] == 'bar':
            fig = go.Figure([go.Bar(x=words, y=counts)])
        elif config['chart_type'] == 'horizontal_bar':
            fig = go.Figure([go.Bar(x=counts, y=words, orientation='h')])
        elif config['chart_type'] == 'line':
            fig = go.Figure([go.Scatter(x=words, y=counts, mode='lines+markers')])
        elif config['chart_type'] == 'area':
            fig = go.Figure([go.Scatter(
                x=words, y=counts, 
                mode='lines', 
                fill='tozeroy'
            )])
        
        # Configurar layout
        fig.update_layout(
            title=config['title'],
            width=config['width'],
            height=config['height'],
            template="plotly_white",
            xaxis_tickangle=-45 if config['chart_type'] != 'horizontal_bar' else 0
        )
        
        # Aplicar esquema de cores
        color_map = {
            'blues': 'Blues',
            'reds': 'Reds', 
            'greens': 'Greens',
            'viridis': 'Viridis',
            'rainbow': 'Rainbow'
        }
        
        if config['chart_type'] in ['bar', 'horizontal_bar']:
            fig.update_traces(marker_color=counts, 
                            marker_colorscale=color_map[config['color_scheme']])
        
        # Salvar
        if output_path.suffix == '.html':
            fig.write_html(output_path)
        else:
            # Para PNG/SVG, precisa do kaleido
            try:
                if output_path.suffix == '.png':
                    fig.write_image(output_path, format='png')
                elif output_path.suffix == '.svg':
                    fig.write_image(output_path, format='svg')
            except Exception:
                # Fallback para HTML se kaleido não estiver instalado
                output_path = output_path.with_suffix('.html')
                fig.write_html(output_path)
    
    def _render_matplotlib(self, items: list, config: Dict[str, Any], 
                          output_path: Path):
        """Renderiza gráfico estático com Matplotlib"""
        import matplotlib.pyplot as plt
        import numpy as np
        
        words, counts = zip(*items) if items else ([], [])
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(config['width']/100, config['height']/100))
        
        # Cores
        colors = self._get_matplotlib_colors(config['color_scheme'], len(words))
        
        # Renderizar baseado no tipo
        if config['chart_type'] == 'bar':
            ax.bar(words, counts, color=colors)
            plt.xticks(rotation=45, ha='right')
        elif config['chart_type'] == 'horizontal_bar':
            ax.barh(words, counts, color=colors)
        elif config['chart_type'] == 'line':
            ax.plot(words, counts, marker='o', color=colors[0], linewidth=2)
            plt.xticks(rotation=45, ha='right')
        elif config['chart_type'] == 'area':
            ax.fill_between(range(len(words)), counts, alpha=0.7, color=colors[0])
            ax.plot(words, counts, color=colors[0], linewidth=2)
            plt.xticks(rotation=45, ha='right')
        
        # Configurar
        ax.set_title(config['title'], fontsize=16, pad=20)
        ax.grid(True, alpha=0.3)
        
        # Labels
        if config['chart_type'] != 'horizontal_bar':
            ax.set_xlabel('Palavras')
            ax.set_ylabel('Frequência')
        else:
            ax.set_xlabel('Frequência')
            ax.set_ylabel('Palavras')
        
        # Ajustar layout
        plt.tight_layout()
        
        # Salvar
        format_map = {'.png': 'png', '.svg': 'svg', '.pdf': 'pdf'}
        save_format = format_map.get(output_path.suffix, 'png')
        plt.savefig(output_path, format=save_format, dpi=150, bbox_inches='tight')
        plt.close()
    
    def _get_matplotlib_colors(self, scheme: str, n: int) -> list:
        """Retorna lista de cores para matplotlib"""
        import matplotlib.cm as cm
        import numpy as np
        
        cmap_map = {
            'blues': cm.Blues,
            'reds': cm.Reds,
            'greens': cm.Greens,
            'viridis': cm.viridis,
            'rainbow': cm.rainbow
        }
        
        cmap = cmap_map.get(scheme, cm.Blues)
        return [cmap(i/n) for i in np.linspace(0.3, 0.9, n)]


# Exportar plugin
__all__ = ['FrequencyChartVisualizer']