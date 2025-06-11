# qualia/cli/commands/pipeline.py
"""
Comando para executar pipelines completos de análise
"""

import click
import json
import yaml
import time
from pathlib import Path
from rich.progress import Progress

from qualia.core import PipelineConfig, PipelineStep, PluginType
from .utils import get_core, console


@click.command()
@click.argument('document_path', type=click.Path(exists=True))
@click.option('--config', '-c', type=click.Path(exists=True), 
              required=True, help='Arquivo de configuração do pipeline')
@click.option('--output-dir', '-o', type=click.Path(), 
              help='Diretório para salvar resultados')
def pipeline(document_path: str, config: str, output_dir: str):
    """Executa pipeline completo de análise"""
    core = get_core()
    
    # Carregar configuração do pipeline
    config_path = Path(config)
    if config_path.suffix in ['.yaml', '.yml']:
        pipeline_data = yaml.safe_load(config_path.read_text())
    else:
        pipeline_data = json.loads(config_path.read_text())
    
    # Criar pipeline
    steps = []
    for step_data in pipeline_data.get('steps', []):
        step = PipelineStep(
            plugin_id=step_data['plugin'],
            config=step_data.get('config', {}),
            output_name=step_data.get('output_name')
        )
        steps.append(step)
    
    pipeline_config = PipelineConfig(
        name=pipeline_data.get('name', 'custom_pipeline'),
        steps=steps,
        metadata=pipeline_data.get('metadata', {})
    )
    
    # Ler documento
    doc_path = Path(document_path)
    content = doc_path.read_text(encoding='utf-8')
    doc = core.add_document(doc_path.stem, content)
    
    # Executar pipeline
    console.print(f"\n[bold]Executando pipeline '{pipeline_config.name}'...[/bold]")
    console.print(f"Etapas: {len(steps)}")
    
    # Preparar diretório de saída se especificado
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    
    with Progress() as progress:
        task = progress.add_task(
            "[cyan]Processando...", 
            total=len(steps)
        )
        
        results = {}
        context = {}  # Context para compartilhar entre steps
        
        for i, step in enumerate(steps):
            plugin_name = core.registry[step.plugin_id].name
            progress.update(
                task, 
                description=f"[cyan]Executando {plugin_name}..."
            )
            
            try:
                plugin_meta = core.registry[step.plugin_id]
                
                # Verificar tipo do plugin
                if plugin_meta.type == PluginType.VISUALIZER:
                    # Visualizadores precisam de dados de steps anteriores
                    if results:
                        # Pegar último resultado com word_frequencies
                        data_for_viz = None
                        for result in reversed(list(results.values())):
                            if isinstance(result, dict) and 'word_frequencies' in result:
                                data_for_viz = result
                                break
                        
                        if data_for_viz:
                            # Criar path de saída
                            if output_dir:
                                viz_output = output_path / f"{step.output_name or step.plugin_id}.png"
                            else:
                                viz_output = Path(f"{step.output_name or step.plugin_id}.png")
                            plugin_instance = core.plugins[step.plugin_id]
                            plugin_instance.render(data_for_viz, step.config or {}, viz_output)
                            results[step.output_name or step.plugin_id] = {"output": str(viz_output)}
                        else:
                            raise ValueError(f"Nenhum dado de frequências encontrado para {step.plugin_id}")
                    else:
                        raise ValueError(f"Visualizador {step.plugin_id} precisa de dados anteriores")
                else:
                    # Outros plugins processam o documento
                    result = core.execute_plugin(
                        step.plugin_id, 
                        doc, 
                        step.config or {},
                        context
                    )
                    output_name = step.output_name or step.plugin_id
                    results[output_name] = result
                    
                    # Adicionar ao context
                    context[output_name] = result
                
                progress.advance(task)
                
            except Exception as e:
                progress.stop()
                console.print(f"\n[red]✗ Erro em {step.plugin_id}: {str(e)}[/red]")
                raise SystemExit(1)
    
    console.print(f"\n[green]✓ Pipeline completo![/green]")
    
    # Salvar resultados se solicitado
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Salvar cada resultado
        for name, result in results.items():
            result_path = output_path / f"{name}_result.json"
            result_path.write_text(json.dumps(result, indent=2))
            console.print(f"  • {name} salvo em: {result_path}")
        
        # Salvar resumo
        summary_path = output_path / "pipeline_summary.yaml"
        summary = {
            'pipeline': pipeline_config.name,
            'document': doc_path.name,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'steps_executed': len(results),
            'results': list(results.keys())
        }
        summary_path.write_text(yaml.dump(summary))
        console.print(f"\n[green]✓ Resumo salvo em: {summary_path}[/green]")