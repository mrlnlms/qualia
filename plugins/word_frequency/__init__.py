# plugins/word_frequency/__init__.py
"""
Plugin de análise que calcula frequência de palavras
"""

from typing import Dict, Any, Set
import re
from collections import Counter

# IMPORTS CORRETOS - incluir TUDO que precisa!
from qualia.core import BaseAnalyzerPlugin
from qualia.core import PluginMetadata, PluginType, Document

class WordFrequencyAnalyzer(BaseAnalyzerPlugin):
    """
    Analisa frequência de palavras em documentos
    CIRCUIT BREAKER AUTOMÁTICO! 🛡️
    """
    
    def meta(self) -> PluginMetadata:
        """Metadados do plugin - OBRIGATÓRIO"""
        return PluginMetadata(
            id="word_frequency",
            name="Word Frequency Analyzer", 
            type=PluginType.ANALYZER,
            version="1.0.0",
            description="Calcula frequência de palavras em documentos",
            requires=[],  # Não depende de outros plugins
            provides=["word_frequencies", "total_words", "unique_words"],
            parameters={
                "min_length": {
                    "type": "integer",
                    "default": 3,
                    "description": "Tamanho mínimo da palavra"
                },
                "max_words": {
                    "type": "integer", 
                    "default": 100,
                    "description": "Número máximo de palavras no resultado"
                },
                "exclude_stopwords": {
                    "type": "boolean",
                    "default": True,
                    "description": "Excluir palavras comuns (stopwords)"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "default": False,
                    "description": "Diferenciar maiúsculas e minúsculas"
                }
            }
        )
    
    def _analyze_impl(self, document: Document, config: Dict[str, Any], 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        LÓGICA PURA DO PLUGIN! 🎯
        Circuit breaker já protege automaticamente!
        """
        text = document.content
        
        # Normalizar case se necessário
        if not config['case_sensitive']:
            text = text.lower()
        
        # Extrair palavras (regex simples)
        words = re.findall(r'\b[a-záàâãäéèêëíìîïóòôõöúùûüçñ]+\b', text, re.IGNORECASE)
        
        # Filtrar por tamanho mínimo
        words = [word for word in words if len(word) >= config['min_length']]
        
        # Excluir stopwords se configurado
        if config['exclude_stopwords']:
            stopwords = self._get_stopwords()
            words = [word for word in words if word not in stopwords]
        
        # Contar frequências
        word_freq = Counter(words)
        
        # Limitar número de palavras
        most_common = word_freq.most_common(config['max_words'])
        
        # Retornar resultados
        return {
            "word_frequencies": dict(most_common),
            "total_words": len(words),
            "unique_words": len(word_freq),
            "top_words": [word for word, count in most_common[:10]]
        }
    
    def _get_stopwords(self) -> Set[str]:
        """Retorna set de stopwords em português"""
        return {
            'a', 'à', 'ao', 'aos', 'as', 'à', 'e', 'é', 'o', 'os', 'da', 'das', 'de', 
            'do', 'dos', 'em', 'na', 'nas', 'no', 'nos', 'para', 'por', 'com', 'sem',
            'que', 'se', 'como', 'mais', 'mas', 'muito', 'muito', 'bem', 'já', 'não',
            'um', 'uma', 'uns', 'umas', 'ele', 'ela', 'eles', 'elas', 'eu', 'tu', 
            'você', 'nós', 'vós', 'vocês', 'meu', 'minha', 'meus', 'minhas', 'seu',
            'sua', 'seus', 'suas', 'nosso', 'nossa', 'nossos', 'nossas', 'este',
            'esta', 'estes', 'estas', 'esse', 'essa', 'esses', 'essas', 'aquele',
            'aquela', 'aqueles', 'aquelas', 'que', 'qual', 'quais', 'quando', 'onde',
            'como', 'porque', 'por', 'que', 'então', 'assim', 'também', 'ainda',
            'sobre', 'entre', 'até', 'depois', 'antes', 'agora', 'hoje', 'ontem',
            'amanhã', 'sempre', 'nunca', 'às', 'vezes', 'pode', 'poder', 'tem',
            'ter', 'vai', 'ir', 'vou', 'foi', 'ser', 'estar', 'sendo', 'estando'
        }

# Exportar plugin
__all__ = ['WordFrequencyAnalyzer']