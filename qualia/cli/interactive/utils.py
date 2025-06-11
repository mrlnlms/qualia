"""
Utilidades para o menu interativo
"""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from rich.prompt import Prompt, Confirm
from ..formatters import console


def get_int_choice(prompt: str, min_val: int, max_val: int) -> int:
    """Solicita uma escolha numérica válida"""
    while True:
        try:
            value = int(Prompt.ask(prompt))
            if min_val <= value <= max_val:
                return value
            else:
                console.print(f"[red]Por favor, escolha um número entre {min_val} e {max_val}[/red]")
        except ValueError:
            console.print("[red]Por favor, digite um número válido[/red]")


def run_qualia_command(args: List[str]) -> Tuple[bool, str, str]:
    """
    Executa um comando qualia e retorna (sucesso, stdout, stderr)
    """
    cmd = ["python", "-m", "qualia"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr


def choose_file(recent_files: List[str]) -> Optional[str]:
    """Interface para escolher arquivo"""
    console.print("\n[bold]Escolher arquivo:[/bold]")
    
    console.print("1. Digitar caminho")
    console.print("2. Escolher de exemplos")
    console.print("3. Arquivo recente")
    console.print("4. Voltar")
    
    choice = Prompt.ask("Opção", choices=["1", "2", "3", "4"])
    
    if choice == "1":
        return _choose_file_by_path()
    elif choice == "2":
        return _choose_file_from_examples()
    elif choice == "3":
        return _choose_file_from_recent(recent_files)
    
    return None


def _choose_file_by_path() -> Optional[str]:
    """Escolhe arquivo digitando o caminho"""
    path = Prompt.ask("Caminho do arquivo")
    if Path(path).exists():
        return path
    else:
        console.print("[red]Arquivo não encontrado![/red]")
        return None


def _choose_file_from_examples() -> Optional[str]:
    """Escolhe arquivo dos exemplos"""
    possible_dirs = [
        Path("examples"),
        Path("docs/examples"),
        Path(".")
    ]
    
    all_files = []
    for dir_path in possible_dirs:
        if dir_path.exists():
            txt_files = list(dir_path.glob("*.txt"))
            for f in txt_files:
                if f not in all_files:
                    all_files.append(f)
    
    if not all_files:
        console.print("[yellow]Nenhum arquivo de exemplo encontrado![/yellow]")
        return None
    
    console.print("\n[bold]Arquivos de exemplo:[/bold]")
    for i, f in enumerate(all_files, 1):
        console.print(f"{i}. {f.name} [dim]({f.parent})[/dim]")
    
    idx = get_int_choice("Escolha", 1, len(all_files))
    return str(all_files[idx-1])


def _choose_file_from_recent(recent_files: List[str]) -> Optional[str]:
    """Escolhe arquivo dos recentes"""
    if not recent_files:
        console.print("[yellow]Nenhum arquivo recente![/yellow]")
        return None
    
    console.print("\n[bold]Arquivos recentes:[/bold]")
    for i, f in enumerate(recent_files[-5:], 1):
        console.print(f"{i}. {f}")
    
    idx = get_int_choice("Escolha", 1, min(5, len(recent_files)))
    return recent_files[-idx]


def parse_plugin_list(output: str, plugin_type: str = "all") -> List[Tuple[str, str, str]]:
    """
    Analisa a saída do comando 'qualia list' e retorna lista de (id, nome, descrição)
    """
    plugins = []
    lines = output.split('\n')
    
    # Procurar por linhas da tabela (que contêm │)
    for line in lines:
        # Pular linhas de borda e cabeçalho
        if any(char in line for char in ['━', '┏', '┓', '┗', '┛', '┃', '┡', '┩', '└', '┴', '─']):
            continue
        
        if 'ID' in line and 'Tipo' in line:  # Cabeçalho
            continue
            
        if '│' in line:
            parts = [p.strip() for p in line.split('│') if p.strip()]
            
            if len(parts) >= 3:
                plugin_id = parts[0]
                plugin_type_found = parts[1]
                plugin_name = parts[2]
                
                # Validar ID
                if plugin_id and len(plugin_id) > 1:
                    # Filtrar por tipo se necessário
                    if plugin_type == "all" or plugin_type.lower() in plugin_type_found.lower():
                        plugins.append((plugin_id, plugin_name, plugin_type_found))
    
    return plugins


def choose_plugin(plugin_type: str = "all") -> Optional[str]:
    """Escolhe um plugin do tipo especificado"""
    success, output, error = run_qualia_command(
        ["list"] + (["-t", plugin_type] if plugin_type != "all" else [])
    )
    
    if not success:
        console.print(f"[red]Erro ao listar plugins: {error}[/red]")
        return None
    
    plugins = parse_plugin_list(output, plugin_type)
    
    if not plugins:
        console.print(f"[red]Nenhum {plugin_type} encontrado![/red]")
        console.print("[yellow]Verifique se os plugins estão instalados corretamente.[/yellow]")
        return None
    
    console.print(f"\n[bold]Escolha um {plugin_type}:[/bold]")
    for i, (plugin_id, plugin_name, plugin_type_str) in enumerate(plugins, 1):
        console.print(f"{i}. [cyan]{plugin_id}[/cyan] - {plugin_name} [dim]({plugin_type_str})[/dim]")
    
    idx = get_int_choice("Escolha", 1, len(plugins))
    return plugins[idx-1][0]


def configure_parameters(plugin: str, context: str = "general") -> Dict[str, str]:
    """Configura parâmetros para um plugin"""
    console.print(f"\n[bold]Configurar {plugin}[/bold]")
    
    # Configurações predefinidas
    presets = {
        "word_frequency": {
            "min_word_length": ("Tamanho mínimo de palavra", "3"),
            "remove_stopwords": ("Remover palavras comuns", "true"),
            "language": ("Idioma", "portuguese")
        },
        "teams_cleaner": {
            "remove_timestamps": ("Remover timestamps", "false"),
            "merge_consecutive": ("Mesclar falas consecutivas", "true")
        },
        "wordcloud_viz": {
            "colormap": ("Esquema de cores", "viridis"),
            "background_color": ("Cor de fundo", "white"),
            "max_words": ("Máximo de palavras", "100")
        },
        "frequency_chart": {
            "chart_type": ("Tipo de gráfico", "bar"),
            "top_n": ("Número de itens", "20")
        }
    }
    
    params = {}
    
    if plugin in presets:
        console.print("[dim]Parâmetros disponíveis:[/dim]")
        for param, (desc, default) in presets[plugin].items():
            value = Prompt.ask(f"{desc}", default=default)
            if value.lower() != "skip":
                params[param] = value
    else:
        if Confirm.ask("Deseja adicionar parâmetros customizados?"):
            console.print("[dim]Digite 'fim' quando terminar[/dim]")
            while True:
                param_name = Prompt.ask("Nome do parâmetro (ou 'fim')")
                if param_name.lower() == 'fim':
                    break
                param_value = Prompt.ask(f"Valor para {param_name}")
                params[param_name] = param_value
    
    return params


def show_file_preview(filepath: str, max_lines: int = 5):
    """Mostra preview de um arquivo"""
    try:
        path = Path(filepath)
        if path.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            console.print("\n[bold]Preview do JSON:[/bold]")
            for key in list(data.keys())[:3]:
                console.print(f"  • {key}: {type(data[key]).__name__}")
        else:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            console.print(f"\n[bold]Preview ({len(lines)} linhas total):[/bold]")
            for line in lines[:max_lines]:
                console.print(f"  {line.rstrip()}")
            if len(lines) > max_lines:
                console.print(f"  [dim]... mais {len(lines) - max_lines} linhas[/dim]")
    except Exception as e:
        console.print(f"[yellow]Não foi possível fazer preview: {e}[/yellow]")