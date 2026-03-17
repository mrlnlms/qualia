#!/usr/bin/env python3
"""
Descobrir o erro REAL do pipeline
"""

import requests
import json

def debug_pipeline_error():
    print("🔍 DEBUG DETALHADO DO ERRO\n")
    
    # Fazer a mesma requisição do teste
    response = requests.post(
        "http://localhost:8000/pipeline",
        json={
            "text": "Teste do pipeline",
            "steps": [{"plugin_id": "word_frequency"}]
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Se for erro 400, mostrar detalhes
    if response.status_code == 400:
        try:
            error_detail = response.json()
            print(f"\nDetalhes do erro: {json.dumps(error_detail, indent=2)}")
        except:
            print(f"\nTexto do erro: {response.text}")
    
    # Verificar se o problema é no core
    print("\n\nTestando pipeline diretamente no core:")
    
    from qualia.core import QualiaCore, PipelineConfig, PipelineStep
    
    core = QualiaCore()
    core.discover_plugins()
    
    # Criar documento
    doc = core.add_document("test", "Teste direto")
    
    # Criar pipeline
    steps = [PipelineStep(plugin_id="word_frequency", config={})]
    pipeline = PipelineConfig(name="Test", steps=steps)
    
    print(f"Pipeline criado: {pipeline}")
    print(f"Steps: {pipeline.steps}")
    
    try:
        result = core.execute_pipeline(pipeline, doc)
        print(f"✅ Sucesso no core! Resultado: {list(result.keys())}")
    except Exception as e:
        print(f"❌ Erro no core: {type(e).__name__}: {e}")
        
        # Debug mais profundo
        import traceback
        print("\nTraceback completo:")
        traceback.print_exc()

if __name__ == "__main__":
    debug_pipeline_error()