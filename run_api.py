#!/usr/bin/env python3
"""
Script para executar a API do Qualia Core

Uso:
    python run_api.py [--host HOST] [--port PORT] [--reload]
"""

import click
import uvicorn
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# =================== SENTRY INTEGRATION ===================
# Apenas 3 linhas adicionadas para monitoramento!
try:
    from ops.monitoring.sentry_config import init_sentry
    init_sentry()  # Inicializa Sentry se configurado
except ImportError:
    pass  # Sentry opcional - sistema funciona sem ele
# ==========================================================

# =================== PROTEÇÃO SIMPLES ===================
# Proteção automática de plugins - não quebra se não existir!
try:
    from qualia.core.auto_protection import add_simple_protection
    print("🛡️ Proteção de plugins habilitada")
except ImportError:
    print("ℹ️ Proteção de plugins não disponível (opcional)")
    def add_simple_protection(core):
        return core  # Fallback - não faz nada
# ========================================================

@click.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=8000, type=int, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
@click.option('--workers', default=1, type=int, help='Number of worker processes')
def run_api(host, port, reload, workers):
    """Run the Qualia Core REST API"""
    
    click.echo(f"""
🚀 Starting Qualia Core API...
    
📍 URL: http://{host}:{port}
📚 Docs: http://{host}:{port}/docs
🔧 OpenAPI: http://{host}:{port}/openapi.json

Press CTRL+C to stop
""")
    
    # Run uvicorn
    uvicorn.run(
        "qualia.api:app",
        host=host,
        port=port,
        reload=reload,
        workers=1 if reload else workers,
        log_level="info"
    )

if __name__ == "__main__":
    run_api()