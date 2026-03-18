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
        qualia visualize freq.json -p wordcloud_d3 -o cloud.html
        qualia visualize data.json -p frequency_chart_plotly -P chart_type=horizontal_bar
        qualia visualize results.json -p wordcloud_d3 -P colormap=plasma -o viz.html
    """
    core = get_core()

    # Verificar se plugin existe
    if plugin not in core.registry:
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

    # Determinar formato de saída
    if format == 'auto':
        if output:
            # Auto-detectar pela extensão do arquivo de saída
            ext = Path(output).suffix.lower().lstrip('.')
            if ext in ['png', 'jpg', 'jpeg']:
                format_ext = 'png'
            elif ext == 'svg':
                format_ext = 'svg'
            elif ext in ['html', 'htm']:
                format_ext = 'html'
            elif ext == 'pdf':
                format_ext = 'pdf'
            else:
                format_ext = 'html'  # padrão
        else:
            format_ext = 'html'  # padrão
    else:
        format_ext = format

    # Determinar arquivo de saída
    if not output:
        output = str(data_path.parent / f"{data_path.stem}_{plugin}.{format_ext}")
        console.print(f"[yellow]Saída não especificada. Usando: {output}[/yellow]")

    output_path = Path(output)

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
            plugin_instance = core.get_plugin(plugin)

            # Verificar se plugin tem método render
            if not hasattr(plugin_instance, 'render'):
                progress.stop()
                console.print(f"[red]Plugin '{plugin}' não suporta visualização![/red]")
                return

            # Renderizar — passa output_format, plugin retorna dict
            params_with_format = {**params, "output_format": format_ext}
            result = plugin_instance.render(data, params_with_format)
            progress.stop()

            # Salvar resultado a partir do dict
            if "html" in result:
                if not str(output_path).endswith('.html'):
                    output_path = output_path.with_suffix('.html')
                output_path.write_text(result["html"], encoding="utf-8")
            elif "data" in result and result.get("encoding") == "base64":
                import base64 as b64_mod
                fmt = result.get("format", "png")
                if output_path.suffix != f".{fmt}":
                    output_path = output_path.with_suffix(f".{fmt}")
                output_path.write_bytes(b64_mod.b64decode(result["data"]))
            else:
                progress.stop()
                console.print("[red]✗ Formato de resultado desconhecido retornado pelo plugin.[/red]")
                raise SystemExit(1)

            # Mostrar sucesso
            file_size = output_path.stat().st_size
            size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / 1024 / 1024:.1f} MB"
            console.print(f"\n[green]✓ Visualização criada: {output_path}[/green]")
            console.print(f"  Tamanho: {size_str}")

            # Dica para HTML interativo
            if "html" in result:
                console.print(f"\n[cyan]Dica: Abra no navegador para visualização interativa[/cyan]")
                console.print(f"  $ open {output_path}  # macOS")
                console.print(f"  $ xdg-open {output_path}  # Linux")
                console.print(f"  $ start {output_path}  # Windows")

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
        except SystemExit:
            raise
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
