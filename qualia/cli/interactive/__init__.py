"""
Menu interativo do Qualia
"""

from .menu import QualiaInteractiveMenu


def start_menu():
    """Ponto de entrada para o menu interativo"""
    menu = QualiaInteractiveMenu()
    try:
        menu.run()
    except KeyboardInterrupt:
        from ..formatters import console
        console.print("\n\n[yellow]Interrompido pelo usuário[/yellow]")
    except Exception as e:
        from ..formatters import console, format_error
        console.print(format_error(e))
        raise


__all__ = ['start_menu', 'QualiaInteractiveMenu']