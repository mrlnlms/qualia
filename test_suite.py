#!/usr/bin/env python3
"""
test_suite.py - Suite de testes automatizados para Qualia

Executa testes em todas as combinações de plugins e parâmetros
para identificar problemas escondidos.
"""

import subprocess
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

console = Console()


class QualiaTestSuite:
    """Suite completa de testes para o Qualia"""
    
    def __init__(self):
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
        self.test_dir = Path("test_suite_output")
        self.test_dir.mkdir(exist_ok=True)
        
        # Arquivo de teste padrão
        self.test_file = self.test_dir / "test_document.txt"
        self._create_test_file()
        
        # Configurações de teste para cada plugin
        self.test_configs = {
            "word_frequency": [
                {},  # Defaults
                {"min_word_length": "2"},
                {"min_word_length": "5", "remove_stopwords": "false"},
                {"language": "english"},
                {"language": "portuguese", "min_word_length": "4"}
            ],
            "teams_cleaner": [
                {},
                {"remove_timestamps": "true"},
                {"merge_consecutive": "false"},
                {"remove_timestamps": "true", "merge_consecutive": "false"}
            ],
            "wordcloud_viz": [
                {"output_format": "png"},
                {"output_format": "svg"},  # Teste específico para SVG!
                {"output_format": "html"},
                {"colormap": "plasma", "background_color": "black"},
                {"colormap": "viridis", "max_words": "50"},
                {"width": "1024", "height": "768", "colormap": "inferno"}
            ],
            "frequency_chart": [
                {"chart_type": "bar"},
                {"chart_type": "horizontal_bar"},
                {"chart_type": "pie"},
                {"chart_type": "treemap"},
                {"chart_type": "sunburst"},
                {"chart_type": "bar", "top_n": "10"},
                {"chart_type": "treemap", "top_n": "15", "output_format": "html"}
            ]
        }
    
    def _create_test_file(self):
        """Cria arquivo de teste com conteúdo variado"""
        content = """
        Este é um documento de teste para o Qualia Framework.
        Contém várias palavras repetidas para testar análise de frequência.
        
        Teste teste teste. Análise análise. Framework framework framework.
        
        Também tem alguns parágrafos diferentes para verificar a variedade.
        O processamento de texto deve funcionar corretamente em todos os casos.
        
        Palavras únicas: xylofone, quântico, paradigma, sinestesia.
        Números também: 123, 456, 789.
        
        E caracteres especiais: @#$%, &*(), []{}
        
        Fim do documento de teste. Teste teste teste.
        """
        
        self.test_file.write_text(content, encoding='utf-8')
    
    def run_all_tests(self):
        """Executa todos os testes"""
        console.print(Panel.fit(
            "[bold cyan]🧪 QUALIA TEST SUITE[/bold cyan]\n"
            "Testando todas as combinações de plugins e parâmetros",
            border_style="cyan"
        ))
        
        start_time = datetime.now()
        
        # 1. Testes de comandos básicos
        self._test_basic_commands()
        
        # 2. Testes de análise
        self._test_analyzers()
        
        # 3. Testes de processamento
        self._test_processors()
        
        # 4. Testes de visualização
        self._test_visualizers()
        
        # 5. Testes de pipeline
        self._test_pipelines()
        
        # 6. Testes de casos extremos
        self._test_edge_cases()
        
        # Relatório final
        duration = datetime.now() - start_time
        self._show_report(duration)
    
    def _run_command(self, args: List[str], test_name: str) -> Tuple[bool, str, str]:
        """Executa um comando e registra o resultado"""
        cmd = ["python", "-m", "qualia"] + args
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # Timeout de 30 segundos
            )
            
            success = result.returncode == 0
            
            if success:
                self.results["passed"].append({
                    "test": test_name,
                    "command": " ".join(args),
                    "output": result.stdout[:200]  # Primeiros 200 chars
                })
            else:
                self.results["failed"].append({
                    "test": test_name,
                    "command": " ".join(args),
                    "error": result.stderr,
                    "stdout": result.stdout
                })
            
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            self.results["failed"].append({
                "test": test_name,
                "command": " ".join(args),
                "error": "Timeout após 30 segundos"
            })
            return False, "", "Timeout"
        except Exception as e:
            self.results["failed"].append({
                "test": test_name,
                "command": " ".join(args),
                "error": str(e)
            })
            return False, "", str(e)
    
    def _test_basic_commands(self):
        """Testa comandos básicos"""
        console.print("\n[bold]1. Testando comandos básicos...[/bold]")
        
        tests = [
            (["--version"], "Versão"),
            (["--help"], "Help"),
            (["list"], "Listar plugins"),
            (["list", "-t", "analyzer"], "Listar analyzers"),
            (["list", "-t", "visualizer"], "Listar visualizers"),
            (["list", "-d"], "Listar detalhado"),
            (["inspect", "word_frequency"], "Inspecionar plugin"),
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Testando comandos...", total=len(tests))
            
            for args, name in tests:
                success, _, _ = self._run_command(args, f"Comando básico: {name}")
                progress.update(task, advance=1, description=f"{'✓' if success else '✗'} {name}")
    
    def _test_analyzers(self):
        """Testa todos os analyzers com diferentes configurações"""
        console.print("\n[bold]2. Testando analyzers...[/bold]")
        
        # Primeiro, obter lista de analyzers
        success, output, _ = self._run_command(["list", "-t", "analyzer"], "Listar analyzers")
        
        if not success:
            console.print("[red]Erro ao listar analyzers![/red]")
            return
        
        # Por enquanto, vamos testar o que sabemos que existe
        analyzers = ["word_frequency"]
        
        total_tests = sum(len(self.test_configs.get(a, [{}])) for a in analyzers)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Testando analyzers...", total=total_tests)
            
            for analyzer in analyzers:
                configs = self.test_configs.get(analyzer, [{}])
                
                for i, config in enumerate(configs):
                    output_file = self.test_dir / f"{analyzer}_test_{i}.json"
                    
                    args = ["analyze", str(self.test_file), "-p", analyzer, "-o", str(output_file)]
                    
                    # Adicionar parâmetros
                    for key, value in config.items():
                        args.extend(["-P", f"{key}={value}"])
                    
                    test_name = f"{analyzer} config {i+1}/{len(configs)}"
                    success, _, _ = self._run_command(args, test_name)
                    
                    progress.update(
                        task, 
                        advance=1, 
                        description=f"{'✓' if success else '✗'} {test_name}"
                    )
                    
                    # Verificar se o arquivo foi criado
                    if success and not output_file.exists():
                        self.results["warnings"].append({
                            "test": test_name,
                            "warning": "Comando sucesso mas arquivo não criado"
                        })
    
    def _test_processors(self):
        """Testa processadores de documento"""
        console.print("\n[bold]3. Testando processadores...[/bold]")
        
        processors = ["teams_cleaner"]
        
        for processor in processors:
            if processor not in self.test_configs:
                continue
                
            configs = self.test_configs[processor]
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"Testando {processor}...", total=len(configs))
                
                for i, config in enumerate(configs):
                    output_file = self.test_dir / f"{processor}_output_{i}.txt"
                    
                    args = ["process", str(self.test_file), "-p", processor, "--save-as", str(output_file)]
                    
                    for key, value in config.items():
                        args.extend(["-P", f"{key}={value}"])
                    
                    test_name = f"{processor} config {i+1}"
                    success, _, _ = self._run_command(args, test_name)
                    
                    progress.update(task, advance=1, description=f"{'✓' if success else '✗'} {test_name}")
    
    def _test_visualizers(self):
        """Testa visualizadores - AQUI VAMOS PEGAR O BUG DO SVG!"""
        console.print("\n[bold]4. Testando visualizadores...[/bold]")
        
        # Primeiro, criar um arquivo de dados para visualizar
        test_data = {
            "word_frequencies": {
                "teste": 10,
                "qualia": 8,
                "framework": 6,
                "análise": 5,
                "documento": 4,
                "palavra": 3,
                "texto": 3,
                "processamento": 2,
                "python": 2,
                "código": 1
            },
            "vocabulary_size": 50,
            "total_words": 100
        }
        
        data_file = self.test_dir / "test_data.json"
        with open(data_file, 'w') as f:
            json.dump(test_data, f)
        
        visualizers = ["wordcloud_viz", "frequency_chart"]
        
        for visualizer in visualizers:
            if visualizer not in self.test_configs:
                continue
            
            configs = self.test_configs[visualizer]
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"Testando {visualizer}...", total=len(configs))
                
                for i, config in enumerate(configs):
                    # Determinar extensão baseada no formato
                    format_map = {
                        "png": ".png",
                        "svg": ".svg",
                        "html": ".html"
                    }
                    
                    # Detectar formato do config ou usar padrão
                    output_format = config.get("output_format", "png")
                    ext = format_map.get(output_format, ".png")
                    
                    output_file = self.test_dir / f"{visualizer}_test_{i}{ext}"
                    
                    args = ["visualize", str(data_file), "-p", visualizer, "-o", str(output_file)]
                    
                    # Adicionar parâmetros (exceto output_format que vai na extensão)
                    for key, value in config.items():
                        if key != "output_format":
                            args.extend(["-P", f"{key}={value}"])
                    
                    test_name = f"{visualizer} {output_format} config {i+1}"
                    success, stdout, stderr = self._run_command(args, test_name)
                    
                    # Verificação especial para SVG
                    if not success and "svg" in test_name.lower():
                        console.print(f"\n[red]⚠️  BUG DO SVG ENCONTRADO![/red]")
                        console.print(f"Erro: {stderr[:200]}")
                    
                    progress.update(task, advance=1, description=f"{'✓' if success else '✗'} {test_name}")
                    
                    # Verificar tamanho do arquivo gerado
                    if success and output_file.exists():
                        size = output_file.stat().st_size
                        if size < 100:  # Arquivo muito pequeno, provavelmente erro
                            self.results["warnings"].append({
                                "test": test_name,
                                "warning": f"Arquivo gerado muito pequeno ({size} bytes)"
                            })
    
    def _test_pipelines(self):
        """Testa execução de pipelines"""
        console.print("\n[bold]5. Testando pipelines...[/bold]")
        
        # Criar um pipeline de teste
        pipeline_config = {
            "name": "test_pipeline",
            "description": "Pipeline de teste automatizado",
            "steps": [
                {
                    "plugin": "word_frequency",
                    "config": {"min_word_length": 3},
                    "output": "step1_frequencies.json"
                },
                {
                    "plugin": "wordcloud_viz",
                    "config": {"colormap": "viridis"},
                    "output": "step2_cloud.png"
                }
            ]
        }
        
        pipeline_file = self.test_dir / "test_pipeline.yaml"
        import yaml
        with open(pipeline_file, 'w') as f:
            yaml.dump(pipeline_config, f)
        
        # Executar pipeline
        output_dir = self.test_dir / "pipeline_output"
        args = ["pipeline", str(self.test_file), "-c", str(pipeline_file), "-o", str(output_dir)]
        
        success, _, _ = self._run_command(args, "Pipeline teste")
        
        if success:
            console.print("✓ Pipeline executado com sucesso")
        else:
            console.print("✗ Erro ao executar pipeline")
    
    def _test_edge_cases(self):
        """Testa casos extremos e entradas inválidas"""
        console.print("\n[bold]6. Testando casos extremos...[/bold]")
        
        # Arquivo vazio
        empty_file = self.test_dir / "empty.txt"
        empty_file.write_text("")
        
        # Arquivo com caracteres especiais
        special_file = self.test_dir / "special.txt"
        special_file.write_text("@#$%^&*()_+ 测试 тест δοκιμή")
        
        # Arquivo grande
        large_file = self.test_dir / "large.txt"
        large_file.write_text("palavra " * 10000)
        
        edge_cases = [
            # Arquivo vazio
            (["analyze", str(empty_file), "-p", "word_frequency", "-o", "empty_result.json"], 
             "Arquivo vazio"),
            
            # Arquivo inexistente
            (["analyze", "arquivo_que_nao_existe.txt", "-p", "word_frequency"], 
             "Arquivo inexistente"),
            
            # Plugin inexistente
            (["analyze", str(self.test_file), "-p", "plugin_falso"], 
             "Plugin inexistente"),
            
            # Parâmetros inválidos
            (["analyze", str(self.test_file), "-p", "word_frequency", "-P", "parametro_falso=valor"], 
             "Parâmetro inválido"),
            
            # Arquivo com caracteres especiais
            (["analyze", str(special_file), "-p", "word_frequency", "-o", "special_result.json"], 
             "Caracteres especiais"),
            
            # Arquivo grande
            (["analyze", str(large_file), "-p", "word_frequency", "-o", "large_result.json"], 
             "Arquivo grande"),
            
            # Output em diretório inexistente
            (["analyze", str(self.test_file), "-p", "word_frequency", "-o", "/diretorio/inexistente/output.json"], 
             "Diretório inexistente"),
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Testando casos extremos...", total=len(edge_cases))
            
            for args, name in edge_cases:
                # Para casos extremos, esperamos alguns erros
                success, _, _ = self._run_command(args, f"Caso extremo: {name}")
                progress.update(task, advance=1, description=f"{'✓' if success else '✗'} {name}")
    
    def _show_report(self, duration):
        """Mostra relatório final dos testes"""
        console.print("\n" + "="*60)
        console.print(Panel.fit(
            "[bold]📊 RELATÓRIO FINAL[/bold]",
            border_style="blue"
        ))
        
        # Estatísticas
        total = len(self.results["passed"]) + len(self.results["failed"])
        passed = len(self.results["passed"])
        failed = len(self.results["failed"])
        warnings = len(self.results["warnings"])
        
        # Tabela de resumo
        table = Table(title="Resumo dos Testes", box=None)
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right")
        
        table.add_row("Total de testes", str(total))
        table.add_row("✅ Passou", f"[green]{passed}[/green]")
        table.add_row("❌ Falhou", f"[red]{failed}[/red]")
        table.add_row("⚠️  Avisos", f"[yellow]{warnings}[/yellow]")
        table.add_row("Taxa de sucesso", f"{(passed/total*100):.1f}%" if total > 0 else "0%")
        table.add_row("Tempo total", f"{duration.total_seconds():.1f}s")
        
        console.print(table)
        
        # Detalhes dos erros
        if self.results["failed"]:
            console.print("\n[bold red]❌ TESTES QUE FALHARAM:[/bold red]")
            for i, failure in enumerate(self.results["failed"], 1):
                console.print(f"\n{i}. [red]{failure['test']}[/red]")
                console.print(f"   Comando: {failure['command']}")
                console.print(f"   Erro: {failure['error'][:200]}")
        
        # Avisos
        if self.results["warnings"]:
            console.print("\n[bold yellow]⚠️  AVISOS:[/bold yellow]")
            for warning in self.results["warnings"]:
                console.print(f"- {warning['test']}: {warning['warning']}")
        
        # Salvar relatório detalhado
        report_file = self.test_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "duration": str(duration),
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "warnings": warnings
                },
                "results": self.results
            }, f, indent=2)
        
        console.print(f"\n[dim]Relatório detalhado salvo em: {report_file}[/dim]")
        
        # Recomendações
        if failed > 0:
            console.print("\n[bold]🔧 RECOMENDAÇÕES:[/bold]")
            
            # Analisar padrões nos erros
            svg_errors = [f for f in self.results["failed"] if "svg" in f["test"].lower()]
            if svg_errors:
                console.print("- [yellow]Problema com geração de SVG detectado[/yellow]")
                console.print("  Verifique as dependências do matplotlib/wordcloud para SVG")
            
            timeout_errors = [f for f in self.results["failed"] if "Timeout" in f.get("error", "")]
            if timeout_errors:
                console.print("- [yellow]Alguns testes excederam o timeout[/yellow]")
                console.print("  Considere otimizar performance ou aumentar timeout")


def main():
    """Executa a suite de testes"""
    console.print("[bold cyan]Iniciando Qualia Test Suite...[/bold cyan]")
    
    # Verificar se estamos no diretório correto
    if not Path("qualia").exists():
        console.print("[red]Erro: Execute este script do diretório raiz do projeto![/red]")
        return 1
    
    try:
        suite = QualiaTestSuite()
        suite.run_all_tests()
        
        # Retornar código de saída baseado nos resultados
        if suite.results["failed"]:
            return 1
        else:
            return 0
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Testes interrompidos pelo usuário[/yellow]")
        return 2
    except Exception as e:
        console.print(f"\n[red]Erro fatal: {e}[/red]")
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    sys.exit(main())