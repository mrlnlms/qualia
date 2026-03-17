"""
Ações de execução extraídas de MenuHandlers — análise, visualização, pipeline.
"""

from pathlib import Path
from typing import Optional, TYPE_CHECKING

from ..formatters import console, format_success, format_error, format_warning

if TYPE_CHECKING:
    from .menu import QualiaInteractiveMenu


def execute_analysis(menu: 'QualiaInteractiveMenu', file_path: str, analyzer: str, params: dict, output: str):
    """Executa análise com feedback visual"""
    # Late imports to use the same names the tests patch on handlers module
    from qualia.cli.interactive.handlers import run_qualia_command, show_file_preview

    console.print(f"\n{format_success('Executando análise...')}")

    # Garantir diretório
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Montar comando
    args = ["analyze", file_path, "-p", analyzer, "-o", str(output_path)]
    for key, value in params.items():
        args.extend(["-P", f"{key}={value}"])

    # Executar
    with console.status("[bold cyan]Analisando...[/bold cyan]"):
        success, stdout, stderr = run_qualia_command(args)

    if success:
        console.print(format_success("Análise concluída!"))
        console.print(stdout)
        menu.current_analysis = str(output_path)
        show_file_preview(str(output_path))
    else:
        console.print(format_error(Exception("Erro na análise")))
        console.print(stderr)


def execute_visualization(data_file: str, visualizer: str, output: str, params: dict,
                          open_file_fn=None):
    """Executa visualização"""
    # Late imports to use the same names the tests patch on handlers module
    from qualia.cli.interactive.handlers import run_qualia_command, Confirm
    from .services import open_file as _default_open_file

    if open_file_fn is None:
        open_file_fn = _default_open_file

    console.print(f"\n{format_success('Gerando visualização...')}")

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    args = ["visualize", data_file, "-p", visualizer, "-o", str(output_path)]
    for key, value in params.items():
        args.extend(["-P", f"{key}={value}"])

    with console.status("[bold cyan]Visualizando...[/bold cyan]"):
        success, stdout, stderr = run_qualia_command(args)

    if success:
        console.print(format_success("Visualização criada!"))
        console.print(stdout)

        if output_path.exists() and Confirm.ask("\nAbrir arquivo?"):
            open_file_fn(str(output_path))
    else:
        console.print(format_error(Exception("Erro na visualização")))
        console.print(stderr)


def execute_pipeline(menu: 'QualiaInteractiveMenu', pipeline_path: Path):
    """Executa um pipeline"""
    # Late imports to use the same names the tests patch on handlers module
    from qualia.cli.interactive.handlers import choose_file, run_qualia_command, Prompt

    file_path = choose_file(menu.recent_files)
    if not file_path:
        return

    menu.add_recent_file(file_path)

    output_dir = Prompt.ask("Diretório de saída", default="results/pipeline_output")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    args = ["pipeline", file_path, "-c", str(pipeline_path), "-o", output_dir]

    with console.status("[bold cyan]Executando pipeline...[/bold cyan]"):
        success, stdout, stderr = run_qualia_command(args)

    if success:
        console.print(format_success("Pipeline executado!"))
        console.print(stdout)
        show_generated_files(Path(output_dir))
    else:
        console.print(format_error(Exception("Erro no pipeline")))
        console.print(stderr)


def choose_data_file(menu: 'QualiaInteractiveMenu') -> Optional[str]:
    """Escolhe arquivo de dados JSON"""
    # Late imports to use the same names the tests patch on handlers module
    from qualia.cli.interactive.handlers import get_int_choice, Confirm, Prompt

    search_dirs = [Path("."), Path("results")]
    json_files = []

    for dir_path in search_dirs:
        if dir_path.exists():
            json_files.extend(list(dir_path.glob("*.json")))

    json_files = list(set(json_files))

    if menu.current_analysis:
        console.print(f"\n[dim]Análise atual: {menu.current_analysis}[/dim]")
        if Confirm.ask("Usar análise atual?"):
            return menu.current_analysis

    if not json_files:
        console.print(format_warning("Nenhum arquivo JSON encontrado"))
        path = Prompt.ask("Digite o caminho do arquivo JSON")
        return path if Path(path).exists() else None

    console.print("\n[bold]Arquivos de dados disponíveis:[/bold]")
    json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    for i, f in enumerate(json_files[:10], 1):
        size = f.stat().st_size / 1024
        console.print(f"{i}. {f.name} [dim]({size:.1f} KB)[/dim]")

    console.print(f"{len(json_files[:10])+1}. Digitar caminho")

    choice = get_int_choice("Escolha", 1, min(10, len(json_files)) + 1)

    if choice <= len(json_files[:10]):
        return str(json_files[choice-1])

    path = Prompt.ask("Caminho do arquivo JSON")
    return path if Path(path).exists() and path.endswith('.json') else None


def show_generated_files(output_dir: Path):
    """Mostra arquivos gerados"""
    if output_dir.exists():
        files = list(output_dir.glob("*"))
        if files:
            console.print("\n[bold]Arquivos gerados:[/bold]")
            for f in files:
                size = f.stat().st_size / 1024
                console.print(f"  • {f.name} ({size:.1f} KB)")
