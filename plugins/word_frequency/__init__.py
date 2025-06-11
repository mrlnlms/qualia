# plugins/word_frequency/__init__.py
"""
Exemplo de Plugin Analyzer - Word Frequency

Este plugin demonstra como criar um analyzer que:
- Se auto-descreve completamente
- Usa bibliotecas externas (NLTK)
- Declara o que produz
- Pode usar dados opcionais de outros plugins
"""

from typing import Dict, List, Any, Tuple, Optional
from collections import Counter
import re

# Imports do Core (interfaces que o plugin deve implementar)
from qualia.core import (
    IAnalyzerPlugin, 
    PluginMetadata, 
    PluginType
)


class WordFrequencyAnalyzer(IAnalyzerPlugin):
    """
    Analyzer que calcula frequência de palavras
    
    É um WRAPPER inteligente do NLTK/collections.Counter
    NÃO reimplementa algoritmos, apenas fornece interface unificada
    """
    
    def meta(self) -> PluginMetadata:
        """Auto-descrição completa do plugin"""
        return PluginMetadata(
            id="word_frequency",
            type=PluginType.ANALYZER,
            name="Word Frequency Analyzer",
            description="Calcula frequência de palavras no documento",
            version="1.0.0",
            
            # O que este plugin produz
            provides=[
                "word_frequencies",      # Dict com frequências
                "vocabulary_size",       # Tamanho do vocabulário
                "top_words",            # Palavras mais frequentes
                "hapax_legomena"        # Palavras que aparecem só uma vez
            ],
            
            # Dependências obrigatórias (neste caso, nenhuma)
            requires=[],
            
            # Dados opcionais que melhoram a análise
            can_use=[
                "segments",         # Se tiver segmentos, analisa por segmento
                "speaker_labels",   # Se tiver speakers, analisa por speaker
                "cleaned_text"      # Se tiver texto limpo, usa ele
            ],
            
            # Schema de parâmetros
            parameters={
                "min_word_length": {
                    "type": "integer",
                    "default": 2,
                    "min": 1,
                    "max": 50,
                    "description": "Comprimento mínimo da palavra"
                },
                "max_words": {
                    "type": "integer",
                    "default": 100,
                    "min": 10,
                    "max": 1000,
                    "description": "Número máximo de palavras no top_words"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "default": False,
                    "description": "Considerar maiúsculas/minúsculas"
                },
                "remove_stopwords": {
                    "type": "boolean",
                    "default": True,
                    "description": "Remover stopwords"
                },
                "language": {
                    "type": "choice",
                    "options": ["portuguese", "english", "spanish"],
                    "default": "portuguese",
                    "description": "Idioma para stopwords"
                },
                "tokenization": {
                    "type": "choice",
                    "options": ["simple", "nltk", "spacy"],
                    "default": "simple",
                    "description": "Método de tokenização"
                },
                "by_segment": {
                    "type": "boolean",
                    "default": False,
                    "description": "Analisar por segmento se disponível"
                },
                "by_speaker": {
                    "type": "boolean",
                    "default": False,
                    "description": "Analisar por speaker se disponível"
                }
            }
        )
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Valida configuração contra schema"""
        meta = self.meta()
        
        for param, value in config.items():
            if param not in meta.parameters:
                return False, f"Parâmetro desconhecido: {param}"
            
            param_schema = meta.parameters[param]
            param_type = param_schema.get("type")
            
            # Validação básica de tipos
            if param_type == "integer" and not isinstance(value, int):
                return False, f"{param} deve ser inteiro"
            elif param_type == "boolean" and not isinstance(value, bool):
                return False, f"{param} deve ser booleano"
            elif param_type == "choice" and value not in param_schema.get("options", []):
                return False, f"{param} deve ser uma das opções: {param_schema.get('options')}"
            
            # Validação de ranges
            if param_type == "integer":
                min_val = param_schema.get("min")
                max_val = param_schema.get("max")
                if min_val is not None and value < min_val:
                    return False, f"{param} deve ser >= {min_val}"
                if max_val is not None and value > max_val:
                    return False, f"{param} deve ser <= {max_val}"
        
        return True, None
    
    def analyze(self, 
                document: Any, 
                config: Dict[str, Any], 
                context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa análise de frequência
        
        Args:
            document: Objeto Document com o texto
            config: Configuração do usuário
            context: Resultados de dependências (se houver)
        """
        # Aplica defaults
        params = self._apply_defaults(config)
        
        # Decide qual texto usar
        text = self._get_text_to_analyze(document, context, params)
        
        # Tokeniza
        tokens = self._tokenize(text, params)
        
        # Remove stopwords se configurado
        if params["remove_stopwords"]:
            tokens = self._remove_stopwords(tokens, params["language"])
        
        # Filtra por comprimento mínimo
        tokens = [t for t in tokens if len(t) >= params["min_word_length"]]
        
        # Calcula frequências
        frequencies = Counter(tokens)
        
        # Prepara resultado
        result = {
            "word_frequencies": dict(frequencies),
            "vocabulary_size": len(frequencies),
            "top_words": frequencies.most_common(params["max_words"]),
            "hapax_legomena": [word for word, count in frequencies.items() if count == 1],
            "total_words": sum(frequencies.values()),
            "parameters_used": params
        }
        
        # Análise por segmento/speaker se solicitado e disponível
        if params["by_segment"] and "segments" in context:
            result["by_segment"] = self._analyze_by_segment(
                context["segments"], params
            )
        
        if params["by_speaker"] and "speaker_labels" in context:
            result["by_speaker"] = self._analyze_by_speaker(
                document, context["speaker_labels"], params
            )
        
        return result
    
    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica valores default aos parâmetros"""
        meta = self.meta()
        params = {}
        
        for param_name, param_schema in meta.parameters.items():
            if param_name in config:
                params[param_name] = config[param_name]
            else:
                params[param_name] = param_schema.get("default")
        
        return params
    
    def _get_text_to_analyze(self, 
                            document: Any, 
                            context: Dict[str, Any], 
                            params: Dict[str, Any]) -> str:
        """Decide qual texto usar baseado no contexto disponível"""
        # Se tem texto limpo no contexto, prefere ele
        if "cleaned_text" in context and context["cleaned_text"]:
            return context["cleaned_text"]
        
        # Senão, usa o texto do documento
        return document.content
    
    def _tokenize(self, text: str, params: Dict[str, Any]) -> List[str]:
        """Tokeniza o texto baseado no método escolhido"""
        if not params["case_sensitive"]:
            text = text.lower()
        
        if params["tokenization"] == "simple":
            # Tokenização simples com regex
            tokens = re.findall(r'\b\w+\b', text)
        elif params["tokenization"] == "nltk":
            # Aqui usaria NLTK se disponível
            try:
                import nltk
                tokens = nltk.word_tokenize(text)
            except ImportError:
                # Fallback para simple
                tokens = re.findall(r'\b\w+\b', text)
        else:
            # spaCy ou outros...
            tokens = re.findall(r'\b\w+\b', text)
        
        return tokens
    
    def _remove_stopwords(self, tokens: List[str], language: str) -> List[str]:
        """Remove stopwords baseado no idioma"""
        # Stopwords simplificadas para exemplo
        stopwords = {
            "portuguese": {
                "o", "a", "os", "as", "um", "uma", "de", "do", "da", 
                "em", "no", "na", "e", "é", "que", "para", "com"
            },
            "english": {
                "the", "a", "an", "and", "or", "but", "in", "on", 
                "at", "to", "for", "of", "with", "is", "are"
            },
            "spanish": {
                "el", "la", "los", "las", "un", "una", "de", "del",
                "en", "y", "es", "que", "para", "con"
            }
        }
        
        stop_set = stopwords.get(language, set())
        return [t for t in tokens if t.lower() not in stop_set]
    
    def _analyze_by_segment(self, 
                           segments: List[Dict[str, Any]], 
                           params: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa frequência por segmento"""
        results = {}
        
        for i, segment in enumerate(segments):
            segment_text = segment.get("text", "")
            tokens = self._tokenize(segment_text, params)
            
            if params["remove_stopwords"]:
                tokens = self._remove_stopwords(tokens, params["language"])
            
            tokens = [t for t in tokens if len(t) >= params["min_word_length"]]
            frequencies = Counter(tokens)
            
            results[f"segment_{i}"] = {
                "word_count": len(tokens),
                "vocabulary_size": len(frequencies),
                "top_10": frequencies.most_common(10)
            }
        
        return results
    
    def _analyze_by_speaker(self,
                           document: Any,
                           speaker_labels: Dict[str, List[Tuple[int, int]]],
                           params: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa frequência por speaker"""
        results = {}
        
        for speaker, ranges in speaker_labels.items():
            speaker_text = ""
            for start, end in ranges:
                speaker_text += document.content[start:end] + " "
            
            tokens = self._tokenize(speaker_text, params)
            
            if params["remove_stopwords"]:
                tokens = self._remove_stopwords(tokens, params["language"])
            
            tokens = [t for t in tokens if len(t) >= params["min_word_length"]]
            frequencies = Counter(tokens)
            
            results[speaker] = {
                "word_count": len(tokens),
                "vocabulary_size": len(frequencies),
                "top_10": frequencies.most_common(10),
                "unique_words": set(frequencies.keys())
            }
        
        return results


# ============================================================================
# REQUIREMENTS para este plugin
# ============================================================================
"""
requirements.txt:
nltk>=3.8
"""

# ============================================================================
# TESTES do plugin (para garantir que funciona isoladamente)
# ============================================================================

if __name__ == "__main__":
    # Teste básico do plugin
    plugin = WordFrequencyAnalyzer()
    
    # Verifica metadados
    meta = plugin.meta()
    print(f"Plugin: {meta.name} v{meta.version}")
    print(f"Fornece: {meta.provides}")
    print(f"Parâmetros: {list(meta.parameters.keys())}")
    
    # Teste de validação
    config_valid = {"min_word_length": 3, "language": "portuguese"}
    valid, error = plugin.validate_config(config_valid)
    print(f"\nConfig válida: {valid}")
    
    config_invalid = {"min_word_length": "três"}  # Tipo errado
    valid, error = plugin.validate_config(config_invalid)
    print(f"Config inválida: {valid}, Erro: {error}")
    
    # Teste de análise (simulando documento)
    class MockDocument:
        def __init__(self):
            self.id = "test_001"
            self.content = """
            Este é um texto de exemplo para testar o analisador de frequência.
            O analisador deve contar quantas vezes cada palavra aparece.
            Palavra palavra palavra - esta palavra aparece várias vezes!
            """
    
    doc = MockDocument()
    result = plugin.analyze(doc, {"min_word_length": 4}, {})
    
    print(f"\nResultado da análise:")
    print(f"Vocabulário: {result['vocabulary_size']} palavras")
    print(f"Top 5 palavras: {result['top_words'][:5]}")