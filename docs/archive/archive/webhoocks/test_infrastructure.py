#!/usr/bin/env python3
"""
Test Infrastructure - Verifica todos os componentes de infra.

Testa:
1. Docker build
2. Webhooks funcionando
3. Monitor mostrando atividade
4. Deploy completo

Coloque este arquivo na RAIZ do projeto!
"""

import subprocess
import requests
import time
import json
import sys
from pathlib import Path

# Try to import Rich (optional but nice to have)
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.panel import Panel
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    # Simple console fallback
    class Console:
        def print(self, *args, **kwargs):
            # Remove rich markup
            text = str(args[0]) if args else ""
            text = text.replace("[blue]", "").replace("[/blue]", "")
            text = text.replace("[green]", "").replace("[/green]", "")
            text = text.replace("[red]", "").replace("[/red]", "")
            text = text.replace("[yellow]", "").replace("[/yellow]", "")
            text = text.replace("[bold]", "").replace("[/bold]", "")
            text = text.replace("[dim]", "").replace("[/dim]", "")
            print(text)
    console = Console()

class InfrastructureTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = []
        
    def run_test(self, name, test_func):
        """Execute a test and track results."""
        try:
            console.print(f"\n[blue]▶ {name}[/blue]")
            test_func()
            self.results.append((name, "✅ PASS", ""))
            console.print(f"[green]✅ {name} - PASS[/green]")
        except Exception as e:
            self.results.append((name, "❌ FAIL", str(e)))
            console.print(f"[red]❌ {name} - FAIL: {e}[/red]")
    
    def test_docker_build(self):
        """Test Docker build."""
        console.print("Building Docker image...")
        
        result = subprocess.run(
            ["docker", "build", "-t", "qualia-core:test", "."],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Docker build failed: {result.stderr}")
        
        console.print("[green]Docker image built successfully![/green]")
    
    def test_docker_compose(self):
        """Test Docker Compose."""
        console.print("Starting services with docker-compose...")
        
        # Start services
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"docker-compose up failed: {result.stderr}")
        
        # Wait for services to be ready
        console.print("Waiting for services to start...")
        time.sleep(10)
        
        # Check health
        response = requests.get(f"{self.base_url}/health", timeout=5)
        if response.status_code != 200:
            raise Exception(f"Health check failed: {response.status_code}")
        
        console.print("[green]Services are running![/green]")
    
    def test_api_endpoints(self):
        """Test basic API endpoints."""
        endpoints = [
            ("/", "API info"),
            ("/health", "Health check"),
            ("/plugins", "List plugins"),
            ("/webhook/stats", "Webhook stats"),
            ("/monitor/", "Monitor dashboard")
        ]
        
        for endpoint, description in endpoints:
            response = requests.get(f"{self.base_url}{endpoint}")
            if response.status_code != 200:
                raise Exception(f"{endpoint} returned {response.status_code}")
            console.print(f"  ✓ {description}")
    
    def test_webhook_github(self):
        """Test GitHub webhook."""
        console.print("Testing GitHub webhook...")
        
        # Test payload
        payload = {
            "action": "opened",
            "pull_request": {
                "title": "Test PR for infrastructure",
                "body": "This is a test pull request to verify webhook functionality."
            }
        }
        
        response = requests.post(
            f"{self.base_url}/webhook/github",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Webhook failed: {response.text}")
        
        data = response.json()
        if data.get("status") != "success":
            raise Exception("Webhook didn't return success")
        
        console.print(f"  Plugin used: {data.get('plugin_used')}")
        console.print(f"  Result: {json.dumps(data.get('result', {}), indent=2)[:200]}...")
    
    def test_webhook_custom(self):
        """Test custom webhook."""
        console.print("Testing custom webhook...")
        
        payload = {
            "text": "Testing infrastructure deployment. Everything looks great!",
            "plugin": "sentiment_analyzer"
        }
        
        response = requests.post(
            f"{self.base_url}/webhook/custom",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Custom webhook failed: {response.text}")
        
        data = response.json()
        console.print(f"  Sentiment: {data.get('result', {}).get('sentiment', {})}")
    
    def test_monitor_stream(self):
        """Test monitor SSE stream."""
        console.print("Testing monitor stream...")
        
        # Make some requests to generate activity
        for i in range(5):
            requests.get(f"{self.base_url}/plugins")
            time.sleep(0.1)
        
        # Check monitor stream
        response = requests.get(
            f"{self.base_url}/monitor/stream",
            stream=True,
            timeout=5
        )
        
        # Read first event
        for line in response.iter_lines():
            if line and line.startswith(b'data:'):
                data = json.loads(line[6:])
                metrics = data.get('metrics', {})
                console.print(f"  Total requests: {metrics.get('requests_total')}")
                console.print(f"  Requests/min: {metrics.get('requests_per_minute')}")
                break
        
        response.close()
    
    def test_file_analysis(self):
        """Test file upload and analysis."""
        console.print("Testing file analysis...")
        
        # Create test file
        test_content = "This is amazing! The infrastructure deployment is working perfectly."
        
        files = {
            'file': ('test.txt', test_content, 'text/plain')
        }
        
        data = {
            'config': '{}',
            'context': '{}'
        }
        
        response = requests.post(
            f"{self.base_url}/analyze/sentiment_analyzer/file",
            files=files,
            data=data
        )
        
        if response.status_code != 200:
            raise Exception(f"File analysis failed: {response.text}")
        
        result = response.json()
        console.print(f"  Sentiment: {result.get('result', {}).get('sentiment', {})}")
    
    def test_pipeline(self):
        """Test pipeline execution."""
        console.print("Testing pipeline...")
        
        payload = {
            "text": "[00:00:00] Speaker: The deployment process is fantastic and efficient!",
            "steps": [
                {"plugin_id": "teams_cleaner", "config": {}},
                {"plugin_id": "sentiment_analyzer", "config": {}}
            ]
        }
        
        response = requests.post(
            f"{self.base_url}/pipeline",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Pipeline failed: {response.text}")
        
        result = response.json()
        console.print(f"  Steps executed: {result.get('steps_executed')}")
    
    def cleanup(self):
        """Clean up Docker resources."""
        console.print("\n[yellow]Cleaning up...[/yellow]")
        
        result = subprocess.run(
            ["docker-compose", "down"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            console.print("[green]Cleanup complete![/green]")
    
    def show_results(self):
        """Display test results."""
        console.print("\n" + "="*60)
        
        if HAS_RICH:
            table = Table(title="Infrastructure Test Results")
            table.add_column("Test", style="cyan")
            table.add_column("Status", style="white")
            table.add_column("Details", style="dim")
            
            for name, status, details in self.results:
                table.add_row(name, status, details[:50] + "..." if len(details) > 50 else details)
            
            console.print(table)
        else:
            console.print("Infrastructure Test Results")
            console.print("-" * 60)
            for name, status, details in self.results:
                console.print(f"{name:<30} {status:<10} {details}")
        
        # Summary
        passed = sum(1 for _, status, _ in self.results if "PASS" in status)
        total = len(self.results)
        
        if passed == total:
            console.print(f"\n[green]✅ All tests passed! ({passed}/{total})[/green]")
        else:
            console.print(f"\n[red]❌ Some tests failed! ({passed}/{total})[/red]")
    
    def run_all_tests(self):
        """Run all infrastructure tests."""
        if HAS_RICH:
            console.print(Panel.fit(
                "[bold blue]Qualia Core Infrastructure Tests[/bold blue]\n"
                "Testing Docker, Webhooks, Monitor, and Deployment",
                border_style="blue"
            ))
        else:
            console.print("\n" + "="*60)
            console.print("Qualia Core Infrastructure Tests")
            console.print("Testing Docker, Webhooks, Monitor, and Deployment")
            console.print("="*60 + "\n")
        
        # Docker tests
        if "--skip-docker" not in sys.argv:
            self.run_test("Docker Build", self.test_docker_build)
            self.run_test("Docker Compose", self.test_docker_compose)
        else:
            console.print("[yellow]Skipping Docker tests (--skip-docker)[/yellow]")
        
        # API tests
        self.run_test("API Endpoints", self.test_api_endpoints)
        
        # Webhook tests
        self.run_test("GitHub Webhook", self.test_webhook_github)
        self.run_test("Custom Webhook", self.test_webhook_custom)
        
        # Monitor test
        self.run_test("Monitor Stream", self.test_monitor_stream)
        
        # Feature tests
        self.run_test("File Analysis", self.test_file_analysis)
        self.run_test("Pipeline Execution", self.test_pipeline)
        
        self.show_results()
        
        if "--no-cleanup" not in sys.argv and "--skip-docker" not in sys.argv:
            self.cleanup()

def main():
    """Main test runner."""
    tester = InfrastructureTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted by user[/yellow]")
        if "--skip-docker" not in sys.argv:
            tester.cleanup()
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        if "--skip-docker" not in sys.argv:
            tester.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    console.print("[dim]Usage: python test_infrastructure.py [--skip-docker] [--no-cleanup][/dim]\n")
    main()