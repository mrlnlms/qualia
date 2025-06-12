# 🔬 Qualia Core

Transforme textos e documentos em insights quantificados com análises automáticas.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-100%25%20funcional-success.svg)](https://github.com/yourusername/qualia)
[![Testes](https://img.shields.io/badge/testes-9%2F9%20passando-brightgreen.svg)](https://github.com/yourusername/qualia)

> **Qualia** é um sistema que analisa seus textos e gera visualizações automaticamente. Funciona local ou na web.

## 🚀 Começar em 2 Minutos

```bash
# 1. Baixar e instalar
git clone https://github.com/yourusername/qualia
cd qualia
pip install -r requirements.txt
pip install -e .

# 2. Usar modo interativo (mais fácil)
qualia menu

# 3. Ou usar API visual
python run_api.py
# Abrir: http://localhost:8000/docs
```

## 💡 O que o Qualia faz?

### Análise de Sentimento
```bash
qualia analyze feedback.txt -p sentiment_analyzer
```
**Resultado**: "70% positivo, 20% neutro, 10% negativo"

### Frequência de Palavras
```bash
qualia analyze reuniao.txt -p word_frequency
```
**Resultado**: Lista das palavras mais usadas e contexto

### Limpeza de Transcrições
```bash
qualia process teams_export.txt -p teams_cleaner
```
**Resultado**: Texto limpo sem timestamps e ruídos

### Visualizações Automáticas
```bash
qualia visualize dados.json -p wordcloud_viz -o nuvem.png
```
**Resultado**: Imagem PNG com nuvem de palavras

## 📊 Interface Visual

### Menu Interativo
<img src="docs/images/menu.png" width="600" alt="Menu Interativo">

Digite `qualia menu` e navegue com as setas. Simples assim!

### API Web
<img src="docs/images/api.png" width="600" alt="API Swagger">

Acesse http://localhost:8000/docs para testar sem código!

### Monitor em Tempo Real
<img src="docs/images/monitor.png" width="600" alt="Monitor Dashboard">

Veja o que está acontecendo em http://localhost:8000/monitor/

## 🎯 Casos de Uso Reais

### 📝 Análise de Feedback
```bash
# Processar todos os feedbacks do mês
qualia batch "feedbacks/*.txt" -p sentiment_analyzer

# Resultado: relatório com sentimentos por arquivo
```

### 🎤 Transcrições de Reunião
```bash
# Pipeline completo: limpar → analisar → visualizar
qualia pipeline reuniao.txt -c pipeline_reuniao.yaml
```

### 📧 Monitorar Pasta
```bash
# Analisar automaticamente novos arquivos
qualia watch inbox/ -p word_frequency -o resultados/
```

## 🔧 Criar Seu Próprio Analisador

```bash
# Gerar template
python tools/create_plugin.py meu_analisador analyzer

# Editar o arquivo gerado
# plugins/meu_analisador/__init__.py

# Pronto! Já funciona em todos os lugares
```

## 📦 O que Vem Pronto?

| Análise | O que faz | Exemplo de uso |
|---------|-----------|----------------|
| **Sentimento** | Detecta se texto é positivo/negativo | Feedbacks, reviews |
| **Frequência** | Conta palavras importantes | Atas, relatórios |
| **Limpeza** | Remove lixo de transcrições | Teams, Zoom |
| **Nuvem** | Cria imagem com palavras-chave | Apresentações |
| **Gráficos** | Pizza, barras, treemap | Dashboards |

## 🌐 Integração Fácil

### Python
```python
import requests
resultado = requests.post("http://localhost:8000/analyze/sentiment_analyzer",
                         json={"text": "Adorei o produto!"})
print(resultado.json()["result"]["sentiment_label"])  # "positivo"
```

### Webhooks
Conecte com Slack, Discord, ou qualquer sistema:
```bash
curl -X POST http://localhost:8000/webhook/custom \
  -d '{"text": "Analisar isso!", "plugin": "sentiment_analyzer"}'
```

## 📁 Estrutura Simples

```
qualia/
├── usar assim:        qualia menu
├── adicionar plugin:  python tools/create_plugin.py
├── rodar testes:      python test_final_complete.py
└── ver docs:          http://localhost:8000/docs
```

## ❓ Perguntas Frequentes

**P: Preciso saber programar?**  
R: Não! Use `qualia menu` ou a interface web.

**P: Funciona com que tipos de arquivo?**  
R: TXT, CSV, JSON. PDF em breve.

**P: Posso usar na minha empresa?**  
R: Sim! Licença MIT permite uso comercial.

**P: Roda offline?**  
R: Sim! Tudo funciona local. Internet só para baixar.

## 🚀 Próximos Passos

1. **Testar**: Execute `qualia menu` e explore
2. **Personalizar**: Crie um analisador para seu caso
3. **Compartilhar**: Suba num servidor para o time usar

## 📖 Documentação Completa

- [Tutorial Passo a Passo](docs/TUTORIAL.md) - Para iniciantes
- [Guia de Plugins](docs/PLUGINS.md) - Criar suas análises
- [Exemplos](examples/) - Casos de uso prontos

## 🤝 Ajuda

- **Bug?** Abra uma [issue](https://github.com/yourusername/qualia/issues)
- **Dúvida?** Veja os [exemplos](examples/)
- **Ideia?** Pull requests são bem-vindos!

---

Feito com ❤️ para facilitar análise de textos

*Versão 0.1.0 - Dezembro 2024*