"""
Sentiment Visualizer Plugin for Qualia

Cria visualizações para resultados de análise de sentimento.
"""

from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import json

from qualia.core import PluginType, PluginMetadata, BaseVisualizerPlugin

class SentimentVisualizer(BaseVisualizerPlugin):
    """
    Visualizador para resultados de análise de sentimento.
    
    Cria:
    - Gauge de polaridade (-1 a 1)
    - Gauge de subjetividade (0 a 1)
    - Gráfico de pizza com distribuição de sentimentos
    - Timeline de sentimentos por sentença
    """
    
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="sentiment_viz",
            name="Sentiment Visualizer",
            type=PluginType.VISUALIZER,
            version="1.0.0",
            description="Visualiza resultados de análise de sentimento",
            provides=["sentiment_visualization"],
            requires=["polarity", "subjectivity"],  # Do sentiment_analyzer
            parameters={
                "chart_type": {
                    "type": "choice",
                    "description": "Tipo de visualização",
                    "default": "dashboard",
                    "options": ["dashboard", "gauge", "timeline", "distribution"]
                },
                "color_scheme": {
                    "type": "choice",
                    "description": "Esquema de cores",
                    "default": "sentiment",
                    "options": ["sentiment", "viridis", "coolwarm", "RdYlGn"]
                },
                "show_examples": {
                    "type": "boolean",
                    "description": "Mostrar exemplos de sentenças",
                    "default": True
                }
            }
        )
    
    def _render_impl(self, data: Dict[str, Any], config: Dict[str, Any], output_path: Path) -> Path:
        """Implementa renderização da visualização"""
        chart_type = config.get('chart_type', 'dashboard')
        
        # Verificar dados necessários
        if 'polarity' not in data or 'subjectivity' not in data:
            raise ValueError("Dados de sentimento não encontrados. Execute sentiment_analyzer primeiro.")
        
        if chart_type == 'dashboard':
            return self._render_dashboard(data, config, output_path)
        elif chart_type == 'gauge':
            return self._render_gauge(data, config, output_path)
        elif chart_type == 'timeline':
            return self._render_timeline(data, config, output_path)
        elif chart_type == 'distribution':
            return self._render_distribution(data, config, output_path)
        else:
            raise ValueError(f"Tipo de gráfico não suportado: {chart_type}")
    
    def _render_dashboard(self, data: Dict[str, Any], config: Dict[str, Any], output_path: Path) -> Path:
        """Renderiza dashboard completo em HTML"""
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Criar subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Polaridade (Sentimento)', 
                'Subjetividade',
                'Distribuição de Sentimentos',
                'Timeline de Sentimentos'
            ),
            specs=[
                [{'type': 'indicator'}, {'type': 'indicator'}],
                [{'type': 'pie'}, {'type': 'scatter'}]
            ],
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        # 1. Gauge de Polaridade
        polarity = data.get('polarity', 0)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=polarity,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': ""},
                delta={'reference': 0},
                gauge={
                    'axis': {'range': [-1, 1]},
                    'bar': {'color': self._get_sentiment_color(polarity)},
                    'steps': [
                        {'range': [-1, -0.6], 'color': '#ff4444'},
                        {'range': [-0.6, -0.2], 'color': '#ff8888'},
                        {'range': [-0.2, 0.2], 'color': '#cccccc'},
                        {'range': [0.2, 0.6], 'color': '#88ff88'},
                        {'range': [0.6, 1], 'color': '#44ff44'}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': 0
                    }
                }
            ),
            row=1, col=1
        )
        
        # 2. Gauge de Subjetividade
        subjectivity = data.get('subjectivity', 0)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=subjectivity,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': ""},
                gauge={
                    'axis': {'range': [0, 1]},
                    'bar': {'color': self._get_subjectivity_color(subjectivity)},
                    'steps': [
                        {'range': [0, 0.3], 'color': '#e6f2ff'},
                        {'range': [0.3, 0.7], 'color': '#99ccff'},
                        {'range': [0.7, 1], 'color': '#3399ff'}
                    ]
                }
            ),
            row=1, col=2
        )
        
        # 3. Distribuição de Sentimentos (se disponível)
        if 'sentiment_stats' in data:
            stats = data['sentiment_stats']
            labels = ['Positivo', 'Neutro', 'Negativo']
            values = [
                stats.get('positive_sentences', 0),
                stats.get('neutral_sentences', 0),
                stats.get('negative_sentences', 0)
            ]
            colors = ['#44ff44', '#cccccc', '#ff4444']
            
            fig.add_trace(
                go.Pie(
                    labels=labels,
                    values=values,
                    marker=dict(colors=colors),
                    textinfo='label+percent',
                    hoverinfo='label+value'
                ),
                row=2, col=1
            )
        
        # 4. Timeline de Sentimentos (se disponível)
        if 'sentence_sentiments' in data:
            sentences = data['sentence_sentiments']
            x = list(range(len(sentences)))
            y = [s['polarity'] for s in sentences]
            colors = [self._get_sentiment_color(p) for p in y]
            
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode='lines+markers',
                    name='Polaridade',
                    line=dict(color='gray', width=1),
                    marker=dict(
                        size=10,
                        color=colors,
                        line=dict(width=2, color='white')
                    ),
                    hovertemplate='Sentença %{x}<br>Polaridade: %{y:.3f}<extra></extra>'
                ),
                row=2, col=2
            )
            
            # Linha de referência neutra
            fig.add_hline(y=0, line_dash="dash", line_color="black", 
                         opacity=0.5, row=2, col=2)
        
        # Configurar layout
        fig.update_layout(
            title={
                'text': f"Análise de Sentimento - {data.get('sentiment_label', 'Neutro').title()}",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24}
            },
            showlegend=False,
            height=800,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        # Adicionar anotações com interpretação
        if 'interpretation' in data:
            interp = data['interpretation']
            annotation_text = f"<b>Interpretação:</b><br>"
            annotation_text += f"{interp.get('sentiment', '')}<br>"
            annotation_text += f"{interp.get('subjectivity', '')}"
            
            fig.add_annotation(
                xref="paper", yref="paper",
                x=0.5, y=-0.15,
                text=annotation_text,
                showarrow=False,
                font=dict(size=12),
                align="center",
                bordercolor="gray",
                borderwidth=1,
                borderpad=10,
                bgcolor="rgba(255,255,255,0.8)"
            )
        
        # Salvar
        if output_path.suffix == '.html':
            fig.write_html(str(output_path), include_plotlyjs='cdn')
        else:
            fig.write_image(str(output_path))
        
        return output_path
    
    def _render_gauge(self, data: Dict[str, Any], config: Dict[str, Any], output_path: Path) -> Path:
        """Renderiza apenas o gauge de sentimento"""
        import plotly.graph_objects as go
        
        polarity = data.get('polarity', 0)
        sentiment = data.get('sentiment_label', 'neutro')
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=polarity,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"Sentimento: {sentiment.title()}", 'font': {'size': 24}},
            delta={'reference': 0, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
            gauge={
                'axis': {'range': [-1, 1], 'tickwidth': 1},
                'bar': {'color': self._get_sentiment_color(polarity), 'thickness': 0.8},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [-1, -0.6], 'color': 'rgba(255,68,68,0.3)'},
                    {'range': [-0.6, -0.2], 'color': 'rgba(255,136,136,0.3)'},
                    {'range': [-0.2, 0.2], 'color': 'rgba(204,204,204,0.3)'},
                    {'range': [0.2, 0.6], 'color': 'rgba(136,255,136,0.3)'},
                    {'range': [0.6, 1], 'color': 'rgba(68,255,68,0.3)'}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': 0
                }
            }
        ))
        
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor='white',
            font={'color': "black", 'family': "Arial"}
        )
        
        if output_path.suffix == '.html':
            fig.write_html(str(output_path), include_plotlyjs='cdn')
        else:
            fig.write_image(str(output_path))
        
        return output_path
    
    def _render_timeline(self, data: Dict[str, Any], config: Dict[str, Any], output_path: Path) -> Path:
        """Renderiza timeline de sentimentos por sentença"""
        import plotly.graph_objects as go
        
        if 'sentence_sentiments' not in data:
            raise ValueError("Dados de sentenças não encontrados. Configure analyze_sentences=True")
        
        sentences = data['sentence_sentiments']
        
        fig = go.Figure()
        
        # Plotar linha de sentimentos
        x = list(range(len(sentences)))
        y = [s['polarity'] for s in sentences]
        texts = [s['text'][:50] + '...' if len(s['text']) > 50 else s['text'] 
                for s in sentences]
        colors = [self._get_sentiment_color(p) for p in y]
        
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='lines+markers+text',
            name='Sentimento',
            line=dict(color='lightgray', width=2),
            marker=dict(
                size=12,
                color=colors,
                line=dict(width=2, color='white'),
                symbol='circle'
            ),
            text=[f"S{i+1}" for i in range(len(sentences))],
            textposition="top center",
            hovertext=texts,
            hoverinfo='text+y'
        ))
        
        # Áreas coloridas
        fig.add_hrect(y0=0.1, y1=1, fillcolor="green", opacity=0.1, 
                     line_width=0, annotation_text="Positivo")
        fig.add_hrect(y0=-0.1, y1=0.1, fillcolor="gray", opacity=0.1, 
                     line_width=0, annotation_text="Neutro")
        fig.add_hrect(y0=-1, y1=-0.1, fillcolor="red", opacity=0.1, 
                     line_width=0, annotation_text="Negativo")
        
        # Linha zero
        fig.add_hline(y=0, line_dash="solid", line_color="black", opacity=0.3)
        
        fig.update_layout(
            title="Timeline de Sentimentos por Sentença",
            xaxis_title="Número da Sentença",
            yaxis_title="Polaridade",
            yaxis=dict(range=[-1.1, 1.1]),
            height=500,
            showlegend=False,
            hovermode='closest'
        )
        
        # Adicionar exemplos se configurado
        if config.get('show_examples', True):
            if 'most_positive_sentence' in data:
                pos = data['most_positive_sentence']
                fig.add_annotation(
                    text=f"Mais positiva: \"{pos['text'][:60]}...\"",
                    xref="paper", yref="paper",
                    x=0.02, y=0.98,
                    showarrow=False,
                    bgcolor="rgba(68,255,68,0.3)",
                    bordercolor="green",
                    borderwidth=1
                )
            
            if 'most_negative_sentence' in data:
                neg = data['most_negative_sentence']
                fig.add_annotation(
                    text=f"Mais negativa: \"{neg['text'][:60]}...\"",
                    xref="paper", yref="paper",
                    x=0.02, y=0.02,
                    showarrow=False,
                    bgcolor="rgba(255,68,68,0.3)",
                    bordercolor="red",
                    borderwidth=1
                )
        
        if output_path.suffix == '.html':
            fig.write_html(str(output_path), include_plotlyjs='cdn')
        else:
            fig.write_image(str(output_path))
        
        return output_path
    
    def _render_distribution(self, data: Dict[str, Any], config: Dict[str, Any], output_path: Path) -> Path:
        """Renderiza distribuição de sentimentos"""
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Gráfico 1: Distribuição de sentimentos
        if 'sentiment_stats' in data:
            stats = data['sentiment_stats']
            labels = ['Positivo', 'Neutro', 'Negativo']
            sizes = [
                stats.get('positive_sentences', 0),
                stats.get('neutral_sentences', 0),
                stats.get('negative_sentences', 0)
            ]
            colors = ['#44ff44', '#cccccc', '#ff4444']
            
            # Pie chart
            wedges, texts, autotexts = ax1.pie(sizes, labels=labels, colors=colors, 
                                               autopct='%1.1f%%', startangle=90)
            ax1.set_title('Distribuição de Sentimentos por Sentença')
        
        # Gráfico 2: Métricas gerais
        metrics = {
            'Polaridade': data.get('polarity', 0),
            'Subjetividade': data.get('subjectivity', 0)
        }
        
        if 'sentiment_stats' in data:
            metrics['Média Polaridade'] = data['sentiment_stats'].get('avg_polarity', 0)
        
        # Bar chart
        bars = ax2.bar(metrics.keys(), metrics.values(), 
                       color=['green' if v > 0 else 'red' if v < 0 else 'gray' 
                             for v in metrics.values()])
        ax2.set_title('Métricas de Sentimento')
        ax2.set_ylim(-1, 1)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Adicionar valores nas barras
        for bar, value in zip(bars, metrics.values()):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{value:.3f}', ha='center', va='bottom')
        
        plt.suptitle(f"Análise de Sentimento - {data.get('sentiment_label', 'Neutro').title()}", 
                    fontsize=16)
        plt.tight_layout()
        
        plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def _get_sentiment_color(self, polarity: float) -> str:
        """Retorna cor baseada na polaridade"""
        if polarity > 0.6:
            return '#00ff00'  # Verde forte
        elif polarity > 0.2:
            return '#88ff88'  # Verde claro
        elif polarity < -0.6:
            return '#ff0000'  # Vermelho forte
        elif polarity < -0.2:
            return '#ff8888'  # Vermelho claro
        else:
            return '#888888'  # Cinza
    
    def _get_subjectivity_color(self, subjectivity: float) -> str:
        """Retorna cor baseada na subjetividade"""
        if subjectivity > 0.7:
            return '#0066ff'  # Azul forte
        elif subjectivity > 0.3:
            return '#66aaff'  # Azul médio
        else:
            return '#ccddff'  # Azul claro


# Para testes diretos
if __name__ == "__main__":
    viz = SentimentVisualizer()
    print(f"Plugin: {viz.meta().name}")
    print(f"Versão: {viz.meta().version}")
    print("\nEste visualizador requer dados do sentiment_analyzer")