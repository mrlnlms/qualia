# 🛠️ Padrões de Implementação - Guia Prático

## Padrões Que Funcionaram

### 1. Progressive Enhancement Pattern

```python
# Nível 1: Interface mínima
class IPlugin(ABC):
    @abstractmethod
    def meta(self) -> PluginMetadata: pass

# Nível 2: Especialização
class IAnalyzerPlugin(IPlugin):
    @abstractmethod
    def analyze(self, doc, config, context): pass

# Nível 3: Implementação comum
class BaseAnalyzerPlugin(IAnalyzerPlugin):
    def analyze(self, doc, config, context):
        # Código comum aqui
        return self._analyze_impl(doc, config, context)

# Nível 4: Plugin específico
class WordFrequencyAnalyzer(BaseAnalyzerPlugin):
    def _analyze_impl(self, doc, config, context):
        # Só a lógica específica
```

**Por que funciona**: Cada camada adiciona valor sem forçar complexidade.

### 2. Configuration Cascade Pattern

```python
# CLI passa string simples
qualia analyze doc.txt -P min_length=5

# CLI converte para dict
params = {"min_length": "5"}  # ainda string

# Base class valida e converte tipos
validated_config = {
    "min_length": 5,  # agora é int
    "remove_stopwords": True  # default aplicado
}

# Plugin recebe config limpo e validado
def _analyze_impl(self, doc, config, context):
    # config já está perfeito aqui
```

**Por que funciona**: Cada camada tem uma responsabilidade clara.

### 3. Dual Interface Pattern

```python
# Interface para humanos (CLI)
qualia visualize data.json -p wordcloud_viz -o cloud.png

# Interface para código
from plugins.wordcloud_viz import WordCloudVisualizer
viz = WordCloudVisualizer()
viz.render(data, config, Path("cloud.png"))
```

**Por que funciona**: Mesma funcionalidade, múltiplos públicos.

### 4. Safe Defaults Pattern

```python
def execute_plugin(self, plugin_id, document, config=None, context=None):
    config = config or {}    # Nunca None
    context = context or {}  # Sempre dict
    
    # Código não precisa checar None
    if "param" in config:  # Sempre seguro
```

**Por que funciona**: Elimina uma classe inteira de bugs.

### 5. Error Context Pattern

```python
# Não apenas "erro"
except Exception as e:
    console.print(f"[red]✗ Erro na visualização: {str(e)}[/red]")
    console.print(f"[dim]Tipo: {type(e).__name__}[/dim]")
    
    # Sugestões baseadas no erro
    if "requires" in str(e).lower():
        console.print("\n[yellow]Dica: Verifique se os dados contêm os campos necessários.[/yellow]")
        console.print("Use 'qualia inspect <plugin>' para ver requisitos.")
```

**Por que funciona**: Transforma erros em oportunidades de aprendizado.

### 6. Discovery Over Configuration

```python
# Plugins se auto-descobrem
plugins/
├── word_frequency/
│   └── __init__.py  # Basta existir
└── my_new_plugin/
    └── __init__.py  # Automaticamente descoberto

# Não precisa registrar em lugar nenhum
```

**Por que funciona**: Menos atrito para adicionar features.

### 7. Metadata as Contract

```python
def meta(self) -> PluginMetadata:
    return PluginMetadata(
        id="word_frequency",
        provides=["word_frequencies", "vocabulary_size"],  # O que eu forneço
        requires=[],  # O que eu preciso
        parameters={  # Como me configurar
            "min_length": {"type": "int", "default": 3}
        }
    )
```

**Por que funciona**: Plugin se auto-documenta completamente.

### 8. Graceful Degradation Pattern

```python
try:
    import nltk
    tokens = nltk.word_tokenize(text)
except ImportError:
    # Fallback para método simples
    tokens = text.split()
    console.print("[yellow]NLTK não instalado, usando tokenização simples[/yellow]")
```

**Por que funciona**: Sistema funciona mesmo sem todas as dependências.

### 9. Output Format Auto-Detection

```python
# Usuario escolhe formato pela extensão
qualia visualize data.json -o output.png   # PNG
qualia visualize data.json -o output.html  # HTML
qualia visualize data.json -o output.svg   # SVG

# Sistema detecta automaticamente
if output_path.suffix == '.png':
    return self._render_png(data)
elif output_path.suffix == '.html':
    return self._render_html(data)
```

**Por que funciona**: Intuitivo, sem flags extras.

### 10. Composable Operations

```bash
# Cada comando faz uma coisa bem
qualia analyze doc.txt -o step1.json
qualia visualize step1.json -o step2.png

# Ou pipeline para conveniência
qualia pipeline doc.txt -c pipeline.yaml
```

**Por que funciona**: Flexibilidade Unix-like.

## Anti-Padrões Evitados

### ❌ God Object
```python
# EVITADO: Core que sabe tudo
class QualiaCore:
    def analyze_sentiment(self): ...
    def create_wordcloud(self): ...
    def clean_transcript(self): ...
```

### ✅ Solução: Plugin Architecture
```python
# Core só orquestra
class QualiaCore:
    def execute_plugin(self, plugin_id, ...):
        # Não sabe o que o plugin faz
```

### ❌ Stringly Typed
```python
# EVITADO: Tudo é string
config = {"type": "analyzer", "subtype": "sentiment"}
```

### ✅ Solução: Enums e Types
```python
class PluginType(Enum):
    ANALYZER = "analyzer"
    VISUALIZER = "visualizer"
```

### ❌ Hidden Dependencies
```python
# EVITADO: Plugin assume que algo existe
def analyze(self, doc):
    # Assume que 'frequencies' existe
    data = doc.analyses['frequencies']  # 💥
```

### ✅ Solução: Explicit Requirements
```python
requires=["word_frequencies"]  # Declarado no metadata
```

## Checklist para Novos Padrões

Antes de adicionar um padrão, pergunte:

- [ ] Reduz código duplicado?
- [ ] Torna erros mais difíceis?
- [ ] É intuitivo para usuários?
- [ ] Escala bem?
- [ ] Tem escape hatch se necessário?

Se sim para todos → implemente!

## Conclusão

Os melhores padrões no Qualia são os que:
1. **Emergem naturalmente** do uso
2. **Reduzem atrito** para desenvolvedores
3. **Melhoram UX** sem adicionar complexidade
4. **São opcionais** quando possível

> "Patterns are discovered, not invented" - e o Qualia provou isso! 🚀