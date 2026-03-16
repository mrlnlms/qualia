"""
Testes de lógica real dos plugins do Qualia

Valida que os plugins produzem resultados corretos,
não apenas que existem e têm metadata.
"""

import pytest
from qualia.core import Document


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def word_freq():
    from plugins.word_frequency import WordFrequencyAnalyzer
    return WordFrequencyAnalyzer()


@pytest.fixture
def readability():
    from plugins.readability_analyzer import ReadabilityAnalyzer
    return ReadabilityAnalyzer()


@pytest.fixture
def teams():
    from plugins.teams_cleaner import TeamsTranscriptCleaner
    return TeamsTranscriptCleaner()


def make_doc(text, doc_id="test"):
    return Document(id=doc_id, content=text)


def default_config(plugin):
    """Extrai config default do plugin metadata"""
    meta = plugin.meta()
    return {k: v["default"] for k, v in meta.parameters.items()}


# =============================================================================
# WORD FREQUENCY
# =============================================================================

class TestWordFrequency:

    def test_basic_count(self, word_freq):
        doc = make_doc("gato gato cachorro gato")
        config = default_config(word_freq)
        config["min_word_length"] = 1
        config["remove_stopwords"] = False
        result = word_freq._analyze_impl(doc, config, {})
        assert result["word_frequencies"]["gato"] == 3
        assert result["word_frequencies"]["cachorro"] == 1

    def test_case_insensitive(self, word_freq):
        doc = make_doc("Gato gato GATO")
        config = default_config(word_freq)
        config["min_word_length"] = 1
        config["remove_stopwords"] = False
        config["case_sensitive"] = False
        result = word_freq._analyze_impl(doc, config, {})
        assert result["word_frequencies"]["gato"] == 3

    def test_case_sensitive(self, word_freq):
        doc = make_doc("Gato gato GATO")
        config = default_config(word_freq)
        config["min_word_length"] = 1
        config["remove_stopwords"] = False
        config["case_sensitive"] = True
        result = word_freq._analyze_impl(doc, config, {})
        assert result["vocabulary_size"] == 3

    def test_min_word_length(self, word_freq):
        doc = make_doc("eu vi um gato grande no parque")
        config = default_config(word_freq)
        config["min_word_length"] = 4
        config["remove_stopwords"] = False
        result = word_freq._analyze_impl(doc, config, {})
        freqs = result["word_frequencies"]
        # "eu", "vi", "um", "no" filtrados (< 4 chars)
        assert "eu" not in freqs
        assert "vi" not in freqs
        assert "gato" in freqs
        assert "grande" in freqs

    def test_max_words(self, word_freq):
        doc = make_doc("alfa beta gama delta epsilon zeta")
        config = default_config(word_freq)
        config["max_words"] = 3
        config["min_word_length"] = 1
        config["remove_stopwords"] = False
        result = word_freq._analyze_impl(doc, config, {})
        assert len(result["word_frequencies"]) <= 3

    def test_hapax_legomena(self, word_freq):
        doc = make_doc("gato gato cachorro pato")
        config = default_config(word_freq)
        config["min_word_length"] = 1
        config["remove_stopwords"] = False
        result = word_freq._analyze_impl(doc, config, {})
        # cachorro e pato aparecem 1x
        assert "cachorro" in result["hapax_legomena"]
        assert "pato" in result["hapax_legomena"]
        assert "gato" not in result["hapax_legomena"]

    def test_empty_text(self, word_freq):
        doc = make_doc("")
        config = default_config(word_freq)
        result = word_freq._analyze_impl(doc, config, {})
        assert result["vocabulary_size"] == 0
        assert result["total_words"] == 0

    def test_stopwords_portuguese(self, word_freq):
        doc = make_doc("o gato estava na casa do vizinho")
        config = default_config(word_freq)
        config["remove_stopwords"] = True
        config["language"] = "portuguese"
        config["min_word_length"] = 1
        result = word_freq._analyze_impl(doc, config, {})
        freqs = result["word_frequencies"]
        # "o", "na", "do" devem ser filtrados
        assert "gato" in freqs or "vizinho" in freqs
        # stopwords comuns não devem estar
        for sw in ["o", "na", "do"]:
            assert sw not in freqs

    def test_total_words(self, word_freq):
        doc = make_doc("teste teste teste outro outro")
        config = default_config(word_freq)
        config["min_word_length"] = 1
        config["remove_stopwords"] = False
        result = word_freq._analyze_impl(doc, config, {})
        assert result["total_words"] == 5

    def test_result_fields(self, word_freq):
        doc = make_doc("texto de exemplo para validar campos")
        config = default_config(word_freq)
        result = word_freq._analyze_impl(doc, config, {})
        assert "word_frequencies" in result
        assert "vocabulary_size" in result
        assert "top_words" in result
        assert "hapax_legomena" in result
        assert "total_words" in result


# =============================================================================
# READABILITY ANALYZER
# =============================================================================

class TestReadability:

    def test_simple_text_high_score(self, readability):
        doc = make_doc("O sol nasceu. O dia é bom. Vamos sair.")
        config = default_config(readability)
        result = readability._analyze_impl(doc, config, {})
        # Frases curtas e palavras curtas = score alto
        assert result["readability_score"] >= 50

    def test_complex_text_lower_score(self, readability):
        doc = make_doc(
            "A implementação de políticas públicas intersetoriais voltadas à promoção "
            "da sustentabilidade socioambiental demanda a articulação de múltiplos "
            "atores institucionais em processos deliberativos de governança participativa "
            "que contemplem a interdependência dos diferentes subsistemas envolvidos."
        )
        config = default_config(readability)
        result = readability._analyze_impl(doc, config, {})
        simple_doc = make_doc("O sol nasceu. O dia é bom. Vamos sair.")
        simple_result = readability._analyze_impl(simple_doc, config, {})
        assert result["readability_score"] < simple_result["readability_score"]

    def test_sentence_count(self, readability):
        doc = make_doc("Primeira frase. Segunda frase. Terceira frase!")
        config = default_config(readability)
        result = readability._analyze_impl(doc, config, {})
        assert result["sentence_count"] == 3

    def test_paragraph_count(self, readability):
        doc = make_doc("Parágrafo um.\n\nParágrafo dois.\n\nParágrafo três.")
        config = default_config(readability)
        result = readability._analyze_impl(doc, config, {})
        assert result["paragraph_count"] == 3

    def test_classification_portuguese(self, readability):
        doc = make_doc("Oi. Tudo bem. Sim.")
        config = default_config(readability)
        config["language"] = "portuguese"
        result = readability._analyze_impl(doc, config, {})
        assert result["readability_level"] in [
            "Muito Fácil", "Fácil", "Moderado", "Difícil", "Muito Difícil"
        ]

    def test_classification_english(self, readability):
        doc = make_doc("Hi. Good. Yes.")
        config = default_config(readability)
        config["language"] = "english"
        result = readability._analyze_impl(doc, config, {})
        assert result["readability_level"] in [
            "Very Easy", "Easy", "Moderate", "Difficult", "Very Difficult"
        ]

    def test_detail_level_full(self, readability):
        doc = make_doc("Frase curta. Uma frase um pouco mais longa aqui.")
        config = default_config(readability)
        config["detail_level"] = "full"
        result = readability._analyze_impl(doc, config, {})
        assert "longest_sentence" in result
        assert "shortest_sentence" in result
        assert result["longest_sentence"] >= result["shortest_sentence"]

    def test_detail_level_basic(self, readability):
        doc = make_doc("Frase curta. Uma frase longa.")
        config = default_config(readability)
        config["detail_level"] = "basic"
        result = readability._analyze_impl(doc, config, {})
        assert "longest_sentence" not in result


# =============================================================================
# TEAMS CLEANER
# =============================================================================

class TestTeamsCleaner:

    SAMPLE_TRANSCRIPT = """[00:00:00] Recording Started
[00:00:05] João Silva: Bom dia pessoal, vamos começar a reunião?
[00:00:10] Maria Santos: Bom dia! Sim, podemos começar.
[00:00:15] João Silva: Ótimo.
[00:00:16] João Silva: Primeiro item da pauta é o orçamento.
[00:00:20] Pedro Oliveira (Guest): Oi, desculpem o atraso pessoal
[00:00:25] Maria Santos: Sem problemas Pedro!
[00:00:30] Sistema: Pedro Oliveira is now presenting"""

    def test_extract_speakers(self, teams):
        doc = make_doc(self.SAMPLE_TRANSCRIPT)
        config = default_config(teams)
        result = teams._process_impl(doc, config, {})
        speaker_names = [s["name"] for s in result["speakers"]]
        assert "João Silva" in speaker_names
        assert "Maria Santos" in speaker_names

    def test_remove_system_messages(self, teams):
        doc = make_doc(self.SAMPLE_TRANSCRIPT)
        config = default_config(teams)
        config["remove_system_messages"] = True
        result = teams._process_impl(doc, config, {})
        cleaned = result["cleaned_document"]
        assert "Recording Started" not in cleaned
        # "Sistema" é filtrado pelo speaker filter (contém "system"-like patterns)
        # mas "Pedro Oliveira is now presenting" é uma fala de um speaker real
        # O plugin filtra por speaker name, não por conteúdo da mensagem para "presenting"

    def test_keep_system_messages(self, teams):
        doc = make_doc(self.SAMPLE_TRANSCRIPT)
        config = default_config(teams)
        config["remove_system_messages"] = False
        result = teams._process_impl(doc, config, {})
        assert result["utterance_count"] > 0

    def test_merge_consecutive(self, teams):
        doc = make_doc(self.SAMPLE_TRANSCRIPT)
        config = default_config(teams)
        config["merge_consecutive"] = True
        config["remove_system_messages"] = True
        result = teams._process_impl(doc, config, {})
        # João fala 2x consecutivas (linhas 15+16), devem mergear
        cleaned = result["cleaned_document"]
        # Após merge, "Ótimo" e "Primeiro item" devem estar na mesma fala
        joao_count = cleaned.count("João Silva:")
        assert joao_count < 3  # Sem merge seriam 3

    def test_no_merge(self, teams):
        doc = make_doc(self.SAMPLE_TRANSCRIPT)
        config = default_config(teams)
        config["merge_consecutive"] = False
        config["remove_system_messages"] = True
        result_no_merge = teams._process_impl(doc, config, {})

        config["merge_consecutive"] = True
        result_merge = teams._process_impl(doc, config, {})
        assert result_no_merge["utterance_count"] >= result_merge["utterance_count"]

    def test_remove_timestamps(self, teams):
        doc = make_doc(self.SAMPLE_TRANSCRIPT)
        config = default_config(teams)
        config["remove_timestamps"] = True
        result = teams._process_impl(doc, config, {})
        assert "[00:" not in result["cleaned_document"]

    def test_quality_report(self, teams):
        doc = make_doc(self.SAMPLE_TRANSCRIPT)
        config = default_config(teams)
        result = teams._process_impl(doc, config, {})
        report = result["quality_report"]
        assert "quality_score" in report
        assert 0 <= report["quality_score"] <= 100
        assert "issues" in report
        assert "warnings" in report

    def test_normalize_speaker_guest(self, teams):
        doc = make_doc("[00:00:01] Pedro Oliveira (Guest): Olá pessoal, tudo bem?")
        config = default_config(teams)
        config["normalize_speakers"] = True
        result = teams._process_impl(doc, config, {})
        speaker_names = [s["name"] for s in result["speakers"]]
        # "(Guest)" deve ser removido
        assert any("Pedro" in name and "Guest" not in name for name in speaker_names)

    def test_create_variants(self, teams):
        doc = make_doc(self.SAMPLE_TRANSCRIPT)
        config = default_config(teams)
        config["create_variants"] = True
        result = teams._process_impl(doc, config, {})
        variants = result["document_variants"]
        assert len(variants) > 0
        # Deve ter variante por speaker
        assert any(k.startswith("speaker_") for k in variants)

    def test_no_variants(self, teams):
        doc = make_doc(self.SAMPLE_TRANSCRIPT)
        config = default_config(teams)
        config["create_variants"] = False
        result = teams._process_impl(doc, config, {})
        assert result["document_variants"] == {}

    def test_metadata_timestamps(self, teams):
        doc = make_doc(self.SAMPLE_TRANSCRIPT)
        config = default_config(teams)
        result = teams._process_impl(doc, config, {})
        meta = result["metadata"]
        assert "total_speakers" in meta
        assert meta["total_speakers"] > 0
        assert meta["total_utterances"] > 0

    def test_plain_text_no_crash(self, teams):
        """Texto sem formato Teams não deve crashar"""
        doc = make_doc("Isso é um texto normal sem formato de transcrição.")
        config = default_config(teams)
        result = teams._process_impl(doc, config, {})
        # Pode não encontrar utterances, mas não deve crashar
        assert "quality_report" in result

    def test_format_without_timestamp(self, teams):
        """Formato Speaker: Text (sem timestamp)"""
        doc = make_doc("Ana: Olá pessoal, tudo bem?\nBruno: Tudo ótimo!")
        config = default_config(teams)
        result = teams._process_impl(doc, config, {})
        assert result["utterance_count"] == 2


# =============================================================================
# SENTIMENT ANALYZER (com mock se textblob não estiver disponível)
# =============================================================================

class TestSentimentAnalyzer:

    @pytest.fixture
    def sentiment(self):
        from plugins.sentiment_analyzer import SentimentAnalyzer
        return SentimentAnalyzer()

    def test_plugin_loads(self, sentiment):
        meta = sentiment.meta()
        assert meta.id == "sentiment_analyzer"

    def test_result_fields_when_available(self, sentiment):
        if not sentiment._textblob_available:
            pytest.skip("TextBlob não instalado")
        doc = make_doc("Este produto é maravilhoso! Adorei muito.")
        config = default_config(sentiment)
        result = sentiment._analyze_impl(doc, config, {})
        assert "polarity" in result
        assert "subjectivity" in result
        assert "sentiment_label" in result
        assert "language" in result

    def test_positive_text(self, sentiment):
        if not sentiment._textblob_available:
            pytest.skip("TextBlob não instalado")
        doc = make_doc("This is wonderful! I love it so much! Amazing and fantastic!")
        config = default_config(sentiment)
        result = sentiment._analyze_impl(doc, config, {})
        assert result["polarity"] > 0
        assert result["sentiment_label"] == "positivo"

    def test_negative_text(self, sentiment):
        if not sentiment._textblob_available:
            pytest.skip("TextBlob não instalado")
        doc = make_doc("This is terrible. I hate it. Awful and horrible experience.")
        config = default_config(sentiment)
        result = sentiment._analyze_impl(doc, config, {})
        assert result["polarity"] < 0
        assert result["sentiment_label"] == "negativo"

    def test_validate_config_no_textblob(self, sentiment):
        if sentiment._textblob_available:
            pytest.skip("TextBlob está instalado, skip teste de fallback")
        valid, msg = sentiment.validate_config({})
        assert valid is False
        assert "TextBlob" in msg

    def test_sentence_analysis(self, sentiment):
        if not sentiment._textblob_available:
            pytest.skip("TextBlob não instalado")
        doc = make_doc("I love this. I hate that. This is ok.")
        config = default_config(sentiment)
        config["analyze_sentences"] = True
        result = sentiment._analyze_impl(doc, config, {})
        assert "sentence_sentiments" in result
        assert len(result["sentence_sentiments"]) > 0
