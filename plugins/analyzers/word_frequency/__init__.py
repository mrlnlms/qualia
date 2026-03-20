# plugins/analyzers/word_frequency/__init__.py
"""
Plugin para análise de frequência de palavras em documentos

Este plugin conta palavras e gera estatísticas sobre vocabulário.
Útil para análise exploratória de transcrições e documentos.
"""

from typing import Dict, Any, List
from collections import Counter
import re
import logging

from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document

logger = logging.getLogger(__name__)


class WordFrequencyAnalyzer(BaseAnalyzerPlugin):
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

    def __init__(self):
        super().__init__()
        self._stopwords_cache: Dict[str, set] = {}
        self._nltk_available = False
        self._warm_up_nltk()
        self._spacy_nlp = None
        self._warm_up_spacy()

    def _warm_up_nltk(self):
        """Pré-carrega recursos NLTK na main thread (antes de concorrência).

        Plugins são singletons compartilhados entre worker threads.
        O LazyCorpusLoader do NLTK não é thread-safe, então forçamos
        a resolução aqui — onde só existe uma thread.
        """
        try:
            import nltk
            # Só baixa se não estiver em cache local (evita tentativa de rede)
            for resource in ('stopwords', 'punkt', 'punkt_tab'):
                try:
                    nltk.data.find(f'corpora/{resource}' if resource == 'stopwords' else f'tokenizers/{resource}')
                except LookupError:
                    nltk.download(resource, quiet=True)
            self._nltk_available = True

            # Forçar LazyCorpusLoader a resolver agora (single-threaded)
            from nltk.corpus import stopwords
            for lang in ('portuguese', 'english', 'spanish'):
                try:
                    self._stopwords_cache[lang] = set(stopwords.words(lang))
                except Exception:
                    pass
        except ImportError:
            self._nltk_available = False

    def _warm_up_spacy(self):
        """Pré-carrega modelo spaCy na main thread (antes de concorrência).

        Plugins são singletons compartilhados entre worker threads.
        spacy.load() não é thread-safe, então forçamos o carregamento
        aqui — onde só existe uma thread.
        """
        try:
            import spacy
            try:
                self._spacy_nlp = spacy.load("pt_core_news_sm")
                logger.debug("spaCy: modelo pt_core_news_sm carregado")
            except OSError:
                try:
                    self._spacy_nlp = spacy.load("en_core_web_sm")
                    logger.debug("spaCy: modelo en_core_web_sm carregado (fallback)")
                except OSError:
                    logger.info("spaCy instalado mas sem modelos — tokenization=spacy indisponível")
        except ImportError:
            logger.debug("spaCy não instalado — tokenization=spacy indisponível")

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
                    "description": "Comprimento mínimo das palavras a considerar",
                    "text_size_adjustments": {
                        "short_text": 2,
                        "long_text": 4,
                    }
                },
                "max_words": {
                    "type": "integer",
                    "default": 100,
                    "description": "Número máximo de palavras no resultado",
                    "text_size_adjustments": {
                        "short_text": 50,
                        "long_text": 200,
                    }
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

        # Análise global
        result = self._analyze_text(document.content, config)

        # Análise por segmento (parágrafos)
        if config['by_segment']:
            segments = self._split_segments(document.content)
            result["segments"] = [
                {"index": i, "preview": seg[:80], **self._analyze_text(seg, config)}
                for i, seg in enumerate(segments)
            ]

        # Análise por speaker (formato "Speaker: texto")
        if config['by_speaker']:
            speaker_texts = self._split_by_speaker(document.content)
            if speaker_texts:
                result["by_speaker"] = {
                    speaker: self._analyze_text(text, config)
                    for speaker, text in speaker_texts.items()
                }

        return result

    def _analyze_text(self, text: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Análise de frequência num bloco de texto."""
        if not config['case_sensitive']:
            text = text.lower()

        words = self._tokenize(text, config['tokenization'])
        words = self._filter_words(words, config)
        word_freq = Counter(words)
        top_words = word_freq.most_common(config['max_words'])
        hapax = [word for word, count in word_freq.items() if count == 1]

        return {
            "word_frequencies": dict(top_words),
            "vocabulary_size": len(word_freq),
            "top_words": top_words,
            "hapax_legomena": hapax,
            "total_words": sum(word_freq.values()),
            "parameters_used": config,
        }

    def _split_segments(self, text: str) -> List[str]:
        """Divide texto em segmentos por parágrafo (linhas em branco)."""
        segments = re.split(r'\n\s*\n', text)
        return [seg.strip() for seg in segments if seg.strip()]

    def _split_by_speaker(self, text: str) -> Dict[str, str]:
        """Extrai texto por speaker — formatos Teams/transcrição.

        Suporta:
          - [HH:MM:SS] Speaker: texto
          - Speaker (HH:MM:SS): texto
          - Speaker: texto
        """
        speaker_texts: Dict[str, str] = {}
        # Padrões ordenados por especificidade
        patterns = [
            r'^\[?\d{1,2}:\d{2}:\d{2}\]?\s*([^:]+):\s*(.+)$',
            r'^([^(]+)\s*\(\d{1,2}:\d{2}:\d{2}\):\s*(.+)$',
            r'^([^:]+):\s*(.+)$',
        ]
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    speaker = match.group(1).strip()
                    utterance = match.group(2).strip()
                    if speaker in speaker_texts:
                        speaker_texts[speaker] += ' ' + utterance
                    else:
                        speaker_texts[speaker] = utterance
                    break
        return speaker_texts
    
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
            if not self._nltk_available:
                return self._tokenize(text, "simple")
            import nltk
            return nltk.word_tokenize(text)
        
        elif method == "spacy":
            if self._spacy_nlp is not None:
                doc = self._spacy_nlp(text)
                return [token.text for token in doc if not token.is_punct]
            else:
                logger.warning("spaCy não disponível. Usando tokenização simples.")
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
        """Obtém lista de stopwords para o idioma (cache ou fallback)."""
        # Cache NLTK (pré-carregado no __init__)
        if language in self._stopwords_cache:
            return self._stopwords_cache[language]

        # Fallback: listas básicas (NLTK não disponível)
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
