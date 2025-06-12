"""
Circuit Breaker Pattern para Plugins do Qualia Core

Protege o sistema de plugins que falham repetidamente:
- Após X falhas consecutivas → Plugin desabilitado temporariamente  
- Após Y minutos → Tenta reabilitar automaticamente
- Logs tudo para análise

Usage:
    @circuit_breaker(max_failures=5, timeout_seconds=300)
    def analyze(self, document, config, context):
        # Plugin normal - se falhar 5x, desabilita por 5min
        return result

Features:
- Estados: CLOSED (normal) → OPEN (desabilitado) → HALF_OPEN (testando)
- Métricas de falha por plugin
- Recovery automático
- Integração opcional com Sentry
"""

import time
import threading
from enum import Enum
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from functools import wraps
import json
from pathlib import Path

class CircuitState(Enum):
    CLOSED = "closed"        # Normal - plugin funcionando
    OPEN = "open"           # Desabilitado - muitas falhas
    HALF_OPEN = "half_open" # Testando - tentando recovery

@dataclass
class CircuitStats:
    """Estatísticas de um circuit breaker"""
    plugin_id: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0
    last_success_time: float = 0
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0
    opened_at: Optional[float] = None
    recovery_attempts: int = 0

class CircuitBreakerManager:
    """Gerencia todos os circuit breakers dos plugins"""
    
    def __init__(self, stats_file: str = "circuit_breaker_stats.json"):
        self.circuits: Dict[str, CircuitStats] = {}
        self.stats_file = Path(stats_file)
        self._lock = threading.Lock()
        self._load_stats()
    
    def _load_stats(self):
        """Carrega estatísticas salvas"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    for plugin_id, stats_dict in data.items():
                        stats = CircuitStats(plugin_id=plugin_id)
                        stats.__dict__.update(stats_dict)
                        stats.state = CircuitState(stats_dict.get('state', 'closed'))
                        self.circuits[plugin_id] = stats
            except Exception as e:
                print(f"⚠️  Erro carregando stats do circuit breaker: {e}")
    
    def _save_stats(self):
        """Salva estatísticas em arquivo"""
        try:
            data = {}
            for plugin_id, stats in self.circuits.items():
                data[plugin_id] = {
                    **stats.__dict__,
                    'state': stats.state.value
                }
            
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.stats_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Erro salvando stats do circuit breaker: {e}")
    
    def get_or_create_circuit(self, plugin_id: str) -> CircuitStats:
        """Obtém ou cria circuit para plugin"""
        with self._lock:
            if plugin_id not in self.circuits:
                self.circuits[plugin_id] = CircuitStats(plugin_id=plugin_id)
            return self.circuits[plugin_id]
    
    def should_allow_call(self, plugin_id: str, timeout_seconds: int = 300) -> bool:
        """Verifica se plugin pode ser executado"""
        circuit = self.get_or_create_circuit(plugin_id)
        current_time = time.time()
        
        with self._lock:
            if circuit.state == CircuitState.CLOSED:
                return True
            
            elif circuit.state == CircuitState.OPEN:
                # Verifica se é hora de tentar recovery
                if circuit.opened_at and (current_time - circuit.opened_at) >= timeout_seconds:
                    circuit.state = CircuitState.HALF_OPEN
                    circuit.recovery_attempts += 1
                    self._save_stats()
                    return True
                return False
            
            elif circuit.state == CircuitState.HALF_OPEN:
                # No half-open, permite UMA tentativa
                return True
        
        return False
    
    def record_success(self, plugin_id: str):
        """Registra sucesso de plugin"""
        circuit = self.get_or_create_circuit(plugin_id)
        current_time = time.time()
        
        with self._lock:
            circuit.total_calls += 1
            circuit.total_successes += 1
            circuit.last_success_time = current_time
            circuit.failure_count = 0  # Reset contador de falhas consecutivas
            
            # Se estava em recovery, volta para normal
            if circuit.state == CircuitState.HALF_OPEN:
                circuit.state = CircuitState.CLOSED
                print(f"✅ Plugin '{plugin_id}' recuperado (circuit fechado)")
            
            self._save_stats()
    
    def record_failure(self, plugin_id: str, max_failures: int = 5):
        """Registra falha de plugin"""
        circuit = self.get_or_create_circuit(plugin_id)
        current_time = time.time()
        
        with self._lock:
            circuit.total_calls += 1
            circuit.total_failures += 1
            circuit.failure_count += 1
            circuit.last_failure_time = current_time
            
            # Se atingiu limite, abre o circuit
            if circuit.failure_count >= max_failures:
                circuit.state = CircuitState.OPEN
                circuit.opened_at = current_time
                print(f"🔥 Plugin '{plugin_id}' desabilitado ({circuit.failure_count} falhas consecutivas)")
                
                # Integração com Sentry se disponível
                try:
                    from ops.monitoring.sentry_config import capture_plugin_error
                    capture_plugin_error(
                        plugin_id, 
                        Exception(f"Circuit breaker opened - {circuit.failure_count} failures"),
                        {"circuit_stats": circuit.__dict__}
                    )
                except ImportError:
                    pass
            
            # Se estava testando recovery e falhou, volta para open
            elif circuit.state == CircuitState.HALF_OPEN:
                circuit.state = CircuitState.OPEN
                circuit.opened_at = current_time
                print(f"❌ Plugin '{plugin_id}' falhou no recovery (circuit reaberto)")
            
            self._save_stats()
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Retorna estatísticas de todos os circuits"""
        with self._lock:
            return {
                plugin_id: {
                    **circuit.__dict__,
                    'state': circuit.state.value,
                    'failure_rate': circuit.total_failures / max(circuit.total_calls, 1),
                    'is_healthy': circuit.state == CircuitState.CLOSED and circuit.failure_count < 3
                }
                for plugin_id, circuit in self.circuits.items()
            }
    
    def force_reset(self, plugin_id: str):
        """Força reset de um circuit (debug/admin)"""
        circuit = self.get_or_create_circuit(plugin_id)
        with self._lock:
            circuit.state = CircuitState.CLOSED
            circuit.failure_count = 0
            circuit.opened_at = None
            self._save_stats()
            print(f"🔄 Circuit do plugin '{plugin_id}' resetado manualmente")

# Instância global do manager
_circuit_manager = CircuitBreakerManager()

def circuit_breaker(max_failures: int = 5, timeout_seconds: int = 300):
    """
    Decorator de Circuit Breaker para plugins
    
    Args:
        max_failures: Número de falhas consecutivas antes de abrir
        timeout_seconds: Tempo em segundos antes de tentar recovery
    
    Usage:
        @circuit_breaker(max_failures=5, timeout_seconds=300)
        def analyze(self, document, config, context):
            # Plugin que pode falhar
            return result
    """
    def decorator(func: Callable) -> Callable:
        plugin_id = getattr(func, '__self__', {}).get('meta', lambda: type('', (), {'id': 'unknown'}))().id
        if plugin_id == 'unknown':
            # Tenta inferir do contexto
            plugin_id = func.__qualname__.split('.')[0] if '.' in func.__qualname__ else func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Verifica se pode executar
            if not _circuit_manager.should_allow_call(plugin_id, timeout_seconds):
                circuit = _circuit_manager.get_or_create_circuit(plugin_id)
                raise Exception(
                    f"Plugin '{plugin_id}' temporariamente desabilitado "
                    f"(circuit breaker open - {circuit.failure_count} falhas)"
                )
            
            try:
                # Executa função original
                result = func(*args, **kwargs)
                
                # Registra sucesso
                _circuit_manager.record_success(plugin_id)
                
                return result
                
            except Exception as e:
                # Registra falha
                _circuit_manager.record_failure(plugin_id, max_failures)
                
                # Re-raise para não quebrar o fluxo
                raise
        
        return wrapper
    return decorator

def get_circuit_stats() -> Dict[str, Dict[str, Any]]:
    """Função pública para obter estatísticas dos circuits"""
    return _circuit_manager.get_stats()

def reset_circuit(plugin_id: str):
    """Função pública para resetar circuit específico"""
    _circuit_manager.force_reset(plugin_id)

def get_healthy_plugins() -> list[str]:
    """Retorna lista de plugins saudáveis (circuit fechado)"""
    stats = _circuit_manager.get_stats()
    return [
        plugin_id for plugin_id, data in stats.items()
        if data['is_healthy']
    ]

def get_disabled_plugins() -> list[str]:
    """Retorna lista de plugins desabilitados (circuit aberto)"""
    stats = _circuit_manager.get_stats()
    return [
        plugin_id for plugin_id, data in stats.items()
        if data['state'] == 'open'
    ]

# Exemplo de uso e teste
if __name__ == "__main__":
    # Teste do circuit breaker
    
    @circuit_breaker(max_failures=3, timeout_seconds=10)
    def plugin_que_falha():
        import random
        if random.random() < 0.7:  # 70% chance de falha
            raise Exception("Plugin falhou!")
        return "Sucesso!"
    
    # Simula várias execuções
    for i in range(10):
        try:
            result = plugin_que_falha()
            print(f"Tentativa {i+1}: {result}")
        except Exception as e:
            print(f"Tentativa {i+1}: {e}")
        
        time.sleep(1)
    
    # Mostra estatísticas
    print("\n📊 Estatísticas dos Circuits:")
    stats = get_circuit_stats()
    for plugin_id, data in stats.items():
        print(f"  {plugin_id}: {data['state']} ({data['total_successes']}/{data['total_calls']} sucessos)")