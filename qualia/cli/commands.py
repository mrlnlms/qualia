# qualia/cli.py
"""
Qualia CLI - Interface de linha de comando para o framework

Comandos principais:
- list: Lista plugins disponíveis
- analyze: Executa análise em documento
- process: Processa documento com plugin
- pipeline: Executa pipeline de análise
- inspect: Inspeciona resultado de análise
"""

import click
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

from qualia.core import (
    QualiaCore, 
    PluginType,
    PipelineConfig,
    PipelineStep
)
from .formatters import console, format_success, format_error, format_warning
from .interactive import start_menu

# Console para output formatado
console = Console()

# Instância global do core (lazy loading)
_core: Optional[QualiaCore] = None

def get_core() -> QualiaCore:
    """Obtém instância do core com lazy loading"""
    global _core
    if _core is None:
        _core = QualiaCore()
        with console.status("[bold green]Descobrindo plugins..."):
            _core.discover_plugins()
    return _core


@click.group()
@click.version_option(version="0.1.0", prog_name="Qualia Core")
def cli():
    """
    🔬 Qualia Core - Framework bare metal para análise qualitativa
    
    Transforma dados qualitativos em insights quantificados através de plugins.
    """
    pass


@cli.command()
@click.option('--type', '-t', 
              type=click.Choice(['all', 'analyzer', 'filter', 'visualizer', 'document', 'composer']),
              default='all',
              help='Tipo de plugin para listar')
@click.option('--detailed', '-d', is_flag=True, help='Mostrar informações detalhadas')
def list(type: str, detailed: bool):
    """Lista plugins disponíveis"""
    core = get_core()
    
    # Filtrar por tipo se necessário
    if type == 'all':
        plugins = core.registry.values()
    else:
        plugin_type = PluginType(type)
        plugins = [p for p in core.registry.values() if p.type == plugin_type]
    
    if not plugins:
        console.print(f"[yellow]Nenhum plugin do tipo '{type}' encontrado.[/yellow]")
        return
    
    # Criar tabela
    table = Table(title=f"Plugins Disponíveis ({len(plugins)} total)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Tipo", style="magenta")
    table.add_column("Nome", style="green")
    table.add_column("Versão", style="yellow")
    
    if detailed:
        table.add_column("Fornece", style="blue")
        table.add_column("Requer", style="red")
    
    # Adicionar plugins à tabela
    for plugin in plugins:
        row = [
            plugin.id,
            plugin.type.value,
            plugin.name,
            plugin.version
        ]
        
        if detailed:
            provides = ", ".join(plugin.provides) if plugin.provides else "-"
            requires = ", ".join(plugin.requires) if plugin.requires else "-"
            row.extend([provides, requires])
        
        table.add_row(*row)
    
    console.print(table)
    
    # Mostrar descrições se detalhado
    if detailed:
        console.print("\n[bold]Descrições:[/bold]")
        for plugin in plugins:
            console.print(f"\n[cyan]{plugin.id}:[/cyan] {plugin.description}")

@cli.command()
def menu():
    """Abre menu interativo para facilitar o uso do Qualia"""
    try:
        start_menu()
    except KeyboardInterrupt:
        console.print("\n[yellow]Menu interrompido pelo usuário[/yellow]")
    except Exception as e:
        console.print(format_error(e))
        raise


@cli.command()
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
        config_path = Path(config)
        if config_path.suffix == '.yaml' or config_path.suffix == '.yml':
            params = yaml.safe_load(config_path.read_text())
        else:
            params = json.loads(config_path.read_text())
    
    # Adicionar parâmetros individuais
    for p in param:
        key, value = p.split('=', 1)
        # Tentar converter para tipo apropriado
        try:
            value = json.loads(value)
        except:
            pass  # Manter como string
        params[key] = value
    
    # Executar análise
    console.print(f"\n[bold]Executando {plugin_meta.name}...[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Analisando...", total=None)
        
        try:
            result = core.execute_plugin(plugin, doc, params)  # Adiciona context vazio
            progress.stop()
            
            # Exibir resultado
            if format == 'pretty':
                _display_result_pretty(plugin_meta.name, result)
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


@cli.command()
@click.argument('document_path', type=click.Path(exists=True))
@click.option('--plugin', '-p', required=True, help='ID do plugin de processamento')
@click.option('--config', '-c', type=click.Path(exists=True), help='Arquivo de configuração')
@click.option('--save-as', '-s', type=click.Path(), help='Salvar documento processado')
@click.option('--param', '-P', multiple=True, help='Parâmetros no formato key=value')  # NOVA LINHA
def process(document_path: str, plugin: str, config: str, save_as: str, param):  # ADICIONAR param
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
        config_path = Path(config)
        if config_path.suffix in ['.yaml', '.yml']:
            params = yaml.safe_load(config_path.read_text())
        else:
            params = json.loads(config_path.read_text())
    
    # NOVO: Processar parâmetros -P
    for p in param:
        if '=' in p:
            key, value = p.split('=', 1)
            # Converter valores booleanos
            if value.lower() in ['true', 'false']:
                params[key] = value.lower() == 'true'
            # Tentar converter números
            elif value.isdigit():
                params[key] = int(value)
            else:
                params[key] = value
    
    # Processar
    console.print(f"\n[bold]Processando com {plugin_meta.name}...[/bold]")
    
    # NOVO: Adicionar context se o plugin precisar
    context = {}
    
    try:
        # MODIFICADO: Passar params e context
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


@cli.command()
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
    
    with Progress() as progress:
        task = progress.add_task(
            "[cyan]Processando...", 
            total=len(steps)
        )
        
        results = {}
        for i, step in enumerate(steps):
            plugin_name = core.registry[step.plugin_id].name
            progress.update(
                task, 
                description=f"[cyan]Executando {plugin_name}..."
            )
            
            try:
                result = core.execute_plugin(
                    step.plugin_id, 
                    doc, 
                    step.config
                )
                output_name = step.output_name or step.plugin_id
                results[output_name] = result
                progress.advance(task)
                
            except Exception as e:
                progress.stop()
                console.print(f"\n[red]✗ Erro em {step.plugin_id}: {str(e)}[/red]")
                raise SystemExit(1)
    
    console.print(f"\n[green]✓ Pipeline completo![/green]")
    
    # Salvar resultados se solicitado
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
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


@cli.command()
@click.argument('plugin_id')
def inspect(plugin_id: str):
    """Inspeciona detalhes de um plugin"""
    core = get_core()
    
    if plugin_id not in core.registry:
        console.print(f"[red]Plugin '{plugin_id}' não encontrado![/red]")
        return
    
    meta = core.registry[plugin_id]
    
    # Painel principal
    console.print(Panel(
        f"[bold cyan]{meta.name}[/bold cyan]\n"
        f"[yellow]v{meta.version}[/yellow]\n\n"
        f"{meta.description}",
        title=f"Plugin: {plugin_id}",
        border_style="blue"
    ))
    
    # Informações técnicas
    console.print("\n[bold]Informações Técnicas:[/bold]")
    console.print(f"  Tipo: [magenta]{meta.type.value}[/magenta]")
    console.print(f"  ID: [cyan]{meta.id}[/cyan]")
    
    # O que fornece
    if meta.provides:
        console.print("\n[bold]Fornece:[/bold]")
        for item in meta.provides:
            console.print(f"  • [green]{item}[/green]")
    
    # Dependências
    if meta.requires:
        console.print("\n[bold]Requer:[/bold]")
        for item in meta.requires:
            console.print(f"  • [red]{item}[/red]")
    
    # Pode usar
    if meta.can_use:
        console.print("\n[bold]Pode usar (opcional):[/bold]")
        for item in meta.can_use:
            console.print(f"  • [yellow]{item}[/yellow]")
    
    # Parâmetros
    if meta.parameters:
        console.print("\n[bold]Parâmetros:[/bold]")
        param_table = Table(show_header=True, header_style="bold")
        param_table.add_column("Nome", style="cyan")
        param_table.add_column("Tipo", style="magenta")
        param_table.add_column("Default", style="green")
        param_table.add_column("Descrição")
        
        for param_name, param_info in meta.parameters.items():
            param_type = param_info.get('type', 'string')
            default = str(param_info.get('default', '-'))
            description = param_info.get('description', '')
            
            # Adicionar opções se for choice
            if param_type == 'choice' and 'options' in param_info:
                param_type = f"choice {param_info['options']}"
            
            param_table.add_row(
                param_name,
                param_type,
                default,
                description
            )
        
        console.print(param_table)


@cli.command()
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
    for p in param:
        if '=' not in p:
            console.print(f"[yellow]Aviso: parâmetro '{p}' ignorado (use formato key=value)[/yellow]")
            continue
            
        key, value = p.split('=', 1)
        # Tentar converter para tipo apropriado
        try:
            # Tenta como JSON primeiro (para números, booleanos, etc)
            value = json.loads(value)
        except:
            # Mantém como string se falhar
            pass
        params[key] = value
    
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


# Adicionar função auxiliar para listar visualizadores (opcional)
@cli.command(name='list-visualizers')
def list_visualizers():
    """Lista apenas plugins visualizadores disponíveis"""
    core = get_core()
    
    visualizers = [p for p in core.registry.values() if p.type == PluginType.VISUALIZER]
    
    if not visualizers:
        console.print("[yellow]Nenhum visualizador encontrado.[/yellow]")
        return
    
    table = Table(title=f"Visualizadores Disponíveis ({len(visualizers)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Nome", style="green")
    table.add_column("Aceita", style="blue")
    table.add_column("Formatos", style="magenta")
    
    for viz in visualizers:
        accepts = ", ".join(viz.requires) if viz.requires else "qualquer"
        formats = ", ".join(viz.provides) if viz.provides else "png"
        table.add_row(
            viz.id,
            viz.name,
            accepts,
            formats
        )
    
    console.print(table)
    console.print("\n[dim]Use 'qualia inspect <id>' para mais detalhes[/dim]")


@cli.command()
def init():
    """Inicializa estrutura do projeto Qualia"""
    console.print("[bold]Inicializando projeto Qualia...[/bold]\n")
    
    # Criar estrutura de pastas
    folders = [
        'plugins',
        'cache', 
        'output',
        'configs',
        'configs/pipelines',
        'configs/methodologies',
        'data',
        'data/raw',
        'data/processed'
    ]
    
    for folder in folders:
        path = Path(folder)
        path.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓[/green] Criado: {folder}/")
    
    # Criar arquivo de exemplo de pipeline
    pipeline_example = {
        'name': 'example_pipeline',
        'description': 'Pipeline de exemplo para análise de transcrições',
        'steps': [
            {
                'plugin': 'teams_cleaner',
                'config': {
                    'remove_timestamps': False,
                    'remove_system_messages': True
                },
                'output_name': 'cleaned'
            },
            {
                'plugin': 'word_frequency',
                'config': {
                    'min_word_length': 4,
                    'remove_stopwords': True
                },
                'output_name': 'frequencies'
            }
        ]
    }
    
    pipeline_path = Path('configs/pipelines/example.yaml')
    pipeline_path.write_text(yaml.dump(pipeline_example, default_flow_style=False))
    console.print(f"\n[green]✓[/green] Criado pipeline de exemplo: {pipeline_path}")
    
    console.print("\n[bold green]Projeto inicializado com sucesso![/bold green]")
    console.print("\nPróximos passos:")
    console.print("  1. Adicione documentos em data/raw/")
    console.print("  2. Crie plugins em plugins/")
    console.print("  3. Execute: qualia list")


def _display_result_pretty(plugin_name: str, result: Dict[str, Any]):
    """Exibe resultado de forma formatada"""
    console.print(f"\n[bold]Resultado: {plugin_name}[/bold]")
    
    # Exibir métricas principais
    if 'vocabulary_size' in result:
        console.print(f"\nVocabulário: [cyan]{result['vocabulary_size']}[/cyan] palavras únicas")
    
    if 'total_words' in result:
        console.print(f"Total de palavras: [cyan]{result['total_words']}[/cyan]")
    
    # Top palavras
    if 'top_words' in result and result['top_words']:
        console.print("\n[bold]Palavras mais frequentes:[/bold]")
        for word, count in result['top_words'][:10]:
            bar_length = int((count / result['top_words'][0][1]) * 30)
            bar = '█' * bar_length
            console.print(f"  {word:15} {bar} {count}")
    
    # Outros dados
    for key, value in result.items():
        if key not in ['word_frequencies', 'top_words', 'vocabulary_size', 
                      'total_words', 'parameters_used', 'hapax_legomena']:
            if isinstance(value, (dict, list)) and len(str(value)) > 100:
                console.print(f"\n{key}: [dim]<dados complexos>[/dim]")
            else:
                console.print(f"\n{key}: {value}")


# Entry point
if __name__ == '__main__':
    cli()