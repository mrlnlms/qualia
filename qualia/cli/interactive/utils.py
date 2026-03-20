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
    recent = recent_files[-5:]
    for i, f in enumerate(recent, 1):
        console.print(f"{i}. {f}")

    idx = get_int_choice("Escolha", 1, len(recent))
    return recent[idx - 1]


def choose_plugin(plugin_type: str = "all") -> Optional[str]:
    """Escolhe um plugin do tipo especificado, lendo direto do registry."""
    from qualia.cli.commands.utils import get_core
    from qualia.core.interfaces import PluginType

    try:
        core = get_core()
    except Exception as e:
        console.print(f"[red]Erro ao carregar core: {e}[/red]")
        return None

    if plugin_type == "all":
        plugin_list = list(core.registry.values())
    else:
        try:
            pt = PluginType(plugin_type)
        except ValueError:
            console.print(f"[red]Tipo desconhecido: {plugin_type}[/red]")
            return None
        plugin_list = [p for p in core.registry.values() if p.type == pt]

    if not plugin_list:
        console.print(f"[red]Nenhum {plugin_type} encontrado![/red]")
        return None

    console.print(f"\n[bold]Escolha um {plugin_type}:[/bold]")
    for i, meta in enumerate(sorted(plugin_list, key=lambda p: p.id), 1):
        console.print(f"{i}. [cyan]{meta.id}[/cyan] - {meta.name} [dim]({meta.type.value})[/dim]")

    idx = get_int_choice("Escolha", 1, len(plugin_list))
    return sorted(plugin_list, key=lambda p: p.id)[idx - 1].id


def configure_parameters(plugin: str, context: str = "general") -> Dict[str, str]:
    """Configura parâmetros para um plugin, lendo schema do registry."""
    from qualia.cli.commands.utils import get_core

    console.print(f"\n[bold]Configurar {plugin}[/bold]")
    params = {}

    try:
        core = get_core()
        meta = core.registry.get(plugin)
    except Exception:
        meta = None

    if meta and meta.parameters:
        console.print("[dim]Parâmetros disponíveis (Enter para default):[/dim]")
        for param_name, spec in meta.parameters.items():
            desc = spec.get("description", param_name)
            default = str(spec.get("default", ""))
            options = spec.get("options")

            hint = f" [{'/'.join(str(o) for o in options)}]" if options else ""
            value = Prompt.ask(f"{desc}{hint}", default=default)
            if value != default:
                params[param_name] = value
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