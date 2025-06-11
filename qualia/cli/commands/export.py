# qualia/cli/commands/export.py
"""
Comando para exportar resultados em diferentes formatos
"""

import click
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List
from rich.table import Table as RichTable

from .utils import console


def export_to_csv(data: Dict[str, Any], output_path: Path):
    """Exporta para CSV"""
    import csv
    
    # Determinar estrutura
    if isinstance(data, dict):
        # Se tem 'results' ou 'data', usar isso
        if 'results' in data:
            data = data['results']
        elif 'data' in data:
            data = data['data']
    
    # Converter para lista de dicts se necessário
    rows = []
    if isinstance(data, dict):
        # Tentar achar dados tabulares
        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                rows = value
                break
            elif isinstance(value, dict):
                # Converter dict para lista de rows
                for k, v in value.items():
                    rows.append({"key": k, "value": v})
                break
        
        if not rows:
            # Fallback: todo o dict como uma linha
            rows = [data]
    elif isinstance(data, list):
        rows = data
    
    # Escrever CSV
    if rows:
        keys = set()
        for row in rows:
            if isinstance(row, dict):
                keys.update(row.keys())
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(keys))
            writer.writeheader()
            writer.writerows(rows)
    else:
        # Dados não estruturados - salvar como texto
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(data))


def export_to_excel(data: Dict[str, Any], output_path: Path):
    """Exporta para Excel"""
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas necessário para exportar Excel. Install: pip install pandas openpyxl")
    
    # Preparar dados
    if isinstance(data, dict) and 'results' in data:
        data = data['results']
    
    # Criar Excel com múltiplas abas se necessário
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Se data é dict de dataframes/listas
        if isinstance(data, dict):
            for sheet_name, sheet_data in data.items():
                if isinstance(sheet_data, (list, dict)):
                    try:
                        df = pd.DataFrame(sheet_data)
                        df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                    except:
                        # Dados não tabulares - criar sheet com info
                        df = pd.DataFrame([{"data": str(sheet_data)}])
                        df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        else:
            # Dados simples
            df = pd.DataFrame(data if isinstance(data, list) else [data])
            df.to_excel(writer, sheet_name='Data', index=False)


def export_to_markdown(data: Dict[str, Any], output_path: Path):
    """Exporta para Markdown"""
    md_lines = ["# Resultados Qualia\n"]
    
    # Metadata se disponível
    if isinstance(data, dict) and 'metadata' in data:
        meta = data['metadata']
        md_lines.append("## Metadata\n")
        for key, value in meta.items():
            md_lines.append(f"- **{key}**: {value}")
        md_lines.append("")
    
    # Resultados principais
    if isinstance(data, dict) and 'results' in data:
        data = data['results']
    
    md_lines.append("## Dados\n")
    
    # Converter dados para markdown
    if isinstance(data, dict):
        for key, value in data.items():
            md_lines.append(f"### {key}\n")
            
            if isinstance(value, list) and value and isinstance(value[0], dict):
                # Tabela
                headers = list(value[0].keys())
                md_lines.append("| " + " | ".join(headers) + " |")
                md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                
                for row in value:
                    cells = [str(row.get(h, "")) for h in headers]
                    md_lines.append("| " + " | ".join(cells) + " |")
                md_lines.append("")
                
            elif isinstance(value, dict):
                # Lista de key-value
                for k, v in value.items():
                    md_lines.append(f"- **{k}**: {v}")
                md_lines.append("")
                
            else:
                # Valor simples
                md_lines.append(f"{value}\n")
    else:
        md_lines.append(f"```json\n{json.dumps(data, indent=2)}\n```\n")
    
    output_path.write_text("\n".join(md_lines))


def export_to_html(data: Dict[str, Any], output_path: Path):
    """Exporta para HTML com estilo"""
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Resultados Qualia</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{ background: #f5f5f5; }}
        .metadata {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .json-data {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
        }}
        .chart-container {{
            margin: 20px 0;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Resultados Qualia</h1>
        {content}
    </div>
</body>
</html>"""
    
    content_parts = []
    
    # Metadata
    if isinstance(data, dict) and 'metadata' in data:
        meta_html = "<div class='metadata'><h2>Metadata</h2><ul>"
        for key, value in data['metadata'].items():
            meta_html += f"<li><strong>{key}:</strong> {value}</li>"
        meta_html += "</ul></div>"
        content_parts.append(meta_html)
    
    # Dados principais
    if isinstance(data, dict) and 'results' in data:
        data = data['results']
    
    # Converter dados
    if isinstance(data, dict):
        for key, value in data.items():
            content_parts.append(f"<h2>{key}</h2>")
            
            if isinstance(value, list) and value and isinstance(value[0], dict):
                # Criar tabela
                headers = list(value[0].keys())
                table_html = "<table><thead><tr>"
                for h in headers:
                    table_html += f"<th>{h}</th>"
                table_html += "</tr></thead><tbody>"
                
                for row in value:
                    table_html += "<tr>"
                    for h in headers:
                        table_html += f"<td>{row.get(h, '')}</td>"
                    table_html += "</tr>"
                
                table_html += "</tbody></table>"
                content_parts.append(table_html)
                
            else:
                # Mostrar como JSON formatado
                json_html = f"<div class='json-data'><pre>{json.dumps(value, indent=2)}</pre></div>"
                content_parts.append(json_html)
    else:
        # Fallback para JSON
        json_html = f"<div class='json-data'><pre>{json.dumps(data, indent=2)}</pre></div>"
        content_parts.append(json_html)
    
    html = html_template.format(content="\n".join(content_parts))
    output_path.write_text(html)


@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--format', '-f', 
              type=click.Choice(['csv', 'excel', 'markdown', 'html', 'yaml']),
              required=True,
              help='Formato de saída')
@click.option('--output', '-o', type=click.Path(), 
              help='Arquivo de saída (padrão: input_file.formato)')
@click.option('--pretty', is_flag=True, 
              help='Formatação bonita (para YAML/JSON)')
def export(input_file: str, format: str, output: str, pretty: bool):
    """Exporta resultados JSON para outros formatos
    
    Exemplos:
        qualia export results.json -f csv
        qualia export analysis.json -f excel -o report.xlsx
        qualia export data.json -f markdown -o README.md
        qualia export results.json -f html -o report.html
    """
    
    # Ler arquivo de entrada
    input_path = Path(input_file)
    
    try:
        if input_path.suffix in ['.json']:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif input_path.suffix in ['.yaml', '.yml']:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        else:
            console.print("[red]Formato de entrada não suportado. Use JSON ou YAML.[/red]")
            return
    except Exception as e:
        console.print(f"[red]Erro ao ler arquivo: {str(e)}[/red]")
        return
    
    # Determinar arquivo de saída
    if not output:
        output = input_path.with_suffix(f'.{format}')
    else:
        output = Path(output)
    
    # Criar diretório se necessário
    output.parent.mkdir(parents=True, exist_ok=True)
    
    # Exportar conforme formato
    console.print(f"[bold]Exportando para {format.upper()}...[/bold]")
    
    try:
        if format == 'csv':
            export_to_csv(data, output)
        elif format == 'excel':
            export_to_excel(data, output)
        elif format == 'markdown':
            export_to_markdown(data, output)
        elif format == 'html':
            export_to_html(data, output)
        elif format == 'yaml':
            with open(output, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=not pretty, 
                         allow_unicode=True, sort_keys=False)
        
        console.print(f"[green]✓ Exportado com sucesso: {output}[/green]")
        
        # Mostrar preview se for texto
        if format in ['csv', 'markdown']:
            preview = output.read_text().split('\n')[:10]
            if len(preview) > 5:
                console.print("\n[dim]Preview:[/dim]")
                for line in preview[:5]:
                    console.print(f"  {line}")
                console.print("  ...")
                
    except ImportError as e:
        console.print(f"[red]Erro de dependência: {str(e)}[/red]")
    except Exception as e:
        console.print(f"[red]Erro ao exportar: {str(e)}[/red]")
        import traceback
        traceback.print_exc()