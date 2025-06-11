# qualia/cli/commands/utils.py
"""
Utilitários compartilhados pelos comandos CLI
"""

from typing import Optional, Dict, Any
from pathlib import Path
import json
import yaml
from rich.console import Console

from qualia.core import QualiaCore

# Console global para output formatado
console = Console()

# Instância global do core (lazy loading)
_core: Optional[QualiaCore] = None


def get_core() -> QualiaCore:
    """Obtém instância do core com lazy loading"""
    global _core
    if _core is None:
        _core = QualiaCore()
        with console.status("[bold green]Descobrindo plugins..."):
            _core.discover_plugins()
    return _core


def load_config(config_path: Path) -> Dict[str, Any]:
    """Carrega arquivo de configuração YAML ou JSON"""
    if config_path.suffix in ['.yaml', '.yml']:
        return yaml.safe_load(config_path.read_text())
    else:
        return json.loads(config_path.read_text())


def parse_params(param_list: tuple) -> Dict[str, Any]:
    """Converte lista de parâmetros key=value em dicionário"""
    params = {}
    for p in param_list:
        if '=' not in p:
            console.print(f"[yellow]Aviso: parâmetro '{p}' ignorado (use formato key=value)[/yellow]")
            continue
            
        key, value = p.split('=', 1)
        
        # Tentar converter para tipo apropriado
        if value.lower() in ['true', 'false']:
            params[key] = value.lower() == 'true'
        elif value.isdigit():
            params[key] = int(value)
        else:
            try:
                # Tenta como JSON para arrays, objetos, etc
                params[key] = json.loads(value)
            except:
                # Mantém como string
                params[key] = value
                
    return params


def display_result_pretty(plugin_name: str, result: Dict[str, Any]):
    """Exibe resultado de forma formatada"""
    console.print(f"\n[bold]Resultado: {plugin_name}[/bold]")
    
    # Exibir métricas principais
    if 'vocabulary_size' in result:
        console.print(f"\nVocabulário: [cyan]{result['vocabulary_size']}[/cyan] palavras únicas")
    
    if 'total_words' in result:
        console.print(f"Total de palavras: [cyan]{result['total_words']}[/cyan]")
    
    # Top palavras
    if 'top_words' in result and result['top_words']:
        console.print("\n[bold]Palavras mais frequentes:[/bold]")
        for word, count in result['top_words'][:10]:
            bar_length = int((count / result['top_words'][0][1]) * 30)
            bar = '█' * bar_length
            console.print(f"  {word:15} {bar} {count}")
    
    # Outros dados
    for key, value in result.items():
        if key not in ['word_frequencies', 'top_words', 'vocabulary_size', 
                      'total_words', 'parameters_used', 'hapax_legomena']:
            if isinstance(value, (dict, list)) and len(str(value)) > 100:
                console.print(f"\n{key}: [dim]<dados complexos>[/dim]")
            else:
                console.print(f"\n{key}: {value}")