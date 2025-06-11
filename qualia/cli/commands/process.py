# qualia/cli/commands/process.py
"""
Comando para processar documentos com plugins de limpeza/preparação
"""

import click
import json
import yaml
from pathlib import Path

from qualia.core import PluginType
from .utils import get_core, console, load_config, parse_params


@click.command()
@click.argument('document_path', type=click.Path(exists=True))
@click.option('--plugin', '-p', required=True, help='ID do plugin de processamento')
@click.option('--config', '-c', type=click.Path(exists=True), help='Arquivo de configuração')
@click.option('--save-as', '-s', type=click.Path(), help='Salvar documento processado')
@click.option('--param', '-P', multiple=True, help='Parâmetros no formato key=value')
def process(document_path: str, plugin: str, config: str, save_as: str, param):
    """Processa documento com plugin de limpeza/preparação"""
    core = get_core()
    
    # Verificar plugin
    if plugin not in core.plugins:
        console.print(f"[red]Plugin '{plugin}' não encontrado![/red]")
        return
    
    plugin_meta = core.registry[plugin]
    if plugin_meta.type != PluginType.DOCUMENT:
        console.print(f"[red]'{plugin}' não é um processador de documentos![/red]")
        return
    
    # Ler documento
    doc_path = Path(document_path)
    content = doc_path.read_text(encoding='utf-8')
    doc = core.add_document(doc_path.stem, content)
    
    # Configuração
    params = {}
    if config:
        params = load_config(Path(config))
    
    # Processar parâmetros -P
    params.update(parse_params(param))
    
    # Processar
    console.print(f"\n[bold]Processando com {plugin_meta.name}...[/bold]")
    
    # Adicionar context se o plugin precisar
    context = {}
    
    try:
        # Passar params e context
        result = core.execute_plugin(plugin, doc, params, context)
        
        # Mostrar resumo
        if 'cleaned_document' in result:
            original_len = result.get('original_length', len(content))
            cleaned_len = result.get('cleaned_length', len(result['cleaned_document']))
            reduction = ((original_len - cleaned_len) / original_len) * 100
            
            console.print(f"\n[green]✓ Documento processado![/green]")
            console.print(f"  Original: {original_len} caracteres")
            console.print(f"  Limpo: {cleaned_len} caracteres")
            console.print(f"  Redução: {reduction:.1f}%")
        
        # Mostrar qualidade se disponível
        if 'quality_report' in result:
            report = result['quality_report']
            score = report.get('quality_score', 'N/A')
            console.print(f"\n[bold]Qualidade: {score}/100[/bold]")
            
            if report.get('issues'):
                console.print("\n[yellow]Problemas encontrados:[/yellow]")
                for issue in report['issues']:
                    console.print(f"  • {issue}")
        
        # Salvar se solicitado
        if save_as and 'cleaned_document' in result:
            save_path = Path(save_as)
            save_path.write_text(result['cleaned_document'])
            console.print(f"\n[green]✓ Documento salvo em: {save_path}[/green]")
            
            # Salvar variantes também
            if 'document_variants' in result:
                for variant_name, variant_content in result['document_variants'].items():
                    variant_path = save_path.parent / f"{save_path.stem}_{variant_name}{save_path.suffix}"
                    variant_path.write_text(variant_content)
                    console.print(f"  • Variante '{variant_name}' salva")
                    
    except Exception as e:
        console.print(f"[red]✗ Erro no processamento: {str(e)}[/red]")
        raise SystemExit(1)