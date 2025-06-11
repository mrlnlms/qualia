#!/usr/bin/env python
import sys
import json
from pathlib import Path
from qualia.core import QualiaCore

if len(sys.argv) < 3:
    print("Uso: python visualize.py <dados.json> <plugin_viz>")
    sys.exit(1)

# Carregar dados
data_file = sys.argv[1]
plugin_name = sys.argv[2]

with open(data_file, 'r') as f:
    data = json.load(f)

# Inicializar core
core = QualiaCore()
core.discover_plugins()

# Criar documento temporário com os dados
doc = core.add_document("viz_temp", str(data))
doc._analyses['source'] = {'result': data}

# Executar visualizador
output_path = Path(f"results/{plugin_name}_output")
result = core.execute_plugin(plugin_name, doc, {})

print(f"Visualização criada: {result}")
