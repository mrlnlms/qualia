# qualia/cli/commands/batch.py
"""
Comando para processar múltiplos arquivos em lote
"""

import click
import json
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table

from .utils import get_core, console, parse_params, load_config


def process_file(file_path: Path, plugin_id: str, config: Dict[str, Any], 
                 output_dir: Path = None) -> Dict[str, Any]:
    """Processa um único arquivo"""
    core = get_core()
    
    try:
        # Ler arquivo
        content = file_path.read_text(encoding='utf-8')
        doc = core.add_document(file_path.stem, content)
        
        # Executar plugin
        result = core.execute_plugin(plugin_id, doc, config)
        
        # Salvar se output_dir especificado
        if output_dir:
            output_path = output_dir / f"{file_path.stem}_result.json"
            output_path.write_text(json.dumps(result, indent=2))
        
        return {
            "file": file_path.name,
            "status": "success",
            "output": str(output_path) if output_dir else None,
            "result": result
        }
        
    except Exception as e:
        return {
            "file": file_path.name,
            "status": "error",
            "error": str(e)
        }


@click.command()
@click.argument('pattern')
@click.option('--plugin', '-p', required=True, help='Plugin para executar')
@click.option('--output-dir', '-o', type=click.Path(), help='Diretório para resultados')
@click.option('--config', '-c', type=click.Path(exists=True), help='Arquivo de configuração')
@click.option('--param', '-P', multiple=True, help='Parâmetros (key=value)')
@click.option('--parallel', '-j', default=1, help='Número de processos paralelos')
@click.option('--recursive', '-r', is_flag=True, help='Buscar em subdiretórios')
@click.option('--dry-run', is_flag=True, help='Apenas mostrar arquivos que seriam processados')
@click.option('--continue-on-error', is_flag=True, help='Continuar mesmo se houver erros')
def batch(pattern: str, plugin: str, output_dir: str, config: str, 
          param: tuple, parallel: int, recursive: bool, dry_run: bool,
          continue_on_error: bool):
    """Processa múltiplos arquivos que correspondem ao padrão
    
    Exemplos:
        qualia batch "*.txt" -p word_frequency
        qualia batch "data/*.csv" -p analyzer -o results/
        qualia batch "**/*.md" -p markdown_cleaner --recursive
        qualia batch "reports/2024*.txt" -p sentiment_analyzer -j 4
    """
    core = get_core()
    
    # Verificar plugin
    if plugin not in core.plugins:
        console.print(f"[red]Plugin '{plugin}' não encontrado![/red]")
        return
    
    plugin_meta = core.registry[plugin]
    
    # Encontrar arquivos
    base_path = Path(".")
    if "/" in pattern or "\\" in pattern:
        # Se pattern tem caminho, separar
        pattern_parts = Path(pattern).parts
        if len(pattern_parts) > 1:
            base_path = Path(*pattern_parts[:-1])
            pattern = pattern_parts[-1]
    
    if recursive and "**" not in str(pattern):
        pattern = f"**/{pattern}"
    
    files = list(base_path.glob(pattern))
    
    if not files:
        console.print(f"[yellow]Nenhum arquivo encontrado com o padrão: {pattern}[/yellow]")
        return
    
    # Mostrar arquivos encontrados
    console.print(f"\n[bold]Arquivos encontrados: {len(files)}[/bold]")
    
    if dry_run:
        console.print("\n[yellow]Modo dry-run - apenas listando arquivos:[/yellow]")
        for f in files[:10]:  # Mostrar só os primeiros 10
            console.print(f"  • {f}")
        if len(files) > 10:
            console.print(f"  ... e mais {len(files) - 10} arquivos")
        return
    
    # Preparar configuração
    params = {}
    if config:
        params = load_config(Path(config))
    params.update(parse_params(param))
    
    # Preparar output
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = None
    
    # Processar arquivos
    console.print(f"\n[bold]Processando com {plugin_meta.name}...[/bold]")
    console.print(f"Paralelo: {parallel} processo(s)\n")
    
    results = []
    errors = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task(
            f"Processando {len(files)} arquivos...", 
            total=len(files)
        )
        
        # Processar em paralelo se solicitado
        if parallel > 1:
            with ThreadPoolExecutor(max_workers=parallel) as executor:
                # Submeter todos os trabalhos
                future_to_file = {
                    executor.submit(
                        process_file, f, plugin, params, output_path
                    ): f for f in files
                }
                
                # Coletar resultados conforme completam
                for future in as_completed(future_to_file):
                    result = future.result()
                    if result["status"] == "success":
                        results.append(result)
                    else:
                        errors.append(result)
                        if not continue_on_error:
                            break
                    progress.advance(task)
        else:
            # Processar sequencialmente
            for f in files:
                result = process_file(f, plugin, params, output_path)
                if result["status"] == "success":
                    results.append(result)
                else:
                    errors.append(result)
                    if not continue_on_error:
                        console.print(f"\n[red]Erro encontrado. Parando...[/red]")
                        break
                progress.advance(task)
    
    # Mostrar resumo
    console.print(f"\n[bold]📊 Resumo do processamento:[/bold]")
    console.print(f"  ✅ Sucesso: [green]{len(results)}[/green]")
    console.print(f"  ❌ Erros: [red]{len(errors)}[/red]")
    
    # Mostrar erros se houver
    if errors:
        console.print(f"\n[red]Arquivos com erro:[/red]")
        error_table = Table(show_header=True)
        error_table.add_column("Arquivo", style="cyan")
        error_table.add_column("Erro", style="red")
        
        for err in errors[:5]:  # Mostrar só os primeiros 5
            error_table.add_row(err["file"], err["error"])
        
        console.print(error_table)
        
        if len(errors) > 5:
            console.print(f"[dim]... e mais {len(errors) - 5} erros[/dim]")
    
    # Salvar log completo se houver output_dir
    if output_path:
        log_path = output_path / "batch_log.json"
        log_data = {
            "plugin": plugin,
            "pattern": pattern,
            "total_files": len(files),
            "successful": len(results),
            "errors": len(errors),
            "results": results,
            "errors": errors
        }
        log_path.write_text(json.dumps(log_data, indent=2))
        console.print(f"\n[green]Log completo salvo em: {log_path}[/green]")