#!/usr/bin/env python3
"""
create_plugin.py - Gerador de templates MELHORADO para plugins Qualia

Uso:
    python create_plugin.py sentiment_analyzer analyzer
    python create_plugin.py network_viz visualizer
    python create_plugin.py markdown_cleaner document
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# CORES ANSI para output colorido
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

TEMPLATES = {
    "analyzer": '''"""
{plugin_title} - {plugin_type} plugin para Qualia Core

Criado em: {date}
Autor: SEU_NOME_AQUI  # 🚨 TODO: COLOQUE SEU NOME!
"""

from typing import Dict, Any, List, Tuple, Optional
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document

# 📚 IMPORTS ÚTEIS DO QUALIA:
# from qualia.core import ExecutionContext  # Para contexto de execução
# from qualia.core import CacheManager      # Para cache de resultados
# from qualia.core import DependencyResolver # Para dependências

# 📦 IMPORTS COMUNS PARA ANALYZERS:
# import nltk                    # Processamento de linguagem natural
# from textblob import TextBlob  # Análise de sentimento
# import spacy                   # NLP avançado
# from collections import Counter # Contagem de elementos
# import re                      # Expressões regulares


class {class_name}(BaseAnalyzerPlugin):
    """
    🚨 TODO: DESCREVA O QUE SEU ANALYZER FAZ!
    
    {description}
    
    Este plugin analisa {what_it_analyzes}.
    
    Exemplo de uso:
        qualia analyze documento.txt -p {plugin_id}
        qualia analyze doc.txt -p {plugin_id} -P param1=valor -P param2=10
    
    Exemplo de resultado:
        {{
            "metric1": 0.75,
            "metric2": ["item1", "item2"],
            "summary": "Análise concluída com sucesso"
        }}
    """
    
    def meta(self) -> PluginMetadata:
        """
        🎯 METADADOS DO PLUGIN - Configure aqui as informações básicas
        """
        return PluginMetadata(
            id="{plugin_id}",
            name="{plugin_title}",
            type=PluginType.ANALYZER,
            version="0.1.0",
            description="{description}",
            
            # 🚨 TODO: O QUE SEU ANALYZER FORNECE?
            # Exemplos comuns:
            # - "sentiment_scores" (para análise de sentimento)
            # - "topics" (para modelagem de tópicos)
            # - "entities" (para reconhecimento de entidades)
            # - "summary" (para sumarização)
            # - "keywords" (para extração de palavras-chave)
            provides=[
                "analysis_result",  # 🚨 MUDE ISTO!
                "metrics",          # 🚨 MUDE ISTO!
                # "sentiment_score",
                # "confidence",
                # "detected_language",
            ],
            
            # 🚨 TODO: SEU ANALYZER PRECISA DE DADOS DE OUTROS PLUGINS?
            # Deixe vazio [] se não precisa de nada
            # Exemplos:
            # - ["word_frequencies"] - se precisa de frequências
            # - ["cleaned_document"] - se precisa de doc limpo
            requires=[
                # "word_frequencies",  # Descomente se precisar
            ],
            
            # 🚨 TODO: DEFINA OS PARÂMETROS CONFIGURÁVEIS
            parameters={{
                # EXEMPLO 1: Parâmetro numérico
                "threshold": {{
                    "type": "float",
                    "default": 0.5,
                    "description": "🚨 TODO: Descreva o que este limiar controla"
                }},
                
                # EXEMPLO 2: Escolha entre opções
                "method": {{
                    "type": "choice",
                    "options": ["method1", "method2", "method3"],  # 🚨 MUDE!
                    "default": "method1",
                    "description": "🚨 TODO: Descreva os métodos disponíveis"
                }},
                
                # EXEMPLO 3: Booleano
                "detailed_analysis": {{
                    "type": "boolean",
                    "default": False,
                    "description": "Incluir análise detalhada no resultado"
                }},
                
                # EXEMPLO 4: Texto/String
                "language": {{
                    "type": "string",
                    "default": "pt",
                    "description": "Código do idioma (pt, en, es)"
                }},
                
                # 🚨 REMOVA OS EXEMPLOS QUE NÃO USAR!
                # 🚨 ADICIONE SEUS PRÓPRIOS PARÂMETROS!
            }}
        )
    
    def _analyze_impl(self, document: Document, config: Dict[str, Any], 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 IMPLEMENTAÇÃO PRINCIPAL - É AQUI QUE A MÁGICA ACONTECE!
        
        Args:
            document: Objeto Document com:
                     - document.content (str): texto completo
                     - document.id (str): identificador
                     - document.metadata (dict): metadados
                     - document.analyses (dict): análises prévias
                     
            config: Dicionário com os parâmetros configurados
                   - Já vem validado e com defaults aplicados!
                   
            context: Contexto compartilhado entre plugins
                    - Use para passar dados entre steps do pipeline
            
        Returns:
            Dict com os resultados prometidos em 'provides'
        """
        
        # 🚨 ============ INÍCIO DO SEU CÓDIGO ============ 🚨
        
        # 1️⃣ ACESSAR O TEXTO DO DOCUMENTO
        text = document.content
        print(f"📝 Analisando documento com {{len(text)}} caracteres...")
        
        # 2️⃣ ACESSAR PARÂMETROS DE CONFIGURAÇÃO
        threshold = config.get('threshold', 0.5)
        method = config.get('method', 'method1')
        detailed = config.get('detailed_analysis', False)
        
        # 3️⃣ ACESSAR ANÁLISES PRÉVIAS (se houver)
        # if 'word_frequencies' in document.analyses:
        #     frequencies = document.analyses['word_frequencies']
        #     top_words = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 🚨 TODO: IMPLEMENTAR SUA ANÁLISE AQUI!
        # 
        # EXEMPLO DE ANÁLISE SIMPLES:
        # import re
        # sentences = re.split(r'[.!?]+', text)
        # words = text.split()
        # 
        # result = {{
        #     "total_sentences": len(sentences),
        #     "total_words": len(words),
        #     "average_words_per_sentence": len(words) / len(sentences) if sentences else 0
        # }}
        
        # 🚨 REMOVA ESTE EXEMPLO E COLOQUE SEU CÓDIGO!
        result = {{
            "analysis_result": "🚨 TODO: Implementar análise real aqui!",
            "metrics": {{
                "example_metric": 42,
                "text_length": len(text),
                "method_used": method,
                "threshold_applied": threshold
            }},
            "debug_info": {{
                "parameters_received": config,
                "context_keys": list(context.keys()) if context else []
            }}
        }}
        
        # 4️⃣ ADICIONAR ANÁLISE DETALHADA SE SOLICITADO
        if detailed:
            result["detailed_analysis"] = {{
                "per_sentence_analysis": "🚨 TODO: Implementar",
                "confidence_scores": "🚨 TODO: Calcular",
                # Adicione mais detalhes aqui
            }}
        
        # 5️⃣ SALVAR NO CONTEXT PARA PRÓXIMOS PLUGINS (se necessário)
        # context['{plugin_id}_result'] = result
        
        # 🚨 ============ FIM DO SEU CÓDIGO ============ 🚨
        
        return result


# 🧪 ÁREA DE TESTES - Execute este arquivo diretamente para testar!
if __name__ == "__main__":
    from qualia.core import Document
    
    print(f"{{Colors.CYAN}}🧪 Testando {class_name}...{{Colors.END}}")
    
    # Criar plugin
    analyzer = {class_name}()
    meta = analyzer.meta()
    
    print(f"\\n📋 Informações do Plugin:")
    print(f"   Nome: {{Colors.GREEN}}{{meta.name}}{{Colors.END}}")
    print(f"   Versão: {{meta.version}}")
    print(f"   Fornece: {{meta.provides}}")
    print(f"   Parâmetros: {{list(meta.parameters.keys())}}")
    
    # Teste com documento exemplo
    test_text = \"\"\"
    Este é um texto de exemplo para testar o analyzer.
    Ele contém múltiplas frases. Algumas são curtas.
    Outras são mais longas e complexas, com várias cláusulas e informações!
    \"\"\"
    
    doc = Document(id="test", content=test_text)
    config = {{"detailed_analysis": True}}  # Testar com análise detalhada
    
    print(f"\\n🔍 Executando análise...")
    try:
        result = analyzer._analyze_impl(doc, config, {{}})
        
        print(f"\\n✅ {{Colors.GREEN}}Análise concluída!{{Colors.END}}")
        print(f"\\n📊 Resultados:")
        
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\\n❌ {{Colors.RED}}Erro: {{e}}{{Colors.END}}")
        import traceback
        traceback.print_exc()
    
    print(f"\\n💡 {{Colors.YELLOW}}Dica: Execute 'qualia analyze <arquivo> -p {plugin_id}' para usar na CLI{{Colors.END}}")
''',

    "visualizer": '''"""
{plugin_title} - {plugin_type} plugin para Qualia Core

Criado em: {date}
Autor: SEU_NOME_AQUI  # 🚨 TODO: COLOQUE SEU NOME!
"""

from typing import Dict, Any, Union
from pathlib import Path
from qualia.core import BaseVisualizerPlugin, PluginMetadata, PluginType

# 📚 IMPORTS ÚTEIS DO QUALIA:
# from qualia.core import ExecutionContext  # Para contexto de execução

# 📊 IMPORTS COMUNS PARA VISUALIZERS:
# import matplotlib.pyplot as plt    # Gráficos estáticos
# import plotly.graph_objects as go  # Gráficos interativos
# import plotly.express as px        # Gráficos rápidos
# import seaborn as sns             # Gráficos estatísticos
# from wordcloud import WordCloud   # Nuvens de palavras
# import networkx as nx             # Grafos e redes
# from PIL import Image             # Manipulação de imagens


class {class_name}(BaseVisualizerPlugin):
    """
    🚨 TODO: DESCREVA O QUE SEU VISUALIZER FAZ!
    
    {description}
    
    Este plugin visualiza {what_it_visualizes}.
    
    Exemplo de uso:
        qualia visualize data.json -p {plugin_id} -o output.png
        qualia visualize data.json -p {plugin_id} -o dashboard.html -P style=dark
    """
    
    def meta(self) -> PluginMetadata:
        """
        🎯 METADADOS DO PLUGIN - Configure aqui as informações básicas
        """
        return PluginMetadata(
            id="{plugin_id}",
            name="{plugin_title}",
            type=PluginType.VISUALIZER,
            version="0.1.0",
            description="{description}",
            
            # 🚨 TODO: QUE DADOS SEU VISUALIZER PRECISA?
            # Exemplos comuns:
            # - "word_frequencies" (para word clouds)
            # - "sentiment_scores" (para gráficos de sentimento)
            # - "topics" (para visualização de tópicos)
            # - "network_data" (para grafos)
            requires=[
                "data_field_required",  # 🚨 MUDE ISTO!
                # "word_frequencies",
                # "sentiment_scores",
            ],
            
            # ✅ NORMALMENTE NÃO PRECISA MUDAR
            provides=[
                "visualization_path",
            ],
            
            # 🚨 TODO: DEFINA OS PARÂMETROS DE VISUALIZAÇÃO
            parameters={{
                # DIMENSÕES
                "width": {{
                    "type": "integer",
                    "default": 800,
                    "description": "Largura em pixels"
                }},
                "height": {{
                    "type": "integer",
                    "default": 600,
                    "description": "Altura em pixels"
                }},
                
                # ESTILO VISUAL
                "theme": {{
                    "type": "choice",
                    "options": ["light", "dark", "seaborn", "minimal"],  # 🚨 CUSTOMIZE!
                    "default": "light",
                    "description": "Tema visual"
                }},
                
                # CORES
                "color_scheme": {{
                    "type": "choice",
                    "options": ["viridis", "plasma", "inferno", "magma", "blues", "reds"],
                    "default": "viridis",
                    "description": "Esquema de cores"
                }},
                
                # FORMATO DE SAÍDA
                "format": {{
                    "type": "choice",
                    "options": ["png", "svg", "html", "pdf"],
                    "default": "png",
                    "description": "Formato do arquivo de saída"
                }},
                
                # INTERATIVIDADE
                "interactive": {{
                    "type": "boolean",
                    "default": False,
                    "description": "Gerar versão interativa (apenas HTML)"
                }},
                
                # 🚨 ADICIONE PARÂMETROS ESPECÍFICOS DO SEU VISUALIZER!
                "show_labels": {{
                    "type": "boolean",
                    "default": True,
                    "description": "🚨 TODO: Descreva o que os labels mostram"
                }},
                
                # 🚨 REMOVA OS QUE NÃO USAR!
            }}
        )
    
    def _render_impl(self, data: Dict[str, Any], config: Dict[str, Any], 
                     output_path: Path) -> Path:
        """
        🎯 IMPLEMENTAÇÃO DA VISUALIZAÇÃO - CRIE GRÁFICOS INCRÍVEIS!
        
        Args:
            data: Dados para visualizar (vem de analyzers ou JSON)
                 Exemplo: {{"word_frequencies": {{"python": 10, "qualia": 8}}}}
                 
            config: Configurações validadas (width, height, theme, etc)
            
            output_path: Path onde salvar (já é Path object!)
                        Extensão define o formato (.png, .html, etc)
            
        Returns:
            Path do arquivo gerado
        """
        
        # 🚨 ============ INÍCIO DO SEU CÓDIGO ============ 🚨
        
        # 1️⃣ EXTRAIR DADOS NECESSÁRIOS
        # 🚨 TODO: Ajuste para os dados que você espera!
        required_data = data.get('data_field_required', {{}})
        if not required_data:
            raise ValueError(f"❌ Dados necessários não encontrados! Esperado: 'data_field_required'")
        
        # 2️⃣ EXTRAIR CONFIGURAÇÕES
        width = config['width']
        height = config['height']
        theme = config['theme']
        colors = config['color_scheme']
        interactive = config['interactive']
        
        # 3️⃣ DECIDIR ENTRE MATPLOTLIB OU PLOTLY
        if interactive or output_path.suffix == '.html':
            # 🎨 USAR PLOTLY PARA GRÁFICOS INTERATIVOS
            self._render_plotly(required_data, config, output_path)
        else:
            # 🖼️ USAR MATPLOTLIB PARA IMAGENS ESTÁTICAS
            self._render_matplotlib(required_data, config, output_path)
        
        return output_path
    
    def _render_matplotlib(self, data: Any, config: Dict[str, Any], output_path: Path):
        """
        🖼️ RENDERIZAÇÃO COM MATPLOTLIB (PNG, SVG, PDF)
        """
        import matplotlib.pyplot as plt
        import numpy as np
        
        # 🚨 TODO: IMPLEMENTAR SUA VISUALIZAÇÃO!
        
        # Configurar figura
        fig, ax = plt.subplots(figsize=(config['width']/100, config['height']/100))
        
        # Aplicar tema
        if config['theme'] == 'dark':
            plt.style.use('dark_background')
        elif config['theme'] == 'seaborn':
            plt.style.use('seaborn-v0_8')
        
        # 🚨 EXEMPLO PLACEHOLDER - SUBSTITUA!
        # Criar visualização de exemplo
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        ax.plot(x, y, label='🚨 TODO: Implementar visualização real!')
        
        ax.set_title(f"{{self.meta().name}} - Visualização", fontsize=16)
        ax.set_xlabel("Eixo X")
        ax.set_ylabel("Eixo Y")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 🚨 ADICIONE SEU CÓDIGO DE VISUALIZAÇÃO AQUI!
        # Exemplos:
        # - ax.bar(labels, values) para barras
        # - ax.scatter(x, y) para dispersão
        # - ax.pie(sizes, labels=labels) para pizza
        # - sns.heatmap(data, ax=ax) para heatmap
        
        # Ajustar layout e salvar
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
    
    def _render_plotly(self, data: Any, config: Dict[str, Any], output_path: Path):
        """
        🎯 RENDERIZAÇÃO COM PLOTLY (HTML INTERATIVO)
        """
        import plotly.graph_objects as go
        import plotly.express as px
        
        # 🚨 TODO: IMPLEMENTAR SUA VISUALIZAÇÃO INTERATIVA!
        
        # 🚨 EXEMPLO PLACEHOLDER - SUBSTITUA!
        fig = go.Figure()
        
        # Adicionar trace de exemplo
        fig.add_trace(go.Scatter(
            x=[1, 2, 3, 4, 5],
            y=[2, 4, 3, 5, 6],
            mode='lines+markers',
            name='🚨 TODO: Dados reais'
        ))
        
        # Configurar layout
        fig.update_layout(
            title={{
                'text': f"{{self.meta().name}} - Visualização Interativa",
                'x': 0.5,
                'xanchor': 'center'
            }},
            width=config['width'],
            height=config['height'],
            template='plotly_dark' if config['theme'] == 'dark' else 'plotly_white'
        )
        
        # 🚨 EXEMPLOS DE GRÁFICOS PLOTLY:
        # - go.Bar() para barras
        # - go.Pie() para pizza
        # - go.Heatmap() para heatmap
        # - go.Scatter3d() para 3D
        # - go.Treemap() para treemap
        # - px.sunburst() para sunburst
        
        # Salvar
        if output_path.suffix == '.html':
            fig.write_html(output_path)
        else:
            # Precisa do kaleido para exportar imagens
            fig.write_image(output_path)
        
        # 🚨 ============ FIM DO SEU CÓDIGO ============ 🚨


# 🧪 ÁREA DE TESTES
if __name__ == "__main__":
    import json
    
    print(f"🧪 Testando {class_name}...")
    
    # Criar plugin
    viz = {class_name}()
    meta = viz.meta()
    
    print(f"\\n📋 Informações do Plugin:")
    print(f"   Nome: {{meta.name}}")
    print(f"   Requer: {{meta.requires}}")
    print(f"   Parâmetros: {{list(meta.parameters.keys())}}")
    
    # Dados de teste
    test_data = {{
        "data_field_required": {{  # 🚨 AJUSTE PARA SEUS DADOS!
            "item1": 10,
            "item2": 20,
            "item3": 15
        }}
    }}
    
    # Configuração de teste
    test_config = {{
        "width": 800,
        "height": 600,
        "theme": "dark",
        "interactive": True
    }}
    
    # Testar renderização
    output_file = Path("test_visualization.html")
    
    print(f"\\n🎨 Gerando visualização...")
    try:
        result = viz._render_impl(test_data, test_config, output_file)
        print(f"✅ Sucesso! Arquivo salvo em: {{result}}")
        print(f"\\n💡 Abra {{output_file}} no navegador para ver o resultado!")
    except Exception as e:
        print(f"❌ Erro: {{e}}")
        import traceback
        traceback.print_exc()
''',

    "document": '''"""
{plugin_title} - {plugin_type} plugin para Qualia Core

Criado em: {date}
Autor: SEU_NOME_AQUI  # 🚨 TODO: COLOQUE SEU NOME!
"""

from typing import Dict, Any, List, Optional, Tuple
from qualia.core import BaseDocumentPlugin, PluginMetadata, PluginType, Document

# 📚 IMPORTS COMUNS PARA PROCESSAMENTO DE DOCUMENTOS:
# import re                      # Expressões regulares
# import unicodedata            # Normalização de texto
# from bs4 import BeautifulSoup # Parser HTML
# import markdown              # Conversão Markdown
# import pypandoc              # Conversão entre formatos
# from cleantext import clean   # Limpeza de texto


class {class_name}(BaseDocumentPlugin):
    """
    🚨 TODO: DESCREVA O QUE SEU PROCESSOR FAZ!
    
    {description}
    
    Este plugin processa {what_it_processes}.
    
    Exemplo de uso:
        qualia process documento.txt -p {plugin_id} --save-as limpo.txt
        qualia process doc.md -p {plugin_id} -P remove_links=true
    """
    
    def meta(self) -> PluginMetadata:
        """
        🎯 METADADOS DO PLUGIN - Configure aqui as informações básicas
        """
        return PluginMetadata(
            id="{plugin_id}",
            name="{plugin_title}",
            type=PluginType.DOCUMENT,
            version="0.1.0",
            description="{description}",
            
            # ✅ PADRÃO PARA DOCUMENT PROCESSORS
            provides=[
                "cleaned_document",    # Documento processado
                "quality_report",      # Relatório de qualidade
                "processing_stats",    # Estatísticas
            ],
            
            # 🚨 TODO: DEFINA OS PARÂMETROS DE PROCESSAMENTO
            parameters={{
                # OPÇÕES DE LIMPEZA
                "remove_extra_spaces": {{
                    "type": "boolean",
                    "default": True,
                    "description": "Remover espaços extras e linhas em branco"
                }},
                
                "fix_encoding": {{
                    "type": "boolean",
                    "default": True,
                    "description": "Corrigir problemas de encoding (acentuação)"
                }},
                
                "remove_urls": {{
                    "type": "boolean",
                    "default": False,
                    "description": "Remover URLs do texto"
                }},
                
                "remove_emails": {{
                    "type": "boolean",
                    "default": False,
                    "description": "Remover endereços de email"
                }},
                
                # FORMATAÇÃO
                "normalize_quotes": {{
                    "type": "boolean",
                    "default": True,
                    "description": "Normalizar aspas curvas para retas"
                }},
                
                "target_format": {{
                    "type": "choice",
                    "options": ["plain", "markdown", "minimal"],  # 🚨 CUSTOMIZE!
                    "default": "plain",
                    "description": "Formato alvo do documento"
                }},
                
                # VALIDAÇÃO
                "min_quality_score": {{
                    "type": "integer",
                    "default": 70,
                    "description": "Score mínimo de qualidade (0-100)"
                }},
                
                # 🚨 ADICIONE SEUS PRÓPRIOS PARÂMETROS!
                "custom_option": {{
                    "type": "string",
                    "default": "",
                    "description": "🚨 TODO: Descreva sua opção customizada"
                }},
            }}
        )
    
    def _process_impl(self, document: Document, config: Dict[str, Any], 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 IMPLEMENTAÇÃO DO PROCESSAMENTO - LIMPE E MELHORE DOCUMENTOS!
        
        Args:
            document: Documento original
            config: Configurações de processamento
            context: Contexto compartilhado
            
        Returns:
            Dict com documento processado e metadados
        """
        
        # 🚨 ============ INÍCIO DO SEU CÓDIGO ============ 🚨
        
        # 1️⃣ OBTER TEXTO ORIGINAL
        text = document.content
        original_length = len(text)
        
        print(f"📝 Processando documento com {{original_length}} caracteres...")
        
        # 2️⃣ APLICAR PROCESSAMENTOS CONFORME CONFIG
        processed_text = text
        changes_made = []
        issues_found = []
        
        # 🧹 REMOVER ESPAÇOS EXTRAS
        if config.get('remove_extra_spaces', True):
            import re
            # Múltiplos espaços → um espaço
            new_text = re.sub(r' +', ' ', processed_text)
            # Múltiplas quebras → duas quebras (parágrafo)
            new_text = re.sub(r'\\n\\n+', '\\n\\n', new_text)
            # Espaços no início/fim das linhas
            new_text = re.sub(r' *\\n *', '\\n', new_text)
            
            if new_text != processed_text:
                changes_made.append("Espaços extras removidos")
                processed_text = new_text
        
        # 🔤 CORRIGIR ENCODING
        if config.get('fix_encoding', True):
            # 🚨 TODO: Implementar correção de encoding
            # Exemplo: substituir caracteres mal codificados
            replacements = {{
                'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
                'Ã ': 'à', 'Ã§': 'ç', 'Ã±': 'ñ', 'Ã¢': 'â', 'Ãª': 'ê',
                # Adicione mais conforme necessário
            }}
            
            for wrong, correct in replacements.items():
                if wrong in processed_text:
                    processed_text = processed_text.replace(wrong, correct)
                    issues_found.append(f"Encoding incorreto: {{wrong}} → {{correct}}")
        
        # 🔗 REMOVER URLS
        if config.get('remove_urls', False):
            import re
            url_pattern = r'https?://\\S+|www\\.\\S+'
            urls_found = re.findall(url_pattern, processed_text)
            if urls_found:
                processed_text = re.sub(url_pattern, '[URL_REMOVIDA]', processed_text)
                changes_made.append(f"{{len(urls_found)}} URLs removidas")
        
        # 📧 REMOVER EMAILS
        if config.get('remove_emails', False):
            import re
            email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{{2,}}\\b'
            emails_found = re.findall(email_pattern, processed_text)
            if emails_found:
                processed_text = re.sub(email_pattern, '[EMAIL_REMOVIDO]', processed_text)
                changes_made.append(f"{{len(emails_found)}} emails removidos")
        
        # 🚨 TODO: ADICIONE SEUS PROCESSAMENTOS AQUI!
        # Exemplos:
        # - Remover números de telefone
        # - Converter para minúsculas/maiúsculas
        # - Remover stopwords
        # - Corrigir pontuação
        # - Remover caracteres especiais
        # - Normalizar datas
        # - Extrair apenas texto de HTML/XML
        
        # 3️⃣ CALCULAR SCORE DE QUALIDADE
        quality_score = self._calculate_quality_score(processed_text, issues_found)
        
        # 4️⃣ CRIAR VARIANTES DO DOCUMENTO (opcional)
        document_variants = {{}}
        
        if config.get('target_format') == 'markdown':
            # 🚨 TODO: Converter para Markdown
            document_variants['markdown'] = f"# Documento Processado\\n\\n{{processed_text}}"
        
        # 5️⃣ PREPARAR RESULTADO
        result = {{
            "cleaned_document": processed_text,
            "original_length": original_length,
            "cleaned_length": len(processed_text),
            "reduction_percentage": round((1 - len(processed_text)/original_length) * 100, 2),
            
            "quality_report": {{
                "quality_score": quality_score,
                "issues_found": issues_found,
                "changes_made": changes_made,
                "recommendations": self._get_recommendations(quality_score, issues_found)
            }},
            
            "processing_stats": {{
                "total_changes": len(changes_made),
                "total_issues": len(issues_found),
                "processing_time": "🚨 TODO: Medir tempo real",
                "config_used": config
            }}
        }}
        
        # Adicionar variantes se existirem
        if document_variants:
            result["document_variants"] = document_variants
        
        # 🚨 ============ FIM DO SEU CÓDIGO ============ 🚨
        
        return result
    
    def _calculate_quality_score(self, text: str, issues: List[str]) -> int:
        """
        📊 CALCULAR SCORE DE QUALIDADE (0-100)
        """
        score = 100
        
        # 🚨 TODO: IMPLEMENTAR CÁLCULO REAL!
        # Exemplos de penalidades:
        score -= len(issues) * 5  # -5 por issue
        
        # Verificações de qualidade
        if len(text) < 100:
            score -= 20  # Texto muito curto
        
        if text.count('🚨') > 0:
            score -= 50  # TODOs não resolvidos!
        
        return max(0, min(100, score))
    
    def _get_recommendations(self, score: int, issues: List[str]) -> List[str]:
        """
        💡 GERAR RECOMENDAÇÕES BASEADAS NA ANÁLISE
        """
        recommendations = []
        
        if score < 70:
            recommendations.append("⚠️ Documento precisa de revisão manual")
        
        if any('encoding' in issue for issue in issues):
            recommendations.append("🔤 Verificar encoding do arquivo original")
        
        # 🚨 TODO: Adicionar mais recomendações inteligentes!
        
        return recommendations


# 🧪 ÁREA DE TESTES
if __name__ == "__main__":
    from qualia.core import Document
    
    print(f"🧪 Testando {class_name}...")
    
    # Criar plugin
    processor = {class_name}()
    meta = processor.meta()
    
    print(f"\\n📋 Informações do Plugin:")
    print(f"   Nome: {{meta.name}}")
    print(f"   Parâmetros: {{list(meta.parameters.keys())}}")
    
    # Documento de teste
    test_text = \"\"\"
    Este  é   um   texto    com     espaços     extras!
    
    
    Tem linhas em branco demais...
    
    E também tem uma URL: https://example.com
    E um email: teste@example.com
    
    Além de problemas de codificaÃ§Ã£o!
    \"\"\"
    
    doc = Document(id="test", content=test_text)
    config = {{
        "remove_extra_spaces": True,
        "fix_encoding": True,
        "remove_urls": True,
        "remove_emails": True
    }}
    
    print(f"\\n🔧 Processando documento...")
    try:
        result = processor._process_impl(doc, config, {{}})
        
        print(f"\\n✅ Processamento concluído!")
        print(f"\\n📊 Estatísticas:")
        print(f"   Original: {{result['original_length']}} chars")
        print(f"   Processado: {{result['cleaned_length']}} chars")
        print(f"   Redução: {{result['reduction_percentage']}}%")
        print(f"   Qualidade: {{result['quality_report']['quality_score']}}/100")
        
        print(f"\\n📝 Texto processado:")
        print("-" * 50)
        print(result['cleaned_document'])
        print("-" * 50)
        
        if result['quality_report']['issues_found']:
            print(f"\\n⚠️ Problemas encontrados:")
            for issue in result['quality_report']['issues_found']:
                print(f"   - {{issue}}")
        
    except Exception as e:
        print(f"❌ Erro: {{e}}")
        import traceback
        traceback.print_exc()
'''
}

def create_plugin(plugin_id: str, plugin_type: str):
    """Cria estrutura de plugin com template melhorado"""
    
    # Validar tipo
    if plugin_type not in ["analyzer", "visualizer", "document"]:
        print(f"{Colors.RED}❌ Tipo inválido: {plugin_type}{Colors.END}")
        print("   Use: analyzer, visualizer, ou document")
        return False
    
    # Preparar variáveis
    class_name = ''.join(word.capitalize() for word in plugin_id.split('_'))
    if plugin_type == "analyzer":
        class_name += "Analyzer"
    elif plugin_type == "visualizer":
        class_name += "Visualizer"
    else:
        class_name += "Processor"
    
    plugin_title = ' '.join(word.capitalize() for word in plugin_id.split('_'))
    
    # Criar diretório
    plugin_dir = Path(f"plugins/{plugin_id}")
    if plugin_dir.exists():
        print(f"{Colors.RED}❌ Plugin {plugin_id} já existe!{Colors.END}")
        return False
    
    plugin_dir.mkdir(parents=True)
    
    # Criar __init__.py
    template_vars = {
        "plugin_id": plugin_id,
        "plugin_type": plugin_type.capitalize(),
        "plugin_title": plugin_title,
        "class_name": class_name,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "description": f"Plugin para {plugin_title.lower()}",
        "what_it_analyzes": "TODO: descrever o que analisa",
        "what_it_visualizes": "TODO: descrever o que visualiza",
        "what_it_processes": "TODO: descrever o que processa",
    }
    
    init_content = TEMPLATES[plugin_type].format(**template_vars)
    (plugin_dir / "__init__.py").write_text(init_content)
    
    # Criar requirements.txt com conteúdo mais útil
    req_content = f"""# Dependências para {plugin_title}
# Gerado em: {datetime.now().strftime("%Y-%m-%d")}

# 🚨 TODO: Adicione as dependências necessárias!

# Para análise de texto:
# nltk>=3.8.1
# textblob>=0.17.1
# spacy>=3.5.0
# vaderSentiment>=3.3.2

# Para visualização:
# matplotlib>=3.5.0
# plotly>=5.14.0
# seaborn>=0.12.0
# wordcloud>=1.9.0

# Para processamento:
# beautifulsoup4>=4.11.0
# markdown>=3.4.0
# cleantext>=1.1.3

# Utilidades:
# numpy>=1.22.0
# pandas>=1.5.0
# scikit-learn>=1.2.0
"""
    (plugin_dir / "requirements.txt").write_text(req_content)
    
    # Criar README.md mais detalhado
    readme_content = f"""# {plugin_title}

**Tipo**: {plugin_type.capitalize()}  
**ID**: `{plugin_id}`  
**Versão**: 0.1.0  
**Autor**: SEU_NOME_AQUI 🚨

## Descrição

{template_vars['description']}

🚨 **TODO**: Adicione uma descrição detalhada do que este plugin faz!

## Instalação

```bash
# Instalar dependências
pip install -r plugins/{plugin_id}/requirements.txt

# Testar o plugin
python plugins/{plugin_id}/__init__.py
```

## Uso

### CLI
```bash
# Comando básico
qualia {plugin_type.replace('analyzer', 'analyze').replace('document', 'process')} arquivo.txt -p {plugin_id}

# Com parâmetros
qualia {plugin_type.replace('analyzer', 'analyze').replace('document', 'process')} arquivo.txt -p {plugin_id} -P param1=valor -P param2=10

# Salvar resultado
qualia {plugin_type.replace('analyzer', 'analyze').replace('document', 'process')} arquivo.txt -p {plugin_id} -o resultado.json
```

### Python
```python
from plugins.{plugin_id} import {class_name}
from qualia.core import Document

# Criar instância
plugin = {class_name}()

# Ver metadados
meta = plugin.meta()
print(f"Plugin: {{meta.name}} v{{meta.version}}")
print(f"Parâmetros: {{list(meta.parameters.keys())}}")

# Executar
doc = Document("id", "Conteúdo do documento...")
result = plugin._process_impl(doc, {{}}, {{}})
print(result)
```

### Pipeline
```yaml
# Em configs/pipelines/meu_pipeline.yaml
name: pipeline_com_{plugin_id}
steps:
  - plugin: {plugin_id}
    config:
      param1: valor
      param2: 10
    output_name: resultado_{plugin_id}
```

## Parâmetros

🚨 **TODO**: Documentar cada parâmetro!

| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `example_param` | integer | 10 | Descrição do parâmetro |
| ... | ... | ... | ... |

## Exemplos

### Exemplo 1: Uso Básico
```bash
qualia {plugin_type.replace('analyzer', 'analyze').replace('document', 'process')} exemplo.txt -p {plugin_id}
```

### Exemplo 2: Com Configurações
```bash
qualia {plugin_type.replace('analyzer', 'analyze').replace('document', 'process')} exemplo.txt -p {plugin_id} \\
  -P param1=valor \\
  -P param2=20 \\
  -o resultado.json
```

## Desenvolvimento

### Estrutura do Código
- `meta()`: Define metadados e parâmetros
- `_analyze_impl()` / `_render_impl()` / `_process_impl()`: Lógica principal
- Testes no final do arquivo

### Como Testar
```bash
# Teste unitário
python plugins/{plugin_id}/__init__.py

# Teste com CLI
echo "Texto de teste" > test.txt
qualia {plugin_type.replace('analyzer', 'analyze').replace('document', 'process')} test.txt -p {plugin_id}
```

### Checklist de Desenvolvimento
- [ ] Implementar lógica principal
- [ ] Definir parâmetros necessários
- [ ] Adicionar validações
- [ ] Escrever testes
- [ ] Documentar uso
- [ ] Adicionar exemplos

## Notas de Implementação

🚨 **TODO**: Adicione notas sobre decisões de design, limitações conhecidas, etc.

## Changelog

### v0.1.0 - {datetime.now().strftime("%Y-%m-%d")}
- Versão inicial
- 🚨 TODO: Listar features implementadas
"""
    
    (plugin_dir / "README.md").write_text(readme_content)
    
    # Criar arquivo de exemplo
    example_content = f"""# Exemplo de dados para {plugin_title}

Este arquivo mostra o formato de dados esperado pelo plugin.

## Para Analyzers
Se seu analyzer produz dados, eles devem ter este formato:
```json
{{
    "analysis_result": "...",
    "metrics": {{
        "metric1": 0.75,
        "metric2": 42
    }}
}}
```

## Para Visualizers
Se seu visualizer consome dados, ele espera:
```json
{{
    "data_field_required": {{
        "item1": 10,
        "item2": 20
    }}
}}
```

🚨 TODO: Adicione exemplos reais!
"""
    (plugin_dir / "example_data.md").write_text(example_content)
    
    print(f"""
{Colors.GREEN}✅ Plugin criado com sucesso!{Colors.END}

{Colors.CYAN}📁 Estrutura criada:{Colors.END}
   plugins/{plugin_id}/
   ├── __init__.py       # {Colors.YELLOW}Código principal (COM MUITOS TODOs!){Colors.END}
   ├── requirements.txt  # Dependências sugeridas
   ├── README.md        # Documentação detalhada
   └── example_data.md  # Exemplos de dados

{Colors.MAGENTA}🎯 Próximos passos:{Colors.END}
   1. {Colors.BOLD}Abrir plugins/{plugin_id}/__init__.py{Colors.END}
   2. {Colors.YELLOW}Procurar por 🚨 TODO e implementar{Colors.END}
   3. Instalar dependências necessárias
   4. Executar teste: {Colors.CYAN}python plugins/{plugin_id}/__init__.py{Colors.END}

{Colors.GREEN}💡 Dicas:{Colors.END}
   • O template tem {Colors.YELLOW}🚨 marcadores{Colors.END} em TODOS os lugares importantes
   • Há exemplos de código comentados para ajudar
   • O arquivo pode ser executado diretamente para teste
   • Use o teste no final do arquivo para debug rápido

{Colors.BLUE}🧪 Teste rápido:{Colors.END}
   python plugins/{plugin_id}/__init__.py
""")
    
    return True


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"{Colors.BOLD}Uso: python create_plugin.py <plugin_id> <tipo>{Colors.END}")
        print(f"Exemplo: python create_plugin.py sentiment_analyzer analyzer")
        print(f"Tipos: {Colors.GREEN}analyzer{Colors.END}, {Colors.BLUE}visualizer{Colors.END}, {Colors.MAGENTA}document{Colors.END}")
        sys.exit(1)
    
    plugin_id = sys.argv[1]
    plugin_type = sys.argv[2]
    
    create_plugin(plugin_id, plugin_type)