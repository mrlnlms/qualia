# fix_plugins.py
"""
Script para corrigir os plugins removendo 'author' do PluginMetadata
"""

import re
from pathlib import Path

def fix_plugin_metadata(file_path):
    """Remove 'author' field from PluginMetadata calls"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove linha com author="..."
    pattern = r',?\s*author="[^"]*",?'
    new_content = re.sub(pattern, ',', content)
    
    # Limpar vírgulas duplas
    new_content = re.sub(r',\s*,', ',', new_content)
    new_content = re.sub(r',\s*\)', ')', new_content)
    
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Fixed: {file_path}")

# Corrigir todos os plugins
plugins_dir = Path("plugins")
for plugin_dir in plugins_dir.iterdir():
    if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
        init_file = plugin_dir / "__init__.py"
        if init_file.exists():
            fix_plugin_metadata(init_file)

print("\nAgora vamos adicionar validate_config aos plugins que precisam...")

# Para word_frequency e teams_cleaner, adicionar validate_config
def add_validate_config(file_path, base_class):
    """Adiciona método validate_config se não existir"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    if "def validate_config" not in content:
        # Encontrar onde adicionar (depois de meta())
        lines = content.split('\n')
        new_lines = []
        added = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # Adicionar após o método meta()
            if not added and "def meta(self)" in line:
                # Encontrar o fim do método meta()
                indent_count = len(line) - len(line.lstrip())
                j = i + 1
                while j < len(lines) and (lines[j].strip() == '' or len(lines[j]) - len(lines[j].lstrip()) > indent_count):
                    j += 1
                
                # Agora estamos no fim do método meta()
                # Esperar até a próxima linha em branco ou próximo método
                while j < len(lines) and lines[j].strip() != '':
                    new_lines.append(lines[j])
                    j += 1
                
                # Adicionar validate_config
                new_lines.append('')
                new_lines.append('    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:')
                new_lines.append('        """Validação de configuração"""')
                new_lines.append('        return True, None')
                
                # Adicionar o resto
                new_lines.extend(lines[j:])
                added = True
                break
        
        if added:
            with open(file_path, 'w') as f:
                f.write('\n'.join(new_lines))
            print(f"✅ Added validate_config to: {file_path}")

# Adicionar para word_frequency
add_validate_config(Path("plugins/word_frequency/__init__.py"), "BaseAnalyzerPlugin")

print("\nPronto! Teste novamente com:")
print("python -m qualia list")