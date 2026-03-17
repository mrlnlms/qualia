#!/bin/bash
# quick_fixes.sh

# 1. Criar arquivo de pipeline exemplo
mkdir -p configs/pipelines

cat > configs/pipelines/example.yaml << 'EOF'
name: example_pipeline
description: Pipeline de exemplo para análise de transcrições
steps:
  - plugin: teams_cleaner
    config:
      remove_timestamps: false
      remove_system_messages: true
  - plugin: word_frequency
    config:
      min_word_length: 4
      remove_stopwords: true
EOF

echo "✅ Pipeline exemplo criado"

# 2. Correção do teams_cleaner - adicionar context vazio no CLI
echo "
⚠️  Para corrigir o erro do teams_cleaner, edite cli.py:

No comando 'process', procure a linha:
    result = core.execute_plugin(plugin, doc, params)

E mude para:
    result = core.execute_plugin(plugin, doc, params, {})

Ou seja, adicione {} como context vazio.
"

# 3. Criar mais arquivos de exemplo
echo "Criando arquivos de teste..."

cat > transcript_example.txt << 'EOF'
[00:00:00] Sistema: Recording Started
[00:00:05] João Silva: Bom dia pessoal, vamos começar nossa reunião semanal
[00:00:10] Maria Santos: Bom dia! Sim, podemos começar
[00:00:15] Sistema: Pedro Oliveira joined the meeting
[00:00:20] Pedro Oliveira: Oi, desculpem o atraso
[00:00:25] João Silva: Sem problemas Pedro. Vamos ao primeiro item da pauta
[00:00:30] Maria Santos: Sobre o projeto Qualia, temos novidades?
[00:00:35] Pedro Oliveira: Sim! O framework está funcional
[00:00:40] João Silva: Excelente notícia!
[00:00:45] Maria Santos: Podemos ver uma demo?
[00:00:50] Sistema: Pedro Oliveira is presenting
EOF

echo "✅ Transcrição exemplo criada"

echo "
🎯 Testes sugeridos:

1. Pipeline:
   qualia pipeline transcript_example.txt -c configs/pipelines/example.yaml -o results/

2. Process (após corrigir cli.py):
   qualia process transcript_example.txt -p teams_cleaner --save-as cleaned.txt

3. Análise da transcrição:
   qualia analyze transcript_example.txt -p word_frequency -o transcript_analysis.json
   qualia visualize transcript_analysis.json -p wordcloud_viz -o transcript_cloud.png
"