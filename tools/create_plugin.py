#!/usr/bin/env python3
"""
create_plugin.py - Gerador de templates para plugins Qualia

Uso:
    python tools/create_plugin.py meu_analyzer analyzer
    python tools/create_plugin.py meu_viz visualizer
    python tools/create_plugin.py meu_cleaner document
"""

import sys
import os
from pathlib import Path
from datetime import datetime


TEMPLATES = {
    "analyzer": '''"""
{plugin_title} - Analyzer plugin para Qualia Core

Criado em: {date}
"""

from typing import Dict, Any, List, Optional, Tuple
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document

# Imports comuns para analyzers:
# import nltk
# from textblob import TextBlob
# import spacy
# from collections import Counter
# import re


class {class_name}(BaseAnalyzerPlugin):
    """
    TODO: Descreva o que este analyzer faz.

    Exemplo de uso:
        qualia analyze documento.txt -p {plugin_id}
        qualia analyze doc.txt -p {plugin_id} -P param1=valor
    """

    def __init__(self):
        super().__init__()
        # Thread-safety: plugins sao singletons compartilhados entre threads.
        # __init__ roda na main thread (sem concorrencia).
        # _analyze_impl roda em worker threads (com concorrencia).
        #
        # Carregue recursos pesados AQUI — modelos, corpora, conexoes.
        # NAO carregue dentro de _analyze_impl.
        #
        # Exemplos:
        #   self.model = SentenceTransformer('all-MiniLM-L6-v2')
        #   self._stopwords = set(stopwords.words('portuguese'))
        pass

    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="{plugin_id}",
            name="{plugin_title}",
            type=PluginType.ANALYZER,
            version="0.1.0",
            description="TODO: descreva o plugin",

            # provides = campos que o dict de resultado DEVE conter.
            # Contrato: o engine valida que o resultado contém estes campos.
            # Outros plugins podem depender destes via requires=["campo"].
            # Dois plugins NAO podem fornecer o mesmo campo (erro no startup).
            provides=[
                "analysis_result",  # TODO: mude para seus campos reais
            ],

            # Dados de outros plugins necessarios (deixe [] se nao precisa)
            # Exemplos: ["word_frequencies"], ["cleaned_document"]
            requires=[],

            # Parametros configuraveis
            parameters={{
                "threshold": {{
                    "type": "float",
                    "default": 0.5,
                    "description": "TODO: descreva o parametro"
                }},
                "language": {{
                    "type": "string",
                    "default": "pt",
                    "description": "Codigo do idioma (pt, en, es)"
                }},
            }}
        )

    def _analyze_impl(self, document: Document, config: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementacao principal da analise.

        Args:
            document: Objeto Document (document.content = texto, document.id, document.metadata)
            config: Parametros validados com defaults aplicados
            context: Resultados de plugins dependentes (se houver requires)

        Returns:
            Dict com os campos prometidos em 'provides'
        """
        text = document.content
        threshold = config.get('threshold', 0.5)
        language = config.get('language', 'pt')

        # TODO: implemente sua analise aqui
        result = {{
            "analysis_result": "TODO: implementar analise real",
            "text_length": len(text),
            "config_used": config,
        }}

        return result


if __name__ == "__main__":
    from qualia.core import Document
    import json

    analyzer = {class_name}()
    meta = analyzer.meta()
    print(f"Plugin: {{meta.name}} v{{meta.version}}")
    print(f"Fornece: {{meta.provides}}")
    print(f"Parametros: {{list(meta.parameters.keys())}}")

    doc = Document(id="test", content="Texto de exemplo para testar o analyzer.")
    result = analyzer._analyze_impl(doc, {{}}, {{}})
    print(f"\\nResultado:\\n{{json.dumps(result, indent=2, ensure_ascii=False)}}")
''',

    "visualizer": '''"""
{plugin_title} - Visualizer plugin para Qualia Core

Criado em: {date}

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


class {class_name}(BaseVisualizerPlugin):
    """
    TODO: Descreva o que este visualizer faz.

    Exemplo de uso:
        qualia visualize data.json -p {plugin_id}
        qualia visualize data.json -p {plugin_id} -P theme=dark
    """

    # Declare qual lib de rendering este plugin usa.
    # Isso controla quais formatos de saida ficam disponiveis:
    #   "plotly"     → html (sempre), png/svg (se kaleido instalado)
    #   "matplotlib" → html, png, svg (todos nativos)
    #   "html"       → apenas html
    RENDER_LIB = "plotly"

    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="{plugin_id}",
            name="{plugin_title}",
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

            parameters={{
                "theme": {{
                    "type": "str",
                    "options": ["light", "dark"],
                    "default": "dark",
                    "description": "Tema visual"
                }},
                # output_format: gerado dinamicamente pelo BaseClass.
                # Mostra apenas formatos que funcionam no ambiente atual.
                "output_format": {{
                    "type": "str",
                    "default": "html",
                    "options": self.get_supported_formats(self.RENDER_LIB),
                    "description": "Formato de saida"
                }},
            }}
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

        required_data = data.get('data_field', {{}})
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


if __name__ == "__main__":
    import json

    viz = {class_name}()
    meta = viz.meta()
    print(f"Plugin: {{meta.name}} v{{meta.version}}")
    print(f"Requer: {{meta.requires}}")
    print(f"Parametros: {{list(meta.parameters.keys())}}")
    print(f"Formatos: {{meta.parameters.get('output_format', {{}}).get('options', [])}}")

    test_data = {{"data_field": {{"item1": 10, "item2": 20, "item3": 15}}}}

    print(f"\\nGerando visualizacao...")
    try:
        result = viz.render(test_data, {{}})
        has_html = "html" in result
        print(f"Resultado: {{'html' if has_html else 'imagem'}} ({{len(str(result.get('html', result.get('data', ''))))}} chars)")
    except Exception as e:
        print(f"Erro: {{e}}")
''',

    "document": '''"""
{plugin_title} - Document plugin para Qualia Core

Criado em: {date}
"""

from typing import Dict, Any, List, Optional
from qualia.core import BaseDocumentPlugin, PluginMetadata, PluginType, Document

# Imports comuns para processamento de documentos:
# import re
# import unicodedata
# from bs4 import BeautifulSoup


class {class_name}(BaseDocumentPlugin):
    """
    TODO: Descreva o que este processador faz.

    Exemplo de uso:
        qualia process documento.txt -p {plugin_id}
        qualia process doc.txt -p {plugin_id} -P remove_urls=true
    """

    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="{plugin_id}",
            name="{plugin_title}",
            type=PluginType.DOCUMENT,
            version="0.1.0",
            description="TODO: descreva o plugin",

            # provides = campos que o dict de resultado DEVE conter.
            # Contrato: o engine valida que o resultado contém estes campos.
            # Outros plugins podem depender destes via requires=["campo"].
            # Dois plugins NAO podem fornecer o mesmo campo (erro no startup).
            provides=[
                "cleaned_document",
                "quality_report",
            ],

            requires=[],

            parameters={{
                "remove_extra_spaces": {{
                    "type": "boolean",
                    "default": True,
                    "description": "Remover espacos extras e linhas em branco"
                }},
                "remove_urls": {{
                    "type": "boolean",
                    "default": False,
                    "description": "Remover URLs do texto"
                }},
            }}
        )

    def _process_impl(self, document: Document, config: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementacao do processamento.

        Args:
            document: Documento original (document.content, document.metadata)
            config: Configuracoes de processamento
            context: Contexto compartilhado

        Returns:
            Dict com documento processado e metadados
        """
        import re

        text = document.content
        original_length = len(text)
        processed = text
        changes = []

        if config.get('remove_extra_spaces', True):
            processed = re.sub(r' +', ' ', processed)
            processed = re.sub(r'\\n\\n+', '\\n\\n', processed)
            if processed != text:
                changes.append("Espacos extras removidos")

        if config.get('remove_urls', False):
            urls = re.findall(r'https?://\\S+', processed)
            if urls:
                processed = re.sub(r'https?://\\S+', '', processed)
                changes.append(f"{{len(urls)}} URLs removidas")

        # TODO: adicione seus processamentos aqui

        return {{
            "cleaned_document": processed,
            "original_length": original_length,
            "cleaned_length": len(processed),
            "quality_report": {{
                "changes_made": changes,
                "total_changes": len(changes),
            }},
        }}


if __name__ == "__main__":
    from qualia.core import Document
    import json

    processor = {class_name}()
    meta = processor.meta()
    print(f"Plugin: {{meta.name}} v{{meta.version}}")
    print(f"Parametros: {{list(meta.parameters.keys())}}")

    doc = Document(id="test", content="Texto  com   espacos   extras   e https://example.com uma URL.")
    result = processor._process_impl(doc, {{"remove_urls": True}}, {{}})
    print(f"\\nResultado:\\n{{json.dumps(result, indent=2, ensure_ascii=False)}}")
''',
}


def create_plugin(plugin_id: str, plugin_type: str):
    """Cria estrutura de plugin com template completo"""

    if plugin_type not in ["analyzer", "visualizer", "document"]:
        print(f"Erro: tipo invalido '{plugin_type}'. Use: analyzer, visualizer, document")
        return False

    # Preparar variaveis
    class_name = ''.join(word.capitalize() for word in plugin_id.split('_'))
    suffixes = {"analyzer": "Analyzer", "visualizer": "Visualizer", "document": "Processor"}
    class_name += suffixes[plugin_type]

    plugin_title = ' '.join(word.capitalize() for word in plugin_id.split('_'))

    # Verificar se ja existe
    plugin_dir = Path(f"plugins/{plugin_id}")
    if plugin_dir.exists():
        print(f"Erro: plugin '{plugin_id}' ja existe em {plugin_dir}")
        return False

    plugin_dir.mkdir(parents=True)

    # Gerar __init__.py
    template_vars = {
        "plugin_id": plugin_id,
        "plugin_title": plugin_title,
        "class_name": class_name,
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    init_content = TEMPLATES[plugin_type].format(**template_vars)
    (plugin_dir / "__init__.py").write_text(init_content)

    cli_cmd = {"analyzer": "analyze", "visualizer": "visualize", "document": "process"}[plugin_type]

    print(f"""
Plugin criado: plugins/{plugin_id}/

Proximos passos:
  1. Editar plugins/{plugin_id}/__init__.py — procurar por TODO
  2. Se precisar de deps novas, adicionar no pyproject.toml (extras)
  3. Testar: python plugins/{plugin_id}/__init__.py
  4. Usar:   qualia {cli_cmd} arquivo.txt -p {plugin_id}
""")

    return True


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python tools/create_plugin.py <plugin_id> <tipo>")
        print("Exemplo: python tools/create_plugin.py meu_analyzer analyzer")
        print("Tipos: analyzer, visualizer, document")
        sys.exit(1)

    create_plugin(sys.argv[1], sys.argv[2])
