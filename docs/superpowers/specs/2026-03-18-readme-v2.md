# README v2 — Design Spec

## Objetivo

Reescrever o README do Qualia com posicionamento atualizado: hub de análise local-first pra pesquisadores e devs que trabalham com dados qualitativos. Tom direto, sem hype, mas comunicando claramente o valor e a experiência de uso.

## Público

Misto: pesquisadores que sabem Python (querem criar plugins, rodar análises customizadas) e pesquisadores que só querem usar a CLI/API. O README serve os dois sem alienar nenhum.

## Mudanças vs README atual

- **Posicionamento:** sai de "framework bare metal" pra "hub de análise local-first extensível por plugins"
- **"Por que existe":** seção nova explicando o problema real (NVivo caro/fechado, scripts soltos sem reuso, APIs cloud com dados sensíveis)
- **DX como diferencial:** mostrar que criar plugin = declarar parâmetros = API/CLI/frontend expõem automaticamente
- **Quick Start compacto:** 3 passos, não 50 linhas
- **Extras explicados:** `[nlp]`, `[ml]`, `[viz]` — o pesquisador entende que instala só o que precisa
- **Ecossistema:** menção ao qualia-coding (Obsidian), sem detalhar os outros projetos
- **Remove:** "core burro", "bare metal", badges excessivas, seção de "limitações" longa

## Estrutura

```markdown
# Qualia

[1-2 frases: o que é]

## Por que

[1 parágrafo: o problema que resolve — NVivo fechado, scripts soltos, cloud com dados sensíveis.
 Qualia: roda local, extensível, qualquer ferramenta consome]

## Plugins

[Tabela dos 8 plugins atuais, organizados por tipo.
 Nota: novos plugins são auto-descobertos — basta criar a pasta]

## Quick Start

[5-6 linhas: Python 3.9+, instalar, subir API, analisar um texto.
 Reforçar que roda local — sem conta, sem cloud, sem mandar dados pra fora]

## CLI

[5 linhas: comandos principais — list, analyze, process, visualize, menu]

## Crie seu próprio plugin

[O diferencial. ~20 linhas mostrando o ciclo completo:]
  1. Roda o gerador: `python tools/create_plugin.py meu_analyzer analyzer`
  2. Mostra o código mínimo (meta com parameters + _analyze_impl)
  3. Mostra que os parâmetros declarados aparecem automaticamente:
     - Na API: GET /config/consolidated retorna o schema
     - Na CLI: `qualia analyze texto.txt -p meu_analyzer -P threshold=0.8`
     - No frontend: form dinâmico gerado do schema
  4. Menciona os 3 tipos (Analyzer, Document, Visualizer) e que visualizer
     retorna figura → BaseClass serializa
  5. Thread-safety: modelos pesados no __init__

## Instale só o que precisa

[Todos os extras do pyproject.toml:
 - pip install qualia-core → core mínimo
 - [api] → FastAPI, uvicorn
 - [nlp] → TextBlob, NLTK, langdetect
 - [ml] → PyTorch, transformers, sentence-transformers, scikit-learn, umap-learn
 - [viz] → plotly, matplotlib, kaleido
 - [transcription] → Groq Whisper (requer GROQ_API_KEY no .env)
 - [all] → tudo acima
 1 linha por extra. Nota sobre .env pra transcription]

## Arquitetura

[Diagrama de texto simples:]
  plugins/ → core (discovery, deps, cache) → API REST → consumers
[2-3 frases: core é agnóstico, plugins fazem o trabalho, consumers interpretam]

## Ecossistema

[2-3 linhas: qualia-coding (plugin Obsidian) consome a API pra codificação
 qualitativa cross-media. Qualia não sabe o que os dados significam — quem
 interpreta é o consumer]

## Status

[1 bloco compacto: 776 testes, 90% coverage, 8 plugins, API + CLI + frontend (Svelte, dark theme).
 CI no GitHub Actions. MIT license]
```

## Tom e estilo

- Direto, sem forçar
- Primeira pessoa evitada — o texto descreve o que o software faz, não o que "nós" fazemos
- Sem slogan, sem tagline, sem badges de "awesome"
- Termos técnicos quando necessários, mas explicados na primeira ocorrência
- Português claro — sem tradução forçada de termos que são melhores em inglês (plugin, cache, pipeline, consumer)
- Exemplos de código reais e funcionais (copia-e-cola funciona)

## O que NÃO entra

- Comparação explícita com NVivo/ATLAS.ti (mencionados no "por que", não como tabela comparativa)
- Roadmap (fica no BACKLOG.md)
- Detalhes de internals do engine (fica no TECHNICAL_STATE.md)
- Instruções de deploy/Docker (fica em docs/)
- Histórico de mudanças (fica no git)
