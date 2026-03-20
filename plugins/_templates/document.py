"""
__PLUGIN_TITLE__ - Document plugin para Qualia Core

Criado em: __DATE__
"""

from typing import Dict, Any, List, Optional
from qualia.core import BaseDocumentPlugin, PluginMetadata, PluginType, Document

# Imports comuns para processamento de documentos:
# import re
# import unicodedata
# from bs4 import BeautifulSoup


class __CLASS_NAME__(BaseDocumentPlugin):
    """
    TODO: Descreva o que este processador faz.

    Exemplo de uso:
        qualia process documento.txt -p __PLUGIN_ID__
        qualia process doc.txt -p __PLUGIN_ID__ -P remove_urls=true
    """

    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="__PLUGIN_ID__",
            name="__PLUGIN_TITLE__",
            type=PluginType.DOCUMENT,
            version="0.1.0",
            description="TODO: descreva o plugin",

            # provides = campos que o dict de resultado DEVE conter.
            # Contrato: o engine valida que o resultado contém estes campos.
            # Outros plugins podem depender destes via requires=["campo"].
            # Múltiplos plugins podem declarar o mesmo campo — mas resolução automática de dependências requer provider único.
            provides=[
                "processed_output",
                "quality_report",
            ],

            requires=[],

            parameters={
                "remove_extra_spaces": {
                    "type": "boolean",
                    "default": True,
                    "description": "Remover espacos extras e linhas em branco"
                },
                "remove_urls": {
                    "type": "boolean",
                    "default": False,
                    "description": "Remover URLs do texto"
                },
            }
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
            processed = re.sub(r'\n\n+', '\n\n', processed)
            if processed != text:
                changes.append("Espacos extras removidos")

        if config.get('remove_urls', False):
            urls = re.findall(r'https?://\S+', processed)
            if urls:
                processed = re.sub(r'https?://\S+', '', processed)
                changes.append(f"{len(urls)} URLs removidas")

        # TODO: adicione seus processamentos aqui

        return {
            "cleaned_document": processed,
            "original_length": original_length,
            "cleaned_length": len(processed),
            "quality_report": {
                "changes_made": changes,
                "total_changes": len(changes),
            },
        }
