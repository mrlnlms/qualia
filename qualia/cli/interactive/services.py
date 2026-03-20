"""
Serviços utilitários extraídos de MenuHandlers — funções que não dependem de estado.
"""

import sys
import shutil
from pathlib import Path

from ..formatters import console, format_success, format_warning, format_error


def clear_cache():
    """Limpa o cache"""
    # Late import to use the same name the tests patch on handlers module
    from qualia.cli.interactive.handlers import Confirm
    if Confirm.ask("Limpar todo o cache?"):
        cache_dir = Path("cache")
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            cache_dir.mkdir()
            console.print(format_success("Cache limpo!"))
        else:
            console.print(format_warning("Diretório de cache não encontrado"))


def show_config():
    """Mostra configuração atual"""
    console.print("\n[bold]Configuração atual:[/bold]")
    console.print(f"Python: {sys.version}")
    console.print(f"Diretório: {Path.cwd()}")

    try:
        from qualia.cli.commands.utils import get_core
        core = get_core()
        plugin_count = len(core.registry)
    except Exception:
        plugin_count = 0

    console.print(f"Plugins instalados: {plugin_count}")

    console.print("\n[bold]Dependências principais:[/bold]")
    deps = ["click", "rich", "nltk", "matplotlib", "wordcloud", "plotly"]
    for dep in deps:
        try:
            __import__(dep)
            console.print(f"  ✓ {dep}")
        except ImportError:
            console.print(f"  ✗ {dep} [red](não instalado)[/red]")


def install_dependencies():
    """Instala dependências de um plugin"""
    # Late import to use the same name the tests patch on handlers module
    from qualia.cli.interactive.handlers import choose_plugin
    plugin = choose_plugin("all")
    if not plugin:
        return

    req_file = Path(f"plugins/{plugin}/requirements.txt")
    if not req_file.exists():
        console.print(format_warning(f"Plugin {plugin} não tem requirements.txt"))
        return

    console.print(f"\n{format_success(f'Instalando dependências de {plugin}...')}")
    import subprocess
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)])

    if result.returncode == 0:
        console.print(format_success("Dependências instaladas!"))
    else:
        console.print(format_error(Exception("Erro ao instalar dependências")))


def verify_installation():
    """Verifica instalação do Qualia"""
    # Late import to use the same name the tests patch on handlers module
    from qualia.cli.interactive.handlers import run_qualia_command
    console.print("\n[bold]Verificando instalação...[/bold]")

    # Testar comando
    success, stdout, _ = run_qualia_command(["--version"])
    if success:
        console.print(format_success("Comando qualia funcionando"))
        console.print(f"  {stdout.strip()}")
    else:
        console.print(format_error(Exception("Problema com comando qualia")))

    # Verificar estrutura
    required_dirs = ["qualia", "plugins", "configs", "results"]
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            console.print(format_success(f"Diretório {dir_name}"))
        else:
            console.print(format_warning(f"Diretório {dir_name} não encontrado"))


def open_file(filepath: str):
    """Abre arquivo no sistema"""
    import subprocess
    if sys.platform == "darwin":
        subprocess.run(["open", filepath])
    elif sys.platform == "linux":
        subprocess.run(["xdg-open", filepath])
    elif sys.platform == "win32":
        subprocess.run(["start", filepath], shell=True)
