#!/usr/bin/env python3
"""
create_plugin.py - Gerador de templates para plugins Qualia

Uso:
    python create_plugin.py sentiment_analyzer analyzer
    python create_plugin.py network_viz visualizer
"""

import sys
import os
from pathlib import Path
from datetime import datetime

TEMPLATES = {
    "analyzer": '''"""
{plugin_title} - {plugin_type} plugin para Qualia Core

Criado em: {date}
"""

from typing import Dict, Any, List, Tuple, Optional
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document


class {class_name}(BaseAnalyzerPlugin):
    """
    {description}
    
    Este plugin analisa {what_it_analyzes}.
    
    Exemplo de uso:
        qualia analyze documento.txt -p {plugin_id}
    """
    
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="{plugin_id}",
            name="{plugin_title}",
            type=PluginType.ANALYZER,
            version="0.1.0",
            description="{description}",
            provides=[
                # TODO: Listar o que este analyzer fornece
                "analysis_result",
                "metrics",
            ],
            requires=[
                # TODO: Listar dependências de outros plugins (se houver)
            ],
            parameters={{
                # TODO: Definir parâmetros configuráveis
                "example_param": {{
                    "type": "integer",
                    "default": 10,
                    "description": "Descrição do parâmetro"
                }},
                "language": {{
                    "type": "choice",
                    "options": ["pt", "en", "es"],
                    "default": "pt",
                    "description": "Idioma para análise"
                }}
            }}
        )
    
    def _analyze_impl(self, document: Document, config: Dict[str, Any], 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementação da análise
        
        Args:
            document: Documento a analisar
            config: Configurações validadas
            context: Contexto de execução
            
        Returns:
            Dict com resultados da análise
        """
        
        # TODO: Implementar análise
        text = document.content
        
        # Exemplo básico
        result = {{
            "analysis_result": "TODO: Implementar análise real",
            "metrics": {{
                "example_metric": 42,
                "text_length": len(text)
            }},
            "parameters_used": config
        }}
        
        return result


# Exemplo de uso standalone
if __name__ == "__main__":
    from qualia.core import Document
    
    # Teste rápido
    analyzer = {class_name}()
    doc = Document(id="test", content="Texto de exemplo para análise")
    result = analyzer._analyze_impl(doc, {{}}, {{}})
    
    print(f"Plugin: {{analyzer.meta().name}}")
    print(f"Resultado: {{result}}")
''',

    "visualizer": '''"""
{plugin_title} - {plugin_type} plugin para Qualia Core

Criado em: {date}
"""

from typing import Dict, Any, Union
from pathlib import Path
from qualia.core import BaseVisualizerPlugin, PluginMetadata, PluginType


class {class_name}(BaseVisualizerPlugin):
    """
    {description}
    
    Este plugin visualiza {what_it_visualizes}.
    
    Exemplo de uso:
        qualia visualize data.json -p {plugin_id} -o output.png
    """
    
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="{plugin_id}",
            name="{plugin_title}",
            type=PluginType.VISUALIZER,
            version="0.1.0",
            description="{description}",
            requires=[
                # TODO: Que tipo de dados este visualizer precisa?
                "data_field_required",
            ],
            provides=[
                "visualization_path",
            ],
            parameters={{
                # TODO: Definir parâmetros de visualização
                "width": {{
                    "type": "integer",
                    "default": 800,
                    "description": "Largura da visualização"
                }},
                "height": {{
                    "type": "integer",
                    "default": 600,
                    "description": "Altura da visualização"
                }},
                "style": {{
                    "type": "choice",
                    "options": ["modern", "classic", "minimal"],
                    "default": "modern",
                    "description": "Estilo visual"
                }}
            }}
        )
    
    def _render_impl(self, data: Dict[str, Any], config: Dict[str, Any], 
                     output_path: Path) -> Path:
        """
        Implementação da visualização
        
        Args:
            data: Dados para visualizar
            config: Configurações validadas
            output_path: Caminho de saída (já é Path)
            
        Returns:
            Path do arquivo gerado
        """
        
        # TODO: Implementar visualização
        
        # Exemplo com matplotlib
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(config['width']/100, config['height']/100))
        
        # TODO: Criar visualização real
        ax.text(0.5, 0.5, f"{{self.meta().name}}\\nTODO: Implementar", 
                ha='center', va='center', fontsize=20)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        # Salvar
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        return output_path
''',

    "document": '''"""
{plugin_title} - {plugin_type} plugin para Qualia Core

Criado em: {date}
"""

from typing import Dict, Any
from qualia.core import BaseDocumentPlugin, PluginMetadata, PluginType, Document


class {class_name}(BaseDocumentPlugin):
    """
    {description}
    
    Este plugin processa {what_it_processes}.
    
    Exemplo de uso:
        qualia process documento.txt -p {plugin_id} --save-as processed.txt
    """
    
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="{plugin_id}",
            name="{plugin_title}",
            type=PluginType.DOCUMENT,
            version="0.1.0",
            description="{description}",
            provides=[
                "processed_document",
                "processing_report",
            ],
            parameters={{
                # TODO: Definir parâmetros de processamento
                "example_option": {{
                    "type": "boolean",
                    "default": True,
                    "description": "Opção de exemplo"
                }}
            }}
        )
    
    def _process_impl(self, document: Document, config: Dict[str, Any], 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementação do processamento
        
        Args:
            document: Documento a processar
            config: Configurações validadas
            context: Contexto de execução
            
        Returns:
            Dict com documento processado e metadados
        """
        
        # TODO: Implementar processamento
        text = document.content
        
        # Exemplo básico
        processed_text = text  # TODO: Aplicar processamento real
        
        return {{
            "processed_document": processed_text,
            "original_length": len(text),
            "processed_length": len(processed_text),
            "processing_report": {{
                "changes_made": 0,  # TODO: Contar mudanças reais
                "issues_found": []  # TODO: Listar problemas encontrados
            }}
        }}
'''
}

REQUIREMENTS = {
    "analyzer": {
        "sentiment": "textblob>=0.17.0\nvader-sentiment>=3.3.0",
        "topic": "scikit-learn>=1.0.0\ngensim>=4.0.0",
        "default": "# Adicione dependências específicas aqui\n"
    },
    "visualizer": {
        "default": "matplotlib>=3.5.0\nseaborn>=0.12.0\n"
    },
    "document": {
        "default": "# Adicione dependências específicas aqui\n"
    }
}


def create_plugin(plugin_id: str, plugin_type: str):
    """Cria estrutura de plugin com template"""
    
    # Validar tipo
    if plugin_type not in ["analyzer", "visualizer", "document"]:
        print(f"❌ Tipo inválido: {plugin_type}")
        print("   Use: analyzer, visualizer, ou document")
        return False
    
    # Preparar variáveis
    class_name = ''.join(word.capitalize() for word in plugin_id.split('_'))
    if plugin_type == "analyzer":
        class_name += "Analyzer"
    elif plugin_type == "visualizer":
        class_name += "Visualizer"
    else:
        class_name += "Processor"
    
    plugin_title = ' '.join(word.capitalize() for word in plugin_id.split('_'))
    
    # Criar diretório
    plugin_dir = Path(f"plugins/{plugin_id}")
    if plugin_dir.exists():
        print(f"❌ Plugin {plugin_id} já existe!")
        return False
    
    plugin_dir.mkdir(parents=True)
    
    # Criar __init__.py
    template_vars = {
        "plugin_id": plugin_id,
        "plugin_type": plugin_type.capitalize(),
        "plugin_title": plugin_title,
        "class_name": class_name,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "description": f"Plugin para {plugin_title.lower()}",
        "what_it_analyzes": "TODO: descrever o que analisa",
        "what_it_visualizes": "TODO: descrever o que visualiza",
        "what_it_processes": "TODO: descrever o que processa",
    }
    
    init_content = TEMPLATES[plugin_type].format(**template_vars)
    (plugin_dir / "__init__.py").write_text(init_content)
    
    # Criar requirements.txt
    req_key = plugin_id.split('_')[0] if plugin_id.split('_')[0] in REQUIREMENTS.get(plugin_type, {}) else "default"
    req_content = REQUIREMENTS[plugin_type].get(req_key, REQUIREMENTS[plugin_type]["default"])
    (plugin_dir / "requirements.txt").write_text(req_content)
    
    # Criar README.md
    readme_content = f"""# {plugin_title}

**Tipo**: {plugin_type.capitalize()}  
**ID**: `{plugin_id}`  
**Versão**: 0.1.0

## Descrição

{template_vars['description']}

## Instalação

```bash
pip install -r plugins/{plugin_id}/requirements.txt
```

## Uso

### CLI
```bash
qualia {plugin_type.replace('analyzer', 'analyze').replace('document', 'process')} arquivo.txt -p {plugin_id}
```

### Python
```python
from plugins.{plugin_id} import {class_name}

plugin = {class_name}()
result = plugin._process_impl(document, config, context)
```

## Parâmetros

TODO: Documentar parâmetros

## Desenvolvimento

TODO: Adicionar instruções de desenvolvimento
"""
    
    (plugin_dir / "README.md").write_text(readme_content)
    
    print(f"""
✅ Plugin criado com sucesso!

📁 Estrutura criada:
   plugins/{plugin_id}/
   ├── __init__.py       # Código principal
   ├── requirements.txt  # Dependências
   └── README.md        # Documentação

🎯 Próximos passos:
   1. Editar plugins/{plugin_id}/__init__.py
   2. Implementar método _analyze_impl() ou _render_impl()
   3. Instalar dependências: pip install -r plugins/{plugin_id}/requirements.txt
   4. Testar: qualia {plugin_type.replace('analyzer', 'analyze').replace('document', 'process')} test.txt -p {plugin_id}

💡 Dica: O template tem TODOs marcando onde adicionar seu código!
""")
    
    return True


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python create_plugin.py <plugin_id> <tipo>")
        print("Exemplo: python create_plugin.py sentiment_analyzer analyzer")
        print("Tipos: analyzer, visualizer, document")
        sys.exit(1)
    
    plugin_id = sys.argv[1]
    plugin_type = sys.argv[2]
    
    create_plugin(plugin_id, plugin_type)