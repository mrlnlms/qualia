#!/usr/bin/env python3
"""
demo_qualia.py - Demonstração completa do Qualia Core

Este script mostra o poder do framework em um fluxo completo:
1. Processar transcrição
2. Analisar conteúdo
3. Gerar visualizações
4. Criar dashboard combinado
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_command(cmd):
    """Executa comando e mostra output"""
    print(f"\n🔹 Executando: {cmd}")
    print("─" * 60)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"⚠️  {result.stderr}")
    return result.returncode == 0

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║           🔬 QUALIA CORE - DEMONSTRAÇÃO COMPLETA          ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Criar diretório para demo
    demo_dir = Path("demo_output")
    demo_dir.mkdir(exist_ok=True)
    print(f"📁 Criando outputs em: {demo_dir}/")
    
    # 1. PREPARAR DADOS
    print("\n\n" + "="*60)
    print("1️⃣  PREPARANDO TRANSCRIÇÃO DE EXEMPLO")
    print("="*60)
    
    transcript = """[00:00:00] Sistema: Recording Started
[00:00:05] Ana Silva: Bom dia! Vamos começar nossa análise do projeto.
[00:00:10] Carlos Santos: Olá Ana! Estou muito animado com os resultados.
[00:00:15] Ana Silva: Sim, o framework Qualia está superando expectativas!
[00:00:20] Sistema: Bruno Oliveira joined the meeting
[00:00:25] Bruno Oliveira: Desculpem o atraso. O que perdi?
[00:00:30] Carlos Santos: Estávamos falando sobre o sucesso do Qualia.
[00:00:35] Ana Silva: Bruno, você precisa ver as visualizações que geramos!
[00:00:40] Bruno Oliveira: Incrível! Isso vai revolucionar nossa pesquisa.
[00:00:45] Carlos Santos: Concordo. A análise qualitativa nunca foi tão fácil.
[00:00:50] Ana Silva: Vamos preparar uma apresentação para a diretoria?
[00:00:55] Bruno Oliveira: Ótima ideia! Podemos mostrar casos reais.
[00:01:00] Carlos Santos: Perfeito. Vou documentar tudo.
[00:01:05] Sistema: Recording Stopped"""
    
    with open("demo_transcript.txt", "w") as f:
        f.write(transcript)
    print("✅ Transcrição criada: demo_transcript.txt")
    
    # 2. LIMPAR TRANSCRIÇÃO
    print("\n\n" + "="*60)
    print("2️⃣  LIMPANDO TRANSCRIÇÃO COM TEAMS CLEANER")
    print("="*60)
    
    if run_command(f"qualia process demo_transcript.txt -p teams_cleaner --save-as {demo_dir}/cleaned.txt"):
        print("✅ Transcrição limpa!")
        
        # Mostrar preview
        with open(f"{demo_dir}/cleaned.txt", "r") as f:
            lines = f.readlines()[:5]
            print("\n📄 Preview (primeiras 5 linhas):")
            for line in lines:
                print(f"   {line.strip()}")
    
    # 3. ANÁLISE DE FREQUÊNCIA
    print("\n\n" + "="*60)
    print("3️⃣  ANALISANDO FREQUÊNCIA DE PALAVRAS")
    print("="*60)
    
    if run_command(f"qualia analyze {demo_dir}/cleaned.txt -p word_frequency "
                   f"-P min_word_length=4 -P remove_stopwords=true "
                   f"-o {demo_dir}/analysis.json"):
        print("✅ Análise completa!")
    
    # 4. GERAR VISUALIZAÇÕES
    print("\n\n" + "="*60)
    print("4️⃣  GERANDO VISUALIZAÇÕES")
    print("="*60)
    
    visualizations = [
        ("wordcloud_viz", "wordcloud.png", {"colormap": "viridis", "background_color": "white"}),
        ("wordcloud_viz", "wordcloud_dark.png", {"colormap": "plasma", "background_color": "black"}),
        ("frequency_chart", "chart_bar.html", {"chart_type": "bar", "max_items": 15}),
        ("frequency_chart", "chart_horizontal.png", {"chart_type": "horizontal_bar", "format": "png"}),
    ]
    
    for viz_plugin, output_file, params in visualizations:
        param_str = " ".join([f"-P {k}={v}" for k, v in params.items()])
        if run_command(f"qualia visualize {demo_dir}/analysis.json "
                      f"-p {viz_plugin} -o {demo_dir}/{output_file} {param_str}"):
            print(f"✅ Gerado: {output_file}")
    
    # 5. ANÁLISE AVANÇADA
    print("\n\n" + "="*60)
    print("5️⃣  ANÁLISE AVANÇADA - PIPELINE COMPLETO")
    print("="*60)
    
    # Criar pipeline config
    pipeline_config = {
        "name": "demo_pipeline",
        "description": "Pipeline de demonstração completo",
        "steps": [
            {
                "plugin": "teams_cleaner",
                "config": {
                    "remove_timestamps": True,
                    "merge_consecutive": True,
                    "create_variants": True
                },
                "output_name": "cleaned"
            },
            {
                "plugin": "word_frequency",
                "config": {
                    "min_word_length": 3,
                    "max_words": 50,
                    "remove_stopwords": True,
                    "language": "portuguese"
                },
                "output_name": "frequency"
            }
        ]
    }
    
    with open(f"{demo_dir}/pipeline.yaml", "w") as f:
        import yaml
        yaml.dump(pipeline_config, f)
    
    if run_command(f"qualia pipeline demo_transcript.txt "
                   f"-c {demo_dir}/pipeline.yaml -o {demo_dir}/pipeline_results"):
        print("✅ Pipeline executado!")
    
    # 6. RELATÓRIO FINAL
    print("\n\n" + "="*60)
    print("6️⃣  GERANDO RELATÓRIO HTML")
    print("="*60)
    
    # Criar um relatório HTML combinado
    html_report = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Qualia Core - Relatório de Demonstração</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            text-align: center;
            padding: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .section {{
            background: white;
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .viz-container {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .viz-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}
        .stats {{
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
        }}
        .stat-box {{
            text-align: center;
            padding: 20px;
            background: #e9ecef;
            border-radius: 8px;
            flex: 1;
            margin: 0 10px;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        code {{
            background: #f1f3f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Consolas', monospace;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 Qualia Core</h1>
        <h2>Relatório de Demonstração</h2>
        <p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    </div>
    
    <div class="section">
        <h2>📊 Resumo da Análise</h2>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">3</div>
                <div>Participantes</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">8</div>
                <div>Interações</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">4</div>
                <div>Visualizações</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>🎨 Visualizações Geradas</h2>
        <div class="grid">
            <div class="viz-container">
                <h3>Nuvem de Palavras</h3>
                <img src="wordcloud.png" alt="Word Cloud">
                <p>Visualização das palavras mais frequentes</p>
            </div>
            <div class="viz-container">
                <h3>Nuvem de Palavras (Dark)</h3>
                <img src="wordcloud_dark.png" alt="Word Cloud Dark">
                <p>Versão com tema escuro</p>
            </div>
        </div>
        
        <div class="viz-container">
            <h3>📈 Gráficos Interativos</h3>
            <p>
                <a href="chart_bar.html" target="_blank">📊 Abrir Gráfico de Barras</a> |
                <a href="pipeline_results/pipeline_summary.yaml">📄 Ver Resumo do Pipeline</a>
            </p>
        </div>
    </div>
    
    <div class="section">
        <h2>💻 Comandos Utilizados</h2>
        <p>Reproduza esta análise com os seguintes comandos:</p>
        <pre><code># 1. Limpar transcrição
qualia process demo_transcript.txt -p teams_cleaner --save-as cleaned.txt

# 2. Analisar frequências
qualia analyze cleaned.txt -p word_frequency -o analysis.json

# 3. Gerar visualizações
qualia visualize analysis.json -p wordcloud_viz -o wordcloud.png
qualia visualize analysis.json -p frequency_chart -o chart.html

# 4. Executar pipeline completo
qualia pipeline demo_transcript.txt -c pipeline.yaml -o results/</code></pre>
    </div>
    
    <div class="section">
        <h2>🚀 Próximos Passos</h2>
        <ul>
            <li>Adicionar análise de sentimentos com <code>sentiment_analyzer</code></li>
            <li>Implementar topic modeling com <code>lda_analyzer</code></li>
            <li>Criar dashboards interativos com <code>dashboard_composer</code></li>
            <li>Integrar com API REST para análises em tempo real</li>
        </ul>
    </div>
    
    <div class="section" style="text-align: center; color: #666;">
        <p>Desenvolvido com ❤️ usando Qualia Core</p>
        <p><a href="https://github.com/mrlnlms/qualia">GitHub</a> | <a href="../README.md">Documentação</a></p>
    </div>
</body>
</html>"""
    
    with open(f"{demo_dir}/relatorio.html", "w") as f:
        f.write(html_report)
    
    print("✅ Relatório HTML gerado!")
    print(f"\n📂 Todos os arquivos estão em: {demo_dir}/")
    print("\n🎉 DEMONSTRAÇÃO COMPLETA!")
    print(f"\nAbra o relatório: {demo_dir}/relatorio.html")

if __name__ == "__main__":
    main()