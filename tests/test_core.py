"""
Testes unitários para o Qualia Core usando pytest
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch

from qualia.core import (
    QualiaCore, Document, PluginMetadata, PluginType,
    BaseAnalyzerPlugin, BaseVisualizerPlugin
)


@pytest.fixture
def temp_dir():
    """Cria diretório temporário para testes"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def core(temp_dir):
    """Cria instância do core para testes"""
    return QualiaCore(
        plugins_dir=Path("plugins"),  # Usa plugins reais
        cache_dir=temp_dir / "cache"
    )


@pytest.fixture
def sample_document():
    """Documento de exemplo para testes"""
    return Document(
        id="test_doc",
        content="Este é um texto de teste. Teste teste palavra.",
        metadata={"source": "test"}
    )


class TestQualiaCore:
    """Testes do core principal"""
    
    def test_core_initialization(self, temp_dir):
        """Testa inicialização básica"""
        core = QualiaCore(cache_dir=temp_dir / "cache")
        assert core is not None
        assert len(core.registry) == 6  # 6 plugins devem ser descobertos
        assert (temp_dir / "cache").exists()
    
    def test_plugin_discovery(self, core):
        """Testa descoberta de plugins"""
        plugins = core.discover_plugins()
        
        # Verifica plugins esperados
        expected_plugins = {
            'word_frequency', 'sentiment_analyzer', 'teams_cleaner',
            'wordcloud_viz', 'frequency_chart', 'sentiment_viz'
        }
        
        assert set(plugins.keys()) == expected_plugins
        
        # Verifica metadados
        for plugin_id, meta in plugins.items():
            assert isinstance(meta, PluginMetadata)
            assert meta.id == plugin_id
            assert meta.type in PluginType
    
    def test_document_management(self, core):
        """Testa gerenciamento de documentos"""
        # Adicionar documento
        doc = core.add_document("doc1", "Conteúdo teste", {"lang": "pt"})
        assert doc.id == "doc1"
        assert doc.content == "Conteúdo teste"
        assert doc.metadata["lang"] == "pt"
        
        # Recuperar documento
        retrieved = core.get_document("doc1")
        assert retrieved == doc
        
        # Documento inexistente
        assert core.get_document("nao_existe") is None
    
    def test_simple_plugin_execution(self, core, sample_document):
        """Testa execução simples de plugin"""
        core.add_document(sample_document.id, sample_document.content)
        
        result = core.execute_plugin("word_frequency", sample_document)
        
        assert 'word_freq' in result
        assert result['word_freq']['teste'] == 3
        assert result['word_freq']['palavra'] == 1
    
    def test_plugin_with_config(self, core, sample_document):
        """Testa plugin com configuração"""
        core.add_document(sample_document.id, sample_document.content)
        
        config = {"min_word_length": 5}
        result = core.execute_plugin("word_frequency", sample_document, config)
        
        # Palavras com menos de 5 caracteres não devem aparecer
        assert 'é' not in result['word_freq']
        assert 'um' not in result['word_freq']
        # Mas 'teste' e 'palavra' devem
        assert 'teste' in result['word_freq']
        assert 'palavra' in result['word_freq']
    
    def test_plugin_dependencies(self, core):
        """Testa resolução de dependências"""
        # sentiment_viz depende de sentiment_analyzer
        doc = core.add_document("dep_test", "Este texto é muito bom!")
        
        # Executar visualizador que depende de analyzer
        with patch('matplotlib.pyplot.savefig'):  # Mock para não criar arquivo
            result = core.execute_plugin("sentiment_viz", doc)
        
        # Deve ter executado sentiment_analyzer automaticamente
        analysis = doc.get_analysis("sentiment_analyzer")
        assert analysis is not None
        assert 'polarity' in analysis
    
    def test_cache_functionality(self, core, sample_document):
        """Testa funcionalidade de cache"""
        core.add_document(sample_document.id, sample_document.content)
        
        # Primeira execução
        result1 = core.execute_plugin("word_frequency", sample_document)
        
        # Segunda execução (deve vir do cache)
        with patch.object(core.plugins['word_frequency'], 'analyze') as mock_analyze:
            result2 = core.execute_plugin("word_frequency", sample_document)
            mock_analyze.assert_not_called()  # Não deve chamar analyze novamente
        
        assert result1 == result2
    
    def test_invalid_plugin(self, core, sample_document):
        """Testa erro ao executar plugin inválido"""
        with pytest.raises(ValueError, match="Plugin 'nao_existe' não encontrado"):
            core.execute_plugin("nao_existe", sample_document)
    
    def test_pipeline_execution(self, core):
        """Testa execução de pipeline"""
        from qualia.core import PipelineConfig, PipelineStep
        
        doc = core.add_document("pipeline_test", "Texto para pipeline. Muito bom!")
        
        pipeline = PipelineConfig(
            name="test_pipeline",
            steps=[
                PipelineStep("word_frequency"),
                PipelineStep("sentiment_analyzer", {"language": "portuguese"})
            ]
        )
        
        results = core.execute_pipeline(pipeline, doc)
        
        assert 'word_frequency' in results
        assert 'sentiment_analyzer' in results
        assert 'word_freq' in results['word_frequency']
        assert 'polarity' in results['sentiment_analyzer']


class TestPluginTypes:
    """Testa diferentes tipos de plugins"""
    
    def test_analyzer_plugin(self, core):
        """Testa plugin analyzer"""
        doc = core.add_document("analyzer_test", "teste de análise")
        result = core.execute_plugin("word_frequency", doc)
        
        assert isinstance(result, dict)
        assert 'word_freq' in result
        assert result['total_words'] == 3
    
    def test_document_plugin(self, core):
        """Testa plugin de documento"""
        # Simula transcrição do Teams
        teams_text = """
        [00:00:00] João Silva
        Olá pessoal, vamos começar?
        
        [00:00:15] Maria Santos
        Sim, podemos começar.
        """
        
        doc = core.add_document("teams_test", teams_text)
        result = core.execute_plugin("teams_cleaner", doc)
        
        assert 'participants' in result
        assert 'clean_text' in result
        assert len(result['participants']) == 2
        assert "João Silva" in result['participants']
    
    @pytest.mark.skipif(not Path("output").exists(), reason="Diretório output não existe")
    def test_visualizer_plugin(self, core, temp_dir):
        """Testa plugin visualizer"""
        # Primeiro executa analyzer
        doc = core.add_document("viz_test", "palavra palavra palavra teste teste")
        analysis = core.execute_plugin("word_frequency", doc)
        
        # Prepara dados para visualizer
        viz_data = {
            'word_freq': analysis['word_freq'],
            'metadata': {'title': 'Teste'}
        }
        
        # Mock para não criar arquivo real
        with patch('matplotlib.pyplot.savefig') as mock_save:
            output_path = temp_dir / "test_viz.png"
            config = {"format": "png", "width": 800}
            
            # Cria plugin e executa
            plugin = core.plugins.get('wordcloud_viz')
            if plugin:
                result = plugin.render(viz_data, config, output_path)
                assert mock_save.called


class TestErrorHandling:
    """Testa tratamento de erros"""
    
    def test_invalid_config(self, core, sample_document):
        """Testa configuração inválida"""
        # Por enquanto, validate_config sempre retorna True
        # Quando implementado, ajustar este teste
        result = core.execute_plugin(
            "word_frequency", 
            sample_document,
            {"invalid_param": "value"}
        )
        assert result is not None  # Deve ignorar parâmetros inválidos
    
    def test_missing_dependencies(self, core):
        """Testa plugin com dependência faltante"""
        # Cria plugin mock que depende de plugin inexistente
        mock_meta = PluginMetadata(
            id="mock_plugin",
            type=PluginType.ANALYZER,
            name="Mock",
            description="Test",
            version="1.0",
            requires=["plugin_inexistente"]
        )
        
        with patch.object(core.registry, 'get', return_value=mock_meta):
            doc = core.add_document("dep_test", "texto")
            # Deve falhar ao tentar resolver dependências
            # Por ora, o sistema ignora dependências não encontradas
            # Ajustar quando implementar validação
    
    def test_circuit_breaker_fallback(self):
        """Testa fallback do circuit breaker"""
        try:
            from ops.monitoring.circuit_breaker import circuit_breaker
            has_cb = True
        except ImportError:
            # Testa se tem fallback
            try:
                from qualia.core import circuit_breaker
                has_cb = True
            except ImportError:
                has_cb = False
        
        assert has_cb  # Deve ter circuit breaker ou fallback


class TestPerformance:
    """Testes de performance"""
    
    def test_large_document(self, core):
        """Testa com documento grande"""
        # Cria documento com 1000 palavras
        large_text = " ".join(["palavra"] * 1000)
        doc = core.add_document("large_doc", large_text)
        
        import time
        start = time.time()
        result = core.execute_plugin("word_frequency", doc)
        duration = time.time() - start
        
        assert duration < 1.0  # Deve processar em menos de 1 segundo
        assert result['total_words'] == 1000
    
    def test_cache_performance(self, core):
        """Testa performance do cache"""
        doc = core.add_document("cache_test", "teste de cache")
        
        # Primeira execução
        import time
        start1 = time.time()
        result1 = core.execute_plugin("word_frequency", doc)
        time1 = time.time() - start1
        
        # Segunda execução (cache)
        start2 = time.time()
        result2 = core.execute_plugin("word_frequency", doc)
        time2 = time.time() - start2
        
        # Cache deve ser muito mais rápido
        assert time2 < time1 * 0.1  # Pelo menos 10x mais rápido
        assert result1 == result2


# Configurações do pytest
def pytest_configure(config):
    """Configuração do pytest"""
    config.addinivalue_line(
        "markers", "slow: marca testes lentos"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )