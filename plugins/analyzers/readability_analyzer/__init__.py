# plugins/readability_analyzer/__init__.py
"""
Plugin de Análise de Legibilidade

Analisa o quão fácil é ler um texto. Conta frases, palavras por frase,
parágrafos, e calcula um índice de legibilidade simples.

Útil para: avaliar documentos, simplificar comunicação, comparar textos.
"""

from typing import Dict, Any, List
import re

from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document


class ReadabilityAnalyzer(BaseAnalyzerPlugin):
    """
    Analisa legibilidade de textos.

    Calcula:
    - Total de frases, palavras e parágrafos
    - Média de palavras por frase
    - Média de frases por parágrafo
    - Índice de legibilidade (0-100, quanto maior = mais fácil)
    - Classificação: Muito Fácil / Fácil / Moderado / Difícil / Muito Difícil

    Exemplo via CLI:
        qualia analyze meu_texto.txt -p readability_analyzer

    Exemplo via API:
        POST /analyze/readability_analyzer
        {"text": "Seu texto aqui..."}
    """

    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="readability_analyzer",
            name="Readability Analyzer",
            type=PluginType.ANALYZER,
            version="1.0.0",
            description="Analisa legibilidade do texto e dá uma nota de facilidade de leitura",
            provides=[
                "readability_score",
                "readability_level",
                "sentence_count",
                "word_count",
                "paragraph_count",
                "avg_words_per_sentence",
                "avg_sentences_per_paragraph",
                "longest_sentence",
                "shortest_sentence",
            ],
            requires=[],
            parameters={
                "language": {
                    "type": "choice",
                    "options": ["portuguese", "english"],
                    "default": "portuguese",
                    "description": "Idioma do texto (afeta classificação)"
                },
                "detail_level": {
                    "type": "choice",
                    "options": ["basic", "full"],
                    "default": "full",
                    "description": "Nível de detalhe: basic (só nota) ou full (tudo)"
                }
            }
        )

    def _analyze_impl(self, document: Document, config: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        text = document.content

        # --- Extrair estrutura do texto ---
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        sentences = self._split_sentences(text)
        words = re.findall(r'\b\w+\b', text)

        # --- Calcular métricas ---
        sentence_count = len(sentences)
        word_count = len(words)
        paragraph_count = len(paragraphs)

        avg_words_per_sentence = (
            word_count / sentence_count if sentence_count > 0 else 0
        )
        avg_sentences_per_paragraph = (
            sentence_count / paragraph_count if paragraph_count > 0 else 0
        )

        # Frase mais longa e mais curta
        sentence_lengths = [len(re.findall(r'\b\w+\b', s)) for s in sentences]

        longest = max(sentence_lengths) if sentence_lengths else 0
        shortest = min(sentence_lengths) if sentence_lengths else 0

        # --- Índice de legibilidade (0-100) ---
        # Inspirado no Flesch Reading Ease, adaptado para ser simples:
        # - Frases curtas = mais fácil
        # - Palavras curtas = mais fácil
        avg_word_length = (
            sum(len(w) for w in words) / len(words) if words else 0
        )

        # Fórmula simplificada: penaliza frases longas e palavras longas
        score = max(0, min(100,
            100 - (avg_words_per_sentence * 2) - (avg_word_length * 5)
        ))
        score = round(score, 1)

        # Classificação
        level = self._classify(score, config.get("language", "portuguese"))

        # --- Montar resultado ---
        result = {
            "readability_score": score,
            "readability_level": level,
            "sentence_count": sentence_count,
            "word_count": word_count,
            "paragraph_count": paragraph_count,
            "avg_words_per_sentence": round(avg_words_per_sentence, 1),
            "avg_sentences_per_paragraph": round(avg_sentences_per_paragraph, 1),
        }

        if config.get("detail_level") == "full":
            result["longest_sentence"] = longest
            result["shortest_sentence"] = shortest
            result["avg_word_length"] = round(avg_word_length, 1)
            result["sentence_lengths"] = sentence_lengths

        return result

    def _split_sentences(self, text: str) -> List[str]:
        """Divide texto em frases usando pontuação."""
        # Quebra em .!? seguidos de espaço ou fim de texto
        raw = re.split(r'[.!?]+(?:\s|$)', text)
        return [s.strip() for s in raw if s.strip()]

    def _classify(self, score: float, language: str) -> str:
        """Classifica o score em um nível legível."""
        if language == "portuguese":
            if score >= 80:
                return "Muito Fácil"
            elif score >= 60:
                return "Fácil"
            elif score >= 40:
                return "Moderado"
            elif score >= 20:
                return "Difícil"
            else:
                return "Muito Difícil"
        else:
            if score >= 80:
                return "Very Easy"
            elif score >= 60:
                return "Easy"
            elif score >= 40:
                return "Moderate"
            elif score >= 20:
                return "Difficult"
            else:
                return "Very Difficult"


# ============================================================================
# TESTE STANDALONE - rode: python plugins/readability_analyzer/__init__.py
# ============================================================================
if __name__ == "__main__":
    import json

    analyzer = ReadabilityAnalyzer()

    # Texto de exemplo
    from qualia.core import Document
    doc = Document(
        id="teste",
        content="""O sol nasceu. O dia está bonito. Vamos passear no parque.

As crianças brincam na praça enquanto os pais conversam tranquilamente nos bancos.

A implementação de políticas públicas intersetoriais voltadas à promoção da
sustentabilidade socioambiental demanda a articulação de múltiplos atores
institucionais em processos deliberativos de governança participativa."""
    )

    result = analyzer._analyze_impl(doc, {"language": "portuguese", "detail_level": "full"}, {})

    print("=" * 50)
    print("  ANÁLISE DE LEGIBILIDADE")
    print("=" * 50)
    print(f"\n  Nota: {result['readability_score']}/100")
    print(f"  Nível: {result['readability_level']}")
    print(f"\n  Frases: {result['sentence_count']}")
    print(f"  Palavras: {result['word_count']}")
    print(f"  Parágrafos: {result['paragraph_count']}")
    print(f"  Palavras/frase (média): {result['avg_words_per_sentence']}")
    print(f"  Frase mais longa: {result['longest_sentence']} palavras")
    print(f"  Frase mais curta: {result['shortest_sentence']} palavras")
    print(f"\n  JSON completo:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
