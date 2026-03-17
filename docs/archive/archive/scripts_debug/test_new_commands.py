#!/usr/bin/env python3
"""
test_new_commands.py - Testa os novos comandos da CLI

Execução:
    python test_new_commands.py
"""

import subprocess
import os
import json
import time
import shutil
from pathlib import Path
from datetime import datetime

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def run_command(cmd):
    """Executa comando e retorna resultado"""
    print(f"{Colors.BLUE}$ {cmd}{Colors.END}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result

def test_passed(test_name):
    print(f"{Colors.GREEN}✓ {test_name}{Colors.END}\n")

def test_failed(test_name, error):
    print(f"{Colors.RED}✗ {test_name}: {error}{Colors.END}\n")

def setup_test_environment():
    """Prepara ambiente de teste"""
    print(f"\n{Colors.BOLD}🔧 Preparando ambiente de teste...{Colors.END}")
    
    # Criar diretórios
    test_dirs = [
        "test_cli_validation",
        "test_cli_validation/documents",
        "test_cli_validation/results",
        "test_cli_validation/configs",
        "test_cli_validation/watch_test"
    ]
    
    for dir in test_dirs:
        Path(dir).mkdir(exist_ok=True)
    
    # Criar documentos de teste
    docs = {
        "test_cli_validation/documents/doc1.txt": "Este é o primeiro documento de teste. Contém várias palavras importantes como análise, qualidade e framework.",
        "test_cli_validation/documents/doc2.txt": "Segundo documento para teste. Framework Qualia é excelente para análise qualitativa de dados.",
        "test_cli_validation/documents/doc3.md": "# Documento Markdown\n\nEste é um **teste** em formato _markdown_.",
    }
    
    for path, content in docs.items():
        Path(path).write_text(content)
    
    # Criar arquivo de dados para visualização
    test_data = {
        "word_frequencies": {
            "teste": 10,
            "qualia": 8,
            "análise": 7,
            "framework": 6,
            "documento": 5,
            "qualitativa": 4,
            "dados": 3,
            "python": 3,
            "plugin": 2,
            "sistema": 2
        },
        "vocabulary_size": 10,
        "total_words": 50
    }
    
    Path("test_cli_validation/test_data.json").write_text(json.dumps(test_data, indent=2))
    
    print(f"{Colors.GREEN}✓ Ambiente preparado{Colors.END}\n")

def test_config_commands():
    """Testa comandos config"""
    print(f"\n{Colors.BOLD}📝 Testando comando CONFIG...{Colors.END}")
    
    tests = [
        # Listar configurações
        ("config list", "qualia config list"),
        
        # Validar configuração (criar uma primeiro)
        ("config validate", None)  # Vamos criar inline
    ]
    
    # Criar config de teste
    test_config = {
        "min_word_length": 3,
        "remove_stopwords": True
    }
    Path("test_cli_validation/configs/test_config.yaml").write_text(
        f"# Config de teste\nmin_word_length: 3\nremove_stopwords: true\n"
    )
    
    # Validar
    result = run_command("python -m qualia config validate test_cli_validation/configs/test_config.yaml")
    if result.returncode == 0:
        test_passed("config validate")
    else:
        test_failed("config validate", result.stderr)
    
    # Nota sobre config create (interativo)
    print(f"{Colors.YELLOW}ℹ️  'config create' é interativo - teste manualmente com:{Colors.END}")
    print(f"   python -m qualia config create\n")

def test_batch_command():
    """Testa comando batch"""
    print(f"\n{Colors.BOLD}📦 Testando comando BATCH...{Colors.END}")
    
    # Teste 1: Batch simples
    cmd = 'python -m qualia batch "test_cli_validation/documents/*.txt" -p word_frequency -o test_cli_validation/results/batch/'
    result = run_command(cmd)
    
    if result.returncode == 0:
        test_passed("batch - processamento básico")
        # Verificar se arquivos foram criados
        batch_results = list(Path("test_cli_validation/results/batch").glob("*_result.json"))
        if len(batch_results) >= 2:
            test_passed(f"batch - criou {len(batch_results)} arquivos")
        else:
            test_failed("batch - arquivos de saída", f"Esperados 2+, encontrados {len(batch_results)}")
    else:
        test_failed("batch - processamento básico", result.stderr)
    
    # Teste 2: Batch com dry-run
    cmd = 'python -m qualia batch "test_cli_validation/documents/*.md" -p word_frequency --dry-run'
    result = run_command(cmd)
    if result.returncode == 0 and "dry-run" in result.stdout:
        test_passed("batch - modo dry-run")
    else:
        test_failed("batch - modo dry-run", "Não mostrou preview")

def test_export_command():
    """Testa comando export"""
    print(f"\n{Colors.BOLD}📤 Testando comando EXPORT...{Colors.END}")
    
    # Preparar arquivo para exportar
    test_json = "test_cli_validation/test_data.json"
    
    formats = [
        ("CSV", "csv", "test_cli_validation/results/export_test.csv"),
        ("Markdown", "markdown", "test_cli_validation/results/export_test.md"),
        ("HTML", "html", "test_cli_validation/results/export_test.html"),
        ("YAML", "yaml", "test_cli_validation/results/export_test.yaml"),
    ]
    
    for format_name, format_ext, output_path in formats:
        cmd = f'python -m qualia export {test_json} -f {format_ext} -o {output_path}'
        result = run_command(cmd)
        
        if result.returncode == 0 and Path(output_path).exists():
            test_passed(f"export - formato {format_name}")
        else:
            test_failed(f"export - formato {format_name}", result.stderr or "Arquivo não criado")
    
    # Teste Excel (pode falhar se pandas/openpyxl não instalado)
    cmd = f'python -m qualia export {test_json} -f excel -o test_cli_validation/results/export_test.xlsx'
    result = run_command(cmd)
    if result.returncode == 0:
        test_passed("export - formato Excel")
    else:
        print(f"{Colors.YELLOW}⚠️  export Excel falhou (pandas/openpyxl pode não estar instalado){Colors.END}")

def test_watch_command():
    """Testa comando watch (com timeout)"""
    print(f"\n{Colors.BOLD}👁️  Testando comando WATCH...{Colors.END}")
    
    # Este teste precisa ser executado em background
    print(f"{Colors.YELLOW}ℹ️  Comando watch roda continuamente. Teste manualmente com:{Colors.END}")
    print(f"   python -m qualia watch test_cli_validation/watch_test/ -p word_frequency")
    print(f"   (Crie arquivos .txt na pasta para ver o processamento)")
    print(f"   Ctrl+C para parar\n")
    
    # Teste rápido de sintaxe
    cmd = 'python -m qualia watch --help'
    result = run_command(cmd)
    if result.returncode == 0 and "Monitor" in result.stdout:
        test_passed("watch - comando existe")
    else:
        test_failed("watch - comando existe", "Comando não encontrado")

def test_combined_workflow():
    """Testa workflow combinado"""
    print(f"\n{Colors.BOLD}🔄 Testando WORKFLOW COMPLETO...{Colors.END}")
    
    # 1. Batch processing
    print("1️⃣  Processando documentos em lote...")
    cmd = 'python -m qualia batch "test_cli_validation/documents/*.txt" -p word_frequency -o test_cli_validation/results/workflow/'
    result = run_command(cmd)
    
    if result.returncode != 0:
        test_failed("workflow - batch", result.stderr)
        return
    
    # 2. Export para CSV
    print("\n2️⃣  Exportando resultados para CSV...")
    batch_log = "test_cli_validation/results/workflow/batch_log.json"
    if Path(batch_log).exists():
        cmd = f'python -m qualia export {batch_log} -f csv -o test_cli_validation/results/workflow/summary.csv'
        result = run_command(cmd)
        
        if result.returncode == 0:
            test_passed("workflow completo - batch → export")
        else:
            test_failed("workflow - export", result.stderr)
    else:
        test_failed("workflow - batch log", "Arquivo não encontrado")

def run_all_tests():
    """Executa todos os testes"""
    print(f"\n{Colors.BOLD}🧪 INICIANDO TESTES DOS NOVOS COMANDOS CLI{Colors.END}")
    print("=" * 60)
    
    # Setup
    setup_test_environment()
    
    # Executar testes
    try:
        test_config_commands()
        test_batch_command()
        test_export_command()
        test_watch_command()
        test_combined_workflow()
    except Exception as e:
        print(f"\n{Colors.RED}Erro durante testes: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
    
    # Resumo
    print(f"\n{Colors.BOLD}📊 RESUMO DOS TESTES{Colors.END}")
    print("=" * 60)
    print(f"{Colors.GREEN}✓ Maioria dos testes executados{Colors.END}")
    print(f"{Colors.YELLOW}ℹ️  Alguns comandos são interativos (config create, watch){Colors.END}")
    
    # Limpeza opcional
    if input(f"\n{Colors.YELLOW}Limpar arquivos de teste? (s/n): {Colors.END}").lower() == 's':
        shutil.rmtree("test_cli_validation", ignore_errors=True)
        print(f"{Colors.GREEN}✓ Arquivos de teste removidos{Colors.END}")

if __name__ == "__main__":
    run_all_tests()