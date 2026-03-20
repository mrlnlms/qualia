"""
__PLUGIN_TITLE__ - Analyzer plugin para Qualia Core

Criado em: __DATE__
"""

from typing import Dict, Any, List, Optional, Tuple
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document

# Imports comuns para analyzers:
# import nltk
# from textblob import TextBlob
# import spacy
# from collections import Counter
# import re


class __CLASS_NAME__(BaseAnalyzerPlugin):
    """
    TODO: Descreva o que este analyzer faz.

    Exemplo de uso:
        qualia analyze documento.txt -p __PLUGIN_ID__
        qualia analyze doc.txt -p __PLUGIN_ID__ -P param1=valor
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
            id="__PLUGIN_ID__",
            name="__PLUGIN_TITLE__",
            type=PluginType.ANALYZER,
            version="0.1.0",
            description="TODO: descreva o plugin",

            # provides = campos que o dict de resultado DEVE conter.
            # Contrato: o engine valida que o resultado contém estes campos.
            # Outros plugins podem depender destes via requires=["campo"].
            # Múltiplos plugins podem declarar o mesmo campo — mas resolução automática de dependências requer provider único.
            provides=[
                "analysis_result",  # TODO: mude para seus campos reais
            ],

            # Dados de outros plugins necessarios (deixe [] se nao precisa)
            # Exemplos: ["word_frequencies"], ["cleaned_document"]
            requires=[],

            # Parametros configuraveis
            parameters={
                "threshold": {
                    "type": "float",
                    "default": 0.5,
                    "description": "TODO: descreva o parametro"
                },
                "language": {
                    "type": "string",
                    "default": "pt",
                    "description": "Codigo do idioma (pt, en, es)"
                },
            }
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
        result = {
            "analysis_result": "TODO: implementar analise real",
            "text_length": len(text),
            "config_used": config,
        }

        return result
