#!/usr/bin/env python3
"""
Orquestrador simplificado de testes
Versão sem dependência do coverage
"""

import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def run_command(cmd, description, shell=True):
    """Executa comando e reporta resultado"""
    print(f"🔄 {description}...", end='', flush=True)
    
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"\r✅ {description}")
        return True
    else:
        print(f"\r❌ {description}")
        if result.stderr:
            print(f"   Erro: {result.stderr.strip()[:100]}")
        return False


def run_quick_tests():
    """Testes rápidos de validação"""
    print(f"\n{Colors.BOLD}⚡ TESTES RÁPIDOS{Colors.RESET}")
    print("-" * 40)
    
    tests = [
        ("Importar Core", 
         "python -c \"from qualia.core import QualiaCore; print('OK')\""),
        
        ("Verificar Plugins", 
         "python -c \"from qualia.core import QualiaCore; c=QualiaCore(); print(f'{len(c.discover_plugins())} plugins')\""),
        
        ("Importar API", 
         "python -c \"import qualia.api; print('OK')\""),
    ]
    
    passed = 0
    for desc, cmd in tests:
        if run_command(cmd, desc):
            passed += 1
    
    print(f"\nResultado: {passed}/{len(tests)} testes passaram")
    return passed == len(tests)


def run_pytest_tests(test_path="tests/", markers=None):
    """Roda testes com pytest"""
    print(f"\n{Colors.BOLD}🧪 PYTEST{Colors.RESET}")
    print("-" * 40)
    
    # Verifica se pytest está instalado
    pytest_check = subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                                  capture_output=True)
    
    if pytest_check.returncode != 0:
        print(f"{Colors.YELLOW}⚠️  pytest não instalado!{Colors.RESET}")
        print("Instale com: pip install pytest")
        return False
    
    # Monta comando
    cmd = [sys.executable, "-m", "pytest", test_path, "-v"]
    
    if markers:
        cmd.extend(["-m", markers])
    
    # Executa
    result = subprocess.run(cmd)
    return result.returncode == 0


def run_integration_tests():
    """Roda suite de integração se existir"""
    print(f"\n{Colors.BOLD}🔗 TESTES DE INTEGRAÇÃO{Colors.RESET}")
    print("-" * 40)
    
    if Path("scripts/test_suite.py").exists():
        cmd = [sys.executable, "scripts/test_suite.py"]
    elif Path("test_suite.py").exists():
        cmd = [sys.executable, "test_suite.py"]
    else:
        print(f"{Colors.YELLOW}Suite de integração não encontrada{Colors.RESET}")
        return True  # Não falha se não existir
    
    result = subprocess.run(cmd)
    return result.returncode == 0


def check_dependencies():
    """Verifica dependências necessárias"""
    print(f"\n{Colors.BOLD}📦 VERIFICANDO DEPENDÊNCIAS{Colors.RESET}")
    print("-" * 40)
    
    deps = {
        "pytest": "pip install pytest",
        "httpx": "pip install httpx",
        "fastapi": "pip install fastapi",
    }
    
    missing = []
    for package, install_cmd in deps.items():
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - instale com: {install_cmd}")
            missing.append(package)
    
    if missing:
        print(f"\n{Colors.YELLOW}Instale as dependências faltantes para todos os testes{Colors.RESET}")
    
    return len(missing) == 0


def main():
    parser = argparse.ArgumentParser(description="Roda testes do Qualia Core")
    parser.add_argument('--quick', action='store_true', help='Apenas testes rápidos')
    parser.add_argument('--unit', action='store_true', help='Testes unitários')
    parser.add_argument('--integration', action='store_true', help='Testes de integração')
    parser.add_argument('--all', action='store_true', help='Todos os testes')
    parser.add_argument('--check', action='store_true', help='Verifica dependências')
    
    args = parser.parse_args()
    
    # Header
    print(f"{Colors.BOLD}🧪 QUALIA CORE - TESTES{Colors.RESET}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Se nenhuma opção, roda quick
    if not any([args.quick, args.unit, args.integration, args.all, args.check]):
        args.quick = True
    
    results = []
    
    # Verifica dependências se solicitado
    if args.check or args.all:
        results.append(("Dependências", check_dependencies()))
    
    # Roda testes solicitados
    if args.quick or args.all:
        results.append(("Testes Rápidos", run_quick_tests()))
    
    if args.unit or args.all:
        if Path("tests").exists():
            results.append(("Testes Unitários", run_pytest_tests("tests/")))
        else:
            print(f"\n{Colors.YELLOW}Pasta 'tests/' não encontrada{Colors.RESET}")
    
    if args.integration or args.all:
        results.append(("Testes Integração", run_integration_tests()))
    
    # Resumo
    print(f"\n{Colors.BOLD}📊 RESUMO{Colors.RESET}")
    print("-" * 40)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}PASSOU{Colors.RESET}" if result else f"{Colors.RED}FALHOU{Colors.RESET}"
        print(f"{name}: {status}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    color = Colors.GREEN if success_rate == 100 else Colors.YELLOW if success_rate >= 50 else Colors.RED
    
    print(f"\n{color}Taxa de sucesso: {success_rate:.0f}% ({passed}/{total}){Colors.RESET}")
    
    return 0 if success_rate == 100 else 1


if __name__ == "__main__":
    sys.exit(main())