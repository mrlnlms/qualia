#!/usr/bin/env python3
"""
Qualia Core - Bateria Completa de Testes
Roda todos os testes do sistema de forma organizada
"""
from __future__ import annotations

import sys
import time
import json
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import psutil
import signal
import os

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class _TestResult:
    """Armazena resultado de um teste"""
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.passed = False
        self.message = ""
        self.duration = 0.0
        self.details = {}

class QualiaTestSuite:
    """Suite completa de testes para Qualia Core"""
    
    def __init__(self):
        self.results: List[_TestResult] = []
        self.api_process = None
        self.dashboard_process = None
        self.start_time = time.time()
        
    def print_header(self):
        """Imprime header bonito"""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}🧪 QUALIA CORE - BATERIA COMPLETA DE TESTES{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🐍 Python: {sys.version.split()[0]}")
        print(f"📁 Diretório: {Path.cwd()}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    def run_test(self, name: str, category: str, test_func):
        """Executa um teste individual"""
        result = _TestResult(name, category)
        start = time.time()
        
        try:
            print(f"🔄 {category} - {name}...", end='', flush=True)
            test_func(result)
            result.passed = True
            result.duration = time.time() - start
            print(f"\r✅ {category} - {name} ({result.duration:.2f}s)")
        except Exception as e:
            result.passed = False
            result.message = str(e)
            result.duration = time.time() - start
            print(f"\r❌ {category} - {name} ({result.duration:.2f}s)")
            print(f"   └─ Erro: {str(e)[:100]}")
        
        self.results.append(result)
        return result.passed
    
    # ========== TESTES DO CORE ==========
    
    def test_core_import(self, result: _TestResult):
        """Testa se o core pode ser importado"""
        from qualia.core import QualiaCore
        result.details['module'] = 'qualia.core'
    
    def test_core_initialization(self, result: _TestResult):
        """Testa inicialização do core"""
        from qualia.core import QualiaCore
        core = QualiaCore()
        result.details['core_type'] = type(core).__name__
    
    def test_plugin_discovery(self, result: _TestResult):
        """Testa descoberta de plugins"""
        from qualia.core import QualiaCore
        core = QualiaCore()
        plugins = core.discover_plugins()
        
        if len(plugins) != 6:
            raise AssertionError(f"Esperado 6 plugins, encontrado {len(plugins)}")
        
        result.details['plugins_found'] = len(plugins)
        result.details['plugin_ids'] = list(plugins.keys())
    
    def test_plugin_loading(self, result: _TestResult):
        """Testa carregamento individual de plugins"""
        from qualia.core import QualiaCore
        core = QualiaCore()
        core.discover_plugins()
        
        required_plugins = [
            'word_frequency', 'sentiment_analyzer', 'teams_cleaner',
            'wordcloud_viz', 'frequency_chart', 'sentiment_viz'
        ]
        
        for plugin_id in required_plugins:
            if plugin_id not in core.registry:
                raise AssertionError(f"Plugin '{plugin_id}' não foi carregado")
        
        result.details['all_plugins_loaded'] = True
    
    def test_document_creation(self, result: _TestResult):
        """Testa criação de documentos"""
        from qualia.core import QualiaCore
        core = QualiaCore()
        
        doc = core.add_document("test_doc", "Este é um texto de teste.")
        if not doc:
            raise AssertionError("Falha ao criar documento")
        
        retrieved = core.get_document("test_doc")
        if not retrieved or retrieved.content != "Este é um texto de teste.":
            raise AssertionError("Documento não foi armazenado corretamente")
        
        result.details['document_id'] = doc.id
    
    def test_simple_analysis(self, result: _TestResult):
        """Testa análise simples com word_frequency"""
        from qualia.core import QualiaCore
        core = QualiaCore()
        core.discover_plugins()
        
        doc = core.add_document("test_analysis", "teste teste palavra")
        result_data = core.execute_plugin("word_frequency", doc)
        
        if 'word_freq' not in result_data:
            raise AssertionError("Análise não retornou 'word_freq'")
        
        if result_data['word_freq'].get('teste') != 2:
            raise AssertionError("Contagem incorreta de palavras")
        
        result.details['analysis_result'] = result_data
    
    # ========== TESTES DA API ==========
    
    def start_api(self):
        """Inicia a API em processo separado"""
        self.api_process = subprocess.Popen(
            [sys.executable, "run_api.py", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)  # Aguarda API iniciar
    
    def stop_api(self):
        """Para a API"""
        if self.api_process:
            self.api_process.terminate()
            self.api_process.wait(timeout=5)
            self.api_process = None
    
    def test_api_health(self, result: _TestResult):
        """Testa endpoint de health da API"""
        response = requests.get("http://localhost:8000/health", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        if data.get('status') != 'healthy':
            raise AssertionError(f"API status: {data.get('status')}")
        
        if data.get('plugins_loaded') != 6:
            raise AssertionError(f"Plugins carregados: {data.get('plugins_loaded')}")
        
        result.details['api_response'] = data
    
    def test_api_plugins_list(self, result: _TestResult):
        """Testa listagem de plugins via API"""
        response = requests.get("http://localhost:8000/plugins", timeout=5)
        response.raise_for_status()
        
        plugins = response.json()
        if len(plugins) != 6:
            raise AssertionError(f"API retornou {len(plugins)} plugins")
        
        result.details['plugin_count'] = len(plugins)
    
    def test_api_analyze(self, result: _TestResult):
        """Testa análise via API"""
        payload = {
            "text": "Este é um teste da API. Teste teste.",
            "config": {}
        }
        
        response = requests.post(
            "http://localhost:8000/analyze/word_frequency",
            json=payload,
            timeout=5
        )
        response.raise_for_status()
        
        data = response.json()
        if 'word_freq' not in data:
            raise AssertionError("Resposta não contém 'word_freq'")
        
        result.details['words_analyzed'] = len(data['word_freq'])
    
    def test_api_pipeline(self, result: _TestResult):
        """Testa pipeline via API"""
        payload = {
            "text": "Texto para análise de pipeline. Muito bom!",
            "steps": [
                {"plugin_id": "word_frequency"},
                {"plugin_id": "sentiment_analyzer"}
            ]
        }
        
        response = requests.post(
            "http://localhost:8000/pipeline",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        if 'word_frequency' not in data['results']:
            raise AssertionError("Pipeline não executou word_frequency")
        
        result.details['pipeline_steps'] = len(data['results'])
    
    # ========== TESTES DO DASHBOARD ==========
    
    def start_dashboard(self):
        """Inicia o dashboard em processo separado"""
        self.dashboard_process = subprocess.Popen(
            [sys.executable, "ops/monitoring/health_dashboard.py", "--port", "8080"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2)  # Aguarda dashboard iniciar
    
    def stop_dashboard(self):
        """Para o dashboard"""
        if self.dashboard_process:
            self.dashboard_process.terminate()
            self.dashboard_process.wait(timeout=5)
            self.dashboard_process = None
    
    def test_dashboard_health(self, result: _TestResult):
        """Testa endpoint de health do dashboard"""
        response = requests.get("http://localhost:8080/health", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        if data.get('overall_status') != 'healthy':
            raise AssertionError(f"Dashboard status: {data.get('overall_status')}")
        
        components = data.get('components', {})
        if not components:
            raise AssertionError("Dashboard não retornou componentes")
        
        result.details['components'] = list(components.keys())
    
    # ========== TESTES DE INFRAESTRUTURA ==========
    
    def test_circuit_breaker_import(self, result: _TestResult):
        """Testa se circuit breaker pode ser importado"""
        try:
            from ops.monitoring.circuit_breaker import circuit_breaker
            result.details['has_circuit_breaker'] = True
        except ImportError:
            # Deve ter fallback
            from qualia.core import circuit_breaker
            result.details['has_circuit_breaker'] = False
            result.details['has_fallback'] = True
    
    def test_backup_script(self, result: _TestResult):
        """Testa se script de backup existe e é executável"""
        backup_script = Path("ops/scripts/backup.sh")
        
        if not backup_script.exists():
            raise AssertionError("Script de backup não encontrado")
        
        # Testa se é executável
        if os.name != 'nt':  # Unix/Linux/Mac
            if not os.access(backup_script, os.X_OK):
                raise AssertionError("Script de backup não é executável")
        
        result.details['backup_script'] = str(backup_script)
    
    def test_docker_files(self, result: _TestResult):
        """Testa se arquivos Docker existem"""
        required_files = ['Dockerfile', 'docker-compose.yml']
        missing = []
        
        for file in required_files:
            if not Path(file).exists():
                missing.append(file)
        
        if missing:
            raise AssertionError(f"Arquivos Docker faltando: {missing}")
        
        result.details['docker_files'] = required_files
    
    # ========== TESTES DE PERFORMANCE ==========
    
    def test_plugin_performance(self, result: _TestResult):
        """Testa performance dos plugins"""
        from qualia.core import QualiaCore
        core = QualiaCore()
        core.discover_plugins()
        
        doc = core.add_document("perf_test", "teste " * 100)  # 100 palavras
        
        # Testa word_frequency
        start = time.time()
        core.execute_plugin("word_frequency", doc)
        wf_time = time.time() - start
        
        if wf_time > 0.5:  # Máximo 500ms
            raise AssertionError(f"word_frequency muito lento: {wf_time:.2f}s")
        
        result.details['word_frequency_time'] = f"{wf_time*1000:.0f}ms"
    
    def test_memory_usage(self, result: _TestResult):
        """Testa uso de memória"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb > 500:  # Máximo 500MB
            raise AssertionError(f"Uso excessivo de memória: {memory_mb:.0f}MB")
        
        result.details['memory_usage'] = f"{memory_mb:.0f}MB"
    
    # ========== EXECUÇÃO PRINCIPAL ==========
    
    def run_all_tests(self):
        """Executa todos os testes"""
        self.print_header()
        
        # Testes do Core
        print(f"\n{Colors.BOLD}1️⃣  TESTES DO CORE{Colors.RESET}")
        print("-" * 40)
        self.run_test("Importar Core", "Core", self.test_core_import)
        self.run_test("Inicializar Core", "Core", self.test_core_initialization)
        self.run_test("Descobrir Plugins", "Core", self.test_plugin_discovery)
        self.run_test("Carregar Plugins", "Core", self.test_plugin_loading)
        self.run_test("Criar Documento", "Core", self.test_document_creation)
        self.run_test("Análise Simples", "Core", self.test_simple_analysis)
        
        # Testes da API
        print(f"\n{Colors.BOLD}2️⃣  TESTES DA API REST{Colors.RESET}")
        print("-" * 40)
        try:
            self.start_api()
            self.run_test("Health Check", "API", self.test_api_health)
            self.run_test("Listar Plugins", "API", self.test_api_plugins_list)
            self.run_test("Análise via API", "API", self.test_api_analyze)
            self.run_test("Pipeline via API", "API", self.test_api_pipeline)
        finally:
            self.stop_api()
        
        # Testes do Dashboard
        print(f"\n{Colors.BOLD}3️⃣  TESTES DO DASHBOARD{Colors.RESET}")
        print("-" * 40)
        try:
            self.start_dashboard()
            self.run_test("Dashboard Health", "Dashboard", self.test_dashboard_health)
        finally:
            self.stop_dashboard()
        
        # Testes de Infraestrutura
        print(f"\n{Colors.BOLD}4️⃣  TESTES DE INFRAESTRUTURA{Colors.RESET}")
        print("-" * 40)
        self.run_test("Circuit Breaker", "Infra", self.test_circuit_breaker_import)
        self.run_test("Script Backup", "Infra", self.test_backup_script)
        self.run_test("Arquivos Docker", "Infra", self.test_docker_files)
        
        # Testes de Performance
        print(f"\n{Colors.BOLD}5️⃣  TESTES DE PERFORMANCE{Colors.RESET}")
        print("-" * 40)
        self.run_test("Performance Plugins", "Perf", self.test_plugin_performance)
        self.run_test("Uso de Memória", "Perf", self.test_memory_usage)
        
        # Relatório Final
        self.print_report()
    
    def print_report(self):
        """Imprime relatório final"""
        total_time = time.time() - self.start_time
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}📊 RELATÓRIO FINAL{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        
        # Resumo
        print(f"\n📈 Resumo:")
        print(f"   • Total de testes: {len(self.results)}")
        print(f"   • {Colors.GREEN}✅ Passou: {passed}{Colors.RESET}")
        print(f"   • {Colors.RED}❌ Falhou: {failed}{Colors.RESET}")
        print(f"   • ⏱️  Tempo total: {total_time:.2f}s")
        
        # Taxa de sucesso
        success_rate = (passed / len(self.results)) * 100 if self.results else 0
        color = Colors.GREEN if success_rate == 100 else Colors.YELLOW if success_rate >= 80 else Colors.RED
        print(f"   • {color}📊 Taxa de sucesso: {success_rate:.1f}%{Colors.RESET}")
        
        # Testes que falharam
        if failed > 0:
            print(f"\n{Colors.RED}❌ Testes que falharam:{Colors.RESET}")
            for r in self.results:
                if not r.passed:
                    print(f"   • {r.category}/{r.name}: {r.message}")
        
        # Estatísticas por categoria
        print(f"\n📊 Por Categoria:")
        categories = {}
        for r in self.results:
            if r.category not in categories:
                categories[r.category] = {'passed': 0, 'failed': 0}
            if r.passed:
                categories[r.category]['passed'] += 1
            else:
                categories[r.category]['failed'] += 1
        
        for cat, stats in categories.items():
            total = stats['passed'] + stats['failed']
            rate = (stats['passed'] / total) * 100 if total > 0 else 0
            print(f"   • {cat}: {stats['passed']}/{total} ({rate:.0f}%)")
        
        # Salvar relatório
        self.save_report()
        
        # Status final
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        if success_rate == 100:
            print(f"{Colors.GREEN}{Colors.BOLD}🎉 TODOS OS TESTES PASSARAM! 🎉{Colors.RESET}")
        elif success_rate >= 80:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  ALGUNS TESTES FALHARAM{Colors.RESET}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ MUITOS TESTES FALHARAM{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
        
        # Exit code
        sys.exit(0 if failed == 0 else 1)
    
    def save_report(self):
        """Salva relatório em arquivo"""
        report_dir = Path("test_reports")
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"test_report_{timestamp}.json"
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total_time': time.time() - self.start_time,
            'summary': {
                'total': len(self.results),
                'passed': sum(1 for r in self.results if r.passed),
                'failed': sum(1 for r in self.results if not r.passed)
            },
            'tests': [
                {
                    'name': r.name,
                    'category': r.category,
                    'passed': r.passed,
                    'duration': r.duration,
                    'message': r.message,
                    'details': r.details
                }
                for r in self.results
            ]
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Relatório salvo em: {report_file}")


if __name__ == "__main__":
    suite = QualiaTestSuite()
    try:
        suite.run_all_tests()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Testes interrompidos pelo usuário{Colors.RESET}")
        suite.stop_api()
        suite.stop_dashboard()
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}❌ Erro fatal: {e}{Colors.RESET}")
        suite.stop_api()
        suite.stop_dashboard()
        sys.exit(1)