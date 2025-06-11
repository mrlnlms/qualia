"""
Wizards (assistentes) para criação guiada
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any
from rich.prompt import Prompt, Confirm
from ..formatters import console, format_success, format_warning
from .utils import choose_plugin, configure_parameters


class PipelineWizard:
    """Assistente para criação de pipelines"""
    
    def create_pipeline(self):
        """Cria um novo pipeline interativamente"""
        console.print("\n[bold]CRIAR NOVO PIPELINE[/bold]\n")
        
        # Nome e descrição
        pipeline_name = self._get_valid_name()
        description = Prompt.ask("Descrição do pipeline", default="")
        
        # Adicionar steps
        steps = self._build_steps()
        
        if not steps:
            console.print(format_warning("Nenhum step adicionado. Pipeline não criado."))
            return
        
        # Criar estrutura do pipeline
        pipeline_data = {
            "name": pipeline_name,
            "description": description,
            "version": "1.0.0",
            "steps": steps
        }
        
        # Adicionar metadados opcionais
        if Confirm.ask("\nAdicionar metadados extras?"):
            pipeline_data.update(self._get_metadata())
        
        # Salvar pipeline
        self._save_pipeline(pipeline_name, pipeline_data)
    
    def _get_valid_name(self) -> str:
        """Obtém um nome válido para o pipeline"""
        while True:
            name = Prompt.ask("Nome do pipeline")
            
            # Validar nome
            if not name:
                console.print("[red]Nome não pode ser vazio[/red]")
                continue
            
            # Remover caracteres inválidos
            safe_name = "".join(c for c in name if c.isalnum() or c in "_- ")
            safe_name = safe_name.replace(" ", "_").lower()
            
            # Verificar se já existe
            pipeline_path = Path(f"configs/pipelines/{safe_name}.yaml")
            if pipeline_path.exists():
                if Confirm.ask(f"Pipeline '{safe_name}' já existe. Sobrescrever?"):
                    return safe_name
            else:
                return safe_name
    
    def _build_steps(self) -> List[Dict[str, Any]]:
        """Constrói a lista de steps do pipeline"""
        steps = []
        
        console.print("\n[dim]Adicione steps ao pipeline. Digite 'fim' quando terminar.[/dim]")
        
        while True:
            step_num = len(steps) + 1
            console.print(f"\n[bold]Step {step_num}:[/bold]")
            
            # Escolher plugin
            plugin = choose_plugin("all")
            if not plugin or plugin.lower() == 'fim':
                break
            
            # Configurar plugin
            config = configure_parameters(plugin, f"step_{step_num}")
            
            # Criar step
            step = {
                "plugin": plugin,
                "config": config if config else {}
            }
            
            # Output opcional
            if Confirm.ask("Salvar resultado deste step?"):
                output_file = Prompt.ask(
                    "Nome do arquivo de saída",
                    default=f"step_{step_num}_{plugin}_output.json"
                )
                step["output"] = output_file
            
            # Adicionar descrição opcional
            if Confirm.ask("Adicionar descrição ao step?"):
                step["description"] = Prompt.ask("Descrição")
            
            steps.append(step)
            
            if not Confirm.ask("\nAdicionar mais um step?"):
                break
        
        return steps
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Obtém metadados opcionais do pipeline"""
        metadata = {}
        
        # Tags
        tags_str = Prompt.ask("Tags (separadas por vírgula)", default="")
        if tags_str:
            metadata["tags"] = [tag.strip() for tag in tags_str.split(",")]
        
        # Autor
        author = Prompt.ask("Autor", default="")
        if author:
            metadata["author"] = author
        
        # Requisitos
        if Confirm.ask("Adicionar requisitos/notas?"):
            requirements = []
            console.print("[dim]Digite os requisitos (um por linha, 'fim' para terminar)[/dim]")
            while True:
                req = Prompt.ask("Requisito")
                if req.lower() == 'fim':
                    break
                requirements.append(req)
            
            if requirements:
                metadata["requirements"] = requirements
        
        return metadata
    
    def _save_pipeline(self, name: str, data: Dict[str, Any]):
        """Salva o pipeline em arquivo YAML"""
        pipeline_path = Path(f"configs/pipelines/{name}.yaml")
        pipeline_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Adicionar comentário no início
        yaml_content = f"""# Pipeline: {data['name']}
# Criado com Qualia Interactive Menu
# {'-' * 50}

"""
        
        # Serializar para YAML
        yaml_content += yaml.dump(data, default_flow_style=False, sort_keys=False)
        
        # Salvar
        with open(pipeline_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        console.print(f"\n{format_success(f'Pipeline {name} criado com sucesso!')}")
        console.print(f"Salvo em: {pipeline_path}")
        
        # Mostrar preview
        if Confirm.ask("\nVisualizar pipeline criado?"):
            console.print("\n[bold]Conteúdo do pipeline:[/bold]")
            console.print(yaml_content)


class ReportWizard:
    """Assistente para criação de relatórios (futuro)"""
    
    def create_report(self):
        """Cria um relatório combinando múltiplas análises"""
        console.print(format_warning("Funcionalidade em desenvolvimento"))
        # TODO: Implementar wizard de relatórios


class MethodologyWizard:
    """Assistente para criação de metodologias (futuro)"""
    
    def create_methodology(self):
        """Cria uma metodologia de análise"""
        console.print(format_warning("Funcionalidade em desenvolvimento"))
        # TODO: Implementar wizard de metodologias