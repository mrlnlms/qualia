"""
Health Dashboard para Qualia Core
Dashboard unificado mostrando saúde de todos os componentes

Features:
- Status de plugins (circuit breaker)
- Métricas do Sentry
- Status da API
- Estatísticas de backup
- Alertas automáticos

Usage:
    python health_dashboard.py --port 8080
    # Acessa http://localhost:8080
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import subprocess
import sys

# Imports condicionais
try:
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

try:
    from ops.monitoring.circuit_breaker import get_circuit_stats, get_healthy_plugins, get_disabled_plugins
    HAS_CIRCUIT_BREAKER = True
except ImportError:
    HAS_CIRCUIT_BREAKER = False

try:
    import sentry_sdk
    HAS_SENTRY = True
except ImportError:
    HAS_SENTRY = False

@dataclass
class ComponentHealth:
    """Status de saúde de um componente"""
    name: str
    status: str  # healthy, warning, critical, unknown
    message: str
    details: Dict[str, Any]
    last_check: float

class HealthChecker:
    """Verificador de saúde dos componentes"""
    
    def __init__(self):
        self.components: Dict[str, ComponentHealth] = {}
        self.alerts: List[Dict[str, Any]] = []
    
    async def check_all(self) -> Dict[str, ComponentHealth]:
        """Verifica saúde de todos os componentes"""
        
        # Limpa componentes antigos
        self.components.clear()
        
        # Verifica cada componente
        await self._check_qualia_core()
        await self._check_plugins()
        await self._check_api()
        await self._check_circuit_breakers()
        await self._check_sentry()
        await self._check_backups()
        await self._check_system_resources()
        
        # Atualiza alertas
        self._update_alerts()
        
        return self.components
    
    async def _check_qualia_core(self):
        """Verifica se o core do Qualia está funcionando"""
        try:
            from qualia.core import QualiaCore
            
            core = QualiaCore()
            plugins = core.discover_plugins()
            
            self.components['qualia_core'] = ComponentHealth(
                name="Qualia Core",
                status="healthy",
                message=f"Core operacional com {len(plugins)} plugins",
                details={
                    "plugins_count": len(plugins),
                    "plugin_types": list(set(p.type.value for p in plugins.values())),
                    "core_version": "0.1.0"
                },
                last_check=time.time()
            )
            
        except Exception as e:
            self.components['qualia_core'] = ComponentHealth(
                name="Qualia Core",
                status="critical",
                message=f"Erro no core: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                last_check=time.time()
            )
    
    async def _check_plugins(self):
        """Verifica status individual dos plugins"""
        try:
            from qualia.core import QualiaCore, Document
            
            core = QualiaCore()
            core.discover_plugins()
            doc = core.add_document("health_check", "Texto de teste para verificação de saúde.")
            
            plugin_status = {}
            total_plugins = len(core.plugins)
            working_plugins = 0
            
            for plugin_id, plugin in core.plugins.items():
                try:
                    # Teste básico do plugin
                    result = core.execute_plugin(plugin_id, doc, {})
                    plugin_status[plugin_id] = {
                        "status": "healthy",
                        "last_result_size": len(str(result)) if result else 0,
                        "type": plugin.meta().type.value
                    }
                    working_plugins += 1
                    
                except Exception as e:
                    plugin_status[plugin_id] = {
                        "status": "error",
                        "error": str(e),
                        "type": plugin.meta().type.value
                    }
            
            # Status geral dos plugins
            if working_plugins == total_plugins:
                status = "healthy"
                message = f"Todos os {total_plugins} plugins funcionando"
            elif working_plugins > total_plugins * 0.8:
                status = "warning"  
                message = f"{working_plugins}/{total_plugins} plugins funcionando"
            else:
                status = "critical"
                message = f"Apenas {working_plugins}/{total_plugins} plugins funcionando"
            
            self.components['plugins'] = ComponentHealth(
                name="Plugins",
                status=status,
                message=message,
                details={
                    "total": total_plugins,
                    "working": working_plugins,
                    "individual_status": plugin_status
                },
                last_check=time.time()
            )
            
        except Exception as e:
            self.components['plugins'] = ComponentHealth(
                name="Plugins",
                status="critical",
                message=f"Erro verificando plugins: {str(e)}",
                details={"error": str(e)},
                last_check=time.time()
            )
    
    async def _check_api(self):
        """Verifica se a API está respondendo"""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                # Testa health endpoint
                response = await client.get("http://localhost:8000/health", timeout=5)
                
                if response.status_code == 200:
                    health_data = response.json()
                    
                    self.components['api'] = ComponentHealth(
                        name="REST API",
                        status="healthy",
                        message="API respondendo normalmente",
                        details={
                            "status_code": response.status_code,
                            "response_time_ms": response.elapsed.total_seconds() * 1000,
                            "plugins_loaded": health_data.get("plugins_loaded", 0),
                            "extensions": health_data.get("extensions", {})
                        },
                        last_check=time.time()
                    )
                else:
                    raise Exception(f"API retornou status {response.status_code}")
                    
        except Exception as e:
            self.components['api'] = ComponentHealth(
                name="REST API", 
                status="critical",
                message=f"API não disponível: {str(e)}",
                details={"error": str(e)},
                last_check=time.time()
            )
    
    async def _check_circuit_breakers(self):
        """Verifica status dos circuit breakers"""
        if not HAS_CIRCUIT_BREAKER:
            self.components['circuit_breakers'] = ComponentHealth(
                name="Circuit Breakers",
                status="unknown",
                message="Módulo circuit_breaker não disponível",
                details={},
                last_check=time.time()
            )
            return
        
        try:
            stats = get_circuit_stats()
            healthy_plugins = get_healthy_plugins()
            disabled_plugins = get_disabled_plugins()
            
            if not stats:
                status = "unknown"
                message = "Nenhum circuit breaker ativo"
            elif len(disabled_plugins) == 0:
                status = "healthy"
                message = f"Todos os {len(healthy_plugins)} plugins saudáveis"
            elif len(disabled_plugins) < len(stats) * 0.2:  # < 20% desabilitados
                status = "warning"
                message = f"{len(disabled_plugins)} plugins desabilitados"
            else:
                status = "critical"
                message = f"Muitos plugins desabilitados: {len(disabled_plugins)}"
            
            self.components['circuit_breakers'] = ComponentHealth(
                name="Circuit Breakers",
                status=status,
                message=message,
                details={
                    "total_circuits": len(stats),
                    "healthy_plugins": healthy_plugins,
                    "disabled_plugins": disabled_plugins,
                    "stats": stats
                },
                last_check=time.time()
            )
            
        except Exception as e:
            self.components['circuit_breakers'] = ComponentHealth(
                name="Circuit Breakers",
                status="critical",
                message=f"Erro verificando circuit breakers: {str(e)}",
                details={"error": str(e)},
                last_check=time.time()
            )
    
    async def _check_sentry(self):
        """Verifica integração com Sentry"""
        if not HAS_SENTRY:
            self.components['sentry'] = ComponentHealth(
                name="Sentry",
                status="unknown",
                message="Sentry SDK não instalado",
                details={},
                last_check=time.time()
            )
            return
        
        try:
            # Novo modo (2.x) - evita warning de deprecação
            if hasattr(sentry_sdk, 'get_current_scope'):
                scope = sentry_sdk.get_current_scope()
                client = sentry_sdk.get_client()
            else:
                # Fallback para versões antigas
                hub = sentry_sdk.Hub.current
                client = hub.client
            
            if client and client.dsn:
                # Testa envio básico
                with sentry_sdk.push_scope() as scope:
                    scope.set_tag("health_check", True)
                    sentry_sdk.capture_message("Health check test", level="info")
                
                self.components['sentry'] = ComponentHealth(
                    name="Sentry",
                    status="healthy",
                    message="Sentry ativo e enviando eventos",
                    details={
                        "dsn": str(client.dsn)[:30] + "...",
                        "environment": client.options.get("environment", "unknown"),
                        "release": client.options.get("release", "unknown")
                    },
                    last_check=time.time()
                )
            else:
                self.components['sentry'] = ComponentHealth(
                    name="Sentry",
                    status="warning",
                    message="Sentry não configurado (DSN ausente)",
                    details={},
                    last_check=time.time()
                )
                
        except Exception as e:
            self.components['sentry'] = ComponentHealth(
                name="Sentry",
                status="critical",
                message=f"Erro no Sentry: {str(e)}",
                details={"error": str(e)},
                last_check=time.time()
            )
    
    async def _check_backups(self):
        """Verifica status dos backups"""
        try:
            backup_dir = Path("./backups")
            backup_script = Path("./scripts/backup.sh")
            
            if not backup_script.exists():
                self.components['backups'] = ComponentHealth(
                    name="Backups",
                    status="warning",
                    message="Script de backup não encontrado",
                    details={"script_path": str(backup_script)},
                    last_check=time.time()
                )
                return
            
            # Lista backups existentes
            backups = []
            if backup_dir.exists():
                for backup_file in backup_dir.glob("qualia_backup_*.tar.gz"):
                    stat = backup_file.stat()
                    backups.append({
                        "name": backup_file.name,
                        "size_mb": stat.st_size / (1024 * 1024),
                        "created": stat.st_mtime,
                        "age_days": (time.time() - stat.st_mtime) / 86400
                    })
            
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            # Avalia status
            if not backups:
                status = "warning"
                message = "Nenhum backup encontrado"
            elif backups[0]['age_days'] > 7:  # Backup mais recente > 7 dias
                status = "warning"
                message = f"Último backup há {backups[0]['age_days']:.1f} dias"
            else:
                status = "healthy"
                message = f"{len(backups)} backups disponíveis"
            
            self.components['backups'] = ComponentHealth(
                name="Backups",
                status=status,
                message=message,
                details={
                    "backup_count": len(backups),
                    "backups": backups[:5],  # Últimos 5
                    "script_exists": True,
                    "backup_dir": str(backup_dir)
                },
                last_check=time.time()
            )
            
        except Exception as e:
            self.components['backups'] = ComponentHealth(
                name="Backups",
                status="critical",
                message=f"Erro verificando backups: {str(e)}",
                details={"error": str(e)},
                last_check=time.time()
            )
    
    async def _check_system_resources(self):
        """Verifica recursos do sistema"""
        try:
            import psutil
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memória
            memory = psutil.virtual_memory()
            
            # Disco
            disk = psutil.disk_usage('.')
            
            # Avalia status geral
            issues = []
            if cpu_percent > 80:
                issues.append(f"CPU alta: {cpu_percent:.1f}%")
            if memory.percent > 85:
                issues.append(f"Memória alta: {memory.percent:.1f}%")
            if disk.percent > 90:
                issues.append(f"Disco cheio: {disk.percent:.1f}%")
            
            if not issues:
                status = "healthy"
                message = "Recursos do sistema OK"
            elif len(issues) == 1:
                status = "warning"
                message = issues[0]
            else:
                status = "critical"
                message = f"{len(issues)} problemas: " + ", ".join(issues)
            
            self.components['system'] = ComponentHealth(
                name="Sistema",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3)
                },
                last_check=time.time()
            )
            
        except ImportError:
            self.components['system'] = ComponentHealth(
                name="Sistema",
                status="unknown",
                message="psutil não instalado - recursos não monitorados",
                details={},
                last_check=time.time()
            )
        except Exception as e:
            self.components['system'] = ComponentHealth(
                name="Sistema",
                status="critical",
                message=f"Erro verificando sistema: {str(e)}",
                details={"error": str(e)},
                last_check=time.time()
            )
    
    def _update_alerts(self):
        """Atualiza lista de alertas baseado no status dos componentes"""
        self.alerts.clear()
        
        for component in self.components.values():
            if component.status in ['warning', 'critical']:
                self.alerts.append({
                    "component": component.name,
                    "status": component.status,
                    "message": component.message,
                    "timestamp": component.last_check,
                    "severity": "high" if component.status == "critical" else "medium"
                })
    
    def get_overall_status(self) -> str:
        """Retorna status geral do sistema"""
        if not self.components:
            return "unknown"
        
        statuses = [comp.status for comp in self.components.values()]
        
        if "critical" in statuses:
            return "critical"
        elif "warning" in statuses:
            return "warning"
        elif all(status == "healthy" for status in statuses):
            return "healthy"
        else:
            return "unknown"

# FastAPI app (se disponível)
if HAS_FASTAPI:
    app = FastAPI(title="Qualia Health Dashboard", version="1.0.0")
    checker = HealthChecker()

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        """Dashboard principal"""
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Qualia Health Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { text-align: center; margin-bottom: 30px; }
                .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .component { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .status-healthy { border-left: 4px solid #4CAF50; }
                .status-warning { border-left: 4px solid #FF9800; }
                .status-critical { border-left: 4px solid #F44336; }
                .status-unknown { border-left: 4px solid #9E9E9E; }
                .status-badge { display: inline-block; padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; }
                .badge-healthy { background: #4CAF50; }
                .badge-warning { background: #FF9800; }
                .badge-critical { background: #F44336; }
                .badge-unknown { background: #9E9E9E; }
                .details { margin-top: 10px; font-size: 14px; color: #666; }
                .refresh { margin: 20px 0; text-align: center; }
                .alerts { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
            </style>
            <script>
                async function loadStatus() {
                    try {
                        const response = await fetch('/health');
                        const data = await response.json();
                        updateDashboard(data);
                    } catch (error) {
                        console.error('Erro carregando status:', error);
                    }
                }
                
                function updateDashboard(data) {
                    const container = document.getElementById('status-container');
                    container.innerHTML = '';
                    
                    Object.values(data.components).forEach(component => {
                        const div = document.createElement('div');
                        div.className = `component status-${component.status}`;
                        div.innerHTML = `
                            <h3>${component.name} <span class="status-badge badge-${component.status}">${component.status.toUpperCase()}</span></h3>
                            <p>${component.message}</p>
                            <div class="details">
                                <small>Verificado: ${new Date(component.last_check * 1000).toLocaleString()}</small>
                            </div>
                        `;
                        container.appendChild(div);
                    });
                    
                    // Atualiza título com status geral
                    document.title = `Qualia Health - ${data.overall_status.toUpperCase()}`;
                    
                    // Mostra alertas
                    const alertsDiv = document.getElementById('alerts');
                    if (data.alerts.length > 0) {
                        alertsDiv.style.display = 'block';
                        alertsDiv.innerHTML = '<h3>⚠️ Alertas</h3>' + 
                            data.alerts.map(alert => `<div>• ${alert.component}: ${alert.message}</div>`).join('');
                    } else {
                        alertsDiv.style.display = 'none';
                    }
                }
                
                // Auto-refresh a cada 30 segundos
                setInterval(loadStatus, 30000);
                
                // Carrega na inicialização
                window.onload = loadStatus;
            </script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏥 Qualia Health Dashboard</h1>
                    <p>Monitoramento em tempo real de todos os componentes</p>
                </div>
                
                <div id="alerts" class="alerts" style="display: none;"></div>
                
                <div class="refresh">
                    <button onclick="loadStatus()">🔄 Atualizar Agora</button>
                    <small>(Auto-atualiza a cada 30s)</small>
                </div>
                
                <div id="status-container" class="status-grid">
                    <div class="component">Carregando...</div>
                </div>
            </div>
        </body>
        </html>
        """)

    @app.get("/health")
    async def health_api():
        """API de status de saúde"""
        components = await checker.check_all()
        
        return {
            "overall_status": checker.get_overall_status(),
            "timestamp": time.time(),
            "components": {name: asdict(comp) for name, comp in components.items()},
            "alerts": checker.alerts,
            "summary": {
                "total_components": len(components),
                "healthy": len([c for c in components.values() if c.status == "healthy"]),
                "warning": len([c for c in components.values() if c.status == "warning"]), 
                "critical": len([c for c in components.values() if c.status == "critical"]),
                "unknown": len([c for c in components.values() if c.status == "unknown"])
            }
        }

def run_dashboard(port: int = 8080):
    """Roda o dashboard de saúde"""
    if not HAS_FASTAPI:
        print("❌ FastAPI não instalado. Instale com: pip install fastapi uvicorn")
        return
    
    print(f"🏥 Iniciando Health Dashboard na porta {port}")
    print(f"   Dashboard: http://localhost:{port}")
    print(f"   API: http://localhost:{port}/health")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

# CLI para uso standalone
def main():
    """Função principal do CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Qualia Health Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Porta do servidor (padrão: 8080)")
    parser.add_argument("--check-only", action="store_true", help="Apenas verificar saúde e sair")
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    
    args = parser.parse_args()
    
    if args.check_only:
        # Modo verificação apenas
        async def check():
            checker = HealthChecker()
            components = await checker.check_all()
            
            if args.json:
                result = {
                    "overall_status": checker.get_overall_status(),
                    "timestamp": time.time(),
                    "components": {name: asdict(comp) for name, comp in components.items()},
                    "alerts": checker.alerts
                }
                print(json.dumps(result, indent=2))
            else:
                print(f"\n🏥 Status Geral: {checker.get_overall_status().upper()}")
                print(f"📅 Verificado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("\n📊 Componentes:")
                
                for name, comp in components.items():
                    status_emoji = {
                        "healthy": "✅",
                        "warning": "⚠️", 
                        "critical": "❌",
                        "unknown": "❓"
                    }.get(comp.status, "❓")
                    
                    print(f"  {status_emoji} {comp.name}: {comp.message}")
                
                if checker.alerts:
                    print(f"\n🚨 Alertas ({len(checker.alerts)}):")
                    for alert in checker.alerts:
                        severity_emoji = "🔥" if alert["severity"] == "high" else "⚠️"
                        print(f"  {severity_emoji} {alert['component']}: {alert['message']}")
                else:
                    print("\n✨ Nenhum alerta ativo")
        
        asyncio.run(check())
    else:
        # Modo servidor web
        run_dashboard(args.port)

if __name__ == "__main__":
    main()