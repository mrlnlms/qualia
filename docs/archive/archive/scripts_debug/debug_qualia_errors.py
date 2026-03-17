#!/usr/bin/env python3
"""
Script para debugar os erros específicos do teste
"""

import subprocess
import sys
import json
from pathlib import Path

def run_command(cmd):
    """Executa comando e retorna output completo"""
    try:
        result = subprocess.run(
            f"python -m qualia {cmd}",
            shell=True,
            capture_output=True,
            text=True
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {
            "returncode": -1,
            "error": str(e)
        }

print("🔍 Debugando erros do Qualia Test Suite\n")

# 1. Testar frequency_chart com treemap
print("1. Testando frequency_chart treemap...")
result = run_command("visualize test_suite_output/test_data.json -p frequency_chart -o test_suite_output/debug_treemap.html -P chart_type=treemap")
if result["returncode"] != 0:
    print(f"❌ Erro: {result['stderr']}")
    print(f"Stdout: {result['stdout']}")
else:
    print("✅ Sucesso!")

# 2. Verificar se o plugin frequency_chart está atualizado
print("\n2. Verificando metadata do frequency_chart...")
result = run_command("inspect frequency_chart")
print(result["stdout"])

# 3. Testar pipeline manualmente step by step
print("\n3. Testando pipeline step by step...")

# Step 1: word_frequency
print("   Step 1: word_frequency")
result = run_command("analyze test_suite_output/test_document.txt -p word_frequency -o test_suite_output/debug_freq.json")
if result["returncode"] != 0:
    print(f"   ❌ Erro: {result['stderr']}")
else:
    print("   ✅ Sucesso!")
    
    # Step 2: wordcloud_viz com o resultado
    print("   Step 2: wordcloud_viz")
    result = run_command("visualize test_suite_output/debug_freq.json -p wordcloud_viz -o test_suite_output/debug_cloud.png")
    if result["returncode"] != 0:
        print(f"   ❌ Erro: {result['stderr']}")
    else:
        print("   ✅ Sucesso!")

# 4. Testar criação de diretório
print("\n4. Testando criação de diretório...")
import tempfile
import os
temp_dir = tempfile.mkdtemp()
new_dir = os.path.join(temp_dir, "novo", "diretorio", "profundo")
result = run_command(f"analyze test_suite_output/test_document.txt -p word_frequency -o {new_dir}/output.json")
if result["returncode"] != 0:
    print(f"❌ Erro ao criar diretório: {result['stderr']}")
else:
    print("✅ Diretório criado com sucesso!")
    if Path(f"{new_dir}/output.json").exists():
        print("   ✅ Arquivo salvo corretamente")

# 5. Verificar conteúdo do test_data.json
print("\n5. Verificando test_data.json...")
try:
    with open("test_suite_output/test_data.json", "r") as f:
        data = json.load(f)
        print(f"   Chaves no JSON: {list(data.keys())}")
        if 'word_frequencies' in data:
            freq_count = len(data['word_frequencies'])
            print(f"   Número de palavras: {freq_count}")
            if freq_count > 0:
                # Mostrar primeiras 5 palavras
                first_5 = list(data['word_frequencies'].items())[:5]
                print(f"   Primeiras palavras: {first_5}")
except Exception as e:
    print(f"❌ Erro ao ler test_data.json: {e}")

print("\n✅ Debug completo!")