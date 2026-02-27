"""
Menu principal do Qualia Interactive
"""

import os
from typing import Optional
from rich.prompt import Prompt
from ..formatters import console, show_banner
from .handlers import MenuHandlers
from .tutorials import TutorialManager


class QualiaInteractiveMenu:
    """Menu interativo principal do Qualia"""
    
    def __init__(self):
        self.current_analysis = None
        self.recent_files = []
        self.handlers = MenuHandlers(self)
        self.tutorials = TutorialManager()
    
    def clear_screen(self):
        """Limpa a tela do terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_banner(self):
        """Exibe o banner do Qualia"""
        self.clear_screen()
        console.print(show_banner())
    
    def run(self):
        """Loop principal do menu"""
        while True:
            self.show_banner()
            self._show_recent_files()
            
            console.print("\n[bold]MENU PRINCIPAL[/bold]\n")
            
            options = {
                "1": ("📄", "Analisar documento", self.handlers.analyze_document),
                "2": ("🧹", "Processar documento", self.handlers.process_document),
                "3": ("🎨", "Visualizar resultados", self.handlers.visualize_results),
                "4": ("🔄", "Executar pipeline", self.handlers.run_pipeline),
                "5": ("📦", "Batch (múltiplos arquivos)", self.handlers.batch_process),
                "6": ("👁️", "Watch (monitorar pasta)", self.handlers.watch_folder),
                "7": ("📤", "Exportar resultados", self.handlers.export_results),
                "8": ("🔍", "Explorar plugins", self.handlers.explore_plugins),
                "9": ("⚙️", "Configurações", self.handlers.settings_menu),
                "10": ("📚", "Exemplos e tutoriais", self.tutorials.show_menu),
                "0": ("❌", "Sair", None)
            }
            
            for key, (icon, text, _) in options.items():
                console.print(f"{key}. {icon} {text}")
            
            choice = Prompt.ask(
                "\n[bold cyan]Escolha uma opção[/bold cyan]", 
                choices=list(options.keys())
            )
            
            if choice == "0":
                console.print("\n[bold green]Até logo! 👋[/bold green]")
                break
            
            if choice in options:
                _, _, handler = options[choice]
                if handler:
                    handler()
    
    def _show_recent_files(self):
        """Mostra arquivos recentes se houver"""
        if self.recent_files:
            console.print("\n[dim]Arquivos recentes:[/dim]")
            for f in self.recent_files[-3:]:
                console.print(f"  • {f}")
    
    def add_recent_file(self, filepath: str):
        """Adiciona arquivo à lista de recentes"""
        if filepath not in self.recent_files:
            self.recent_files.append(filepath)
            # Manter apenas os últimos 10
            self.recent_files = self.recent_files[-10:]