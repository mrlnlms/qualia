# 🔬 Qualia Core

Um framework bare metal para transformação de dados qualitativos em insights quantificados, que inicia vazio e cresce organicamente através de plugins.

> **Qualia** (do latim "qualis") - experiências subjetivas qualitativas que este framework transforma em métricas objetivas para pesquisa mixed methods.

## 🎯 O Problema que Resolvemos

**Situação Atual**: 
- "Cadê aquele script de limpeza que fiz 6 meses atrás?"
- Procura em várias pastas: `lda_test_v3_final_FINAL.py`
- "Qual ambiente virtual era? Precisa instalar sklearn..."
- 30min debugando conflitos de versão
- Parâmetros diferentes da última vez

**Com Qualia**:
```bash
$ qualia analyze documento.txt --analyzer="lda"
✅ Pronto! (usa configuração que funcionou antes)
```

## 🚀 Filosofia Core

### Bare Metal = Orquestração Pura
- Core NÃO implementa features, apenas orquestra
- Core não conhece NENHUM tipo de análise
- Toda inteligência vem dos plugins
- **Zero conhecimento de domínio** no Core

### Scripts → Plugins Permanentes
Seus scripts úteis (limpeza Teams/Meet, preprocessamento) viram plugins permanentes:
```bash
# Antes: procurar script perdido
# Agora:
$ qualia process transcript.txt --plugin="teams-cleaner"
✅ Sempre disponível com mesma config!
```

### Configuration as Methodology
- Cada parâmetro tem justificativa científica
- Configurações são assets reutilizáveis
- "tese_diabetes_2024" vira receita permanente

## 🏗️ Arquitetura

```
qualia/
├── core/              # Engine bare metal
├── document_lab/      # Preparação de documentos
├── para_meta/         # Parametrização + metadados
├── quali_metrics/     # Configurações metodológicas
└── visual_engine/     # Visualizações

plugins/               # Seus scripts viram plugins aqui!
├── word_frequency/    # Exemplo: analyzer
├── teams_cleaner/     # Exemplo: seu script como plugin
└── your_plugin/       # Adicione os seus!
```

## 📦 Instalação

```bash
# Clonar repositório
git clone https://github.com/mrlnlms/qualia.git
cd qualia

# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Testar instalação
python -m qualia.core
```

## 🎨 Como Funciona

### 1. Core Completamente Vazio
```python
from qualia.core import QualiaCore

# Core inicia sem conhecer NADA
core = QualiaCore()
print(len(core.plugins))  # 0 - vazio!

# Descobre plugins disponíveis
core.discover_plugins()
```

### 2. Plugins se Auto-Descrevem
```python
class YourAnalyzer(IAnalyzerPlugin):
    def meta(self):
        return PluginMetadata(
            provides=["word_frequencies", "vocabulary_size"],
            requires=[],  # Dependências auto-resolvidas
            parameters={...}  # Schema completo
        )
```

### 3. Execução Agnóstica
```python
# Core não sabe que "word_frequency" conta palavras!
result = core.execute_plugin("word_frequency", document)
```

## 🧪 Status: Pre-Alpha

Este é um projeto experimental em desenvolvimento ativo. A API pode mudar.

### Implementado
- [x] Core bare metal funcional
- [x] Sistema de plugins com auto-descrição
- [x] Resolução de dependências
- [x] Cache inteligente
- [x] Exemplo: Word Frequency Analyzer
- [x] Exemplo: Teams Transcript Cleaner

### Em Desenvolvimento
- [ ] CLI completa
- [ ] API REST
- [ ] Plugin Obsidian
- [ ] Mais analyzers
- [ ] Sistema de configuração YAML

## 🤝 Contribuindo

Este projeto está em fase inicial. Contribuições são bem-vindas!

### Como Criar um Plugin
1. Crie uma pasta em `plugins/seu_plugin/`
2. Implemente uma das interfaces (IAnalyzerPlugin, etc)
3. Declare metadados completos
4. O Core descobrirá automaticamente!

### Princípios
- **Modularidade extrema** - tudo é plugin
- **Zero conhecimento no Core** - inteligência nos plugins  
- **Seus scripts são valiosos** - transforme em plugins permanentes

## 📚 Documentação

- [Decisões Técnicas](docs/technical_decisions.md) - Arquitetura e aprendizados
- [Plugin Development](docs/plugin_guide.md) - Como criar plugins
- [API Reference](docs/api.md) - Documentação completa

## 🔗 Relacionado

- [transcript-analyzer](https://github.com/mrlnlms/transcript-analyser) - Sistema atual em produção
- Este projeto eventualmente substituirá o core do transcript-analyzer

## 📜 Licença

MIT License - Livre para uso acadêmico e comercial.

---

**Visão**: Transformar a análise qualitativa de "procurar scripts perdidos" para "funcionalidade permanente e organizada".