#!/usr/bin/env python3
"""
Teste direto do execute_pipeline no core para entender a assinatura correta
"""

from qualia.core import QualiaCore

def test_pipeline_directly():
    print("🧪 TESTE DIRETO DO PIPELINE NO CORE\n")
    
    # Inicializar core
    core = QualiaCore()
    core.discover_plugins()
    
    # Criar documento
    doc = core.add_document("test_doc", "Este é um teste do pipeline")
    print(f"1. Documento criado: {doc.id}")
    print(f"   Tipo do doc: {type(doc)}")
    print(f"   doc.id type: {type(doc.id)}\n")
    
    # Criar pipeline config
    pipeline_config = {
        "name": "Test Pipeline",
        "steps": [
            {
                "plugin": "word_frequency",
                "config": {"min_length": 3}
            }
        ]
    }
    
    print("2. Pipeline config:")
    print(f"   {pipeline_config}\n")
    
    # Tentar diferentes assinaturas
    print("3. Testando diferentes assinaturas:\n")
    
    # Teste A: (doc_id, pipeline_config)
    try:
        print("   A) execute_pipeline(doc.id, pipeline_config)")
        result = core.execute_pipeline(doc.id, pipeline_config)
        print(f"      ✅ SUCESSO! Resultado: {list(result.keys())}")
    except Exception as e:
        print(f"      ❌ ERRO: {e}")
    
    # Teste B: (pipeline_config, doc)
    try:
        print("\n   B) execute_pipeline(pipeline_config, doc)")
        result = core.execute_pipeline(pipeline_config, doc)
        print(f"      ✅ SUCESSO! Resultado: {list(result.keys())}")
    except Exception as e:
        print(f"      ❌ ERRO: {e}")
    
    # Teste C: (pipeline_config, doc.id)
    try:
        print("\n   C) execute_pipeline(pipeline_config, doc.id)")
        result = core.execute_pipeline(pipeline_config, doc.id)
        print(f"      ✅ SUCESSO! Resultado: {list(result.keys())}")
    except Exception as e:
        print(f"      ❌ ERRO: {e}")
    
    # Teste D: (doc, pipeline_config)
    try:
        print("\n   D) execute_pipeline(doc, pipeline_config)")
        result = core.execute_pipeline(doc, pipeline_config)
        print(f"      ✅ SUCESSO! Resultado: {list(result.keys())}")
    except Exception as e:
        print(f"      ❌ ERRO: {e}")

if __name__ == "__main__":
    test_pipeline_directly()