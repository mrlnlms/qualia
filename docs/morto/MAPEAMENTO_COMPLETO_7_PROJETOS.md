# Mapa Completo de Desenvolvimento: 7 Projetos → Qualia Cloud

> Documento gerado em Fevereiro/2026 — revisão consolidada de todos os projetos de análise desenvolvidos, mapeando a evolução desde o protótipo original até a visão de plataforma (Qualia Cloud).

## Contexto

### Os 7 projetos

| Projeto | Local | O que é | Época |
|---------|-------|---------|-------|
| **transcript-analyser-prototype** | `local-workbench/` | Protótipo: scripts soltos de análise de transcrições | Jan 2025 |
| **transcript-analyser** V2.1 | `local-workbench/` | Evolução modular: 9 analyzers + auto-discovery + configs | Jun 2025 |
| **Qualia Core** v0.2.0 | `Desktop/qualia/` | Framework bare-metal: plugins + API + infra | Dez 2024 |
| **DeepVoC** | `Desktop/DeepVoC/` | Pipeline BERTopic + LLM para feedbacks de pesquisa | 2025-2026 |
| **Observatório VoC** | `Desktop/observatorio-voc/` | Diagnóstico de programas VoC no Qualtrics | 2025-2026 |
| **WhatsApp DS Analytics** | `Desktop/Whatsapps Project/` | Pipeline DS para análise de conversas WhatsApp (v1) | Nov-Dez 2025 |
| **whats-le** | `local-workbench/whats-le/` | Evolução do WhatsApp analytics com features enriquecidas (v2) | Nov 2025 |

### Linha evolutiva

```
Prototype (scripts) → Analyser V2 (modular) → Qualia (framework + API)
                                                       ↑
                                    DeepVoC (ML/NLP) ──┘
                                    Observatório (ETL/Stats) ──┘
                                    WhatsApp DS (conversational) ──┘
```

---

## Projetos originais: Transcript Analyser

### Prototype (scripts soltos, ~7.000 linhas)

8 scripts Python com 11 tipos de análise, todos em português:
- `interview_analyzer_v4.py` (1268 linhas) — versão mais completa
- `smart-analyzer.py` (752 linhas) — comparação inteligente entre textos
- `interview_visualizer_v2.py` (1230 linhas) — suite de visualizações

**Capacidades:** word frequency, sentiment (léxico), topic modeling (LDA), análise temporal/narrativa, padrões linguísticos (hesitação, certeza/incerteza), detecção de contradições, redes conceituais, comparação multi-texto, geração de hipóteses.

**Limitações:** hardcoded, sem API, sem testes, sem Git, código duplicado entre versões.

### Analyser V2.1-beta (modular, ~5.000 linhas)

Evolução para sistema plug-and-play:
- 9 analyzers auto-descobertos com 60 parâmetros configuráveis via JSON
- 8 tipos de gráfico com fallback 3-tier (Plotly → Matplotlib → Text)
- `ConfigurationRegistry` com schemas e 3 perfis (academic, interview, medical)
- Auto-ajuste por tamanho de texto
- Dependency resolution (topological sort)
- Git versionado (V1 → V2 → V2.1)
- CLI com project management

**O que migrou para o Qualia:** auto-discovery, dependency resolution, plugin architecture, configuração por schema — a fundação conceitual.

---

## Qualia Core v0.2.0 (Dez/2024)

Framework bare-metal para análise qualitativa. O core não sabe nada sobre domínio — tudo vem via plugins auto-descobertos.

**Stack:** Python 3.9+ | FastAPI | Click (CLI) | Rich (TUI) | NLTK/TextBlob | Matplotlib/Plotly | Docker

**Arquitetura:**
```
qualia/
├── core/          → Motor agnóstico: discovery, dependências, cache, pipelines
├── api/           → FastAPI REST (11+ endpoints) + webhooks + monitor SSE
├── cli/           → 13 comandos + menu interativo (Rich TUI)
plugins/           → 6 plugins funcionais (auto-descobertos)
ops/               → Circuit breaker, Sentry, backups, health checks
configs/           → Pipelines em YAML
docs/              → ~30 arquivos MD
```

**6 plugins existentes:** `word_frequency`, `sentiment_analyzer`, `teams_cleaner`, `wordcloud_viz`, `frequency_chart`, `sentiment_viz`

**Infra completa:** Docker multi-stage, nginx, circuit breaker, Sentry, backups automáticos, health dashboard SSE, webhooks genéricos.

**API automática:** Qualquer plugin em `/plugins/` fica disponível via REST instantaneamente — `POST /analyze/{plugin_id}`, `POST /visualize/{plugin_id}`, etc. Auto-documentado no Swagger (`/docs`).

---

## DeepVoC (2025-2026)

Framework end-to-end para análise de feedbacks abertos de pesquisas de satisfação (Smiles). Combina BERTopic com análise qualitativa via LLM (Claude).

**Stack:** Python 3.14 | BERTopic + HDBSCAN + UMAP | Sentence-Transformers (MiniLM-384d) | Quarto | Plotly | Claude Code CLI

**Pipeline em 3 Fases:**

1. **Quantitativa (~10min):** Parquet → Filtro qualidade → Embeddings 384d → BERTopic (UMAP→HDBSCAN→c-TF-IDF) → Hierarquia 3 níveis → Perfil temporal → Co-ocorrência
2. **Qualitativa (~20min):** P1 (4 Sonnet por meta-tema) → P2 (1 Opus cruzamento) → P3 (4 Sonnet narrativas) → P4 (síntese executiva)
3. **Visualização (~5min):** Cards → Relatório HTML → Segmentação ACM → Parquet enriquecido (286 colunas)

**6 projetos ativos:** club (23k), cob (9k), churn (2.3k), shop (1.3k), voebiz (900), inativos (130)

**Destaques:** Parâmetros adaptativos por corpus, fallback inteligente, templates centralizados, multi-projeto via `setup.yaml`.

---

## Observatório VoC (2025-2026)

Framework de diagnóstico e analytics para programas de pesquisa VoC rodando no Qualtrics. Integra dados de distribuição (email) com respostas de pesquisa.

**Stack:** Python 3.14 | Polars | Quarto | Plotly | Kaleido | Parquet

**3 Camadas Diagnósticas:**
1. **Coleta:** Distribuição (entrega→abertura→clique) + Preenchimento (início→conclusão)
2. **Validação:** Speeders, straightliners, power analysis
3. **Inteligência:** Alcance único, saturação, fadiga, ROI

**+ 5 perspectivas transversais:** Waves, Convites/Lembretes, Cohorts, Pipeline, Domínios

**6 projetos ativos:** Club (2.4M registros, 1M clientes), COB (587K), VoeBiz (152K), Churn (107K), SHOP (80K), COB_Inativos (36K)

**Destaques:** Polars (5-10x mais rápido que pandas), non-destructive tagging, 53 QMDs de documentação, template master v12 (823KB), análises avançadas no Club (sobrevivência, NPS+clustering, power, drivers, bridges).

---

## WhatsApp DS Analytics (Nov-Dez 2025)

Pipeline de Data Science completo para analisar exportações de WhatsApp. Duas versões: v1 (Whatsapps Project) e v2 (whats-le), mesma ideia com refinamento progressivo.

**Stack:** Python 3.11-3.13 | pandas | Quarto | Transformers (RoBERTa, DistilBERT, DeBERTa) | Groq Whisper | scikit-learn | Plotly

**Caso de estudo:** ~92-97k mensagens ao longo de 14 meses entre 2 participantes, com integração de 10 encontros presenciais como contexto externo.

**Pipeline:**
```
Export WhatsApp (.txt, ~97K linhas)
    → Profiling (investigação sem modificar)
    → Cleaning (7 etapas: Unicode, timestamps, anonimização)
    → Wrangling (21 tipos de msg, multiline, media linking)
    → Feature Engineering (43 features: temporal, texto, conversacional, contexto)
    → Sentiment (4 modelos BERT, ensemble, 91K msgs analisadas)
    → Transcrição de áudio/vídeo (Groq Whisper, ~700 arquivos)
    → Clustering (K-means, PCA, MCA)
    → EDA + Análises Avançadas
    → Relatórios HTML via Quarto
```

**Destaques:**
- Parser robusto para 15+ edge cases do WhatsApp (Unicode invisível, multiline, batch media, mensagens editadas/deletadas)
- 43 features enriquecidas em 5 categorias (temporal, texto, conversacional, contexto, modelos)
- Transcrição automática de áudio com Groq Whisper (resumable, ~40min para 700 arquivos)
- Sentiment ensemble com 4 modelos BERT + confidence scores
- Análise de impacto de encontros presenciais (10 viagens rastreadas)
- Arquitetura modular: lógica em `src/`, apresentação em `notebooks/`, operações pesadas em `scripts/`
- Audit trail para cada transformação
- Privacy-first: dados não versionados, suporte a anonimização

**v2 (whats-le) adiciona:** 31 features enriquecidas com métricas comportamentais (tempo_resposta, msgs_seguidas, is_conversation_start), melhor tratamento de edge cases, documentação extensiva.

---

## Direção Estratégica: Qualia Cloud

**Visão:** Qualia evolui de framework local para plataforma de análise completa, onde qualquer operação — leve ou pesada — é acessível via API.

**Arquitetura-alvo:**

```
┌─────────────────────────────────────────────────────────────┐
│                      QUALIA CLOUD                            │
│                                                              │
│  API Layer (FastAPI)                                         │
│  ├── Sync endpoints   → operações <5s (NPS, sentiment)      │
│  ├── Async tasks      → operações 5s-5min (embeddings)      │
│  └── Worker queue     → operações >5min (BERTopic corpus)   │
│                                                              │
│  Task Manager                                                │
│  ├── POST /tasks      → aceita job, retorna task_id         │
│  ├── GET  /tasks/{id} → status + progresso + ETA            │
│  └── SSE  /tasks/{id}/stream → progresso real-time          │
│                                                              │
│  Plugin Engine (core atual + evoluções)                      │
│  ├── Plugins de texto     (sentiment, word_freq, quality)   │
│  ├── Plugins estatísticos (NPS, power, survival, drivers)   │
│  ├── Plugins ML           (embeddings, UMAP, HDBSCAN)       │
│  ├── Plugins de qualidade (speeder, straightliner)           │
│  └── Plugins visuais      (wordcloud, sankey, charts)       │
│                                                              │
│  Resource Manager (modelos ML carregados uma vez)            │
│  Cache Layer (SHA256 → resultados reutilizáveis)            │
│  Worker Pool (Celery/Redis para jobs pesados)                │
└──────────────┬──────────────────┬────────────────────────────┘
               │                  │
    ┌──────────▼──────┐  ┌───────▼──────────────┐
    │    DeepVoC       │  │  Observatório VoC     │  │  WhatsApp DS   │
    │  (consome API)   │  │  (consome API)        │  │  (consome API) │
    │  Orquestração +  │  │  ETL + Templates +    │  │  Parser +      │
    │  Pipeline LLM    │  │  Relatórios Quarto    │  │  EDA + Quarto  │
    └─────────────────┘  └───────────────────────┘  └────────────────┘
```

**Princípio:** Uma vez que a infra async + workers está pronta, o peso do processamento deixa de ser limitante. O foco passa a ser 100% nos plugins. Qualquer plugin roda — de 50ms a 10 minutos — a API aceita, enfileira, processa e entrega.

**Evolução natural:**
1. Background tasks (threads locais) → funciona na máquina local
2. Worker queue (Celery + Redis) → escala para múltiplos clientes
3. Mesma interface para o consumidor em ambos os cenários

---

## O que VIRA plugin (todos os projetos)

### Fase 1 — Drop-in (zero mudança no core)

| Plugin | Origem | Tipo | O que faz |
|--------|--------|------|-----------|
| `text_quality_filter` | DeepVoC `nlp_filters.py` | Filter | Marca textos inúteis (<3 palavras, "ok", "n/a", vazio) |
| `nps_analyzer` | Observatório | Analyzer | Cálculo NPS (promoters/detractors/passives) |
| `power_analyzer` | Ambos | Analyzer | Poder estatístico (sample size, effect size) |
| `speeder_detector` | Observatório `flags.py` | Filter | Detecta respostas rápidas demais |
| `straightliner_detector` | Observatório `flags.py` | Filter | Detecta variância zero em matrizes |
| `linguistic_patterns` | Prototype v4 / Analyser V2 | Analyzer | Hesitação, certeza/incerteza, complexidade |
| `contradiction_detector` | Prototype v4 / Analyser V2 | Analyzer | Inconsistências narrativas (sentimento oposto no mesmo tópico) |
| `concept_network` | Prototype v4 / Analyser V2 | Analyzer | Rede de co-ocorrência com centralidade e comunidades |
| `temporal_narrative` | Prototype v4 / Analyser V2 | Analyzer | Arco narrativo, evolução emocional por segmento |
| `global_metrics` | Prototype v4 / Analyser V2 | Analyzer | Abertura emocional, coerência temática, hesitações |
| `topic_modeler_lda` | Prototype v4 / Analyser V2 | Analyzer | Topic modeling via LDA/NMF/LSA |
| `network_viz` | Prototype visualizer | Visualizer | Grafos NetworkX de conceitos |
| `timeline_viz` | Prototype visualizer | Visualizer | Timeline emocional multi-painel |
| `whatsapp_parser` | WhatsApp DS | Document | Transforma export .txt em dados estruturados (21 tipos de msg, multiline, media) |
| `conversation_features` | WhatsApp DS | Analyzer | Tempo de resposta, sequências, iniciador, bursts, quick replies |

### Fase 2 — Requer suporte a dados estruturados no Document

| Plugin | Origem | Tipo | O que faz |
|--------|--------|------|-----------|
| `cooccurrence_analyzer` | DeepVoC | Analyzer | Matriz de co-ocorrência + Lift entre categorias |
| `funnel_analyzer` | Observatório | Analyzer | Taxas de funil (delivery, open, click, start, completion) |
| `driver_analyzer` | Observatório | Analyzer | Key drivers via importância relativa / Shapley |
| `sankey_viz` | DeepVoC | Visualizer | Diagrama Sankey de fluxos temáticos |
| `survival_analyzer` | Observatório | Analyzer | Kaplan-Meier + Cox Proportional Hazards |
| `wave_detector` | Observatório `enrich.py` | Analyzer | Segmentação temporal (monthly / gap-based) |
| `cohort_assigner` | Observatório `enrich.py` | Analyzer | Atribuição de cohort por primeira aparição |

### Fase 3 — Requer Corpus Mode (multi-documento)

| Plugin | Origem | Tipo | O que faz |
|--------|--------|------|-----------|
| `embedding_generator` | DeepVoC `embeddings.py` | Analyzer | Gera embeddings MiniLM-384d (parametrizável) |
| `umap_reducer` | DeepVoC | Analyzer | Reduz dimensionalidade (384d → 5d) |
| `hdbscan_clusterer` | DeepVoC | Analyzer | Clustering por densidade |
| `ctfidf_keywords` | DeepVoC | Analyzer | Extrai keywords representativas por cluster |
| `hierarchical_merger` | DeepVoC | Composer | Agrupa tópicos em meta-temas |
| `transformer_sentiment` | DeepVoC `sentiment.py` | Analyzer | Sentimento via RoBERTa/DistilBERT/DeBERTa |
| `acm_segmenter` | DeepVoC | Analyzer | Segmentação ACM (MCA + K-Means) |
| `temporal_classifier` | DeepVoC | Analyzer | Classifica temas: emergente/crônico/declinante |

---

## O que NÃO vira plugin (e por quê)

### Orquestração demais (pertence ao nível de pipeline)

| Funcionalidade | Origem | Por que não |
|----------------|--------|-------------|
| **Pipeline qualitativa LLM (P1-P4)** | DeepVoC | Spawna subprocessos Claude, parallelismo ThreadPoolExecutor, validação entre fases, retry logic. Plugin deve ser stateless e determinístico. |
| **Pipeline BERTopic completo** | DeepVoC | Como monolito não cabe. Decomposto em 5+ plugins (Fase 3). A orquestração fica no pipeline YAML do Qualia. |
| **ETL Pipeline (`run.py`)** | Observatório | 9 fases com aprovação interativa, multi-source, multi-format. É pré-Qualia, não dentro dele. |

### Domínio-específico demais

| Funcionalidade | Origem | Por que não |
|----------------|--------|-------------|
| **Reminder Linking** | Observatório | Transaction_Id + regex de Link — puro Qualtrics |
| **Bounce Flagging** | Observatório | Padrões SMTP, categorias Hard/Soft — infraestrutura de email |
| **Column Mapping** | DeepVoC | Normalização schema-specific por projeto |
| **Qualtrics CSV Reader** | Observatório | Header de 3 linhas, nomes de coluna Qualtrics-specific |
| **Wave Month Correction** | Observatório | Correção operacional específica do workflow |

### Requer infraestrutura que plugin não deve ter

| Funcionalidade | Origem | Por que não |
|----------------|--------|-------------|
| **Relatório HTML consolidado** | DeepVoC | Requer Quarto rendering engine |
| **Detecção interativa de waves** | Observatório | Requer stdin/stdout durante execução |
| **Export multi-formato** | Observatório | Concern de CLI/exportação, não de análise |
| **Transcrição Whisper (Groq)** | WhatsApp DS | Chamada API externa com retry, resumable, rate limiting — pertence a IExternalPlugin ou orquestração |
| **Análise de encontros presenciais** | WhatsApp DS | Dados de contexto externo específicos do caso de estudo |

---

## O que o Qualia Core precisa mudar

### Mudança 0 (Fundação): Task Manager + Async API

**Problema:** A API atual é síncrona. Operações pesadas (embeddings, clustering) causam timeout HTTP. Para funcionar como plataforma (Qualia Cloud), qualquer plugin precisa rodar sem bloquear a API.

**Solução:**
- `TaskManager` no core — aceita jobs, executa em background (ThreadPoolExecutor), reporta progresso
- Novos endpoints: `POST /tasks`, `GET /tasks/{id}`, `GET /tasks/{id}/stream` (SSE)
- O monitor SSE que já existe (`/monitor/stream`) serve de base
- Redis + Celery já estão no docker-compose — ativar quando escalar

**Arquivos:**
- `qualia/api/__init__.py` — novos endpoints de tasks
- `qualia/core/task_manager.py` — novo componente
- `docker-compose.yml` — ativar Redis worker

**Por que é a Mudança 0:** Sem isso, os plugins pesados das Fases 2 e 3 não funcionam via API. Com isso, qualquer plugin funciona independente do peso.

### Mudança 1: Suporte a dados estruturados

**Problema:** `Document.content` é `str`. Muitos plugins trabalham com dados tabulares.

**Solução:** Adicionar `Document.structured_data: Optional[Dict[str, Any]]` para dados não-textuais. Plugins declaram se esperam `content` (texto) ou `structured_data` (tabular/numérico).

**Arquivo:** `qualia/core/__init__.py` — classe `Document` (linhas 124-152)

### Mudança 2: Corpus Mode (multi-documento)

**Problema:** `execute_plugin()` recebe um `Document`. BERTopic, embeddings e clustering precisam de todos os documentos simultaneamente.

**Solução:** Introduzir `Corpus` como conceito (lista de Documents). Plugins declaram `scope: "document" | "corpus"` no metadata. Core roteia execução conforme scope.

**Arquivo:** `qualia/core/__init__.py` — `QualiaCore.execute_plugin()` (linhas 540-650)

### Mudança 3: Resource Manager (cache de modelos)

**Problema:** Plugins como `embedding_generator` e `transformer_sentiment` carregam modelos pesados (centenas de MB). Carregar a cada invocação é inviável.

**Solução:** `ResourceManager` no core — carrega modelo uma vez, compartilha entre invocações. Plugins declaram `resources_needed` no metadata.

**Arquivo:** Novo componente `qualia/core/resource_manager.py`

---

## Grafo de dependências entre plugins

```
  --- Cadeia Text/NLP (Prototype + DeepVoC) ---

                    ┌─────────────────┐
                    │ text_quality_    │
                    │ filter (Filter)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              v              v              v
     ┌────────────┐  ┌────────────┐  ┌────────────────┐
     │ embedding_  │  │ word_      │  │ sentiment_     │
     │ generator   │  │ frequency  │  │ analyzer       │
     └──────┬─────┘  └──────┬─────┘  └───────┬────────┘
            │               │                 │
            v               │                 v
     ┌────────────┐         │        ┌────────────────┐
     │ umap_      │         │        │ transformer_   │
     │ reducer    │         │        │ sentiment      │
     └──────┬─────┘         │        └───────┬────────┘
            │               │                 │
            v               v                 v
     ┌────────────┐  ┌────────────┐  ┌────────────────┐
     │ hdbscan_   │  │ wordcloud_ │  │ sentiment_viz  │
     │ clusterer  │  │ viz        │  │                │
     └──────┬─────┘  └────────────┘  └────────────────┘
            │
            v
     ┌────────────┐
     │ ctfidf_    │
     │ keywords   │
     └──────┬─────┘
            │
            v
     ┌────────────────┐     ┌──────────────────┐
     │ hierarchical_  │────>│ temporal_        │
     │ merger         │     │ classifier       │
     └───────┬────────┘     └──────────────────┘
             │
             v
     ┌────────────────┐     ┌──────────────────┐
     │ cooccurrence_  │────>│ sankey_viz       │
     │ analyzer       │     └──────────────────┘
     └────────────────┘

  --- Cadeia Transcript Analysis (Prototype) ---

     text_quality_filter
             │
     ┌───────┼────────┬──────────┬──────────────┐
     v       v        v          v              v
  linguistic temporal  concept   contradiction  topic_
  _patterns  _narrative _network _detector      modeler_lda
     │       │        │                         │
     v       v        v                         v
  global_   timeline_ network_                 wordcloud_
  metrics   viz       viz                      viz

  --- Cadeia Survey Diagnostics (Observatório) ---

     ┌────────────────┐
     │ survey_data    │
     │ (Document)     │
     └───────┬────────┘
             │
     ┌───────┼────────┬──────────┬──────────┐
     v       v        v          v          v
  speeder  straight  nps_     funnel_   power_
  detector liner_det analyzer analyzer  analyzer
     │       │        │          │
     v       v        v          v
           ┌──────────────┐  ┌──────────┐
           │ driver_      │  │ funnel_  │
           │ analyzer     │  │ viz      │
           └──────────────┘  └──────────┘

  --- Cadeia Conversational (WhatsApp) ---

     ┌────────────────┐
     │ whatsapp_      │
     │ parser (Doc)   │
     └───────┬────────┘
             │
     ┌───────┼────────┬──────────────┐
     v       v        v              v
  text_    conver-   transformer_  temporal_
  quality  sation_   sentiment    narrative
  filter   features  (BERT x4)
             │
             v
         embedding_generator → clustering
```

---

## Inventário consolidado: ~28.500 linhas de código entre 7 projetos

| Projeto | Linhas (est.) | Capacidades únicas |
|---------|--------------|-------------------|
| Prototype | ~7.000 | Análise narrativa, contradições, hipóteses, comparação multi-texto |
| Analyser V2 | ~5.000 | Auto-discovery, configs por JSON, 60 parâmetros, perfis |
| Qualia | ~3.500 | API REST, Docker, webhooks, monitoring, circuit breaker |
| DeepVoC | ~3.500 | BERTopic, embeddings, LLM qualitativa, ACM |
| Observatório | ~3.500 | ETL Qualtrics, survival analysis, funnel metrics, wave detection |
| WhatsApp v1 | ~3.500 | Parser WhatsApp, 43 features, Whisper transcrição, sentiment BERT |
| whats-le v2 | ~2.500 | 31 features enriquecidas, edge cases refinados, trip analysis |

## Resumo executivo

| Métrica | Valor |
|---------|-------|
| **Total de projetos** | 7 |
| **Plugins candidatos (drop-in)** | 15 (incluindo WhatsApp parser + conversation features) |
| **Plugins candidatos (structured_data)** | 7 |
| **Plugins candidatos (corpus mode)** | 9 |
| **Não vira plugin** | 10 |
| **Mudanças no core** | 4 (task manager, structured_data, corpus, resource cache) |

## Ordem de implementação recomendada

```
Mudança 0: Task Manager + Async API          <- habilita tudo, independente do peso
    |
    |-- Fase 1: 15 plugins drop-in            <- valor imediato, validam a plataforma
    |
    |-- Mudança 1: structured_data            <- desbloqueia plugins tabulares
    |   '-- Fase 2: 7 plugins estatísticos    <- survey diagnostics, funnel, drivers
    |
    |-- Mudança 2: Corpus Mode                <- desbloqueia ML multi-documento
    |   |-- Mudança 3: Resource Manager       <- cache de modelos pesados
    |   '-- Fase 3: 9 plugins ML              <- embeddings, BERTopic, segmentação
    |
    '-- DeepVoC + Observatório + WhatsApp consomem via API
```

**Conclusão:** O Qualia tem a arquitetura certa. A fundação (Task Manager async) habilita a plataforma independente do peso do processamento. A partir daí, 3 evoluções incrementais no core (structured_data, corpus, resource cache) desbloqueiam ~80% das funcionalidades dos dois projetos como plugins reutilizáveis.

A pipeline qualitativa LLM (P1-P4 do DeepVoC) e o ETL do Observatório ficam **fora** do Qualia — são orquestradores que consomem/alimentam a plataforma via API.

## Notas sobre embedding models

O plugin `embedding_generator` será parametrizável por modelo:

| Modelo | Dimensões | Velocidade | Caso de uso |
|--------|-----------|------------|-------------|
| `all-MiniLM-L6-v2` | 384d | Rápido | Textos curtos (surveys) — validado no DeepVoC |
| `all-mpnet-base-v2` | 768d | Médio | Maior precisão semântica |
| `multilingual-e5-large` | 1024d | Lento | Multilíngue forte (PT/EN/ES) |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384d | Rápido | Multilíngue leve |

O `ResourceManager` (Mudança 3) garante que o modelo é carregado uma vez e reutilizado entre invocações.

---

## Mapa completo: capacidades x projetos

| Capacidade | Prototype | Analyser V2 | Qualia | DeepVoC | Observatório | WhatsApp | Vira Plugin? |
|------------|:---------:|:-----------:|:------:|:-------:|:------------:|:--------:|:------------:|
| Word Frequency | v4 | plugin | plugin | — | — | — | Já existe |
| Sentiment (léxico) | v4 | plugin | plugin | — | — | — | Já existe |
| Sentiment (transformer) | — | — | — | ensemble | — | 4 modelos BERT | Fase 3 |
| Topic Modeling (LDA) | v4 | plugin | — | — | — | — | Fase 1 |
| Topic Modeling (BERTopic) | — | — | — | pipeline | — | — | Fase 3 |
| Temporal/Narrativa | v4 | plugin | — | perfil | — | heatmaps | Fase 1 |
| Contradições | v4 | plugin | — | — | — | — | Fase 1 |
| Redes Conceituais | v4 | plugin | — | co-ocorrência | — | — | Fase 1 |
| Padrões Linguísticos | v4 | plugin | — | — | — | — | Fase 1 |
| Hesitação | v4 | plugin | — | — | — | — | Fase 1 |
| Métricas Globais | v4 | plugin | — | — | — | — | Fase 1 |
| Comparação Textos | smart | — | — | — | — | — | Fase 2 |
| Embeddings (MiniLM) | — | — | — | pipeline | — | exploratório | Fase 3 |
| UMAP + HDBSCAN | — | — | — | pipeline | — | — | Fase 3 |
| Clustering Hierárquico | — | — | — | pipeline | — | K-means | Fase 3 |
| LLM Qualitativa (P1-P4) | — | — | — | pipeline | — | — | Não (orquestração) |
| ACM Segmentation | — | — | — | notebook | — | MCA | Fase 3 |
| NPS Analysis | — | — | — | — | notebook | — | Fase 1 |
| Power Analysis | — | — | — | notebook | notebook | — | Fase 1 |
| Survival Analysis | — | — | — | — | notebook | — | Fase 2 |
| Driver Analysis | — | — | — | — | notebook | — | Fase 2 |
| Funnel Metrics | — | — | — | — | pipeline | — | Fase 2 |
| Speeder/Straightliner | — | — | — | — | flags.py | — | Fase 1 |
| Wave Detection | — | — | — | — | enrich.py | — | Fase 2 |
| Cohort Analysis | — | — | — | — | enrich.py | — | Fase 2 |
| Teams Transcript Clean | — | — | plugin | — | — | — | Já existe |
| WhatsApp Parser | — | — | — | — | — | wrangler.py | Fase 1 |
| Conversation Features | — | — | — | — | — | 43 features | Fase 1 |
| Audio Transcription | — | — | — | — | — | Groq Whisper | Não (API ext.) |
| WordCloud | v2 | chart | plugin | — | — | — | Já existe |
| Timeline Emocional | v2 | chart | — | — | — | — | Fase 1 |
| Network Graph | v2 | chart | — | — | — | — | Fase 1 |
| Sankey Diagram | — | — | — | notebook | — | — | Fase 2 |
| REST API | — | — | FastAPI | — | — | — | Já existe |
| Docker | — | — | multi-stage | — | — | — | Já existe |
| Auto-discovery | — | V2.1 | core | — | — | — | Já existe |
| Config Schemas | — | V2.1 (60 params) | metadata | — | — | — | Já existe |

**Totais:** 37 capacidades identificadas. 4 já existem no Qualia. 15 drop-in. 7 precisam de structured_data. 9 precisam de corpus mode. 2 não viram plugin (orquestração/API externa).
