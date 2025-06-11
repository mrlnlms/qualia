# qualia/cli/commands/analyze.py
"""
Comando para executar análise em documentos
"""

import click
import json
import yaml
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn

from qualia.core import PluginType
from .utils import get_core, console, load_config, parse_params, display_result_pretty


@click.command()
@click.argument('document_path', type=click.Path(exists=True))
@click.option('--plugin', '-p', required=True, help='ID do plugin analyzer')
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Arquivo de configuração (YAML ou JSON)')
@click.option('--param', '-P', multiple=True, 
              help='Parâmetros individuais (ex: -P min_length=3)')
@click.option('--output', '-o', type=click.Path(), 
              help='Salvar resultado em arquivo')
@click.option('--format', '-f', 
              type=click.Choice(['json', 'yaml', 'pretty']), 
              default='pretty',
              help='Formato de saída')
def analyze(document_path: str, plugin: str, config: str, param: tuple, 
           output: str, format: str):
    """Executa análise em um documento"""
    core = get_core()
    
    # Verificar se plugin existe
    if plugin not in core.plugins:
        console.print(f"[red]Plugin '{plugin}' não encontrado![/red]")
        console.print("\nUse 'qualia list' para ver plugins disponíveis.")
        return
    
    # Verificar se é analyzer
    plugin_meta = core.registry[plugin]
    if plugin_meta.type != PluginType.ANALYZER:
        console.print(f"[red]'{plugin}' não é um analyzer! Tipo: {plugin_meta.type.value}[/red]")
        return
    
    # Ler documento
    doc_path = Path(document_path)
    with console.status(f"[bold green]Lendo {doc_path.name}..."):
        content = doc_path.read_text(encoding='utf-8')
        doc = core.add_document(doc_path.stem, content)
    
    # Preparar configuração
    params = {}
    
    # Carregar de arquivo se fornecido
    if config:
        params = load_config(Path(config))
    
    # Adicionar parâmetros individuais
    params.update(parse_params(param))
    
    # Executar análise
    console.print(f"\n[bold]Executando {plugin_meta.name}...[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Analisando...", total=None)
        
        try:
            result = core.execute_plugin(plugin, doc, params)
            progress.stop()
            
            # Exibir resultado
            if format == 'pretty':
                display_result_pretty(plugin_meta.name, result)
            elif format == 'json':
                console.print_json(json.dumps(result, indent=2))
            else:  # yaml
                console.print(yaml.dump(result, default_flow_style=False))
            
            # Salvar se solicitado
            if output:
                output_path = Path(output)
                if format == 'json' or output_path.suffix == '.json':
                    output_path.write_text(json.dumps(result, indent=2))
                else:
                    output_path.write_text(yaml.dump(result))
                console.print(f"\n[green]✓ Resultado salvo em: {output_path}[/green]")
                
        except Exception as e:
            progress.stop()
            console.print(f"[red]✗ Erro na análise: {str(e)}[/red]")
            raise SystemExit(1)