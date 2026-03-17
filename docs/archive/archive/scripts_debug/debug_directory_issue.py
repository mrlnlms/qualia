#!/usr/bin/env python3
"""
Debug específico para o problema de diretório inexistente
"""

import subprocess
import os
from pathlib import Path

print("🔍 Debugando problema de diretório inexistente\n")

# Teste 1: Verificar se é problema de permissão
print("1. Testando criação de diretório em /tmp...")
cmd = "python -m qualia analyze test_suite_output/test_document.txt -p word_frequency -o /tmp/teste_qualia/profundo/output.json"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Funciona em /tmp!")
    if Path("/tmp/teste_qualia/profundo/output.json").exists():
        print("   ✅ Arquivo criado com sucesso")
else:
    print(f"❌ Erro: {result.stderr}")

# Teste 2: Tentar diretório relativo profundo
print("\n2. Testando diretório relativo profundo...")
cmd = "python -m qualia analyze test_suite_output/test_document.txt -p word_frequency -o teste_profundo/nivel1/nivel2/nivel3/output.json"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Funciona com diretório relativo!")
else:
    print(f"❌ Erro: {result.stderr}")

# Teste 3: Verificar se é o /diretorio específico
print("\n3. Problema específico com /diretorio...")
# No macOS/Linux, criar em / requer sudo
# Vamos testar se é isso
import platform
if platform.system() == "Darwin":  # macOS
    print("⚠️  No macOS, criar em / requer permissões de root")
    print("   O teste está tentando criar /diretorio/inexistente/")
    print("   Isso falha por falta de permissão, não por bug do código")

# Teste 4: Verificar se o erro é capturado corretamente
print("\n4. Testando captura de erro...")
try:
    # Tentar criar direto com Python
    Path("/diretorio/inexistente/").mkdir(parents=True)
except PermissionError as e:
    print(f"✅ Erro esperado de permissão: {e}")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")

# Teste 5: Sugestão de correção para o test_suite.py
print("\n💡 SUGESTÃO DE CORREÇÃO:")
print("No test_suite.py, mude o teste de:")
print('  "/diretorio/inexistente/output.json"')
print("Para:")
print('  "test_suite_output/diretorio_profundo/nivel1/nivel2/output.json"')
print("\nIsso testará a criação de diretórios sem problemas de permissão!")