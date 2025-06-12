"""
Sentry Configuration for Qualia Core
Monitoring e alertas de erro em tempo real (GRÁTIS!)

Setup:
1. Criar conta em sentry.io (grátis - 5k eventos/mês)
2. Criar projeto Python
3. Copiar DSN e colocar em .env: SENTRY_DSN=https://...
4. Importar este módulo uma vez: from sentry_config import init_sentry; init_sentry()

Features:
- Email instantâneo quando plugin quebra
- Stack trace completo
- Context do plugin que falhou
- Performance monitoring básico
"""

import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from typing import Optional, Dict, Any

def init_sentry(
    dsn: Optional[str] = None,
    environment: str = "development",
    sample_rate: float = 1.0,
    debug: bool = False
) -> bool:
    """
    Inicializa Sentry para monitoramento de erros
    
    Args:
        dsn: DSN do Sentry (pega do .env se não fornecido)
        environment: dev/staging/production  
        sample_rate: % de eventos para capturar (1.0 = 100%)
        debug: Mostrar logs do Sentry
    
    Returns:
        True se inicializou com sucesso
    """
    # Pega DSN do .env se não fornecido
    dsn = dsn or os.getenv("SENTRY_DSN")
    
    if not dsn:
        print("⚠️  SENTRY_DSN não encontrado no .env - Sentry desabilitado")
        return False
    
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            sample_rate=sample_rate,
            debug=debug,
            
            # Integrações para FastAPI + async
            integrations=[
                FastApiIntegration(auto_error_capture=True),
                AsyncioIntegration(),
            ],
            
            # Configurações de performance
            traces_sample_rate=0.1,  # 10% das requests para performance
            
            # Configurações de release
            release=os.getenv("APP_VERSION", "0.1.0"),
            
            # Tags globais úteis
            before_send=_enrich_event,
        )
        
        print(f"✅ Sentry inicializado: {environment} ({dsn[:30]}...)")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inicializar Sentry: {e}")
        return False

def _enrich_event(event: Dict[str, Any], hint: Dict[str, Any]) -> Dict[str, Any]:
    """Enriquece eventos com contexto do Qualia"""
    
    # Tags úteis para debugging
    event.setdefault("tags", {}).update({
        "component": "qualia-core",
        "language": "python",
    })
    
    # Context extra se for erro de plugin
    if "exception" in event:
        for exception in event["exception"]["values"]:
            # Se erro menciona plugin, adicionar contexto
            if "plugin" in exception.get("value", "").lower():
                event.setdefault("extra", {})["plugin_error"] = True
    
    return event

def capture_plugin_error(plugin_id: str, error: Exception, context: Dict[str, Any] = None):
    """
    Captura erro específico de plugin com contexto rico
    
    Args:
        plugin_id: ID do plugin que falhou
        error: Exceção capturada  
        context: Context adicional (config, document, etc)
    """
    with sentry_sdk.push_scope() as scope:
        # Tags específicas
        scope.set_tag("plugin_id", plugin_id)
        scope.set_tag("error_type", type(error).__name__)
        
        # Context rico
        scope.set_context("plugin", {
            "id": plugin_id,
            "error_message": str(error),
            "error_type": type(error).__name__,
        })
        
        if context:
            scope.set_context("execution", context)
        
        # Captura o erro
        sentry_sdk.capture_exception(error)

def capture_performance_issue(operation: str, duration_ms: float, metadata: Dict[str, Any] = None):
    """
    Captura issues de performance (operações lentas)
    
    Args:
        operation: Nome da operação (ex: "analyze_sentiment")
        duration_ms: Duração em milissegundos
        metadata: Metadados adicionais
    """
    # Se muito lento, reportar como issue
    if duration_ms > 5000:  # > 5 segundos
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("performance_issue", True)
            scope.set_tag("operation", operation)
            scope.set_context("performance", {
                "operation": operation,
                "duration_ms": duration_ms,
                "metadata": metadata or {}
            })
            
            sentry_sdk.capture_message(
                f"Operação lenta detectada: {operation} ({duration_ms:.1f}ms)",
                level="warning"
            )

def test_sentry():
    """Testa se Sentry está funcionando enviando erro proposital"""
    try:
        # Erro proposital para testar
        1 / 0
    except Exception as e:
        capture_plugin_error("test_plugin", e, {"test": True})
        print("✅ Erro de teste enviado para Sentry!")

# Decorador para capturar erros automaticamente
def monitor_plugin(plugin_id: str):
    """
    Decorator para monitorar plugins automaticamente
    
    Usage:
        @monitor_plugin("word_frequency")
        def analyze(self, document, config, context):
            # Se der erro, Sentry captura automaticamente
            return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                import time
                start = time.time()
                
                result = func(*args, **kwargs)
                
                # Captura performance se necessário
                duration_ms = (time.time() - start) * 1000
                if duration_ms > 1000:  # > 1 segundo
                    capture_performance_issue(
                        f"{plugin_id}.{func.__name__}",
                        duration_ms,
                        {"args_count": len(args), "kwargs_keys": list(kwargs.keys())}
                    )
                
                return result
                
            except Exception as e:
                capture_plugin_error(plugin_id, e, {
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs": list(kwargs.keys())
                })
                raise  # Re-raise para não quebrar o fluxo
        
        return wrapper
    return decorator

# Exemplo de uso:
if __name__ == "__main__":
    # Teste local
    init_sentry(debug=True)
    test_sentry()
    print("Verifique seu email ou dashboard do Sentry!")