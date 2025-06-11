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