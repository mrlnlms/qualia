#!/usr/bin/env python3
"""
Script de validação rápida do Qualia Core
Testa apenas o essencial para garantir que está funcionando
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qualia.core import QualiaCore
from qualia.api import app
from fastapi.testclient import TestClient

# Cores
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def test_core():
    """Testa funcionalidades básicas do core"""
    print(f"\n{BOLD}=== TESTANDO CORE ==={RESET}")
    
    try:
        # 1. Inicialização
        print("1. Inicializando Core...", end='')
        core = QualiaCore()
        print(f" {GREEN}✓{RESET}")
        
        # 2. Descoberta de plugins
        print("2. Descobrindo plugins...", end='')
        plugins = core.discover_plugins()
        print(f" {GREEN}✓{RESET} ({len(plugins)} plugins)")
        
        # 3. Criar documento
        print("3. Criando documento...", end='')
        doc = core.add_document("test", "Este é um teste simples")
        print(f" {GREEN}✓{RESET}")
        
        # 4. Executar análise
        print("4. Executando word_frequency...", end='')
        result = core.execute_plugin("word_frequency", doc)
        print(f" {GREEN}✓{RESET}")
        
        # 5. Verificar resultado
        print("5. Verificando resultado...", end='')
        assert "total_words" in result
        assert result["total_words"] > 0
        print(f" {GREEN}✓{RESET}")
        
        print(f"\n{GREEN}Core funcionando perfeitamente!{RESET}")
        return True
        
    except Exception as e:
        print(f" {RED}✗{RESET}")
        print(f"{RED}Erro: {e}{RESET}")
        return False


def test_api():
    """Testa API básica"""
    print(f"\n{BOLD}=== TESTANDO API ==={RESET}")
    
    try:
        client = TestClient(app)
        
        # 1. Health check
        print("1. Health check...", end='')
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        print(f" {GREEN}✓{RESET}")
        
        # 2. Listar plugins
        print("2. Listando plugins...", end='')
        response = client.get("/plugins")
        assert response.status_code == 200
        assert len(response.json()) == 6
        print(f" {GREEN}✓{RESET}")
        
        # 3. Análise simples
        print("3. Testando análise...", end='')
        response = client.post("/analyze/word_frequency", 
                              json={"text": "teste teste", "config": {}})
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        print(f" {GREEN}✓{RESET}")
        
        print(f"\n{GREEN}API funcionando perfeitamente!{RESET}")
        return True
        
    except Exception as e:
        print(f" {RED}✗{RESET}")
        print(f"{RED}Erro: {e}{RESET}")
        return False


def test_plugins():
    """Testa cada plugin individualmente"""
    print(f"\n{BOLD}=== TESTANDO PLUGINS ==={RESET}")
    
    core = QualiaCore()
    core.discover_plugins()
    
    test_cases = {
        "word_frequency": "Teste de análise de frequência",
        "sentiment_analyzer": "Este produto é muito bom!",
        "teams_cleaner": "[00:00:00] João\nOlá pessoal",
    }
    
    passed = 0
    for plugin_id, test_text in test_cases.items():
        print(f"{plugin_id}...", end='')
        try:
            doc = core.add_document(f"test_{plugin_id}", test_text)
            result = core.execute_plugin(plugin_id, doc)
            assert isinstance(result, dict)
            assert len(result) > 0
            print(f" {GREEN}✓{RESET}")
            passed += 1
        except Exception as e:
            print(f" {RED}✗{RESET} ({str(e)[:50]}...)")
    
    print(f"\n{GREEN if passed == len(test_cases) else YELLOW}{passed}/{len(test_cases)} plugins funcionando{RESET}")
    return passed == len(test_cases)


def main():
    """Executa todos os testes"""
    print(f"{BOLD}🧪 QUALIA CORE - VALIDAÇÃO RÁPIDA{RESET}")
    print("=" * 40)
    
    results = []
    
    # Testa cada componente
    results.append(("Core", test_core()))
    results.append(("API", test_api()))
    results.append(("Plugins", test_plugins()))
    
    # Resumo
    print(f"\n{BOLD}=== RESUMO ==={RESET}")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}PASSOU{RESET}" if result else f"{RED}FALHOU{RESET}"
        print(f"{name}: {status}")
    
    if passed == total:
        print(f"\n{GREEN}{BOLD}✅ TUDO FUNCIONANDO! ({passed}/{total}){RESET}")
        return 0
    else:
        print(f"\n{YELLOW}{BOLD}⚠️  ALGUNS PROBLEMAS ({passed}/{total}){RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())