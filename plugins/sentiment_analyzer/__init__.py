"""
Sentiment Analyzer Plugin for Qualia

Analisa sentimento e subjetividade de textos em português e inglês.
Usa TextBlob com suporte para PT-BR.
"""

from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import logging

from qualia.core import PluginType, PluginMetadata, BaseAnalyzerPlugin, Document, ExecutionContext

# Configurar logging
logger = logging.getLogger(__name__)

class SentimentAnalyzer(BaseAnalyzerPlugin):
    """
    Analyzer que detecta sentimento (polaridade) e subjetividade em textos.
    
    Retorna:
    - polarity: -1.0 (negativo) a 1.0 (positivo)
    - subjectivity: 0.0 (objetivo) a 1.0 (subjetivo)
    - sentiment_label: negativo/neutro/positivo
    - language: idioma detectado
    - sentence_sentiments: sentimento por sentença
    """
    
    def __init__(self):
        super().__init__()
        self._textblob_available = False
        self._langdetect_available = False
        
        # Tentar importar dependências
        try:
            from textblob import TextBlob
            self._textblob_available = True
            self.TextBlob = TextBlob
            
            # Baixar corpora se necessário
            try:
                import nltk
                nltk.download('brown', quiet=True)
                nltk.download('punkt', quiet=True)
            except:
                pass
                
        except ImportError:
            logger.warning("TextBlob não instalado. Instale com: pip install textblob")
        
        try:
            import langdetect
            self._langdetect_available = True
            self.langdetect = langdetect
        except ImportError:
            logger.warning("langdetect não instalado. Instale com: pip install langdetect")
    
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="sentiment_analyzer",
            name="Sentiment Analyzer",
            type=PluginType.ANALYZER,
            version="1.0.0",
            description="Analisa sentimento (polaridade) e subjetividade de textos",
            provides=[
                "polarity",           # -1 a 1
                "subjectivity",       # 0 a 1
                "sentiment_label",    # negativo/neutro/positivo
                "language",           # pt/en/etc
                "sentence_sentiments" # lista de sentimentos por sentença
            ],
            requires=[],
            parameters={
                "language": {
                    "type": "string",
                    "description": "Idioma do texto (auto-detecta se não especificado)",
                    "default": "auto",
                    "options": ["auto", "pt", "en"]
                },
                "polarity_threshold": {
                    "type": "float",
                    "description": "Threshold para classificar como positivo/negativo (default: 0.1)",
                    "default": 0.1,
                    "min": 0.0,
                    "max": 1.0
                },
                "analyze_sentences": {
                    "type": "boolean",
                    "description": "Analisar sentimento por sentença",
                    "default": True
                },
                "include_examples": {
                    "type": "boolean",
                    "description": "Incluir exemplos de sentenças mais positivas/negativas",
                    "default": True
                }
            }
        )
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Valida configuração do plugin"""
        if not self._textblob_available:
            return False, "TextBlob não está instalado. Execute: pip install textblob"
        
        threshold = config.get('polarity_threshold', 0.1)
        if not 0 <= threshold <= 1:
            return False, "polarity_threshold deve estar entre 0 e 1"
        
        language = config.get('language', 'auto')
        if language not in ['auto', 'pt', 'en']:
            return False, f"Idioma '{language}' não suportado. Use: auto, pt, en"
        
        return True, None
    
    def _detect_language(self, text: str) -> str:
        """Detecta idioma do texto"""
        if self._langdetect_available:
            try:
                return self.langdetect.detect(text)
            except:
                pass
        
        # Fallback: detectar por palavras comuns
        pt_words = ['de', 'que', 'o', 'a', 'e', 'do', 'da', 'em', 'um', 'para', 'é', 'com']
        en_words = ['the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'as', 'are', 'been', 'be']
        
        text_lower = text.lower()
        pt_count = sum(1 for word in pt_words if f' {word} ' in f' {text_lower} ')
        en_count = sum(1 for word in en_words if f' {word} ' in f' {text_lower} ')
        
        return 'pt' if pt_count > en_count else 'en'
    
    def _get_sentiment_label(self, polarity: float, threshold: float) -> str:
        """Converte polaridade em rótulo"""
        if polarity > threshold:
            return "positivo"
        elif polarity < -threshold:
            return "negativo"
        else:
            return "neutro"
    
    def _analyze_impl(self, document: Document, config: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Implementa análise de sentimento"""
        text = document.content
        
        # Configurações
        language_config = config.get('language', 'auto')
        threshold = config.get('polarity_threshold', 0.1)
        analyze_sentences = config.get('analyze_sentences', True)
        include_examples = config.get('include_examples', True)
        
        # Detectar idioma se necessário
        if language_config == 'auto':
            language = self._detect_language(text)
        else:
            language = language_config
        
        # Criar TextBlob
        blob = self.TextBlob(text)
        
        # Análise principal
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        sentiment_label = self._get_sentiment_label(polarity, threshold)
        
        result = {
            'polarity': round(polarity, 4),
            'subjectivity': round(subjectivity, 4),
            'sentiment_label': sentiment_label,
            'language': language,
            'text_length': len(text),
            'word_count': len(text.split())
        }
        
        # Análise por sentença
        if analyze_sentences and blob.sentences:
            sentence_sentiments = []
            most_positive = None
            most_negative = None
            max_polarity = -1
            min_polarity = 1
            
            for sentence in blob.sentences:
                sent_polarity = sentence.sentiment.polarity
                sent_subjectivity = sentence.sentiment.subjectivity
                sent_label = self._get_sentiment_label(sent_polarity, threshold)
                
                sentence_info = {
                    'text': str(sentence)[:100] + ('...' if len(str(sentence)) > 100 else ''),
                    'polarity': round(sent_polarity, 4),
                    'subjectivity': round(sent_subjectivity, 4),
                    'sentiment': sent_label
                }
                sentence_sentiments.append(sentence_info)
                
                # Rastrear exemplos extremos
                if sent_polarity > max_polarity:
                    max_polarity = sent_polarity
                    most_positive = sentence_info
                if sent_polarity < min_polarity:
                    min_polarity = sent_polarity
                    most_negative = sentence_info
            
            result['sentence_sentiments'] = sentence_sentiments
            result['sentence_count'] = len(sentence_sentiments)
            
            # Estatísticas
            polarities = [s['polarity'] for s in sentence_sentiments]
            result['sentiment_stats'] = {
                'positive_sentences': sum(1 for s in sentence_sentiments if s['sentiment'] == 'positivo'),
                'negative_sentences': sum(1 for s in sentence_sentiments if s['sentiment'] == 'negativo'),
                'neutral_sentences': sum(1 for s in sentence_sentiments if s['sentiment'] == 'neutro'),
                'avg_polarity': round(sum(polarities) / len(polarities), 4) if polarities else 0,
                'polarity_std': round(self._calculate_std(polarities), 4) if polarities else 0
            }
            
            # Exemplos
            if include_examples:
                if most_positive:
                    result['most_positive_sentence'] = most_positive
                if most_negative:
                    result['most_negative_sentence'] = most_negative
        
        # Interpretação
        result['interpretation'] = self._get_interpretation(
            polarity, subjectivity, sentiment_label, language
        )
        
        return result
    
    def _calculate_std(self, values: list) -> float:
        """Calcula desvio padrão"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _get_interpretation(self, polarity: float, subjectivity: float, 
                          sentiment: str, language: str) -> Dict[str, str]:
        """Gera interpretação dos resultados"""
        interpretation = {}
        
        # Interpretação de polaridade
        if language == 'pt':
            if sentiment == 'positivo':
                if polarity > 0.5:
                    interpretation['sentiment'] = "O texto expressa sentimento muito positivo"
                else:
                    interpretation['sentiment'] = "O texto expressa sentimento levemente positivo"
            elif sentiment == 'negativo':
                if polarity < -0.5:
                    interpretation['sentiment'] = "O texto expressa sentimento muito negativo"
                else:
                    interpretation['sentiment'] = "O texto expressa sentimento levemente negativo"
            else:
                interpretation['sentiment'] = "O texto é neutro em termos de sentimento"
            
            # Interpretação de subjetividade
            if subjectivity > 0.7:
                interpretation['subjectivity'] = "O texto é altamente subjetivo (opiniões pessoais)"
            elif subjectivity > 0.3:
                interpretation['subjectivity'] = "O texto mistura fatos e opiniões"
            else:
                interpretation['subjectivity'] = "O texto é principalmente objetivo (factual)"
        else:
            # Versão em inglês
            if sentiment == 'positivo':
                if polarity > 0.5:
                    interpretation['sentiment'] = "The text expresses very positive sentiment"
                else:
                    interpretation['sentiment'] = "The text expresses slightly positive sentiment"
            elif sentiment == 'negativo':
                if polarity < -0.5:
                    interpretation['sentiment'] = "The text expresses very negative sentiment"
                else:
                    interpretation['sentiment'] = "The text expresses slightly negative sentiment"
            else:
                interpretation['sentiment'] = "The text is neutral in terms of sentiment"
            
            if subjectivity > 0.7:
                interpretation['subjectivity'] = "The text is highly subjective (personal opinions)"
            elif subjectivity > 0.3:
                interpretation['subjectivity'] = "The text mixes facts and opinions"
            else:
                interpretation['subjectivity'] = "The text is mainly objective (factual)"
        
        return interpretation


# Para testes diretos
if __name__ == "__main__":
    import json
    
    analyzer = SentimentAnalyzer()
    print(f"Plugin: {analyzer.meta().name}")
    print(f"Versão: {analyzer.meta().version}")
    
    # Teste com texto de exemplo
    test_text = """
    Este produto é absolutamente maravilhoso! Superou todas as minhas expectativas.
    A qualidade é excelente e o atendimento foi perfeito.
    Recomendo fortemente para todos.
    """
    
    doc = Document("test_doc", test_text)
    config = {
        "analyze_sentences": True,
        "include_examples": True
    }
    
    try:
        result = analyzer._analyze_impl(doc, config, ExecutionContext())
        print("\nResultado da análise:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\nErro: {e}")
        print("Certifique-se de instalar: pip install textblob langdetect")
