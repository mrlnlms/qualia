# plugins/frequency_chart/__init__.py
"""
Frequency Chart Visualizer Plugin

Gera gráficos de barras e linhas para dados de frequência
Outputs: PNG, HTML interativo
"""

from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path

from qualia.core import (
    IVisualizerPlugin,
    PluginMetadata,
    PluginType
)


class FrequencyChartVisualizer(IVisualizerPlugin):
    """
    Cria gráficos de barras/linhas para frequências
    """
    
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="frequency_chart",
            type=PluginType.VISUALIZER,
            name="Frequency Chart Visualizer",
            description="Gera gráficos de barras e linhas para dados de frequência",
            version="1.0.0",
            
            accepts=[
                "word_frequencies",
                "top_words",
                "by_segment",
                "by_speaker"
            ],
            
            provides=[
                "visualization_path",
                "visualization_html"
            ],
            
            parameters={
                "chart_type": {
                    "type": "choice",
                    "options": ["bar", "horizontal_bar", "line", "area"],
                    "default": "bar",
                    "description": "Tipo de gráfico"
                },
                "top_n": {
                    "type": "integer",
                    "default": 20,
                    "min": 5,
                    "max": 50,
                    "description": "Número de itens a mostrar"
                },
                "title": {
                    "type": "string",
                    "default": "Frequência de Palavras",
                    "description": "Título do gráfico"
                },
                "interactive": {
                    "type": "boolean",
                    "default": True,
                    "description": "Gerar versão interativa (HTML)"
                },
                "color_scheme": {
                    "type": "choice",
                    "options": ["plotly", "viridis", "blues", "reds", "rainbow"],
                    "default": "plotly",
                    "description": "Esquema de cores"
                },
                "width": {
                    "type": "integer",
                    "default": 1200,
                    "min": 600,
                    "max": 2000,
                    "description": "Largura do gráfico em pixels"
                },
                "height": {
                    "type": "integer",
                    "default": 800,
                    "min": 400,
                    "max": 1500,
                    "description": "Altura do gráfico em pixels"
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
            elif param_type == "boolean" and not isinstance(value, bool):
                return False, f"{param} deve ser booleano"
            elif param_type == "string" and not isinstance(value, str):
                return False, f"{param} deve ser string"
            elif param_type == "choice" and value not in param_schema.get("options", []):
                return False, f"{param} deve ser uma das opções: {param_schema.get('options')}"
            
            # Validação de ranges
            if param_type == "integer":
                min_val = param_schema.get("min")
                max_val = param_schema.get("max")
                if min_val is not None and value < min_val:
                    return False, f"{param} deve ser >= {min_val}"
                if max_val is not None and value > max_val:
                    return False, f"{param} deve ser <= {max_val}"
        
        return True, None
    
    def render(self, data: Dict[str, Any], config: Dict[str, Any], output_path: Path) -> str:
        """Renderiza gráfico de frequências"""
        params = self._apply_defaults(config)
        
        # Extrair dados
        frequencies = self._extract_frequencies(data)
        
        if not frequencies:
            raise ValueError("Nenhuma frequência encontrada nos dados")
        
        # Preparar dados para visualização
        sorted_items = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
        top_items = sorted_items[:params["top_n"]]
        
        words = [item[0] for item in top_items]
        counts = [item[1] for item in top_items]
        
        # Garantir que o diretório existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Renderizar
        if params["interactive"]:
            return self._render_plotly(words, counts, params, output_path)
        else:
            return self._render_matplotlib(words, counts, params, output_path)
    
    def _render_plotly(self, words: List[str], counts: List[int], 
                      params: Dict[str, Any], output_path: Path) -> str:
        """Renderiza com Plotly (interativo)"""
        try:
            import plotly.graph_objects as go
            
            # Configurar cores
            if params["color_scheme"] == "blues":
                color = 'lightblue'
                line_color = 'darkblue'
            elif params["color_scheme"] == "reds":
                color = 'lightcoral'
                line_color = 'darkred'
            elif params["color_scheme"] == "viridis":
                # Criar gradiente viridis
                import plotly.express as px
                colors = px.colors.sample_colorscale("viridis", len(words))
                color = colors
                line_color = 'darkgreen'
            else:
                color = 'lightblue'
                line_color = 'darkblue'
            
            # Criar figura baseado no tipo
            if params["chart_type"] == "bar":
                fig = go.Figure([go.Bar(
                    x=words, 
                    y=counts,
                    marker_color=color,
                    marker_line_color=line_color,
                    marker_line_width=1.5,
                    text=counts,
                    textposition='auto',
                )])
                fig.update_xaxes(tickangle=45)
                
            elif params["chart_type"] == "horizontal_bar":
                fig = go.Figure([go.Bar(
                    x=counts, 
                    y=words, 
                    orientation='h',
                    marker_color=color,
                    marker_line_color=line_color,
                    marker_line_width=1.5,
                    text=counts,
                    textposition='auto',
                )])
                # Inverter ordem para maiores no topo
                fig.update_yaxes(autorange="reversed")
                
            elif params["chart_type"] == "line":
                fig = go.Figure([go.Scatter(
                    x=words, 
                    y=counts, 
                    mode='lines+markers',
                    line=dict(color=line_color, width=3),
                    marker=dict(size=10, color=color, line=dict(width=2, color=line_color))
                )])
                fig.update_xaxes(tickangle=45)
                
            elif params["chart_type"] == "area":
                fig = go.Figure([go.Scatter(
                    x=words, 
                    y=counts, 
                    fill='tozeroy',
                    fillcolor='rgba(0,100,200,0.3)',
                    line=dict(color='rgb(0,100,200)', width=3)
                )])
                fig.update_xaxes(tickangle=45)
            
            # Configurar layout
            fig.update_layout(
                title={
                    'text': params["title"],
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 24}
                },
                xaxis_title="Palavras" if params["chart_type"] != "horizontal_bar" else "Frequência",
                yaxis_title="Frequência" if params["chart_type"] != "horizontal_bar" else "Palavras",
                showlegend=False,
                template="plotly_white",
                width=params["width"],
                height=params["height"],
                margin=dict(l=100, r=50, t=100, b=100),
                font=dict(size=14),
                hovermode='closest'
            )
            
            # Adicionar hover customizado
            if params["chart_type"] in ["bar", "horizontal_bar"]:
                fig.update_traces(
                    hovertemplate='<b>%{y}</b><br>Frequência: %{x}<extra></extra>' 
                    if params["chart_type"] == "horizontal_bar" 
                    else '<b>%{x}</b><br>Frequência: %{y}<extra></extra>'
                )
            
            # Salvar HTML
            output_file = output_path.with_suffix('.html')
            fig.write_html(
                str(output_file),
                config={
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d']
                }
            )
            
            # Também salvar como imagem se kaleido estiver instalado
            try:
                img_file = output_path.with_suffix('.png')
                fig.write_image(str(img_file), scale=2)
            except:
                # Kaleido pode não estar instalado ou configurado
                pass
            
            return str(output_file)
            
        except ImportError as e:
            raise ImportError(f"Erro ao importar Plotly: {e}. Instale com: pip install plotly kaleido")
    
    def _render_matplotlib(self, words: List[str], counts: List[int],
                          params: Dict[str, Any], output_path: Path) -> str:
        """Renderiza com matplotlib (estático)"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Configurar estilo
            plt.style.use('seaborn-v0_8-whitegrid')
            
            # Criar figura com tamanho personalizado
            fig_width = params["width"] / 100
            fig_height = params["height"] / 100
            fig, ax = plt.subplots(figsize=(fig_width, fig_height))
            
            # Selecionar cores
            if params["color_scheme"] == "blues":
                color = 'steelblue'
            elif params["color_scheme"] == "reds":
                color = 'indianred'
            elif params["color_scheme"] == "viridis":
                cmap = plt.cm.viridis
                colors = cmap(np.linspace(0, 1, len(words)))
                color = colors
            else:
                color = 'skyblue'
            
            # Criar gráfico baseado no tipo
            if params["chart_type"] == "bar":
                bars = ax.bar(range(len(words)), counts, color=color, edgecolor='darkblue', linewidth=1)
                ax.set_xticks(range(len(words)))
                ax.set_xticklabels(words, rotation=45, ha='right')
                
                # Adicionar valores no topo das barras
                for bar, count in zip(bars, counts):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + max(counts)*0.01,
                           f'{count}', ha='center', va='bottom', fontsize=10)
                           
            elif params["chart_type"] == "horizontal_bar":
                bars = ax.barh(range(len(words)), counts, color=color, edgecolor='darkblue', linewidth=1)
                ax.set_yticks(range(len(words)))
                ax.set_yticklabels(words)
                ax.invert_yaxis()  # Maiores no topo
                
                # Adicionar valores
                for bar, count in zip(bars, counts):
                    width = bar.get_width()
                    ax.text(width + max(counts)*0.01, bar.get_y() + bar.get_height()/2.,
                           f'{count}', ha='left', va='center', fontsize=10)
                           
            elif params["chart_type"] == "line":
                ax.plot(range(len(words)), counts, 'o-', color='darkblue', 
                       linewidth=2, markersize=8, markerfacecolor='lightblue',
                       markeredgecolor='darkblue', markeredgewidth=2)
                ax.set_xticks(range(len(words)))
                ax.set_xticklabels(words, rotation=45, ha='right')
                
                # Adicionar valores nos pontos
                for i, count in enumerate(counts):
                    ax.text(i, count + max(counts)*0.02, f'{count}', 
                           ha='center', va='bottom', fontsize=9)
                           
            elif params["chart_type"] == "area":
                ax.fill_between(range(len(words)), counts, alpha=0.3, color='skyblue')
                ax.plot(range(len(words)), counts, color='darkblue', linewidth=2)
                ax.set_xticks(range(len(words)))
                ax.set_xticklabels(words, rotation=45, ha='right')
            
            # Configurar labels e título
            ax.set_title(params["title"], fontsize=18, fontweight='bold', pad=20)
            ax.set_xlabel("Palavras" if params["chart_type"] != "horizontal_bar" else "Frequência", 
                         fontsize=14)
            ax.set_ylabel("Frequência" if params["chart_type"] != "horizontal_bar" else "Palavras", 
                         fontsize=14)
            
            # Grid sutil
            ax.grid(True, alpha=0.3)
            
            # Ajustar layout
            plt.tight_layout()
            
            # Salvar
            output_file = output_path.with_suffix('.png')
            plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return str(output_file)
            
        except ImportError as e:
            raise ImportError(f"Erro ao importar matplotlib: {e}. Instale com: pip install matplotlib")
    
    def _extract_frequencies(self, data: Dict[str, Any]) -> Dict[str, int]:
        """Extrai frequências dos dados em vários formatos"""
        # Tenta diferentes formatos
        if "word_frequencies" in data:
            return data["word_frequencies"]
        elif "top_words" in data:
            return dict(data["top_words"])
        elif "vocabulary" in data:
            return data["vocabulary"]
        elif all(isinstance(v, (int, float)) for v in data.values()):
            return data
        
        # Tentar extrair de análise por speaker/segment
        if "by_speaker" in data:
            # Combinar frequências de todos os speakers
            combined = {}
            for speaker_data in data["by_speaker"].values():
                if "word_frequencies" in speaker_data:
                    for word, freq in speaker_data["word_frequencies"].items():
                        combined[word] = combined.get(word, 0) + freq
            return combined
            
        return {}
    
    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica defaults aos parâmetros"""
        meta = self.meta()
        params = {}
        
        for param_name, param_schema in meta.parameters.items():
            if param_name in config:
                params[param_name] = config[param_name]
            else:
                params[param_name] = param_schema.get("default")
        
        return params