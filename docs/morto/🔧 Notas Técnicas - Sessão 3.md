# 🔧 Notas Técnicas - Sessão 3

## Lições Aprendidas e Gotchas

### 1. Python 3.13 Breaking Changes
```python
# ❌ Não existe mais em Python 3.13
raise click.Exit(1)

# ✅ Use em vez disso
raise SystemExit(1)
```

### 2. Assinaturas de Métodos Abstratos
```python
# ❌ Interface define uma assinatura
@abstractmethod
def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    pass

# ❌ Base class implementa com assinatura diferente
def validate_config(self, config: Dict[str, Any]) -> bool:
    return True

# ✅ Base class DEVE manter mesma assinatura
def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    return True, None
```

### 3. PluginLoader e Classes Abstratas
```python
# ❌ PluginLoader tentava instanciar TUDO que herda de IPlugin
for name, obj in inspect.getmembers(module):
    if issubclass(obj, IPlugin):
        instance = obj()  # Erro se obj é BaseAnalyzerPlugin!

# ✅ Ignorar base classes e abstratas
for name, obj in inspect.getmembers(module):
    if name.startswith('Base'):
        continue
    if inspect.isabstract(obj):
        continue
    if issubclass(obj, IPlugin):
        instance = obj()
```

### 4. Conflito de Nomes de Variáveis
```python
# ❌ Usar mesmo nome para coisas diferentes
def execute_plugin(self, ..., context: Dict = None):
    context = context or {}  # context do parâmetro
    # ...
    context = ExecutionContext()  # CONFLITO! Sobrescreve
    
# ✅ Usar nomes distintos
def execute_plugin(self, ..., context: Dict = None):
    context = context or {}
    # ...
    exec_context = ExecutionContext()  # Nome diferente
```

### 5. Path vs String em Plugins
```python
# ❌ Plugin espera Path mas recebe string
def render(self, data, config, output_path):
    output_path.parent.mkdir()  # Erro se output_path é string!

# ✅ Base class converte automaticamente
class BaseVisualizerPlugin:
    def render(self, data, config, output_path):
        output_path = Path(output_path) if isinstance(output_path, str) else output_path
        output_path.parent.mkdir(exist_ok=True)
        return self._render_impl(data, config, output_path)
```

### 6. Número de Argumentos em Chamadas
```python
# ❌ CLI passa 4 args mas método aceita só 3
# Em cli.py:
core.execute_plugin(plugin, doc, config, context)

# Em core:
def execute_plugin(self, plugin_id, document, config):  # Só 3!

# ✅ Sincronizar assinaturas
def execute_plugin(self, plugin_id, document, config, context=None):
```

### 7. Ordem de Definição de Classes
```python
# ❌ Base class antes da classe que ela estende
class BaseAnalyzerPlugin(IAnalyzerPlugin):
    def analyze(self, document: Document, ...):  # Document não definido ainda!

class Document:
    ...

# ✅ Ordem correta
class Document:
    ...

class BaseAnalyzerPlugin(IAnalyzerPlugin):
    def analyze(self, document: Document, ...):  # OK!
```

## Padrões Estabelecidos

### Base Classes Pattern
```python
class BaseAnalyzerPlugin(IAnalyzerPlugin):
    # Implementa métodos da interface
    def analyze(self, document, config, context):
        validated_config = self._validate_config(config)
        return self._analyze_impl(document, validated_config, context)
    
    # Plugin implementa apenas a lógica
    def _analyze_impl(self, document, config, context):
        raise NotImplementedError
```

### CLI Command Pattern
```python
@cli.command()
@click.argument('data_path', type=click.Path(exists=True))
@click.option('--plugin', '-p', required=True)
@click.option('--param', '-P', multiple=True)
def visualize(data_path, plugin, param):
    # 1. Validar inputs
    # 2. Carregar dados
    # 3. Processar parâmetros
    # 4. Executar plugin
    # 5. Feedback ao usuário
```

## Debug Tips

### 1. Testar Plugin Diretamente
```python
from plugins.word_frequency import WordFrequencyAnalyzer
analyzer = WordFrequencyAnalyzer()
print("Herda de:", analyzer.__class__.__bases__)
print("Tem método:", hasattr(analyzer, '_analyze_impl'))
```

### 2. Verificar MRO (Method Resolution Order)
```python
print(WordFrequencyAnalyzer.__mro__)
# Mostra ordem de resolução de métodos
```

### 3. Debug de Type Errors
```python
try:
    result = function(args)
except TypeError as e:
    print(f"Args esperados: {function.__code__.co_argcount}")
    print(f"Args passados: {len(args)}")
```

## Checklist para Novos Plugins

- [ ] Herdar da Base class apropriada
- [ ] Implementar `meta()` retornando PluginMetadata
- [ ] Implementar `_*_impl()` (não o método original)
- [ ] validate_config retorna `(bool, Optional[str])`
- [ ] Não incluir campo 'author' no PluginMetadata
- [ ] Testar com Python direto antes de testar via CLI

## Scripts de Debug Úteis

Durante o desenvolvimento, vários scripts de debug foram criados e agora estão em `archive/scripts_debug/`:
- `debug_plugins.py` - Verifica carregamento de plugins
- `debug_validate.py` - Debug de validate_config
- `fix_execute_plugin.py` - Correções do execute_plugin
- `check_execute_plugin.py` - Verificação de assinaturas

Estes scripts são documentação viva de como resolver problemas comuns.

---

Essas notas técnicas capturam os principais aprendizados e gotchas encontrados durante a implementação.