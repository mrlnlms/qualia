#!/usr/bin/env python3
"""
cleanup.py - Limpa arquivos de teste e organiza o projeto

Uso:
    python cleanup.py           # Modo interativo
    python cleanup.py --force   # Remove tudo sem perguntar
    python cleanup.py --dry-run # Mostra o que seria removido
"""

import os
import shutil
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

console = Console()


class ProjectCleaner:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.files_to_remove = []
        self.dirs_to_remove = []
        self.space_saved = 0
        
        # Padrões de arquivos temporários
        self.temp_patterns = [
            "test*.json", "test*.png", "test*.txt", "test*.html",
            "debug*.py", "check*.py", "verify*.py", "investigate*.py",
            "emergency*.py", "*_result.json", "*_output.*",
            "cleaned.txt", "chart.png", "resultado.json",
            "quick_test.*", "teste*.*"
        ]
        
        # Diretórios temporários
        self.temp_dirs = [
            "emergency_test", "debug_output", "test_suite_output",
            "__pycache__", ".pytest_cache", "*.egg-info"
        ]
        
        # Arquivos/diretórios para manter
        self.keep_patterns = [
            "test_suite.py",  # Suite de testes principal
            "configs/", "plugins/", "qualia/", "docs/", "examples/",
            "setup.py", "README.md", "requirements.txt",
            "DEVELOPMENT_LOG.md", "PROJECT_STATE.md"
        ]
    
    def scan_files(self):
        """Escaneia arquivos para remover"""
        root = Path(".")
        
        # Procurar arquivos temporários
        for pattern in self.temp_patterns:
            for file in root.glob(pattern):
                # Verificar se não está em diretório importante
                if not any(keep in str(file) for keep in ["plugins/", "qualia/", "docs/"]):
                    self.files_to_remove.append(file)
                    self.space_saved += file.stat().st_size
        
        # Procurar diretórios temporários
        for pattern in self.temp_dirs:
            for dir_path in root.glob(pattern):
                if dir_path.is_dir():
                    self.dirs_to_remove.append(dir_path)
                    self.space_saved += sum(f.stat().st_size for f in dir_path.rglob("*") if f.is_file())
    
    def show_summary(self):
        """Mostra resumo do que será removido"""
        console.print("\n[bold]🧹 Limpeza do Projeto Qualia[/bold]\n")
        
        if not self.files_to_remove and not self.dirs_to_remove:
            console.print("[green]✨ Projeto já está limpo![/green]")
            return False
        
        # Tabela de arquivos
        if self.files_to_remove:
            table = Table(title="Arquivos para remover")
            table.add_column("Arquivo", style="cyan")
            table.add_column("Tamanho", justify="right")
            
            for file in sorted(self.files_to_remove)[:10]:  # Mostrar até 10
                size = file.stat().st_size / 1024
                table.add_row(file.name, f"{size:.1f} KB")
            
            if len(self.files_to_remove) > 10:
                table.add_row(f"... e mais {len(self.files_to_remove) - 10} arquivos", "")
            
            console.print(table)
        
        # Lista de diretórios
        if self.dirs_to_remove:
            console.print("\n[bold]Diretórios para remover:[/bold]")
            for dir_path in sorted(self.dirs_to_remove):
                file_count = len(list(dir_path.rglob("*")))
                console.print(f"  • {dir_path} ({file_count} arquivos)")
        
        # Resumo
        console.print(f"\n[bold]Total:[/bold]")
        console.print(f"  • Arquivos: {len(self.files_to_remove)}")
        console.print(f"  • Diretórios: {len(self.dirs_to_remove)}")
        console.print(f"  • Espaço a liberar: {self.space_saved / 1024 / 1024:.1f} MB")
        
        return True
    
    def clean(self):
        """Remove arquivos e diretórios"""
        if self.dry_run:
            console.print("\n[yellow]Modo DRY RUN - nada será removido[/yellow]")
            return
        
        removed_files = 0
        removed_dirs = 0
        errors = []
        
        # Remover arquivos
        with console.status("[bold cyan]Removendo arquivos...[/bold cyan]"):
            for file in self.files_to_remove:
                try:
                    file.unlink()
                    removed_files += 1
                except Exception as e:
                    errors.append((file, str(e)))
        
        # Remover diretórios
        with console.status("[bold cyan]Removendo diretórios...[/bold cyan]"):
            for dir_path in self.dirs_to_remove:
                try:
                    shutil.rmtree(dir_path)
                    removed_dirs += 1
                except Exception as e:
                    errors.append((dir_path, str(e)))
        
        # Relatório
        console.print(f"\n[green]✅ Limpeza concluída![/green]")
        console.print(f"  • Arquivos removidos: {removed_files}")
        console.print(f"  • Diretórios removidos: {removed_dirs}")
        
        if errors:
            console.print(f"\n[red]⚠️  Erros encontrados:[/red]")
            for path, error in errors:
                console.print(f"  • {path}: {error}")
    
    def organize_archive(self):
        """Move arquivos úteis para archive/"""
        archive_dir = Path("archive")
        
        # Scripts de debug úteis para preservar
        debug_scripts = [
            "debug_plugins.py", "debug_validate.py",
            "fix_execute_plugin.py", "check_execute_plugin.py"
        ]
        
        moved = 0
        for script in debug_scripts:
            if Path(script).exists():
                dest = archive_dir / "scripts_debug" / script
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(script, dest)
                moved += 1
                console.print(f"  • Arquivado: {script}")
        
        if moved > 0:
            console.print(f"\n[green]📁 {moved} scripts movidos para archive/[/green]")


@click.command()
@click.option('--force', '-f', is_flag=True, help='Remove sem perguntar')
@click.option('--dry-run', '-n', is_flag=True, help='Mostra o que seria removido')
@click.option('--archive', '-a', is_flag=True, help='Arquiva scripts úteis')
def main(force, dry_run, archive):
    """Limpa arquivos temporários do projeto Qualia"""
    
    cleaner = ProjectCleaner(dry_run)
    
    # Escanear arquivos
    cleaner.scan_files()
    
    # Mostrar resumo
    has_files = cleaner.show_summary()
    
    if not has_files:
        return
    
    # Confirmar ou executar
    if dry_run:
        console.print("\n[dim]Use sem --dry-run para executar a limpeza[/dim]")
    elif force or Confirm.ask("\nProsseguir com a limpeza?"):
        if archive:
            cleaner.organize_archive()
        cleaner.clean()
    else:
        console.print("\n[yellow]Limpeza cancelada[/yellow]")


if __name__ == "__main__":
    main()