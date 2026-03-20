# qualia/cli/commands/utils.py
"""
Utilitários compartilhados pelos comandos CLI
"""

from typing import Optional, Dict, Any
from pathlib import Path
import hashlib
import json
import click
import yaml
from rich.console import Console

from qualia.core import QualiaCore

# Console global para output formatado
console = Console()

# Instância global do core (lazy loading)
_core: Optional[QualiaCore] = None


def get_core() -> QualiaCore:
    """Obtém instância do core com lazy loading.

    QualiaCore.__init__ já chama discover_plugins() — não chamar de novo.
    """
    global _core
    if _core is None:
        with console.status("[bold green]Descobrindo plugins..."):
            _core = QualiaCore()
    return _core


def load_config(config_path: Path) -> Dict[str, Any]:
    """Carrega arquivo de configuração YAML ou JSON. Falha se não for dict."""
    if config_path.suffix in ['.yaml', '.yml']:
        data = yaml.safe_load(config_path.read_text())
    else:
        data = json.loads(config_path.read_text())
    if not isinstance(data, dict):
        raise click.BadParameter(
            f"Config deve ser um objeto (dict), não {type(data).__name__}. "
            f"Arquivo: {config_path}"
        )
    return data


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
            except (json.JSONDecodeError, ValueError):
                # Mantém como string
                params[key] = value
                
    return params


def make_doc_id(file_path: Path, content: str) -> str:
    """Gera doc_id com hash do conteúdo — evita cache stale quando arquivo muda.

    Formato: {stem}_{hash[:8]} — legível e único por conteúdo.
    Alinhado com a API que já inclui hash no doc_id.
    """
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"{file_path.stem}_{content_hash}"


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
            max_count = result['top_words'][0][1]
            if max_count > 0:
                bar_length = int((count / max_count) * 30)
            else:
                bar_length = 0
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