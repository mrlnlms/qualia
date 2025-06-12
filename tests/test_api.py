"""
Testes da API REST do Qualia Core
"""

import pytest
import httpx
from fastapi.testclient import TestClient
import json
import tempfile
from pathlib import Path

from qualia.api import app


@pytest.fixture
def client():
    """Cliente de teste para a API"""
    return TestClient(app)


@pytest.fixture
def sample_text():
    """Texto de exemplo para testes"""
    return "Este é um texto de teste. Teste teste palavra."


class TestHealthEndpoints:
    """Testa endpoints de saúde"""
    
    def test_health_check(self, client):
        """Testa endpoint /health"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["plugins_loaded"] == 6
        assert "uptime" in data
    
    def test_root_redirect(self, client):
        """Testa redirect da raiz para docs"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"


class TestPluginEndpoints:
    """Testa endpoints de plugins"""
    
    def test_list_plugins(self, client):
        """Testa GET /plugins"""
        response = client.get("/plugins")
        assert response.status_code == 200
        
        plugins = response.json()
        assert len(plugins) == 6
        
        # Verifica estrutura
        for plugin in plugins:
            assert "id" in plugin
            assert "type" in plugin
            assert "name" in plugin
            assert "description" in plugin
    
    def test_get_plugin_info(self, client):
        """Testa GET /plugins/{plugin_id}"""
        response = client.get("/plugins/word_frequency")
        assert response.status_code == 200
        
        plugin = response.json()
        assert plugin["id"] == "word_frequency"
        assert plugin["type"] == "analyzer"
        assert "parameters" in plugin
    
    def test_get_invalid_plugin(self, client):
        """Testa plugin inexistente"""
        response = client.get("/plugins/nao_existe")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestAnalysisEndpoints:
    """Testa endpoints de análise"""
    
    def test_analyze_word_frequency(self, client, sample_text):
        """Testa análise word_frequency"""
        response = client.post(
            "/analyze/word_frequency",
            json={"text": sample_text, "config": {}}
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "word_freq" in result
        assert result["word_freq"]["teste"] == 3
        assert result["total_words"] == 9
    
    def test_analyze_with_config(self, client, sample_text):
        """Testa análise com configuração"""
        response = client.post(
            "/analyze/word_frequency",
            json={
                "text": sample_text,
                "config": {"min_word_length": 5}
            }
        )
        assert response.status_code == 200
        
        result = response.json()
        # Palavras curtas não devem aparecer
        assert "é" not in result["word_freq"]
        assert "um" not in result["word_freq"]
        # Mas palavras longas sim
        assert "teste" in result["word_freq"]
        assert "palavra" in result["word_freq"]
    
    def test_analyze_sentiment(self, client):
        """Testa análise de sentimento"""
        response = client.post(
            "/analyze/sentiment_analyzer",
            json={
                "text": "Este produto é muito bom! Adorei!",
                "config": {}
            }
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "polarity" in result
        assert result["polarity"] > 0  # Sentimento positivo
    
    def test_analyze_invalid_plugin(self, client, sample_text):
        """Testa análise com plugin inexistente"""
        response = client.post(
            "/analyze/plugin_invalido",
            json={"text": sample_text, "config": {}}
        )
        assert response.status_code == 404
    
    def test_analyze_empty_text(self, client):
        """Testa análise com texto vazio"""
        response = client.post(
            "/analyze/word_frequency",
            json={"text": "", "config": {}}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["total_words"] == 0


class TestPipelineEndpoints:
    """Testa endpoints de pipeline"""
    
    def test_simple_pipeline(self, client, sample_text):
        """Testa pipeline simples"""
        response = client.post(
            "/pipeline",
            json={
                "text": sample_text,
                "steps": [
                    {"plugin_id": "word_frequency"},
                    {"plugin_id": "sentiment_analyzer"}
                ]
            }
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "results" in result
        assert "word_frequency" in result["results"]
        assert "sentiment_analyzer" in result["results"]
        assert "metadata" in result
    
    def test_pipeline_with_config(self, client):
        """Testa pipeline com configurações"""
        response = client.post(
            "/pipeline",
            json={
                "text": "Texto para análise complexa",
                "steps": [
                    {
                        "plugin_id": "word_frequency",
                        "config": {"min_word_length": 4}
                    },
                    {
                        "plugin_id": "sentiment_analyzer",
                        "config": {"language": "portuguese"}
                    }
                ]
            }
        )
        assert response.status_code == 200
        
        result = response.json()
        # Verifica que configs foram aplicadas
        wf_result = result["results"]["word_frequency"]
        assert all(len(word) >= 4 for word in wf_result["word_freq"].keys())
    
    def test_empty_pipeline(self, client, sample_text):
        """Testa pipeline vazio"""
        response = client.post(
            "/pipeline",
            json={"text": sample_text, "steps": []}
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["results"] == {}


class TestUploadEndpoints:
    """Testa endpoints de upload"""
    
    def test_upload_text_file(self, client):
        """Testa upload de arquivo texto"""
        # Cria arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Conteúdo do arquivo de teste")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/upload/word_frequency",
                    files={"file": ("test.txt", f, "text/plain")}
                )
            
            assert response.status_code == 200
            result = response.json()
            assert "word_freq" in result
            assert result["word_freq"]["teste"] == 1
        
        finally:
            Path(temp_path).unlink()
    
    def test_upload_with_config(self, client):
        """Testa upload com configuração"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("palavra palavra palavra curta")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/upload/word_frequency",
                    files={"file": ("test.txt", f, "text/plain")},
                    data={"config": json.dumps({"min_word_length": 6})}
                )
            
            assert response.status_code == 200
            result = response.json()
            assert "palavra" in result["word_freq"]
            assert "curta" not in result["word_freq"]  # < 6 caracteres
        
        finally:
            Path(temp_path).unlink()
    
    def test_upload_invalid_file_type(self, client):
        """Testa upload de tipo inválido"""
        # Por enquanto a API aceita qualquer arquivo
        # Este teste pode ser ajustado quando implementar validação
        pass


class TestDocumentEndpoints:
    """Testa endpoints de documentos"""
    
    def test_process_teams_transcript(self, client):
        """Testa processamento de transcrição Teams"""
        teams_text = """
        [00:00:00] João Silva
        Olá pessoal, vamos começar a reunião?
        
        [00:00:15] Maria Santos
        Sim, pode começar. Estou pronta.
        
        [00:01:00] João Silva
        Ótimo! Vamos discutir o projeto.
        """
        
        response = client.post(
            "/analyze/teams_cleaner",
            json={"text": teams_text, "config": {}}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "participants" in result
        assert len(result["participants"]) == 2
        assert "João Silva" in result["participants"]
        assert "clean_text" in result


class TestVisualizationEndpoints:
    """Testa endpoints de visualização"""
    
    @pytest.mark.skip(reason="Visualizações geram arquivos reais")
    def test_visualization_pipeline(self, client):
        """Testa pipeline com visualização"""
        # Este teste é pulado por padrão pois gera arquivos
        # Pode ser habilitado em ambientes de teste específicos
        response = client.post(
            "/pipeline",
            json={
                "text": "teste teste palavra",
                "steps": [
                    {"plugin_id": "word_frequency"},
                    {"plugin_id": "wordcloud_viz"}
                ]
            }
        )
        assert response.status_code == 200


class TestErrorHandling:
    """Testa tratamento de erros"""
    
    def test_invalid_json(self, client):
        """Testa JSON inválido"""
        response = client.post(
            "/analyze/word_frequency",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_field(self, client):
        """Testa campo obrigatório faltando"""
        response = client.post(
            "/analyze/word_frequency",
            json={"config": {}}  # Falta 'text'
        )
        assert response.status_code == 422
    
    def test_server_error_handling(self, client):
        """Testa tratamento de erro do servidor"""
        # Simula erro forçando plugin inválido em pipeline
        response = client.post(
            "/pipeline",
            json={
                "text": "teste",
                "steps": [{"plugin_id": "plugin_que_nao_existe"}]
            }
        )
        # Deve retornar resultado parcial, não 500
        assert response.status_code == 200
        assert "metadata" in response.json()


# Testes assíncronos (se necessário)
@pytest.mark.asyncio
async def test_async_health_check():
    """Testa endpoint assíncrono"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200