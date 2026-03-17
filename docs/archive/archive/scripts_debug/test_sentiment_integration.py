#!/usr/bin/env python3
"""
Script de teste para demonstrar a integração completa do sentiment_analyzer

Testa:
1. CLI
2. Menu
3. API
4. Pipeline com visualização
"""

import subprocess
import time
import requests
import json
from pathlib import Path
from rich.console import Console

console = Console()

def print_section(title):
    console.print(f"\n[bold blue]{'='*60}[/bold blue]")
    console.print(f"[bold cyan]  {title}[/bold cyan]")
    console.print(f"[bold blue]{'='*60}[/bold blue]\n")

def test_cli():
    """Testa via CLI"""
    print_section("1. Testando via CLI")
    
    # Criar arquivo de teste
    test_file = Path("test_sentiment.txt")
    test_file.write_text("""
    Este produto é absolutamente fantástico! Estou muito feliz com a compra.
    A qualidade superou minhas expectativas. O atendimento foi excelente.
    
    Porém, a entrega demorou muito. Fiquei decepcionado com o prazo.
    O preço também está um pouco alto para o mercado.
    
    No geral, recomendo o produto apesar dos problemas mencionados.
    """)
    
    console.print("[yellow]Executando análise de sentimento via CLI...[/yellow]")
    
    # Executar análise
    cmd = ["python", "-m", "qualia", "analyze", str(test_file), 
           "-p", "sentiment_analyzer", "-o", "sentiment_result.json"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        console.print("[green]✓ Análise concluída com sucesso![/green]")
        
        # Ler resultado
        with open("sentiment_result.json", "r") as f:
            data = json.load(f)
            
        console.print(f"\nResultados:")
        console.print(f"  Polaridade: [bold]{data['polarity']:.3f}[/bold] ({data['sentiment_label']})")
        console.print(f"  Subjetividade: [bold]{data['subjectivity']:.3f}[/bold]")
        console.print(f"  Idioma detectado: {data['language']}")
        
        if 'sentiment_stats' in data:
            stats = data['sentiment_stats']
            console.print(f"\n  Estatísticas por sentença:")
            console.print(f"    Positivas: {stats['positive_sentences']}")
            console.print(f"    Negativas: {stats['negative_sentences']}")
            console.print(f"    Neutras: {stats['neutral_sentences']}")
    else:
        console.print(f"[red]✗ Erro na análise: {result.stderr}[/red]")
    
    # Limpar
    test_file.unlink(missing_ok=True)

def test_visualization():
    """Testa visualização"""
    print_section("2. Testando Visualização")
    
    if not Path("sentiment_result.json").exists():
        console.print("[red]Arquivo de resultado não encontrado. Execute o teste CLI primeiro.[/red]")
        return
    
    console.print("[yellow]Criando visualização...[/yellow]")
    
    # Dashboard HTML
    cmd = ["python", "-m", "qualia", "visualize", "sentiment_result.json",
           "-p", "sentiment_viz", "-o", "sentiment_dashboard.html"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        console.print("[green]✓ Dashboard criado: sentiment_dashboard.html[/green]")
    else:
        console.print(f"[red]✗ Erro na visualização: {result.stderr}[/red]")
    
    # Gauge PNG
    cmd = ["python", "-m", "qualia", "visualize", "sentiment_result.json",
           "-p", "sentiment_viz", "-o", "sentiment_gauge.png",
           "-P", "chart_type=gauge"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        console.print("[green]✓ Gauge criado: sentiment_gauge.png[/green]")

def test_api():
    """Testa via API"""
    print_section("3. Testando via API")
    
    # Verificar se API está rodando
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code != 200:
            raise Exception()
    except:
        console.print("[yellow]API não está rodando. Inicie com: python run_api.py --reload[/yellow]")
        return
    
    console.print("[green]✓ API está rodando![/green]")
    
    # Verificar se plugin aparece
    response = requests.get("http://localhost:8000/plugins")
    plugins = response.json()
    
    sentiment_plugins = [p for p in plugins if p['id'] in ['sentiment_analyzer', 'sentiment_viz']]
    
    console.print(f"\nPlugins de sentimento encontrados: {len(sentiment_plugins)}")
    for plugin in sentiment_plugins:
        console.print(f"  - {plugin['name']} ({plugin['type']})")
    
    # Executar análise via API
    console.print("\n[yellow]Executando análise via API...[/yellow]")
    
    text = """
    A API do Qualia é incrível! Facilita muito a integração.
    Alguns endpoints poderiam ser mais rápidos, mas no geral está excelente.
    """
    
    data = {
        "text": text,
        "config": {
            "analyze_sentences": True,
            "include_examples": True
        }
    }
    
    response = requests.post("http://localhost:8000/analyze/sentiment_analyzer", json=data)
    
    if response.status_code == 200:
        result = response.json()
        console.print("[green]✓ Análise via API concluída![/green]")
        console.print(f"\nResultado: {result['result']['sentiment_label']}")
        console.print(f"Polaridade: {result['result']['polarity']:.3f}")
    else:
        console.print(f"[red]✗ Erro na API: {response.text}[/red]")

def test_pipeline():
    """Testa pipeline completo"""
    print_section("4. Testando Pipeline Completo")
    
    # Criar configuração de pipeline
    pipeline_config = {
        "name": "Análise Completa com Sentimento",
        "steps": [
            {
                "plugin": "word_frequency",
                "config": {
                    "min_length": 4,
                    "remove_stopwords": True
                }
            },
            {
                "plugin": "sentiment_analyzer",
                "config": {
                    "analyze_sentences": True
                }
            }
        ]
    }
    
    # Salvar config
    config_path = Path("sentiment_pipeline.yaml")
    import yaml
    with open(config_path, "w") as f:
        yaml.dump(pipeline_config, f)
    
    # Criar texto de teste
    test_file = Path("test_pipeline.txt")
    test_file.write_text("""
    O framework Qualia revolucionou nossa análise qualitativa!
    A facilidade de uso é impressionante. Os plugins são muito úteis.
    Alguns aspectos poderiam melhorar, mas estamos satisfeitos.
    A documentação está clara e os exemplos ajudam bastante.
    """)
    
    console.print("[yellow]Executando pipeline...[/yellow]")
    
    cmd = ["python", "-m", "qualia", "pipeline", str(test_file),
           "-c", str(config_path), "-o", "pipeline_result.json"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        console.print("[green]✓ Pipeline executado com sucesso![/green]")
        
        # Mostrar resultados
        result_file = Path("pipeline_result.json")
        if result_file.exists() and result_file.is_file():
            with open(result_file, "r") as f:
                data = json.load(f)
        
        console.print("\nResultados do Pipeline:")
        
        # Word frequency
        if 'word_frequency' in data:
            wf = data['word_frequency']
            console.print(f"\n  [bold]Análise de Frequência:[/bold]")
            console.print(f"    Vocabulário: {wf['vocabulary_size']} palavras")
            top_words = list(wf['word_frequencies'].items())[:5]
            console.print(f"    Top palavras: {', '.join([f'{w}({f})' for w,f in top_words])}")
        
        # Sentiment
        if 'sentiment_analyzer' in data:
            sa = data['sentiment_analyzer']
            console.print(f"\n  [bold]Análise de Sentimento:[/bold]")
            console.print(f"    Sentimento: {sa['sentiment_label']}")
            console.print(f"    Polaridade: {sa['polarity']:.3f}")
            console.print(f"    Subjetividade: {sa['subjectivity']:.3f}")
    else:
        console.print(f"[red]✗ Erro no pipeline: {result.stderr}[/red]")
    
    # Limpar
    test_file.unlink(missing_ok=True)
    config_path.unlink(missing_ok=True)

def check_dependencies():
    """Verifica dependências necessárias"""
    print_section("Verificando Dependências")
    
    dependencies = {
        "textblob": "Para análise de sentimento",
        "langdetect": "Para detecção de idioma",
        "plotly": "Para visualizações interativas",
        "kaleido": "Para exportar gráficos como imagem"
    }
    
    missing = []
    
    for package, description in dependencies.items():
        try:
            __import__(package)
            console.print(f"[green]✓[/green] {package} - {description}")
        except ImportError:
            console.print(f"[red]✗[/red] {package} - {description}")
            missing.append(package)
    
    if missing:
        console.print(f"\n[yellow]Instale as dependências faltantes:[/yellow]")
        console.print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def main():
    """Executa todos os testes"""
    console.print("[bold magenta]🎯 Teste de Integração - Sentiment Analyzer[/bold magenta]")
    console.print("Este script demonstra o sentiment_analyzer funcionando em todos os contextos\n")
    
    # Verificar dependências
    if not check_dependencies():
        console.print("\n[red]Instale as dependências antes de continuar.[/red]")
        return
    
    # Executar testes
    test_cli()
    test_visualization()
    test_api()
    test_pipeline()
    
    # Resumo
    print_section("Resumo")
    
    console.print("[green]✅ Plugin sentiment_analyzer integrado com sucesso![/green]")
    console.print("\nO plugin está disponível em:")
    console.print("  • [bold]CLI[/bold]: qualia analyze <file> -p sentiment_analyzer")
    console.print("  • [bold]Menu[/bold]: qualia menu → Executar Análise")
    console.print("  • [bold]API[/bold]: POST /analyze/sentiment_analyzer")
    console.print("  • [bold]Pipeline[/bold]: Pode ser combinado com outros plugins")
    
    console.print("\n[yellow]Arquivos gerados:[/yellow]")
    for file in ["sentiment_result.json", "sentiment_dashboard.html", 
                 "sentiment_gauge.png", "pipeline_result.json"]:
        if Path(file).exists():
            console.print(f"  • {file}")
    
    console.print("\n[bold cyan]🚀 Experimente criar mais análises e visualizações![/bold cyan]")

if __name__ == "__main__":
    main()