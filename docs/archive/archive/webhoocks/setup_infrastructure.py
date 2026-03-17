#!/usr/bin/env python3
"""
Setup Infrastructure - Cria todos os arquivos necessários que estão faltando.

Execute este script para configurar a infraestrutura completa.
"""

import os
from pathlib import Path

def create_file(path: Path, content: str):
    """Cria arquivo com conteúdo."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        print(f"⚠️  Arquivo já existe: {path}")
    else:
        path.write_text(content)
        print(f"✅ Criado: {path}")

def restore_run_api():
    """Restaura o run_api.py original na raiz."""
    content = '''#!/usr/bin/env python3
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
'''
    
    path = Path("run_api.py")
    create_file(path, content)

def main():
    print("🔧 Configurando infraestrutura do Qualia Core...\n")
    
    root = Path.cwd()
    api_dir = root / "qualia" / "api"
    
    # 1. Restaurar run_api.py
    print("1️⃣ Restaurando run_api.py na raiz...")
    restore_run_api()
    
    # 2. Criar test_quick_infra.py se não existir
    if not (root / "test_quick_infra.py").exists():
        print("\n2️⃣ Criando test_quick_infra.py...")
        print("   ⚠️  Use o conteúdo do artifact test_quick_infra.py")
    
    # 3. Verificar arquivos da API
    print("\n3️⃣ Verificando arquivos da API...")
    
    required_files = {
        "webhooks.py": "⚠️  FALTANDO! Copie do artifact webhooks_module",
        "monitor.py": "⚠️  FALTANDO! Copie do artifact monitor_module",
        "run.py": "✅ Existe" if (api_dir / "run.py").exists() else "⚠️  FALTANDO! Copie do artifact api_run"
    }
    
    for file, status in required_files.items():
        path = api_dir / file
        if path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   {status}")
    
    # 4. Criar pasta examples se não existir
    examples_dir = api_dir / "examples"
    if not examples_dir.exists():
        examples_dir.mkdir(parents=True)
        print(f"\n4️⃣ Criado diretório: {examples_dir}")
    
    # 5. Verificar arquivos de infraestrutura na raiz
    print("\n5️⃣ Arquivos de infraestrutura (raiz do projeto):")
    
    infra_files = [
        ".env.example",
        "Dockerfile", 
        ".dockerignore",
        "docker-compose.yml",
        "nginx.conf",
        "DEPLOY.md",
        "INFRASTRUCTURE.md"
    ]
    
    for file in infra_files:
        path = root / file
        if path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ⚠️  {file} - FALTANDO! Copie do artifact correspondente")
    
    print("\n" + "="*60)
    print("\n📝 INSTRUÇÕES:\n")
    
    print("1. Para os arquivos FALTANDO, copie o conteúdo dos artifacts:")
    print("   - webhooks.py → copiar de 'webhooks_module'")
    print("   - monitor.py → copiar de 'monitor_module'")
    print("   - Arquivos de infra → copiar dos artifacts correspondentes")
    
    print("\n2. Depois de copiar os arquivos, teste com:")
    print("   python run_api.py --reload")
    
    print("\n3. Em outro terminal, execute:")
    print("   python test_infrastructure.py --skip-docker")
    
    print("\n✨ Boa sorte!")

if __name__ == "__main__":
    main()