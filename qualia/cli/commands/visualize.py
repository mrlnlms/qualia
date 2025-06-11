# qualia/cli/commands/visualize.py
"""
Comando para visualizar dados com plugins
"""

import click
import json
import yaml
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn

from qualia.core import PluginType
from .utils import get_core, console, parse_params


@click.command()
@click.argument('data_path', type=click.Path(exists=True))
@click.option('--plugin', '-p', required=True, help='ID do plugin visualizador')
@click.option('--output', '-o', type=click.Path(), help='Arquivo de saída para visualização')
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Arquivo de configuração (YAML ou JSON)')
@click.option('--param', '-P', multiple=True, 
              help='Parâmetros individuais (ex: -P colormap=viridis)')
@click.option('--format', '-f', 
              type=click.Choice(['auto', 'png', 'svg', 'html', 'pdf']), 
              default='auto',
              help='Formato de saída (auto detecta pela extensão)')
def visualize(data_path: str, plugin: str, output: str, config: str, 
              param: tuple, format: str):
    """Visualiza dados com plugin específico
    
    Exemplos:
        qualia visualize freq.json -p wordcloud_viz -o cloud.png
        qualia visualize data.json -p frequency_chart -P chart_type=horizontal_bar
        qualia visualize results.json -p wordcloud_viz -P colormap=plasma -o viz.html
    """
    core = get_core()
    
    # Verificar se plugin existe
    if plugin not in core.plugins:
        console.print(f"[red]Plugin '{plugin}' não encontrado![/red]")
        console.print("\nUse 'qualia list -t visualizer' para ver visualizadores disponíveis.")
        return
    
    # Verificar se é visualizer
    plugin_meta = core.registry[plugin]
    if plugin_meta.type != PluginType.VISUALIZER:
        console.print(f"[red]'{plugin}' não é um visualizador! Tipo: {plugin_meta.type.value}[/red]")
        return
    
    # Ler dados
    data_path = Path(data_path)
    console.print(f"[bold]Lendo dados de {data_path.name}...[/bold]")
    
    try:
        if data_path.suffix in ['.json']:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif data_path.suffix in ['.yaml', '.yml']:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        else:
            console.print("[red]Formato de dados não suportado! Use JSON ou YAML.[/red]")
            return
    except Exception as e:
        console.print(f"[red]Erro ao ler dados: {str(e)}[/red]")
        return
    
    # Preparar configuração
    params = {}
    
    # Carregar de arquivo se fornecido
    if config:
        config_path = Path(config)
        try:
            if config_path.suffix in ['.yaml', '.yml']:
                params = yaml.safe_load(config_path.read_text())
            else:
                params = json.loads(config_path.read_text())
        except Exception as e:
            console.print(f"[red]Erro ao ler configuração: {str(e)}[/red]")
            return
    
    # Adicionar parâmetros individuais
    params.update(parse_params(param))
    
    # Determinar arquivo de saída
    if not output:
        # Gerar nome padrão baseado no plugin e formato
        if format == 'auto':
            # Usar formato padrão do plugin
            default_formats = {
                'wordcloud_viz': 'png',
                'frequency_chart': 'html',
                'network_viz': 'html',
                'dashboard_composer': 'html'
            }
            ext = default_formats.get(plugin, 'png')
        else:
            ext = format
            
        output = f"{data_path.stem}_{plugin}.{ext}"
        console.print(f"[yellow]Saída não especificada. Usando: {output}[/yellow]")
    
    output_path = Path(output)
    
    # Auto-detectar formato pela extensão se 'auto'
    if format == 'auto':
        ext = output_path.suffix.lower().lstrip('.')
        if ext in ['png', 'jpg', 'jpeg']:
            format = 'png'
        elif ext == 'svg':
            format = 'svg'
        elif ext in ['html', 'htm']:
            format = 'html'
        elif ext == 'pdf':
            format = 'pdf'
        else:
            format = 'png'  # padrão
    
    # Adicionar formato aos parâmetros se o plugin suportar
    if 'format' not in params:
        params['format'] = format
    
    # Executar visualização
    console.print(f"\n[bold]Gerando visualização com {plugin_meta.name}...[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Renderizando...", total=None)
        
        try:
            # Instanciar plugin
            plugin_instance = core.plugins[plugin]
            
            # Verificar se plugin tem método render
            if not hasattr(plugin_instance, 'render'):
                progress.stop()
                console.print(f"[red]Plugin '{plugin}' não suporta visualização![/red]")
                return
            
            # Renderizar (passar Path object, não string)
            result_path = plugin_instance.render(data, params, output_path)
            progress.stop()
            
            # Mostrar sucesso
            console.print(f"\n[green]✓ Visualização criada: {result_path}[/green]")
            
            # Informações adicionais baseadas no formato
            if format == 'html':
                console.print(f"\n[cyan]Dica: Abra no navegador para visualização interativa[/cyan]")
                console.print(f"  $ open {result_path}  # macOS")
                console.print(f"  $ xdg-open {result_path}  # Linux")
                console.print(f"  $ start {result_path}  # Windows")
            elif format in ['png', 'svg', 'pdf']:
                file_size = Path(result_path).stat().st_size
                size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / 1024 / 1024:.1f} MB"
                console.print(f"  Tamanho: {size_str}")
                
                # Tentar obter dimensões se for imagem
                if format == 'png':
                    try:
                        from PIL import Image
                        with Image.open(result_path) as img:
                            width, height = img.size
                            console.print(f"  Dimensões: {width}x{height} pixels")
                    except ImportError:
                        pass  # PIL não instalado
            
            # Mostrar configuração usada
            if params:
                console.print(f"\n[dim]Parâmetros utilizados:[/dim]")
                for key, value in params.items():
                    console.print(f"  • {key}: {value}")
                    
        except FileNotFoundError as e:
            progress.stop()
            console.print(f"[red]✗ Erro: arquivo não encontrado - {str(e)}[/red]")
            raise SystemExit(1)
        except ValueError as e:
            progress.stop()
            console.print(f"[red]✗ Erro de valor: {str(e)}[/red]")
            raise SystemExit(1)
        except Exception as e:
            progress.stop()
            console.print(f"[red]✗ Erro na visualização: {str(e)}[/red]")
            console.print(f"[dim]Tipo: {type(e).__name__}[/dim]")
            
            # Sugestões baseadas no erro
            if "requires" in str(e).lower():
                console.print("\n[yellow]Dica: Verifique se os dados contêm os campos necessários.[/yellow]")
                console.print("Use 'qualia inspect <plugin>' para ver requisitos.")
            elif "format" in str(e).lower():
                console.print("\n[yellow]Dica: Este plugin pode não suportar o formato solicitado.[/yellow]")
            
            raise SystemExit(1)