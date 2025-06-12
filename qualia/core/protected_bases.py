"""
Protected Base Classes - Circuit Breaker Integrado

Classes base que automaticamente protegem plugins com circuit breaker.
O desenvolvedor de plugin só foca na lógica de negócio, 
a proteção é transparente e automática.

Usage:
    # Antes (plugin antigo):
    class MyPlugin(BaseVisualizerPlugin):
        def _render_impl(self, data, config, output_path):
            # lógica do plugin
    
    # Depois (plugin protegido automaticamente):
    class MyPlugin(ProtectedVisualizerPlugin):
        def _render_impl(self, data, config, output_path):
            # MESMA lógica do plugin - zero mudanças!
            # Circuit breaker é transparente!
"""

from typing import Dict, Any, Union
from pathlib import Path
from functools import wraps

# Import das classes base originais
from qualia.core import BaseAnalyzerPlugin, BaseVisualizerPlugin, BaseDocumentPlugin, Document

# Import circuit breaker com fallback
try:
    from ops.monitoring.circuit_breaker import circuit_breaker
    HAS_CIRCUIT_BREAKER = True
except ImportError:
    # Fallback se circuit breaker não estiver disponível
    def circuit_breaker(max_failures=5, timeout_seconds=300):
        def decorator(func):
            return func  # Sem proteção, mas funciona
        return decorator
    HAS_CIRCUIT_BREAKER = False

# Import sentry com fallback
try:
    from ops.monitoring.sentry_config import monitor_plugin
    HAS_SENTRY = True
except ImportError:
    def monitor_plugin(plugin_id: str):
        def decorator(func):
            return func
        return decorator
    HAS_SENTRY = False


class ProtectedAnalyzerPlugin(BaseAnalyzerPlugin):
    """
    Analyzer com circuit breaker automático
    
    O desenvolvedor só implementa _analyze_impl() normalmente.
    Circuit breaker + Sentry são transparentes.
    """
    
    def analyze(self, document: Document, config: Dict[str, Any], 
                context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper automático que adiciona proteção
        O plugin filho não precisa saber de nada disso!
        """
        # Aplicar proteções automaticamente
        protected_method = self._apply_protection(self._analyze_impl)
        
        # Validar e executar
        validated_config = self._validate_config(config)
        return protected_method(document, validated_config, context)
    
    def _apply_protection(self, method):
        """Aplica circuit breaker + sentry automaticamente"""
        plugin_id = self.meta().id
        
        # Aplicar circuit breaker
        protected = circuit_breaker(
            max_failures=getattr(self, 'max_failures', 5),
            timeout_seconds=getattr(self, 'timeout_seconds', 300)
        )(method)
        
        # Aplicar monitoramento Sentry
        if HAS_SENTRY:
            protected = monitor_plugin(plugin_id)(protected)
        
        return protected
    
    # Plugin filho só implementa isso - limpo e simples!
    def _analyze_impl(self, document: Document, config: Dict[str, Any], 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Override este método - circuit breaker é automático!"""
        raise NotImplementedError("Plugin deve implementar _analyze_impl()")
    
    # Método meta é herdado da classe base - não precisa reimplementar!


class ProtectedVisualizerPlugin(BaseVisualizerPlugin):
    """
    Visualizer com circuit breaker automático
    
    Adiciona validação defensiva automática para dados de visualização.
    """
    
    def render(self, data: Dict[str, Any], config: Dict[str, Any], 
               output_path: Union[str, Path]) -> Union[str, Path]:
        """
        Wrapper automático que adiciona proteção + validação
        """
        # Garantir que output_path é Path
        output_path = self._ensure_path(output_path)
        
        # Criar diretório se necessário
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Validar config
        validated_config = self._validate_config(config)
        
        # Aplicar proteções + validação defensiva
        protected_method = self._apply_protection_with_validation(self._render_impl)
        
        # Executar
        return protected_method(data, validated_config, output_path)
    
    def _apply_protection_with_validation(self, method):
        """Aplica circuit breaker + validação defensiva automática"""
        plugin_id = self.meta().id
        
        @wraps(method)
        def protected_wrapper(data: Dict[str, Any], config: Dict[str, Any], 
                             output_path: Path) -> Path:
            # =================== VALIDAÇÃO AUTOMÁTICA ===================
            # Verifica se plugin tem dependências e se dados existem
            meta = self.meta()
            
            if meta.requires:
                if not data:
                    raise ValueError(
                        f"Plugin '{plugin_id}' requer dados, mas nenhum foi fornecido"
                    )
                
                for required_field in meta.requires:
                    if required_field not in data:
                        raise ValueError(
                            f"Plugin '{plugin_id}' requer campo '{required_field}' nos dados. "
                            f"Campos disponíveis: {list(data.keys())}"
                        )
                    
                    if not data[required_field]:
                        raise ValueError(
                            f"Campo '{required_field}' está vazio"
                        )
            # ============================================================
            
            # Executar método original
            return method(data, config, output_path)
        
        # Aplicar circuit breaker
        protected = circuit_breaker(
            max_failures=getattr(self, 'max_failures', 5),
            timeout_seconds=getattr(self, 'timeout_seconds', 300)
        )(protected_wrapper)
        
        # Aplicar monitoramento Sentry
        if HAS_SENTRY:
            protected = monitor_plugin(plugin_id)(protected)
        
        return protected
    
    # Plugin filho só implementa isso - sem validação manual!
    def _render_impl(self, data: Dict[str, Any], config: Dict[str, Any], 
                     output_path: Path) -> Path:
        """Override este método - validação + circuit breaker é automático!"""
        raise NotImplementedError("Plugin deve implementar _render_impl()")
    
    # Método meta é herdado da classe base - não precisa reimplementar!


class ProtectedDocumentPlugin(BaseDocumentPlugin):
    """Document processor com circuit breaker automático"""
    
    def process(self, document: Document, config: Dict[str, Any], 
                context: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper automático que adiciona proteção"""
        # Aplicar proteções automaticamente
        protected_method = self._apply_protection(self._process_impl)
        
        # Validar e executar
        validated_config = self._validate_config(config)
        return protected_method(document, validated_config, context)
    
    def _apply_protection(self, method):
        """Aplica circuit breaker + sentry automaticamente"""
        plugin_id = self.meta().id
        
        # Aplicar circuit breaker
        protected = circuit_breaker(
            max_failures=getattr(self, 'max_failures', 5),
            timeout_seconds=getattr(self, 'timeout_seconds', 300)
        )(method)
        
        # Aplicar monitoramento Sentry
        if HAS_SENTRY:
            protected = monitor_plugin(plugin_id)(protected)
        
        return protected
    
    # Plugin filho só implementa isso!
    def _process_impl(self, document: Document, config: Dict[str, Any], 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Override este método - circuit breaker é automático!"""
        raise NotImplementedError("Plugin deve implementar _process_impl()")
    
    # Método meta é herdado da classe base - não precisa reimplementar!


# Factory function para facilitar migração
def make_plugin_protected(plugin_class, max_failures: int = 5, timeout_seconds: int = 300):
    """
    Decorator para tornar qualquer plugin existente protegido
    
    Usage:
        @make_plugin_protected(max_failures=3, timeout_seconds=60)
        class ExistingPlugin(BaseVisualizerPlugin):
            # Plugin não muda nada!
    """
    # Salvar método original
    if hasattr(plugin_class, '_render_impl'):
        original_method = plugin_class._render_impl
        method_name = '_render_impl'
    elif hasattr(plugin_class, '_analyze_impl'):
        original_method = plugin_class._analyze_impl  
        method_name = '_analyze_impl'
    elif hasattr(plugin_class, '_process_impl'):
        original_method = plugin_class._process_impl
        method_name = '_process_impl'
    else:
        return plugin_class  # Não tem método para proteger
    
    # Aplicar proteção
    protected_method = circuit_breaker(
        max_failures=max_failures,
        timeout_seconds=timeout_seconds
    )(original_method)
    
    # Substituir método
    setattr(plugin_class, method_name, protected_method)
    
    return plugin_class


# Exportar para uso fácil
__all__ = [
    'ProtectedAnalyzerPlugin',
    'ProtectedVisualizerPlugin', 
    'ProtectedDocumentPlugin',
    'make_plugin_protected'
]