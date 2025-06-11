"""
Exemplos de uso da API do Qualia Core

Requer que a API esteja rodando:
    python run_api.py
"""

import requests
import json
from pathlib import Path
import base64

# Base URL da API
BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def example_list_plugins():
    """Example: List all available plugins"""
    print_section("1. Listar Plugins Disponíveis")
    
    response = requests.get(f"{BASE_URL}/plugins")
    plugins = response.json()
    
    print(f"Total de plugins: {len(plugins)}\n")
    
    for plugin in plugins:
        print(f"📦 {plugin['name']} ({plugin['id']})")
        print(f"   Tipo: {plugin['type']}")
        print(f"   Descrição: {plugin['description']}")
        print()

def example_analyze_text():
    """Example: Analyze text with word_frequency plugin"""
    print_section("2. Analisar Texto")
    
    text = """
    O Qualia Core é um framework incrível para análise qualitativa.
    Ele permite análise de texto de forma simples e eficiente.
    A análise de frequência de palavras é muito útil.
    """
    
    data = {
        "text": text,
        "config": {
            "min_length": 4,
            "remove_stopwords": True
        }
    }
    
    print(f"Texto: {text[:100]}...")
    print(f"Configuração: {data['config']}")
    
    response = requests.post(f"{BASE_URL}/analyze/word_frequency", json=data)
    result = response.json()
    
    if result['status'] == 'success':
        print(f"\n✅ Análise concluída!")
        print(f"Palavras mais frequentes:")
        for word, freq in list(result['result']['word_frequencies'].items())[:5]:
            print(f"  - {word}: {freq}")
        print(f"\nTamanho do vocabulário: {result['result']['vocabulary_size']}")

def example_process_document():
    """Example: Process document with teams_cleaner"""
    print_section("3. Processar Documento")
    
    text = """
    [00:00:00] João Silva: Olá pessoal!
    [00:00:05] Maria Santos: Oi João!
    [00:00:10] João Silva: Vamos começar a reunião?
    """
    
    data = {
        "text": text,
        "config": {
            "remove_timestamps": True,
            "remove_speaker_names": False
        }
    }
    
    print(f"Texto original:\n{text}")
    print(f"\nConfiguracao: {data['config']}")
    
    response = requests.post(f"{BASE_URL}/process/teams_cleaner", json=data)
    result = response.json()
    
    if result['status'] == 'success':
        print(f"\n✅ Processamento concluído!")
        print(f"Texto limpo:\n{result['processed_text']}")

def example_visualize():
    """Example: Create visualization"""
    print_section("4. Criar Visualização")
    
    # Dados de exemplo (normalmente viriam de um analyzer)
    data = {
        "data": {
            "word_frequencies": {
                "python": 15,
                "api": 12,
                "qualia": 10,
                "análise": 8,
                "framework": 6
            },
            "vocabulary_size": 50
        },
        "config": {
            "max_words": 5,
            "background_color": "white",
            "colormap": "viridis"
        },
        "output_format": "png"
    }
    
    print("Criando nuvem de palavras...")
    print(f"Palavras: {list(data['data']['word_frequencies'].keys())}")
    
    response = requests.post(f"{BASE_URL}/visualize/wordcloud_viz", json=data)
    result = response.json()
    
    if result['status'] == 'success':
        print(f"\n✅ Visualização criada!")
        print(f"Formato: {result['format']}")
        print(f"Encoding: {result['encoding']}")
        
        # Salvar imagem
        if result['encoding'] == 'base64':
            image_data = base64.b64decode(result['data'])
            output_path = Path("wordcloud_example.png")
            output_path.write_bytes(image_data)
            print(f"Imagem salva em: {output_path}")

def example_pipeline():
    """Example: Execute a pipeline"""
    print_section("5. Executar Pipeline")
    
    text = """
    A inteligência artificial está transformando o mundo.
    Machine learning e deep learning são tecnologias revolucionárias.
    O futuro da IA é promissor e cheio de possibilidades.
    """
    
    pipeline_data = {
        "text": text,
        "steps": [
            {
                "plugin_id": "word_frequency",
                "config": {
                    "min_length": 3,
                    "remove_stopwords": True
                }
            }
            # Poderia adicionar mais steps aqui
        ]
    }
    
    print(f"Texto: {text[:100]}...")
    print(f"Pipeline com {len(pipeline_data['steps'])} steps")
    
    response = requests.post(f"{BASE_URL}/pipeline", json=pipeline_data)
    result = response.json()
    
    if result['status'] == 'success':
        print(f"\n✅ Pipeline executado!")
        print(f"Steps executados: {result['steps_executed']}")
        
        # Mostrar resultados do primeiro step
        if result['results']:
            first_result = result['results'][0]
            print(f"\nResultado do word_frequency:")
            for word, freq in list(first_result['result']['word_frequencies'].items())[:5]:
                print(f"  - {word}: {freq}")

def example_upload_file():
    """Example: Upload and analyze file"""
    print_section("6. Upload e Análise de Arquivo")
    
    # Criar arquivo temporário
    test_file = Path("test_document.txt")
    test_file.write_text("""
    Este é um documento de teste para a API do Qualia.
    Vamos testar o upload de arquivos e análise.
    O sistema deve processar este texto corretamente.
    """)
    
    print(f"Arquivo: {test_file}")
    
    with open(test_file, 'rb') as f:
        files = {'file': f}
        data = {
            'config': json.dumps({
                'min_length': 4,
                'remove_stopwords': True
            }),
            'context': json.dumps({})
        }
        
        response = requests.post(
            f"{BASE_URL}/analyze/word_frequency/file",
            files=files,
            data=data
        )
    
    result = response.json()
    
    if result['status'] == 'success':
        print(f"\n✅ Arquivo analisado!")
        print(f"Arquivo: {result['filename']}")
        print(f"Palavras encontradas: {result['result']['vocabulary_size']}")
    
    # Limpar
    test_file.unlink()

def example_health_check():
    """Example: Check API health"""
    print_section("7. Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    health = response.json()
    
    print(f"Status: {health['status']}")
    print(f"Plugins carregados: {health['plugins_loaded']}")
    print(f"Tipos de plugins:")
    for plugin_type, count in health['plugin_types'].items():
        print(f"  - {plugin_type}: {count}")

def run_all_examples():
    """Run all examples"""
    print("""
🚀 Exemplos de Uso da API do Qualia Core
==========================================

Certifique-se de que a API está rodando:
    python run_api.py

""")
    
    try:
        # Test connection
        response = requests.get(BASE_URL)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("❌ Erro: API não está rodando!")
        print("Execute: python run_api.py")
        return
    
    # Run examples
    example_list_plugins()
    example_analyze_text()
    example_process_document()
    example_visualize()
    example_pipeline()
    example_upload_file()
    example_health_check()
    
    print_section("Exemplos Concluídos!")
    print("📚 Documentação interativa: http://localhost:8000/docs")
    print("🔧 OpenAPI spec: http://localhost:8000/openapi.json")

if __name__ == "__main__":
    run_all_examples()