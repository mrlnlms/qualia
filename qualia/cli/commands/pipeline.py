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
from .utils import get_core, console, make_doc_id


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

    if not isinstance(pipeline_data, dict):
        console.print(f"[red]Config do pipeline deve ser um objeto (dict), não {type(pipeline_data).__name__}[/red]")
        raise SystemExit(1)

    if not isinstance(pipeline_data.get('steps'), list):
        console.print("[red]Config do pipeline deve ter campo 'steps' (lista de steps)[/red]")
        raise SystemExit(1)

    # Criar pipeline
    steps = []
    for step_data in pipeline_data.get('steps', []):
        step = PipelineStep(
            plugin_id=step_data.get('plugin_id', step_data.get('plugin', '')),
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
    try:
        content = doc_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        content = doc_path.read_text(encoding='latin-1')
    doc = core.add_document(make_doc_id(doc_path, content), content)
    
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

        # Validar que todos os plugins existem antes de executar
        for step in steps:
            if step.plugin_id not in core.registry:
                console.print(f"[red]Plugin '{step.plugin_id}' não encontrado![/red]")
                raise SystemExit(1)

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
                    # Visualizadores usam último resultado como dados (alinhado com API)
                    if not results:
                        raise ValueError(f"Visualizador {step.plugin_id} precisa de dados anteriores")
                    last_result = list(results.values())[-1]
                    if not isinstance(last_result, dict):
                        raise ValueError(f"Resultado anterior não é dict para {step.plugin_id}")
                    plugin_instance = core.get_plugin(step.plugin_id)
                    viz_config = dict(step.config or {})
                    output_format = viz_config.pop("format", "html")
                    viz_config["output_format"] = output_format
                    viz_result = plugin_instance.render(last_result, viz_config)
                    if output_dir and "html" in viz_result:
                        viz_output = output_path / f"{step.output_name or step.plugin_id}.html"
                        viz_output.write_text(viz_result["html"], encoding="utf-8")
                        viz_result["output"] = str(viz_output)
                    results[step.output_name or step.plugin_id] = viz_result
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

                    # Encadear texto: se resultado contém texto processado, usar como input do próximo step
                    if isinstance(result, dict):
                        chained_text = (
                            result.get("cleaned_document")
                            or result.get("processed_text")
                            or result.get("transcription")
                        )
                        if chained_text:
                            doc = core.add_document(f"{doc.id}_{output_name}", chained_text)
                
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