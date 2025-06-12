# 🔬 Qualia Core

![Testes](https://github.com/SEU_USUARIO/qualia/actions/workflows/tests.yml/badge.svg)

Um framework para análise qualitativa de textos que nasceu da frustração de ter scripts espalhados e reescrever a mesma coisa toda vez.

## Por que existe?

Depois de anos fazendo análise de dados qualitativos, percebi que sempre recriava as mesmas ferramentas: limpeza de transcrições, análise de frequência, visualizações básicas. Cada projeto novo era copiar e colar código antigo, adaptar, quebrar, consertar...

Qualia Core é minha tentativa de resolver isso de uma vez. É um sistema que:
- Organiza análises em plugins reutilizáveis
- Funciona tanto via terminal quanto API
- Cada análise pode ter sua própria estrutura (sem forçar padrões)
- Fácil de estender com novos métodos

## O que faz?

### Análises incluídas:

- **word_frequency**: Conta palavras, encontra as mais comuns
- **sentiment_analyzer**: Analisa se o texto é positivo/negativo (usando TextBlob)
- **teams_cleaner**: Limpa aquelas transcrições bagunçadas do Teams/Zoom
- **wordcloud_viz**: Gera nuvens de palavras
- **frequency_chart**: Cria gráficos diversos (barras, pizza, treemap)
- **sentiment_viz**: Visualiza sentimentos ao longo do texto

### Como usar:

**Terminal (mais direto):**
```bash
# Ver o que tem disponível
qualia list

# Analisar um texto
qualia analyze "seu texto aqui" -p word_frequency

# Processar arquivo de transcrição
qualia process transcript.txt -p teams_cleaner

# Menu interativo (mais fácil)
qualia menu
```

**API (para integrar com outras coisas):**
```python
# Rodar servidor
python run_api.py

# Usar via requests
import requests
response = requests.post('http://localhost:8000/analyze/word_frequency',
                       json={'text': 'seu texto aqui'})
```

## Setup

```bash
# Clonar
git clone <este-repo>
cd qualia

# Ambiente virtual (recomendo)
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instalar
pip install -r requirements.txt
pip install -e .

# Testar se funcionou
qualia list
```

**Nota sobre dependências**: O sentiment_analyzer precisa do TextBlob, que por sua vez precisa baixar uns dados do NLTK. Se não quiser usar análise de sentimento, o resto funciona sem isso.

## Arquitetura (para quem curte)

O sistema tem um core "burro" que só sabe executar plugins. Cada plugin declara:
- O que ele precisa receber
- O que ele produz
- De quais outros plugins depende (se houver)

Isso permite que cada análise tenha seu próprio formato de saída. O word_frequency retorna frequências, o sentiment retorna polaridade, cada um no seu formato. Sem forçar estruturas.

```
qualia/
├── core/          # Motor que executa plugins
├── plugins/       # Análises específicas
├── cli/           # Interface de terminal
└── api/           # Servidor REST
```

## Desenvolvimento

**Criar novo plugin:**
```bash
qualia init meu_plugin --type analyzer
```

Isso cria a estrutura básica. Daí é só implementar o método `_analyze_impl()`.

**Rodar testes:**
```bash
make test-quick  # Validação rápida
make test        # Testes completos
```

**Filosofia dos testes**: Não forçamos estruturas esperadas. Cada plugin define seu output, os testes respeitam isso.

## Estado atual

- ✅ 6 plugins funcionando
- ✅ CLI com 13 comandos
- ✅ API REST com documentação automática
- ✅ 95% dos testes passando localmente
- ⚠️ CI/CD com algumas dependências faltando (TextBlob)

## Limitações conhecidas

1. **TextBlob no CI/CD**: Precisa baixar dados após instalar, o que complica automação
2. **Dependências por plugin**: Ainda não resolvi bem como cada plugin declarar suas deps
3. **Visualizações**: Algumas ficam melhores que outras dependendo dos dados

## Ideias para o futuro

- Sistema para cada plugin ter seu requirements.txt
- Mais métodos de análise (LDA, NER, etc)
- Interface web simples
- Melhorar documentação com mais exemplos

## Sobre

Desenvolvido entre sessions de análise e xícaras de café. 

A ideia não é ser uma ferramenta comercial ou competir com softwares grandes. É só um jeito organizado de ter minhas análises favoritas sempre à mão, e se for útil para outros pesquisadores, melhor ainda.

## Licença

MIT - Use como quiser, modifique à vontade. Se fizer algo legal, me conta!

---

*"De script bagunçado para ferramenta organizada, mantendo a simplicidade de uso"*