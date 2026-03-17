# debug_plugins.py
"""
Script para debugar o carregamento de plugins
"""

import sys
import traceback
from pathlib import Path

# Adicionar diretório atual ao path
sys.path.insert(0, str(Path.cwd()))

print("=== DEBUG PLUGINS ===\n")

# 1. Verificar imports do core
print("1. Testando imports do core...")
try:
    from qualia.core import (
        IAnalyzerPlugin, IVisualizerPlugin, IDocumentPlugin,
        BaseAnalyzerPlugin, BaseVisualizerPlugin, BaseDocumentPlugin,
        PluginMetadata, PluginType
    )
    print("✅ Imports do core OK")
    print(f"   - BaseAnalyzerPlugin: {BaseAnalyzerPlugin}")
    print(f"   - BaseVisualizerPlugin: {BaseVisualizerPlugin}")
    print(f"   - BaseDocumentPlugin: {BaseDocumentPlugin}")
except Exception as e:
    print(f"❌ Erro ao importar core: {e}")
    traceback.print_exc()

print("\n2. Verificando se as base classes têm os métodos abstratos...")
try:
    # Verificar métodos abstratos
    from abc import ABC, abstractmethod
    import inspect
    
    print("\nMétodos abstratos em IAnalyzerPlugin:")
    for name, method in inspect.getmembers(IAnalyzerPlugin):
        if hasattr(method, '__isabstractmethod__') and method.__isabstractmethod__:
            print(f"   - {name}")
    
    print("\nMétodos abstratos em BaseAnalyzerPlugin:")
    for name, method in inspect.getmembers(BaseAnalyzerPlugin):
        if hasattr(method, '__isabstractmethod__') and method.__isabstractmethod__:
            print(f"   - {name}")
            
except Exception as e:
    print(f"❌ Erro: {e}")

print("\n3. Testando plugins individuais...")

# Testar word_frequency
print("\n📦 Plugin: word_frequency")
try:
    from plugins.word_frequency import WordFrequencyAnalyzer
    print("✅ Import OK")
    
    # Verificar herança
    print(f"   Herda de: {WordFrequencyAnalyzer.__bases__}")
    
    # Verificar se tem os métodos necessários
    analyzer = WordFrequencyAnalyzer()
    print(f"   meta(): {hasattr(analyzer, 'meta')}")
    print(f"   _analyze_impl(): {hasattr(analyzer, '_analyze_impl')}")
    print(f"   analyze(): {hasattr(analyzer, 'analyze')}")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    traceback.print_exc()

# Testar wordcloud_viz
print("\n📦 Plugin: wordcloud_viz")
try:
    from plugins.wordcloud_viz import WordCloudVisualizer
    print("✅ Import OK")
    
    print(f"   Herda de: {WordCloudVisualizer.__bases__}")
    
    visualizer = WordCloudVisualizer()
    print(f"   meta(): {hasattr(visualizer, 'meta')}")
    print(f"   _render_impl(): {hasattr(visualizer, '_render_impl')}")
    print(f"   render(): {hasattr(visualizer, 'render')}")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    traceback.print_exc()

# Testar carregamento pelo PluginLoader
print("\n4. Testando PluginLoader...")
try:
    from qualia.core import PluginLoader
    
    loader = PluginLoader()
    plugins_dir = Path("plugins")
    
    print(f"   Diretório de plugins: {plugins_dir}")
    print(f"   Existe? {plugins_dir.exists()}")
    
    if plugins_dir.exists():
        print("\n   Plugins encontrados:")
        for plugin_dir in plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                print(f"   - {plugin_dir.name}")
                
                # Tentar carregar
                try:
                    plugin = loader.load_plugin(str(plugin_dir))
                    if plugin:
                        print(f"     ✅ Carregado com sucesso")
                    else:
                        print(f"     ❌ Retornou None")
                except Exception as e:
                    print(f"     ❌ Erro: {e}")
                    
except Exception as e:
    print(f"❌ Erro com PluginLoader: {e}")
    traceback.print_exc()

print("\n5. Verificando estrutura dos arquivos...")
# Verificar se os arquivos dos plugins foram modificados
for plugin_name in ['word_frequency', 'wordcloud_viz', 'teams_cleaner', 'frequency_chart']:
    plugin_file = Path(f"plugins/{plugin_name}/__init__.py")
    if plugin_file.exists():
        with open(plugin_file, 'r') as f:
            content = f.read()
            
        print(f"\n📄 {plugin_name}:")
        # Verificar imports
        if "BaseAnalyzerPlugin" in content:
            print("   ✅ Importa BaseAnalyzerPlugin")
        elif "BaseVisualizerPlugin" in content:
            print("   ✅ Importa BaseVisualizerPlugin")
        elif "BaseDocumentPlugin" in content:
            print("   ✅ Importa BaseDocumentPlugin")
        else:
            print("   ❌ Ainda usa interface antiga?")
            
        # Verificar método
        if "_analyze_impl" in content:
            print("   ✅ Tem _analyze_impl")
        elif "_render_impl" in content:
            print("   ✅ Tem _render_impl")
        elif "_process_impl" in content:
            print("   ✅ Tem _process_impl")
        else:
            print("   ❌ Ainda usa método antigo?")
    else:
        print(f"\n❌ Arquivo não encontrado: {plugin_file}")

print("\n=== FIM DO DEBUG ===")