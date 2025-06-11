"""
Sistema de tutoriais do menu interativo
"""

from rich.panel import Panel
from rich.prompt import Prompt
from ..formatters import console
from .utils import get_int_choice


class TutorialManager:
    """Gerenciador de tutoriais"""
    
    def __init__(self):
        self.tutorials = {
            "basic_analysis": {
                "title": "Análise Básica de Texto",
                "content": self._tutorial_basic_analysis()
            },
            "transcript_cleaning": {
                "title": "Limpeza de Transcrições",
                "content": self._tutorial_transcript_cleaning()
            },
            "visualization": {
                "title": "Criação de Visualizações",
                "content": self._tutorial_visualization()
            },
            "pipelines": {
                "title": "Pipelines Complexos",
                "content": self._tutorial_pipelines()
            },
            "complete_flow": {
                "title": "Fluxo Completo de Análise",
                "content": self._tutorial_complete_flow()
            }
        }
    
    def show_menu(self):
        """Mostra menu de tutoriais"""
        from .menu import QualiaInteractiveMenu
        menu = QualiaInteractiveMenu()
        menu.show_banner()
        
        console.print("\n[bold]EXEMPLOS E TUTORIAIS[/bold]\n")
        
        tutorial_list = list(self.tutorials.items())
        
        for i, (key, info) in enumerate(tutorial_list, 1):
            console.print(f"{i}. {info['title']}")
        
        console.print(f"{len(tutorial_list)+1}. Voltar")
        
        choice = get_int_choice("Escolha", 1, len(tutorial_list)+1)
        
        if choice <= len(tutorial_list):
            key, info = tutorial_list[choice-1]
            self._show_tutorial(info['title'], info['content'])
    
    def _show_tutorial(self, title: str, content: str):
        """Exibe um tutorial"""
        console.print(Panel(
            content,
            title=f"Tutorial: {title}",
            border_style="cyan"
        ))
        
        Prompt.ask("\nPressione Enter para continuar")
    
    def _tutorial_basic_analysis(self) -> str:
        return """
1. [cyan]Prepare seu documento[/cyan]
   - Formato: arquivo .txt simples
   - Codificação: UTF-8
   - Exemplo: artigo, transcrição, notas

2. [cyan]Execute a análise[/cyan]
   ```
   qualia analyze documento.txt -p word_frequency
   ```

3. [cyan]Parâmetros úteis[/cyan]
   - min_word_length: tamanho mínimo das palavras (padrão: 3)
   - remove_stopwords: remove palavras comuns (padrão: true)
   - language: português, inglês ou espanhol

4. [cyan]Interprete resultados[/cyan]
   - word_frequencies: palavras mais comuns e suas contagens
   - hapax_legomena: palavras que aparecem apenas uma vez
   - vocabulary_size: tamanho do vocabulário
   - type_token_ratio: diversidade lexical

[dim]Dica: Use -o para salvar resultados em JSON para visualização posterior[/dim]
"""
    
    def _tutorial_transcript_cleaning(self) -> str:
        return """
1. [cyan]Formatos suportados[/cyan]
   - Microsoft Teams (completo)
   - Zoom (em desenvolvimento)
   - Google Meet (planejado)

2. [cyan]Comando básico[/cyan]
   ```
   qualia process transcript.txt -p teams_cleaner --save-as clean.txt
   ```

3. [cyan]O que é removido[/cyan]
   - Mensagens do sistema
   - Notificações de entrada/saída
   - Timestamps (opcional)
   - Metadados desnecessários

4. [cyan]Variantes automáticas[/cyan]
   - _participants_only: apenas falas dos participantes
   - _speaker_[nome]: arquivo individual por pessoa
   - _questions_only: apenas perguntas identificadas

5. [cyan]Métricas fornecidas[/cyan]
   - quality_score: qualidade geral da transcrição
   - speaker_stats: estatísticas por participante
   - interaction_patterns: padrões de interação

[dim]Dica: Use o arquivo limpo como entrada para análises mais precisas[/dim]
"""
    
    def _tutorial_visualization(self) -> str:
        return """
1. [cyan]Visualizadores disponíveis[/cyan]
   - [bold]wordcloud_viz[/bold]: nuvem de palavras
     • Formatos: PNG, SVG, HTML
     • Personalização: cores, tamanho, fundo
   
   - [bold]frequency_chart[/bold]: gráficos de frequência
     • Tipos: barras, pizza, treemap, sunburst
     • Interativo em HTML com Plotly

2. [cyan]Workflow típico[/cyan]
   ```bash
   # 1. Analisar documento
   qualia analyze doc.txt -p word_frequency -o dados.json
   
   # 2. Criar nuvem de palavras
   qualia visualize dados.json -p wordcloud_viz -o nuvem.png \\
     -P colormap=viridis -P background_color=white
   
   # 3. Criar gráfico interativo
   qualia visualize dados.json -p frequency_chart -o grafico.html \\
     -P chart_type=treemap -P top_n=30
   ```

3. [cyan]Parâmetros de personalização[/cyan]
   
   [bold]wordcloud_viz:[/bold]
   - colormap: viridis, plasma, inferno, magma, coolwarm
   - background_color: white, black, transparent
   - width/height: dimensões em pixels
   - max_words: número máximo de palavras
   
   [bold]frequency_chart:[/bold]
   - chart_type: bar, horizontal_bar, pie, treemap, sunburst
   - top_n: quantidade de itens a mostrar
   - color_scale: esquema de cores

4. [cyan]Dicas avançadas[/cyan]
   - HTML permite zoom e interação
   - SVG é escalável sem perder qualidade
   - PNG é ideal para apresentações
   - Combine múltiplas visualizações em relatórios

[dim]Dica: Exporte em HTML para dashboards interativos[/dim]
"""
    
    def _tutorial_pipelines(self) -> str:
        return """
1. [cyan]O que são pipelines[/cyan]
   - Sequência automatizada de operações
   - Configuração em YAML
   - Reutilizáveis e compartilháveis
   - Garantem reprodutibilidade

2. [cyan]Estrutura de um pipeline[/cyan]
   ```yaml
   name: analise_completa
   description: Pipeline completo de análise
   steps:
     - plugin: teams_cleaner
       config:
         remove_timestamps: true
         merge_consecutive: true
       output: cleaned.txt
     
     - plugin: word_frequency
       config:
         min_word_length: 4
         remove_stopwords: true
       output: frequencies.json
     
     - plugin: wordcloud_viz
       config:
         colormap: viridis
         max_words: 100
       output: wordcloud.png
   ```

3. [cyan]Executar pipeline[/cyan]
   ```
   qualia pipeline documento.txt -c configs/pipelines/analise_completa.yaml -o resultados/
   ```

4. [cyan]Pipelines prontos[/cyan]
   - example.yaml: demonstração básica
   - full_analysis.yaml: análise completa
   - visualization_suite.yaml: múltiplas visualizações

5. [cyan]Criar pipeline pelo menu[/cyan]
   - Use a opção "Criar novo pipeline"
   - Assistente guiado passo a passo
   - Salva automaticamente em YAML

[dim]Dica: Pipelines são ótimos para análises repetitivas[/dim]
"""
    
    def _tutorial_complete_flow(self) -> str:
        return """
[cyan]Cenário:[/cyan] Analisar transcrição de reunião do Teams

1. [cyan]Limpeza inicial[/cyan]
   ```
   qualia process reuniao.txt -p teams_cleaner --save-as reuniao_limpa.txt
   ```
   ✓ Remove ruído e organiza o texto

2. [cyan]Análise de frequência[/cyan]
   ```
   qualia analyze reuniao_limpa.txt -p word_frequency -o analise.json \\
     -P min_word_length=4 -P language=portuguese
   ```
   ✓ Identifica termos mais relevantes

3. [cyan]Visualizações[/cyan]
   ```
   # Nuvem de palavras
   qualia visualize analise.json -p wordcloud_viz -o nuvem_palavras.png \\
     -P colormap=plasma -P background_color=white
   
   # Gráfico interativo
   qualia visualize analise.json -p frequency_chart -o grafico.html \\
     -P chart_type=treemap -P top_n=25
   ```
   ✓ Cria visualizações para apresentação

4. [cyan]Análises futuras (em desenvolvimento)[/cyan]
   - Análise de sentimento
   - Modelagem de tópicos (LDA)
   - Dinâmicas de interação
   - Estrutura narrativa

5. [cyan]Relatório final[/cyan]
   - Combine outputs em apresentação
   - Use HTML para dashboards interativos
   - Exporte insights principais

[bold]Resultado:[/bold] De transcrição bruta para insights visuais!

[dim]Dica: Salve este workflow como pipeline para reutilizar[/dim]
"""