# qualia/cli/commands/config.py
"""
Comando para criar e gerenciar configurações
"""

import click
import yaml
import json
from pathlib import Path
from typing import Dict, Any
from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm
from rich.panel import Panel
from rich.syntax import Syntax

from qualia.core import PluginType
from .utils import get_core, console


def prompt_for_value(param_name: str, param_info: Dict[str, Any]) -> Any:
    """Solicita valor para um parâmetro baseado em seu tipo"""
    param_type = param_info.get('type', 'string')
    default = param_info.get('default')
    description = param_info.get('description', '')
    
    # Mostrar descrição
    if description:
        console.print(f"  [dim]{description}[/dim]")
    
    # Solicitar baseado no tipo
    if param_type == 'boolean':
        return Confirm.ask(f"  {param_name}", default=default)
    
    elif param_type == 'integer':
        return IntPrompt.ask(f"  {param_name}", default=default)
    
    elif param_type == 'float':
        return FloatPrompt.ask(f"  {param_name}", default=default)
    
    elif param_type == 'choice':
        options = param_info.get('options', [])
        console.print(f"  Opções: {', '.join(options)}")
        while True:
            value = Prompt.ask(f"  {param_name}", default=str(default))
            if value in options:
                return value
            console.print(f"  [red]Valor inválido. Escolha entre: {', '.join(options)}[/red]")
    
    else:  # string ou qualquer outro
        return Prompt.ask(f"  {param_name}", default=str(default) if default else "")


@click.group()
def config():
    """Gerencia configurações do Qualia"""
    pass


@config.command()
@click.option('--plugin', '-p', help='Plugin específico para configurar')
@click.option('--output', '-o', type=click.Path(), help='Arquivo de saída')
@click.option('--format', '-f', 
              type=click.Choice(['yaml', 'json']), 
              default='yaml',
              help='Formato do arquivo')
def create(plugin: str, output: str, format: str):
    """Cria arquivo de configuração interativamente
    
    Exemplos:
        qualia config create
        qualia config create -p word_frequency
        qualia config create -p sentiment_analyzer -o config.yaml
    """
    core = get_core()
    
    console.print(Panel(
        "[bold cyan]Assistente de Configuração Qualia[/bold cyan]\n\n"
        "Este assistente ajudará você a criar um arquivo de configuração\n"
        "para plugins ou pipelines.",
        border_style="blue"
    ))
    
    # Se plugin não especificado, deixar escolher
    if not plugin:
        # Listar plugins disponíveis
        plugins = list(core.registry.values())
        
        console.print("\n[bold]Plugins disponíveis:[/bold]")
        for i, p in enumerate(plugins, 1):
            console.print(f"  {i}. [{p.type.value}] {p.name} ({p.id})")
        
        # Escolher plugin
        while True:
            choice = IntPrompt.ask("\nEscolha um plugin", default=1)
            if 1 <= choice <= len(plugins):
                plugin_meta = plugins[choice - 1]
                plugin = plugin_meta.id
                break
            console.print("[red]Escolha inválida![/red]")
    else:
        if plugin not in core.registry:
            console.print(f"[red]Plugin '{plugin}' não encontrado![/red]")
            return
        plugin_meta = core.registry[plugin]
    
    console.print(f"\n[bold]Configurando: {plugin_meta.name}[/bold]")
    console.print(f"[dim]{plugin_meta.description}[/dim]\n")
    
    # Coletar valores para cada parâmetro
    config_data = {}
    
    if plugin_meta.parameters:
        console.print("[bold]Parâmetros:[/bold]")
        for param_name, param_info in plugin_meta.parameters.items():
            value = prompt_for_value(param_name, param_info)
            
            # Só adicionar se diferente do default
            if value != param_info.get('default'):
                config_data[param_name] = value
            
            console.print()  # Linha em branco entre parâmetros
    
    # Perguntar se quer criar pipeline
    if Confirm.ask("\nDeseja criar um pipeline com este plugin?", default=False):
        pipeline_name = Prompt.ask("Nome do pipeline", default=f"{plugin}_pipeline")
        
        # Estrutura do pipeline
        pipeline_config = {
            'name': pipeline_name,
            'description': f'Pipeline usando {plugin_meta.name}',
            'steps': [
                {
                    'plugin': plugin,
                    'config': config_data,
                    'output_name': f'{plugin}_result'
                }
            ]
        }
        
        # Adicionar mais steps?
        if Confirm.ask("\nAdicionar mais steps ao pipeline?", default=False):
            console.print("\n[yellow]Funcionalidade de múltiplos steps em desenvolvimento[/yellow]")
            console.print("Por enquanto, você pode editar o arquivo manualmente depois.\n")
        
        final_config = pipeline_config
        config_type = "pipeline"
    else:
        final_config = config_data
        config_type = "plugin"
    
    # Determinar arquivo de saída
    if not output:
        if config_type == "pipeline":
            output = f"configs/pipelines/{pipeline_name}.{format}"
        else:
            output = f"configs/{plugin}_config.{format}"
    
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Mostrar preview
    console.print("\n[bold]Preview da configuração:[/bold]")
    if format == 'yaml':
        preview = yaml.dump(final_config, default_flow_style=False, allow_unicode=True)
        syntax = Syntax(preview, "yaml", theme="monokai", line_numbers=True)
    else:
        preview = json.dumps(final_config, indent=2, ensure_ascii=False)
        syntax = Syntax(preview, "json", theme="monokai", line_numbers=True)
    
    console.print(syntax)
    
    # Confirmar salvamento
    if Confirm.ask("\nSalvar configuração?", default=True):
        if format == 'yaml':
            output_path.write_text(yaml.dump(final_config, default_flow_style=False, allow_unicode=True))
        else:
            output_path.write_text(json.dumps(final_config, indent=2, ensure_ascii=False))
        
        console.print(f"\n[green]✓ Configuração salva em: {output_path}[/green]")
        
        # Mostrar como usar
        console.print("\n[bold]Como usar:[/bold]")
        if config_type == "pipeline":
            console.print(f"  qualia pipeline documento.txt -c {output_path}")
        else:
            console.print(f"  qualia analyze documento.txt -p {plugin} -c {output_path}")
    else:
        console.print("\n[yellow]Configuração não salva.[/yellow]")


@config.command()
@click.argument('config_file', type=click.Path(exists=True))
def validate(config_file: str):
    """Valida um arquivo de configuração
    
    Exemplos:
        qualia config validate config.yaml
        qualia config validate pipelines/meu_pipeline.yaml
    """
    config_path = Path(config_file)
    
    try:
        # Ler arquivo
        if config_path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        else:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        console.print(f"[green]✓ Arquivo válido: {config_path.name}[/green]")
        
        # Detectar tipo
        if 'steps' in data and isinstance(data.get('steps'), list):
            console.print("  Tipo: [cyan]Pipeline[/cyan]")
            validate_pipeline_config(data)
        else:
            console.print("  Tipo: [cyan]Plugin Config[/cyan]")
            # Poderia validar contra schema do plugin
        
    except Exception as e:
        console.print(f"[red]✗ Arquivo inválido: {str(e)}[/red]")


def validate_pipeline_config(data: Dict[str, Any]):
    """Valida configuração de pipeline"""
    core = get_core()
    
    if 'name' not in data:
        console.print("  [yellow]⚠ Campo 'name' ausente[/yellow]")
    
    steps = data.get('steps', [])
    console.print(f"  Steps: {len(steps)}")
    
    for i, step in enumerate(steps):
        plugin_id = step.get('plugin')
        if not plugin_id:
            console.print(f"  [red]✗ Step {i+1}: plugin não especificado[/red]")
            continue
        
        if plugin_id not in core.registry:
            console.print(f"  [red]✗ Step {i+1}: plugin '{plugin_id}' não encontrado[/red]")
        else:
            plugin_meta = core.registry[plugin_id]
            console.print(f"  [green]✓ Step {i+1}: {plugin_meta.name}[/green]")


@config.command()
def list():
    """Lista configurações disponíveis"""
    configs_dir = Path("configs")
    
    if not configs_dir.exists():
        console.print("[yellow]Diretório 'configs' não encontrado.[/yellow]")
        return
    
    # Buscar arquivos de config
    yaml_files = list(configs_dir.rglob("*.yaml")) + list(configs_dir.rglob("*.yml"))
    json_files = list(configs_dir.rglob("*.json"))
    
    all_files = yaml_files + json_files
    
    if not all_files:
        console.print("[yellow]Nenhuma configuração encontrada.[/yellow]")
        return
    
    # Organizar por tipo
    plugin_configs = []
    pipeline_configs = []
    
    for f in all_files:
        try:
            if f.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f.read_text())
            else:
                data = json.loads(f.read_text())
            
            if 'steps' in data:
                pipeline_configs.append((f, data))
            else:
                plugin_configs.append((f, data))
        except:
            pass  # Ignorar arquivos inválidos
    
    # Mostrar configurações
    if plugin_configs:
        console.print("\n[bold]Configurações de Plugins:[/bold]")
        for path, data in plugin_configs:
            console.print(f"  • {path.relative_to(configs_dir)}")
    
    if pipeline_configs:
        console.print("\n[bold]Pipelines:[/bold]")
        for path, data in pipeline_configs:
            name = data.get('name', 'sem nome')
            steps = len(data.get('steps', []))
            console.print(f"  • {path.relative_to(configs_dir)} - {name} ({steps} steps)")