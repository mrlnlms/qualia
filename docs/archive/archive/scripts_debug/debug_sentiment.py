#!/usr/bin/env python3
"""Debug script para o sentiment_analyzer plugin"""

import sys
import traceback
from pathlib import Path

print("=== Debug Sentiment Analyzer Plugin ===\n")

# 1. Verificar se o arquivo existe
plugin_file = Path("plugins/sentiment_analyzer/__init__.py")
print(f"1. Arquivo existe? {plugin_file.exists()}")
print(f"   Tamanho: {plugin_file.stat().st_size if plugin_file.exists() else 'N/A'} bytes\n")

# 2. Tentar importar o módulo
print("2. Tentando importar o módulo...")
try:
    import plugins.sentiment_analyzer
    print("   ✓ Módulo importado com sucesso!")
    
    # Listar conteúdo do módulo
    print("\n3. Conteúdo do módulo:")
    for item in dir(plugins.sentiment_analyzer):
        if not item.startswith('_'):
            print(f"   - {item}")
    
except Exception as e:
    print(f"   ✗ Erro ao importar: {e}")
    print("\n   Traceback completo:")
    traceback.print_exc()
    sys.exit(1)

# 3. Tentar importar a classe
print("\n4. Tentando importar SentimentAnalyzer...")
try:
    from plugins.sentiment_analyzer import SentimentAnalyzer
    print("   ✓ Classe importada com sucesso!")
    
    # Instanciar
    print("\n5. Tentando instanciar...")
    analyzer = SentimentAnalyzer()
    print("   ✓ Instância criada!")
    
    # Verificar metadata
    print("\n6. Metadata do plugin:")
    meta = analyzer.meta()
    print(f"   ID: {meta.id}")
    print(f"   Nome: {meta.name}")
    print(f"   Tipo: {meta.type}")
    print(f"   Versão: {meta.version}")
    
except ImportError as e:
    print(f"   ✗ Erro de importação: {e}")
    print("\n   Verificando nomes disponíveis no módulo...")
    if 'plugins.sentiment_analyzer' in sys.modules:
        module = sys.modules['plugins.sentiment_analyzer']
        classes = [name for name in dir(module) if name[0].isupper() and not name.startswith('_')]
        print(f"   Classes encontradas: {classes}")
except Exception as e:
    print(f"   ✗ Erro: {e}")
    traceback.print_exc()

# 4. Verificar se está sendo descoberto pelo core
print("\n7. Testando descoberta pelo Core...")
try:
    from qualia.core import QualiaCore
    core = QualiaCore()
    core.discover_plugins()
    
    print(f"   Plugins descobertos: {len(core.plugins)}")
    
    if 'sentiment_analyzer' in core.plugins:
        print("   ✓ sentiment_analyzer FOI descoberto!")
    else:
        print("   ✗ sentiment_analyzer NÃO foi descoberto")
        print("\n   Plugins encontrados:")
        for pid in core.plugins:
            print(f"   - {pid}")
        
        # Verificar erros de carregamento
        print("\n   Verificando log de erros...")
        # O core pode ter logs de erro
        
except Exception as e:
    print(f"   ✗ Erro ao testar core: {e}")
    traceback.print_exc()

print("\n=== Fim do Debug ===")