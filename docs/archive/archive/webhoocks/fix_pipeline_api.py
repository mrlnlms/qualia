#!/usr/bin/env python3
"""
Corrigir o pipeline para usar PipelineConfig e PipelineStep corretos
"""

def fix_pipeline_api():
    file_path = 'qualia/api/__init__.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Primeiro, adicionar imports necessários se não existirem
    if 'from qualia.core import QualiaCore, Document' in content and 'PipelineConfig' not in content:
        # Adicionar PipelineConfig e PipelineStep ao import
        content = content.replace(
            'from qualia.core import QualiaCore, Document',
            'from qualia.core import QualiaCore, Document, PipelineConfig, PipelineStep'
        )
        print("✅ Adicionados imports: PipelineConfig, PipelineStep")
    
    # Agora corrigir a função execute_pipeline
    lines = content.split('\n')
    in_pipeline_func = False
    modified = False
    
    for i, line in enumerate(lines):
        if 'async def execute_pipeline' in line:
            in_pipeline_func = True
            
        elif in_pipeline_func and 'pipeline_config = {' in line:
            # Encontrou onde criar o pipeline_config
            # Vamos substituir a criação do dict por objetos corretos
            
            # Encontrar o fim do dict (procurar pelo }
            end_idx = i
            brace_count = 0
            for j in range(i, len(lines)):
                brace_count += lines[j].count('{') - lines[j].count('}')
                if brace_count == 0 and '}' in lines[j]:
                    end_idx = j
                    break
            
            # Substituir todo o bloco
            indent = '        '  # 8 espaços
            new_code = [
                f'{indent}# Convert steps to PipelineStep objects',
                f'{indent}pipeline_steps = [',
                f'{indent}    PipelineStep(',
                f'{indent}        plugin_id=step.plugin_id,',
                f'{indent}        config=step.config,',
                f'{indent}        output_name=None',
                f'{indent}    )',
                f'{indent}    for step in request.steps',
                f'{indent}]',
                f'{indent}',
                f'{indent}# Create PipelineConfig object',
                f'{indent}pipeline_config = PipelineConfig(',
                f'{indent}    name="API Pipeline",',
                f'{indent}    steps=pipeline_steps',
                f'{indent})'
            ]
            
            # Substituir linhas
            lines[i:end_idx+1] = new_code
            modified = True
            print("✅ Modificada criação do pipeline_config")
            break
    
    if modified:
        # Salvar arquivo
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))
        
        print("\n✅ Arquivo salvo com sucesso!")
        print("\nAs mudanças foram:")
        print("1. Import de PipelineConfig e PipelineStep")
        print("2. Criação de objetos PipelineStep em vez de dicts")
        print("3. Criação de objeto PipelineConfig em vez de dict")
    else:
        print("❌ Não foi possível encontrar o padrão para modificar")

if __name__ == "__main__":
    fix_pipeline_api()