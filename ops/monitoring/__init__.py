"""
Monitoring - Monitoramento e Observabilidade

Módulos para monitoramento de aplicações:
- Sentry: Alertas de erro
- Circuit Breaker: Proteção contra falhas
- Health Dashboard: Status visual
"""

# Imports condicionais para evitar problemas de dependências
try:
    from .sentry_config import init_sentry, capture_plugin_error, monitor_plugin
    _HAS_SENTRY = True
except ImportError:
    _HAS_SENTRY = False

try:
    from .circuit_breaker import circuit_breaker, get_circuit_stats, reset_circuit
    _HAS_CIRCUIT_BREAKER = True
except ImportError:
    _HAS_CIRCUIT_BREAKER = False

try:
    from .health_dashboard import HealthChecker
    _HAS_HEALTH_DASHBOARD = True
except ImportError:
    _HAS_HEALTH_DASHBOARD = False

# Exports condicionais
__all__ = []

if _HAS_SENTRY:
    __all__.extend(['init_sentry', 'capture_plugin_error', 'monitor_plugin'])

if _HAS_CIRCUIT_BREAKER:
    __all__.extend(['circuit_breaker', 'get_circuit_stats', 'reset_circuit'])

if _HAS_HEALTH_DASHBOARD:
    __all__.extend(['HealthChecker'])