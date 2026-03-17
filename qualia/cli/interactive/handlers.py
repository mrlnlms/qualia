"""
Handlers para os comandos do menu interativo
"""

from pathlib import Path
from typing import Optional, TYPE_CHECKING
from rich.prompt import Prompt, Confirm

from ..formatters import console, format_success, format_error, format_warning
from .utils import (
    choose_file, choose_plugin, configure_parameters,
    run_qualia_command, get_int_choice, show_file_preview
)
from .wizards import PipelineWizard
from .services import (
    clear_cache, show_config, install_dependencies,
    verify_installation, open_file
)
from .actions import (
    execute_analysis, execute_visualization, execute_pipeline,
    choose_data_file, show_generated_files
)

if TYPE_CHECKING:
    from .menu import QualiaInteractiveMenu


class MenuHandlers:
    """Handlers para as opções do menu"""

    def __init__(self, menu: 'QualiaInteractiveMenu'):
        self.menu = menu
        self.pipeline_wizard = PipelineWizard()

    def analyze_document(self):
        """Handler para análise de documentos"""
        self.menu.show_banner()
        console.print("\n[bold]ANÁLISE DE DOCUMENTO[/bold]\n")

        # Escolher arquivo
        file_path = choose_file(self.menu.recent_files)
        if not file_path:
            return

        self.menu.add_recent_file(file_path)

        # Escolher analyzer
        analyzer = choose_plugin("analyzer")
        if not analyzer:
            return

        # Configurar parâmetros
        params = configure_parameters(analyzer, "analysis")

        # Nome do arquivo de saída
        output_name = Prompt.ask(
            "Nome do arquivo de saída",
            default=f"{Path(file_path).stem}_analysis.json"
        )

        # Executar análise
        self._execute_analysis(file_path, analyzer, params, output_name)

        # Oferecer visualização
        if Path(output_name).exists() and Confirm.ask("\nDeseja visualizar os resultados?"):
            self.visualize_results(output_name)

        Prompt.ask("\nPressione Enter para voltar ao menu")

    def visualize_results(self, data_file: Optional[str] = None):
        """Handler para visualização de resultados"""
        self.menu.show_banner()
        console.print("\n[bold]VISUALIZAÇÃO DE RESULTADOS[/bold]\n")

        # Escolher arquivo de dados
        if not data_file:
            data_file = self._choose_data_file()
            if not data_file:
                return

        # Mostrar preview dos dados
        show_file_preview(data_file)

        # Escolher visualizer
        visualizer = choose_plugin("visualizer")
        if not visualizer:
            return

        # Configurar formato de saída
        formats = {
            "1": ("png", "Imagem PNG"),
            "2": ("html", "HTML interativo"),
            "3": ("svg", "Imagem vetorial SVG")
        }

        console.print("\n[bold]Formato de saída:[/bold]")
        for key, (ext, desc) in formats.items():
            console.print(f"{key}. {desc}")

        format_choice = Prompt.ask("Escolha", choices=list(formats.keys()))
        format_ext = formats[format_choice][0]

        # Nome do arquivo
        output_name = Prompt.ask(
            "Nome do arquivo de saída",
            default=f"{Path(data_file).stem}_{visualizer}.{format_ext}"
        )

        # Parâmetros específicos
        params = configure_parameters(visualizer, "visualization")

        # Executar visualização
        self._execute_visualization(data_file, visualizer, output_name, params)

        if not data_file:  # Só pausa se não veio da análise
            Prompt.ask("\nPressione Enter para voltar ao menu")

    def run_pipeline(self):
        """Handler para execução de pipelines"""
        self.menu.show_banner()
        console.print("\n[bold]EXECUTAR PIPELINE[/bold]\n")

        pipeline_dir = Path("configs/pipelines")
        if not pipeline_dir.exists():
            if Confirm.ask("Diretório de pipelines não existe. Criar agora?"):
                pipeline_dir.mkdir(parents=True, exist_ok=True)
                console.print(format_success("Diretório criado!"))
            else:
                return

        pipelines = list(pipeline_dir.glob("*.yaml"))

        if not pipelines:
            console.print(format_warning("Nenhum pipeline encontrado."))
            if Confirm.ask("Deseja criar um novo pipeline?"):
                self.pipeline_wizard.create_pipeline()
            return

        console.print("[bold]Pipelines disponíveis:[/bold]")
        for i, p in enumerate(pipelines, 1):
            console.print(f"{i}. {p.stem}")

        console.print(f"{len(pipelines)+1}. Criar novo pipeline")

        choice = get_int_choice("Escolha", 1, len(pipelines)+1)

        if choice <= len(pipelines):
            pipeline = pipelines[choice-1]
            self._execute_pipeline(pipeline)
        else:
            self.pipeline_wizard.create_pipeline()

        Prompt.ask("\nPressione Enter para voltar ao menu")

    def explore_plugins(self):
        """Handler para exploração de plugins"""
        self.menu.show_banner()
        console.print("\n[bold]EXPLORAR PLUGINS[/bold]\n")

        # Mostrar todos os plugins
        success, output, error = run_qualia_command(["list", "-d"])

        if success:
            console.print(output)
        else:
            console.print(format_error(Exception(error)))

        # Oferecer inspeção detalhada
        console.print("\n[dim]Digite o ID do plugin para ver detalhes[/dim]")
        plugin_id = Prompt.ask("Plugin ID (ou Enter para voltar)", default="")

        if plugin_id:
            success, output, error = run_qualia_command(["inspect", plugin_id])

            if success:
                console.print("\n" + output)
            else:
                console.print(format_warning(f"Plugin '{plugin_id}' não encontrado"))

        Prompt.ask("\nPressione Enter para continuar")

    def settings_menu(self):
        """Handler para menu de configurações"""
        self.menu.show_banner()
        console.print("\n[bold]CONFIGURAÇÕES[/bold]\n")

        options = {
            "1": ("Limpar cache", self._clear_cache),
            "2": ("Ver configuração atual", self._show_config),
            "3": ("Instalar dependências de plugin", self._install_dependencies),
            "4": ("Verificar instalação", self._verify_installation),
            "5": ("Voltar", None)
        }

        for key, (text, _) in options.items():
            console.print(f"{key}. {text}")

        choice = Prompt.ask("Opção", choices=list(options.keys()))

        if choice != "5" and choice in options:
            _, handler = options[choice]
            if handler:
                handler()
                Prompt.ask("\nPressione Enter para continuar")

    # --- Thin wrappers delegating to actions module ---

    def _execute_analysis(self, file_path: str, analyzer: str, params: dict, output: str):
        return execute_analysis(self.menu, file_path, analyzer, params, output)

    def _execute_visualization(self, data_file: str, visualizer: str, output: str, params: dict):
        return execute_visualization(data_file, visualizer, output, params,
                                     open_file_fn=self._open_file)

    def _execute_pipeline(self, pipeline_path: Path):
        return execute_pipeline(self.menu, pipeline_path)

    def _choose_data_file(self) -> Optional[str]:
        return choose_data_file(self.menu)

    def _show_generated_files(self, output_dir: Path):
        return show_generated_files(output_dir)

    # --- Thin wrappers delegating to services module ---

    def _clear_cache(self):
        return clear_cache()

    def _show_config(self):
        return show_config()

    def _install_dependencies(self):
        return install_dependencies()

    def _verify_installation(self):
        return verify_installation()

    def _open_file(self, filepath: str):
        return open_file(filepath)

    # --- Public methods that remain in handlers ---

    def process_document(self):
        """Handler para processamento de documentos (limpeza/preparação)"""
        self.menu.show_banner()
        console.print("\n[bold]PROCESSAR DOCUMENTO[/bold]\n")

        file_path = choose_file(self.menu.recent_files)
        if not file_path:
            return

        self.menu.add_recent_file(file_path)

        plugin = choose_plugin("document")
        if not plugin:
            return

        params = configure_parameters(plugin, "processing")

        args = ["process", file_path, "-p", plugin]
        for key, value in params.items():
            args.extend(["-P", f"{key}={value}"])

        with console.status("[bold cyan]Processando...[/bold cyan]"):
            success, stdout, stderr = run_qualia_command(args)

        if success:
            console.print(format_success("Documento processado!"))
            console.print(stdout)
        else:
            console.print(format_error(Exception("Erro no processamento")))
            console.print(stderr)

        Prompt.ask("\nPressione Enter para voltar ao menu")

    def batch_process(self):
        """Handler para processamento em batch"""
        self.menu.show_banner()
        console.print("\n[bold]BATCH — PROCESSAR MÚLTIPLOS ARQUIVOS[/bold]\n")

        pattern = Prompt.ask("Padrão de arquivos (ex: *.txt, data/*.md)")
        plugin = choose_plugin("analyzer")
        if not plugin:
            return

        output_dir = Prompt.ask("Diretório de saída", default="results/batch")
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        params = configure_parameters(plugin, "batch")

        args = ["batch", pattern, "-p", plugin, "-o", output_dir]
        for key, value in params.items():
            args.extend(["-P", f"{key}={value}"])

        if Confirm.ask("Continuar mesmo se houver erros?", default=True):
            args.append("--continue-on-error")

        with console.status("[bold cyan]Processando arquivos...[/bold cyan]"):
            success, stdout, stderr = run_qualia_command(args)

        if success:
            console.print(format_success("Batch concluído!"))
            console.print(stdout)
        else:
            console.print(format_error(Exception("Erro no batch")))
            console.print(stderr)

        Prompt.ask("\nPressione Enter para voltar ao menu")

    def watch_folder(self):
        """Handler para monitoramento de pasta"""
        self.menu.show_banner()
        console.print("\n[bold]WATCH — MONITORAR PASTA[/bold]\n")

        folder = Prompt.ask("Pasta para monitorar")
        if not Path(folder).exists():
            console.print(format_warning(f"Pasta '{folder}' não encontrada"))
            Prompt.ask("\nPressione Enter para voltar ao menu")
            return

        plugin = choose_plugin("analyzer")
        if not plugin:
            return

        file_pattern = Prompt.ask("Padrão de arquivos", default="*.txt")
        output_dir = Prompt.ask("Diretório de saída", default="results/watch")

        args = ["watch", folder, "-p", plugin, "--pattern", file_pattern, "-o", output_dir]

        console.print(format_success(f"Monitorando {folder} com {plugin}..."))
        console.print("[dim]Pressione Ctrl+C para parar[/dim]\n")

        success, stdout, stderr = run_qualia_command(args)

        if success:
            console.print(stdout)
        else:
            console.print(stderr)

        Prompt.ask("\nPressione Enter para voltar ao menu")

    def export_results(self):
        """Handler para exportação de resultados"""
        self.menu.show_banner()
        console.print("\n[bold]EXPORTAR RESULTADOS[/bold]\n")

        input_file = self._choose_data_file()
        if not input_file:
            return

        formats = {
            "1": ("csv", "CSV"),
            "2": ("excel", "Excel"),
            "3": ("markdown", "Markdown"),
            "4": ("html", "HTML"),
            "5": ("yaml", "YAML")
        }

        console.print("[bold]Formato de saída:[/bold]")
        for key, (_, desc) in formats.items():
            console.print(f"{key}. {desc}")

        choice = Prompt.ask("Escolha", choices=list(formats.keys()))
        fmt, _ = formats[choice]

        default_output = f"{Path(input_file).stem}.{fmt}"
        output = Prompt.ask("Arquivo de saída", default=default_output)

        args = ["export", input_file, "-f", fmt, "-o", output]

        with console.status("[bold cyan]Exportando...[/bold cyan]"):
            success, stdout, stderr = run_qualia_command(args)

        if success:
            console.print(format_success(f"Exportado para {output}"))
            console.print(stdout)
        else:
            console.print(format_error(Exception("Erro na exportação")))
            console.print(stderr)

        Prompt.ask("\nPressione Enter para voltar ao menu")
