#!/usr/bin/env python3
"""
Corrige o import errado em webhooks.py
"""

from pathlib import Path

print("🔧 Corrigindo webhooks.py...\n")

webhooks_file = Path("qualia/api/webhooks.py")

if not webhooks_file.exists():
    print("❌ Arquivo webhooks.py não encontrado!")
    exit(1)

# Ler o arquivo
content = webhooks_file.read_text()

# Remover a linha problemática
old_line = "from qualia.cli.formatters import format_analysis_result"
new_line = "# from qualia.cli.formatters import format_analysis_result  # Removido - não usado"

if old_line in content:
    content = content.replace(old_line, new_line)
    webhooks_file.write_text(content)
    print("✅ Linha problemática comentada!")
    print(f"   Antiga: {old_line}")
    print(f"   Nova: {new_line}")
else:
    print("⚠️  Linha não encontrada. Verificando se já foi corrigida...")

# Limpar cache
import shutil
pycache = Path("qualia/api/__pycache__")
if pycache.exists():
    shutil.rmtree(pycache)
    print("\n✅ Cache Python limpo!")

print("\n🎯 Próximos passos:")
print("1. Reinicie a API (Ctrl+C e rode novamente)")
print("2. A mensagem de warning deve sumir")
print("3. Execute: python test_new_features.py")