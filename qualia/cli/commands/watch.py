# qualia/cli/commands/watch.py
"""
Comando para monitorar pasta e processar novos arquivos automaticamente
"""

import click
import time
from pathlib import Path
from typing import Optional, Dict, Any
from rich.live import Live
from rich.table import Table
from rich.panel import Panel

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from .utils import get_core, console, parse_params


class QualiaFileHandler(FileSystemEventHandler):
    """Handler para processar arquivos quando detectados"""
    
    def __init__(self, plugin_id: str, config: Dict[str, Any], 
                 output_dir: Optional[Path] = None, 
                 pattern: str = "*.txt"):
        self.plugin_id = plugin_id
        self.config = config
        self.output_dir = output_dir
        self.pattern = pattern
        self.core = get_core()
        self.processed_files = set()
        self.stats = {
            "processed": 0,
            "errors": 0,
            "skipped": 0
        }
        
    def on_created(self, event: FileCreatedEvent):
        """Quando um novo arquivo é criado"""
        if not event.is_directory:
            self._process_file(event.src_path)
    
    def on_modified(self, event: FileModifiedEvent):
        """Quando um arquivo é modificado"""
        if not event.is_directory:
            # Evitar reprocessar muito rápido
            path = Path(event.src_path)
            if path in self.processed_files:
                # Esperar um pouco para evitar múltiplos eventos
                time.sleep(0.5)
            self._process_file(event.src_path)
    
    def _process_file(self, file_path: str):
        """Processa um arquivo se corresponder ao padrão"""
        path = Path(file_path)
        
        # Verificar padrão
        if not path.match(self.pattern):
            return
        
        # Evitar reprocessar imediatamente
        if path in self.processed_files:
            last_modified = path.stat().st_mtime
            if time.time() - last_modified < 2:  # 2 segundos de cooldown
                return
        
        console.print(f"\n[cyan]📄 Novo arquivo detectado: {path.name}[/cyan]")
        
        try:
            # Ler documento
            content = path.read_text(encoding='utf-8')
            doc = self.core.add_document(path.stem, content)
            
            # Executar plugin
            result = self.core.execute_plugin(
                self.plugin_id, 
                doc, 
                self.config
            )
            
            # Salvar resultado se output_dir especificado
            if self.output_dir:
                output_path = self.output_dir / f"{path.stem}_result.json"
                import json
                output_path.write_text(json.dumps(result, indent=2))
                console.print(f"[green]✓ Processado → {output_path}[/green]")
            else:
                console.print(f"[green]✓ Processado com sucesso[/green]")
            
            self.processed_files.add(path)
            self.stats["processed"] += 1
            
        except Exception as e:
            console.print(f"[red]✗ Erro ao processar {path.name}: {str(e)}[/red]")
            self.stats["errors"] += 1


@click.command()
@click.argument('folder', type=click.Path(exists=True, file_okay=False))
@click.option('--plugin', '-p', required=True, help='Plugin para executar')
@click.option('--pattern', default='*.txt', help='Padrão de arquivos (ex: *.txt, *.md)')
@click.option('--output-dir', '-o', type=click.Path(), help='Diretório para resultados')
@click.option('--config', '-c', type=click.Path(exists=True), help='Arquivo de configuração')
@click.option('--param', '-P', multiple=True, help='Parâmetros (key=value)')
@click.option('--recursive', '-r', is_flag=True, help='Monitorar subpastas também')
def watch(folder: str, plugin: str, pattern: str, output_dir: str, 
          config: str, param: tuple, recursive: bool):
    """Monitora pasta e processa novos arquivos automaticamente
    
    Exemplos:
        qualia watch documents/ -p word_frequency
        qualia watch inbox/ -p sentiment_analyzer --pattern "*.eml"
        qualia watch data/ -p teams_cleaner -o cleaned/ --recursive
    """
    core = get_core()
    
    # Verificar plugin
    if plugin not in core.plugins:
        console.print(f"[red]Plugin '{plugin}' não encontrado![/red]")
        return
    
    plugin_meta = core.registry[plugin]
    
    # Preparar configuração
    params = {}
    if config:
        from .utils import load_config
        params = load_config(Path(config))
    params.update(parse_params(param))
    
    # Preparar output
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = None
    
    # Criar handler e observer
    folder_path = Path(folder).resolve()
    handler = QualiaFileHandler(plugin, params, output_path, pattern)
    observer = Observer()
    observer.schedule(handler, str(folder_path), recursive=recursive)
    
    # Interface de monitoramento
    console.print(Panel(
        f"[bold cyan]Monitorando: {folder_path}[/bold cyan]\n"
        f"Plugin: [yellow]{plugin_meta.name}[/yellow]\n"
        f"Padrão: [green]{pattern}[/green]\n"
        f"Recursivo: {'Sim' if recursive else 'Não'}\n\n"
        f"[dim]Pressione Ctrl+C para parar[/dim]",
        title="🔍 Qualia Watch",
        border_style="blue"
    ))
    
    # Iniciar monitoramento
    observer.start()
    
    try:
        # Loop principal com estatísticas
        while True:
            time.sleep(1)
            # Poderia adicionar live stats aqui se necessário
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Parando monitoramento...[/yellow]")
        observer.stop()
        
    observer.join()
    
    # Mostrar estatísticas finais
    console.print(f"\n[bold]📊 Estatísticas finais:[/bold]")
    console.print(f"  Processados: [green]{handler.stats['processed']}[/green]")
    console.print(f"  Erros: [red]{handler.stats['errors']}[/red]")
    console.print(f"  Ignorados: [yellow]{handler.stats['skipped']}[/yellow]")