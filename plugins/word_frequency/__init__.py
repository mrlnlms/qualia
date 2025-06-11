# plugins/word_frequency/__init__.py
"""
Plugin para análise de frequência de palavras em documentos

Este plugin conta palavras e gera estatísticas sobre vocabulário.
Útil para análise exploratória de transcrições e documentos.
"""

from typing import Dict, Any, List, Tuple
from collections import Counter
import re

# MUDANÇA: Importar BaseAnalyzerPlugin ao invés de IAnalyzerPlugin
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document


class WordFrequencyAnalyzer(BaseAnalyzerPlugin):  # MUDANÇA: Herdar de Base
    """
    Analisa frequência de palavras em documentos
    
    Features:
    - Contagem de palavras com filtros configuráveis
    - Suporte para múltiplos idiomas (stopwords)
    - Análise por segmento ou speaker
    - Identificação de hapax legomena
    
    Exemplo de uso via CLI:
        qualia analyze documento.txt -p word_frequency
        qualia analyze documento.txt -p word_frequency -P min_word_length=4
        qualia analyze documento.txt -p word_frequency -P remove_stopwords=true -P language=portuguese
    
    Exemplo de uso via Python:
        from qualia.core import QualiaCore
        
        core = QualiaCore()
        doc = core.add_document("exemplo", "Este é um texto de exemplo.")
        
        result = core.execute_plugin("word_frequency", doc, {
            "min_word_length": 3,
            "remove_stopwords": True
        })
        
        print(f"Palavras únicas: {result['vocabulary_size']}")
        print(f"Top 5 palavras: {result['top_words'][:5]}")
    """
    
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="word_frequency",
            name="Word Frequency Analyzer",
            type=PluginType.ANALYZER,
            version="1.0.0",
            description="Conta frequência de palavras com várias opções de processamento",
            provides=["word_frequencies", "vocabulary_size", "top_words", "hapax_legomena"],
            requires=[],  # Não depende de outros plugins
            parameters={
                "min_word_length": {
                    "type": "integer",
                    "default": 3,
                    "description": "Comprimento mínimo das palavras a considerar"
                },
                "max_words": {
                    "type": "integer",
                    "default": 100,
                    "description": "Número máximo de palavras no resultado"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "default": False,
                    "description": "Considerar maiúsculas/minúsculas como diferentes"
                },
                "remove_stopwords": {
                    "type": "boolean",
                    "default": True,
                    "description": "Remover palavras comuns (stopwords)"
                },
                "language": {
                    "type": "choice",
                    "options": ["portuguese", "english", "spanish"],
                    "default": "portuguese",
                    "description": "Idioma para lista de stopwords"
                },
                "tokenization": {
                    "type": "choice",
                    "options": ["simple", "nltk", "spacy"],
                    "default": "simple",
                    "description": "Método de tokenização (simple=regex, nltk=melhor)"
                },
                "by_segment": {
                    "type": "boolean",
                    "default": False,
                    "description": "Analisar por segmento/parágrafo separadamente"
                },
                "by_speaker": {
                    "type": "boolean",
                    "default": False,
                    "description": "Analisar por speaker (requer doc estruturado)"
                }
            }
        )
    
    # MUDANÇA: Renomear analyze para _analyze_impl
    def _analyze_impl(self, document: Document, config: Dict[str, Any], 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementação da análise de frequência
        
        Args:
            document: Documento a analisar
            config: Configurações (já validadas pela BaseClass)
            context: Contexto de execução
            
        Returns:
            Dict com word_frequencies, vocabulary_size, top_words, etc.
        """
        
        # Obter texto do documento
        text = document.content
        
        # Aplicar case sensitivity
        if not config['case_sensitive']:
            text = text.lower()
        
        # Tokenizar
        words = self._tokenize(text, config['tokenization'])
        
        # Filtrar palavras
        words = self._filter_words(words, config)
        
        # Contar frequências
        word_freq = Counter(words)
        
        # Preparar top words
        top_words = word_freq.most_common(config['max_words'])
        
        # Hapax legomena (palavras que aparecem apenas uma vez)
        hapax = [word for word, count in word_freq.items() if count == 1]
        
        # Retornar análise
        return {
            "word_frequencies": dict(top_words),
            "vocabulary_size": len(word_freq),
            "top_words": top_words,
            "hapax_legomena": hapax,
            "total_words": sum(word_freq.values()),
            "parameters_used": config
        }
    
    def _tokenize(self, text: str, method: str) -> List[str]:
        """
        Tokeniza o texto usando o método especificado
        
        Args:
            text: Texto para tokenizar
            method: 'simple', 'nltk' ou 'spacy'
            
        Returns:
            Lista de palavras/tokens
        """
        if method == "simple":
            # Tokenização simples com regex - rápida e eficaz
            return re.findall(r'\b\w+\b', text)
        
        elif method == "nltk":
            try:
                import nltk
                # Tentar usar tokenizador NLTK
                try:
                    tokens = nltk.word_tokenize(text)
                except LookupError:
                    # Baixar recursos se necessário
                    nltk.download('punkt')
                    tokens = nltk.word_tokenize(text)
                return tokens
            except ImportError:
                # NLTK não instalado, usar simple
                print("NLTK não instalado. Usando tokenização simples.")
                return self._tokenize(text, "simple")
        
        elif method == "spacy":
            try:
                import spacy
                # Tentar carregar modelo português
                try:
                    nlp = spacy.load("pt_core_news_sm")
                except OSError:
                    # Tentar modelo inglês
                    nlp = spacy.load("en_core_web_sm")
                
                doc = nlp(text)
                return [token.text for token in doc if not token.is_punct]
            except (ImportError, OSError):
                # spaCy não instalado ou sem modelo
                print("spaCy não disponível. Usando tokenização simples.")
                return self._tokenize(text, "simple")
        
        return []
    
    def _filter_words(self, words: List[str], config: Dict[str, Any]) -> List[str]:
        """
        Filtra palavras baseado na configuração
        
        Args:
            words: Lista de palavras
            config: Configurações de filtro
            
        Returns:
            Lista de palavras filtradas
        """
        filtered = []
        
        # Obter stopwords se necessário
        stopwords = set()
        if config['remove_stopwords']:
            stopwords = self._get_stopwords(config['language'])
        
        for word in words:
            # Verificar comprimento mínimo
            if len(word) < config['min_word_length']:
                continue
            
            # Verificar stopwords
            if config['remove_stopwords'] and word.lower() in stopwords:
                continue
            
            # Remover palavras com números/símbolos
            if not word.isalpha():
                continue
            
            filtered.append(word)
        
        return filtered
    
    def _get_stopwords(self, language: str) -> set:
        """
        Obtém lista de stopwords para o idioma
        
        Args:
            language: 'portuguese', 'english' ou 'spanish'
            
        Returns:
            Set de stopwords
        """
        try:
            import nltk
            from nltk.corpus import stopwords
            
            # Mapear para nomes NLTK
            lang_map = {
                'portuguese': 'portuguese',
                'english': 'english', 
                'spanish': 'spanish'
            }
            
            try:
                return set(stopwords.words(lang_map[language]))
            except LookupError:
                # Baixar stopwords se necessário
                nltk.download('stopwords')
                return set(stopwords.words(lang_map[language]))
                
        except ImportError:
            # NLTK não disponível - usar lista básica
            # Lista mínima de stopwords em português
            basic_pt = {
                'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 
                'é', 'com', 'não', 'uma', 'os', 'no', 'se', 'na', 'por',
                'mais', 'as', 'dos', 'como', 'mas', 'foi', 'ao', 'ele',
                'das', 'tem', 'seu', 'sua', 'ou', 'ser', 'quando', 'muito',
                'já', 'eu', 'também', 'só', 'pelo', 'pela', 'até', 'isso',
                'ela', 'entre', 'era', 'depois', 'sem', 'mesmo', 'aos',
                'ter', 'seus', 'quem', 'nas', 'me', 'esse', 'eles', 'estão',
                'você', 'tinha', 'foram', 'essa', 'num', 'nem', 'suas',
                'meu', 'às', 'minha', 'têm', 'numa', 'pelos', 'elas'
            }
            
            basic_en = {
                'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
                'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
                'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they',
                'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one',
                'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out',
                'if', 'about', 'who', 'get', 'which', 'go', 'me'
            }
            
            if language == 'portuguese':
                return basic_pt
            elif language == 'english':
                return basic_en
            else:
                return set()


# Exemplo de uso standalone (para testes)
if __name__ == "__main__":
    # Teste rápido
    analyzer = WordFrequencyAnalyzer()
    
    # Criar documento fake
    from qualia.core import Document
    doc = Document(
        id="test",
        content="Este é um teste de análise de frequência. Teste teste teste."
    )
    
    # Executar análise
    result = analyzer._analyze_impl(doc, {"min_word_length": 3}, {})
    
    print("Resultado da análise:")
    print(f"Vocabulário: {result['vocabulary_size']} palavras")
    print(f"Top palavras: {result['top_words'][:5]}")
    print(f"Hapax legomena: {len(result['hapax_legomena'])}")