# tests/test_word_frequency_spacy.py
"""Testes para cache de modelo spaCy no word_frequency."""

import pytest
from unittest.mock import patch, MagicMock
from qualia.core import Document


class TestSpacyCaching:
    """spaCy model deve ser carregado uma vez no __init__, não por execução."""

    def test_spacy_model_cached_across_calls(self):
        """Duas chamadas com tokenization=spacy devem usar o mesmo modelo."""
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__iter__ = lambda self: iter([
            MagicMock(text="palavra", is_punct=False),
            MagicMock(text="teste", is_punct=False),
        ])
        mock_nlp.return_value = mock_doc

        from plugins.analyzers.word_frequency import WordFrequencyAnalyzer
        analyzer = WordFrequencyAnalyzer.__new__(WordFrequencyAnalyzer)
        analyzer._stopwords_cache = {}
        analyzer._nltk_available = False
        analyzer._spacy_nlp = mock_nlp  # simular cache

        tokens1 = analyzer._tokenize("palavra teste", "spacy")
        tokens2 = analyzer._tokenize("outra frase", "spacy")

        # modelo cached deve ser usado diretamente, sem spacy.load
        assert mock_nlp.call_count == 2  # chamado 2x (uma por _tokenize)
        assert isinstance(tokens1, list)
        assert isinstance(tokens2, list)

    def test_spacy_fallback_uses_logger_not_print(self):
        """Quando spaCy não está disponível, deve usar logger, não print."""
        with patch("builtins.print") as mock_print:
            from plugins.analyzers.word_frequency import WordFrequencyAnalyzer
            analyzer = WordFrequencyAnalyzer.__new__(WordFrequencyAnalyzer)
            analyzer._stopwords_cache = {}
            analyzer._nltk_available = False
            analyzer._spacy_nlp = None

            with patch.dict("sys.modules", {"spacy": None}):
                tokens = analyzer._tokenize("texto", "spacy")

            # Não deve usar print
            mock_print.assert_not_called()
            # Deve fazer fallback pra simple
            assert isinstance(tokens, list)
