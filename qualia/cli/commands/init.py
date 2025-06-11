# qualia/cli/commands/init.py
"""
Comando para inicializar estrutura do projeto Qualia
"""

import click
import yaml
from pathlib import Path

from .utils import console


@click.command()
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