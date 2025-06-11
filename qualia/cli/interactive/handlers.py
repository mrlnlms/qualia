"""
Handlers para os comandos do menu interativo
"""

import sys
import json
import shutil
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from rich.prompt import Prompt, Confirm

from ..formatters import console, format_success, format_error, format_warning
from .utils import (
    choose_file, choose_plugin, configure_parameters,
    run_qualia_command, get_int_choice, show_file_preview
)
from .wizards import PipelineWizard

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
    
    def _execute_analysis(self, file_path: str, analyzer: str, params: dict, output: str):
        """Executa análise com feedback visual"""
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
            self.menu.current_analysis = str(output_path)
            show_file_preview(str(output_path))
        else:
            console.print(format_error(Exception("Erro na análise")))
            console.print(stderr)
    
    def _execute_visualization(self, data_file: str, visualizer: str, output: str, params: dict):
        """Executa visualização"""
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
                self._open_file(str(output_path))
        else:
            console.print(format_error(Exception("Erro na visualização")))
            console.print(stderr)
    
    def _execute_pipeline(self, pipeline_path: Path):
        """Executa um pipeline"""
        file_path = choose_file(self.menu.recent_files)
        if not file_path:
            return
        
        self.menu.add_recent_file(file_path)
        
        output_dir = Prompt.ask("Diretório de saída", default="results/pipeline_output")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        args = ["pipeline", file_path, "-c", str(pipeline_path), "-o", output_dir]
        
        with console.status("[bold cyan]Executando pipeline...[/bold cyan]"):
            success, stdout, stderr = run_qualia_command(args)
        
        if success:
            console.print(format_success("Pipeline executado!"))
            console.print(stdout)
            self._show_generated_files(Path(output_dir))
        else:
            console.print(format_error(Exception("Erro no pipeline")))
            console.print(stderr)
    
    def _choose_data_file(self) -> Optional[str]:
        """Escolhe arquivo de dados JSON"""
        search_dirs = [Path("."), Path("results")]
        json_files = []
        
        for dir_path in search_dirs:
            if dir_path.exists():
                json_files.extend(list(dir_path.glob("*.json")))
        
        json_files = list(set(json_files))
        
        if self.menu.current_analysis:
            console.print(f"\n[dim]Análise atual: {self.menu.current_analysis}[/dim]")
            if Confirm.ask("Usar análise atual?"):
                return self.menu.current_analysis
        
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
    
    def _clear_cache(self):
        """Limpa o cache"""
        if Confirm.ask("Limpar todo o cache?"):
            cache_dir = Path("cache")
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                cache_dir.mkdir()
                console.print(format_success("Cache limpo!"))
            else:
                console.print(format_warning("Diretório de cache não encontrado"))
    
    def _show_config(self):
        """Mostra configuração atual"""
        console.print("\n[bold]Configuração atual:[/bold]")
        console.print(f"Python: {sys.version}")
        console.print(f"Diretório: {Path.cwd()}")
        
        plugin_count = 0
        if Path('plugins').exists():
            for item in Path('plugins').iterdir():
                if item.is_dir() and (item / '__init__.py').exists():
                    plugin_count += 1
        
        console.print(f"Plugins instalados: {plugin_count}")
        
        console.print("\n[bold]Dependências principais:[/bold]")
        deps = ["click", "rich", "nltk", "matplotlib", "wordcloud", "plotly"]
        for dep in deps:
            try:
                __import__(dep)
                console.print(f"  ✓ {dep}")
            except ImportError:
                console.print(f"  ✗ {dep} [red](não instalado)[/red]")
    
    def _install_dependencies(self):
        """Instala dependências de um plugin"""
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
    
    def _verify_installation(self):
        """Verifica instalação do Qualia"""
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
    
    def _open_file(self, filepath: str):
        """Abre arquivo no sistema"""
        import subprocess
        if sys.platform == "darwin":
            subprocess.run(["open", filepath])
        elif sys.platform == "linux":
            subprocess.run(["xdg-open", filepath])
        elif sys.platform == "win32":
            subprocess.run(["start", filepath], shell=True)
    
    def _show_generated_files(self, output_dir: Path):
        """Mostra arquivos gerados"""
        if output_dir.exists():
            files = list(output_dir.glob("*"))
            if files:
                console.print("\n[bold]Arquivos gerados:[/bold]")
                for f in files:
                    size = f.stat().st_size / 1024
                    console.print(f"  • {f.name} ({size:.1f} KB)")