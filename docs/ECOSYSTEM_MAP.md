# Mapa do Ecossistema Qualia

Levantamento completo dos 5 projetos que compõem o ecossistema de análise qualitativa. Documento de referência para planejamento de migração de funcionalidades pro Qualia Core.

Data: 2026-03-18

---

## Visão Geral

```
                         ┌─────────────────┐
                         │   Qualia Core    │  Engine genérico
                         │  (API REST)      │  texto → JSON
                         └────────┬────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
     ┌────────▼──────┐  ┌────────▼──────┐  ┌────────▼──────┐
     │   DeepVoC     │  │ Observatório  │  │   whats-le    │
     │  (pesquisa    │  │    VoC        │  │  (análise     │
     │  qualitativa) │  │ (surveys)     │  │   WhatsApp)   │
     └───────────────┘  └───────────────┘  └───────────────┘
              │
     ┌────────▼──────┐
     │  transcript-  │  (predecessor do Qualia,
     │  analyser     │   agora legado)
     └───────────────┘
```

---

## Qualia Core (este repo)

**O que é:** API REST local stateless. Recebe texto/áudio/vídeo, devolve JSON. Motor agnóstico — não sabe o que os dados significam.

**Stack:** Python 3.13, FastAPI, pytest (772 testes, 90% coverage)

**Plugins atuais (8):**
- Analyzers: `word_frequency`, `sentiment_analyzer`, `readability_analyzer`
- Document: `teams_cleaner`, `transcription`
- Visualizers: `wordcloud_d3`, `frequency_chart_plotly`, `sentiment_viz_plotly`

**Infra pronta:** auto-discovery, DependencyResolver (topológico), cache LRU/TTL, ConfigurationRegistry, provides/requires, BaseClass serializa visualizações.

---

## DeepVoC — Análise Qualitativa Profunda

**Path:** `/Users/mosx/Desktop/DeepVoC`

**O que é:** Pipeline completo de pesquisa qualitativa para VoC (Voice of Customer). Pega respostas abertas de surveys, gera embeddings, clusteriza, faz BERTopic, análise de sentimento com RoBERTa, e automatiza análise qualitativa P1/P2/P3 via Claude Code CLI.

**Peças-chave:**
- `src/embeddings.py` — SentenceTransformer (MiniLM, MPNet) + MiniBatchKMeans clustering
- `src/sentiment.py` — RoBERTa multilingual, DistilBERT, DeBERTa (modelos reais de ML, não lexicon)
- `src/analysis.py` — NPS segmentation, co-ocorrência de temas, LDA topic modeling, detecção de anomalias temporais
- `src/qualitative.py` — Automação de análise qualitativa via Claude Code CLI (P1=meta-temas, P2=profiling, P3=consolidação)
- `src/pipeline.py` — Orquestra 12+ notebooks Quarto em sequência (data quality → embedding → BERTopic → síntese → ACM → power analysis)

**Projetos reais:** `club`, `churn`, `cob`, `shop`, `voebiz`, `inativos`, `club_cross`

**Stack pesada:** PyTorch, transformers, sentence-transformers, scikit-learn, BERTopic, UMAP, HDBSCAN

---

## Observatório VoC — Metadados e Operação de Surveys

**Path:** `/Users/mosx/Desktop/observatorio-voc`

**O que é:** Site Quarto que analisa a operação dos surveys — não o conteúdo das respostas, mas a eficiência do processo de coleta. Consolidação de dados Qualtrics (Distribution History + Survey Responses).

**Peças-chave:**
- `qualtrics/pipeline/readers.py` — Lê CSVs/Parquets do Qualtrics
- `qualtrics/pipeline/consolidate.py` — Join distribution + responses
- `qualtrics/pipeline/enrich.py` — Detecta ondas (waves), cohorts, tipo de envio, reminders
- `qualtrics/pipeline/flags.py` — Bounce flags
- `qualtrics/pipeline/context.py` — Métricas de contexto por segmento

**5 perspectivas analíticas:**
1. Distribuição (delivery → open → click → start → completion → conversion)
2. Preenchimento (tempo resposta, jornada, qualidade, psicometria)
3. Inferência (amostra, intervalos, poder, viés, testes)
4. Cobertura (penetração, saturação, representatividade, engajamento)
5. Transversal (ondas, invites/reminders, cohorts, domínios)

**Projetos reais:** `VoeBiz`, `Club`, `COB`, `SHOP`, `Churn_Club`, `COB_Inativos`

**Stack:** Polars (não pandas — performance pra 500k+ rows), Quarto website

---

## whats-le — Análise de WhatsApp

**Path:** `/Users/mosx/Desktop/local-workbench/whats-le`

**O que é:** Pipeline de análise de chat WhatsApp. Parsing → limpeza → enrichment → análises → visualizações. Focado em padrões de comunicação (2 pessoas, 44k mensagens, 15 meses).

**Peças-chave:**
- `data-wrangling/scripts/whatsapp_wrangler.py` — Parse raw export → mensagens estruturadas (238 linhas)
- `data-wrangling/scripts/reprocess_chat_clean.py` — Feature enrichment (35 colunas)
- `encontros_dates.py` — 10 viagens mapeadas com contexto relacional
- Notebooks Quarto: descriptive stats, advanced analyses, trip exploration, emoji analysis

**Dados processados:**
- 44,956 mensagens com 35 features (temporal, texto, interação, sentimento, contexto relacional)
- 1,047 transcrições de áudio (Groq Whisper)
- Sentimento BERT pré-computado

**Stack:** pandas, plotly, Quarto, Groq API

---

## transcript-analyser — Predecessor do Qualia (legado)

**Path:** `/Users/mosx/Desktop/local-workbench/transcript-analyser`

**O que é:** Sistema modular de análise de entrevistas transcritas. Predecessor direto do Qualia — arquitetura quase idêntica (auto-discovery, ConfigurationRegistry, schemas com text_size adjustments).

**9 analyzers:**
1. `word_frequency` — frequência de palavras
2. `temporal_analysis` — evolução emocional ao longo do texto
3. `global_metrics` — sentimento geral, coerência, abertura emocional
4. `linguistic_patterns` — hesitações, certeza/incerteza, complexidade
5. `sentiment_analysis` — polaridade baseada em léxico
6. `topic_modeling` — extração de temas (keyword-based, LDA, NMF, LSA)
7. `concept_network` — rede de co-ocorrência semântica
8. `contradiction_detection` — detecta inconsistências
9. `test_velocity` — mock para benchmarks

**8 charts:** timeline, wordcloud, frequency, network, metrics, patterns, topics, contradictions

**Extras:** lexicons PT-BR (stopwords, emocionais positivos/negativos, modalizadores certeza, hesitação, conectores discursivos), profiles (academic, interview, medical), calibração por text_size

**Stack:** NLTK, TextBlob, NetworkX, plotly, matplotlib, scikit-learn

---

## Candidatos a Migração pro Qualia

### Camada NLP Pesada (do DeepVoC)

| Componente | Plugin Qualia | Tipo | Provides |
|------------|--------------|------|----------|
| `embeddings.py` — SentenceTransformer | `embedding_generator` | Analyzer | `embeddings`, `embedding_model` |
| MiniBatchKMeans/HDBSCAN | `kmeans_clustering` | Analyzer | `clusters`, `centroids`, `labels` |
| BERTopic pipeline | `bertopic_modeling` | Analyzer | `topics`, `topic_distribution` |
| RoBERTa/DistilBERT sentiment | `sentiment_roberta` | Analyzer | `sentiment_score`, `sentiment_label` |
| LDA topic modeling | `lda_topics` | Analyzer | `lda_topics`, `topic_distribution` |

### Camada Linguística (do transcript-analyser)

| Componente | Plugin Qualia | Tipo | Provides |
|------------|--------------|------|----------|
| Evolução temporal | `temporal_evolution` | Analyzer | `temporal_analysis`, `segments` |
| Padrões linguísticos | `linguistic_patterns` | Analyzer | `hesitations`, `certainty_markers`, `complexity` |
| Rede de conceitos | `concept_network` | Analyzer | `concept_network`, `centrality` |
| Detecção contradições | `contradiction_detection` | Analyzer | `contradictions` |
| Métricas globais | `global_metrics` | Analyzer | `global_sentiment`, `coherence`, `emotional_openness` |

### Camada Document Processing (do whats-le e observatório)

| Componente | Plugin Qualia | Tipo | Provides |
|------------|--------------|------|----------|
| WhatsApp wrangler | `whatsapp_cleaner` | Document | `cleaned_document`, `messages`, `speakers` |
| Qualtrics consolidation | `qualtrics_consolidator` | Document | `consolidated_data`, `waves`, `cohorts` |
| Enrichment temporal | `temporal_features` | Analyzer | `hour`, `day_of_week`, `is_weekend`, `gap_hours` |
| Enrichment texto | `text_features` | Analyzer | `word_count`, `char_count`, `has_emoji`, `has_question` |
| Emoji analysis | `emoji_analyzer` | Analyzer | `emoji_list`, `emoji_count`, `top_emojis` |
| Communication patterns | `communication_patterns` | Analyzer | `response_time`, `consecutive_msgs`, `is_conversation_start` |

### Camada Visualização

| Componente | Plugin Qualia | Tipo | Requires |
|------------|--------------|------|----------|
| Timeline emocional | `timeline_plotly` | Visualizer | `temporal_analysis` |
| Grafo de conceitos | `network_plotly` | Visualizer | `concept_network` |
| Heatmap dia×hora | `heatmap_plotly` | Visualizer | `temporal_features` |
| Dendrograma clusters | `dendrogram_plotly` | Visualizer | `clusters`, `centroids` |
| Hierarquia tópicos | `topics_plotly` | Visualizer | `topics` |
| Padrões linguísticos | `patterns_plotly` | Visualizer | `hesitations`, `certainty_markers` |
| Contradições | `contradictions_plotly` | Visualizer | `contradictions` |
| Métricas dashboard | `metrics_plotly` | Visualizer | `global_sentiment`, `coherence` |

### Recursos Compartilhados (do transcript-analyser)

| Recurso | Uso |
|---------|-----|
| `stopwords_custom.txt` | Stopwords PT-BR para analyzers |
| `emocionais_positivos.txt` | Léxico positivo para sentiment |
| `emocionais_negativos.txt` | Léxico negativo para sentiment |
| `modalizadores_certeza.txt` | Marcadores de certeza para linguistic_patterns |
| `hesitacao_termos.txt` | Marcadores de hesitação para linguistic_patterns |
| `conectores_discursivos.txt` | Conectores para concept_network |

---

## Observações

**Divisão natural:**
- Observatório → mais relação com visualizers e análise operacional/estatística
- DeepVoC + transcript-analyser → mais relação com analyzers (NLP, ML, linguística)
- whats-le → misto (document processing + enrichment + visualização)

**Duas direções de complexidade:**
1. **NLP/ML pesado** (DeepVoC) — embeddings, clustering, BERTopic, transformers. Exige GPU, modelos GB, execução longa
2. **Análise leve** (Observatório, whats-le, transcript-analyser) — parsing, enrichment, estatísticas, visualizações. Roda instantâneo, sem deps pesadas

**O transcript-analyser é legado** — o Qualia nasceu dele. A migração de volta (TA → plugins Qualia) fecha o ciclo.
