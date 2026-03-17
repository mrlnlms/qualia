#!/bin/bash
# cleanup_project.sh - Organiza e limpa o projeto Qualia

echo "🧹 Limpando e organizando o projeto Qualia..."
echo "==========================================="

# 1. Criar estrutura de organização
echo -e "\n📁 Criando estrutura de diretórios..."
mkdir -p archive/scripts_debug
mkdir -p archive/test_outputs
mkdir -p examples
mkdir -p docs/notebooks

# 2. Mover scripts de debug/fix para archive
echo -e "\n📦 Arquivando scripts de debug..."
mv check_execute_plugin.py archive/scripts_debug/ 2>/dev/null
mv debug_*.py archive/scripts_debug/ 2>/dev/null
mv fix_*.py archive/scripts_debug/ 2>/dev/null
mv final_fixes.py archive/scripts_debug/ 2>/dev/null
mv quick_fixes.sh archive/scripts_debug/ 2>/dev/null

# 3. Mover outputs de teste para archive
echo -e "\n📦 Arquivando outputs de teste..."
mv test_*.py archive/scripts_debug/ 2>/dev/null
mv test_*.png archive/test_outputs/ 2>/dev/null
mv test_*.html archive/test_outputs/ 2>/dev/null
mv test_*.svg archive/test_outputs/ 2>/dev/null
mv test_*.json archive/test_outputs/ 2>/dev/null

# 4. Mover arquivos cleaned_* para examples
echo -e "\n📝 Movendo exemplos..."
mv cleaned_*.txt examples/ 2>/dev/null
mv cleaned.txt examples/ 2>/dev/null
mv transcript*.txt examples/ 2>/dev/null
mv demo_transcript.txt examples/ 2>/dev/null 

# 5. Mover outputs soltos para results
echo -e "\n📊 Organizando resultados..."
mv *.png results/ 2>/dev/null
mv *.html results/ 2>/dev/null
mv *.svg results/ 2>/dev/null
mv freq*.json results/ 2>/dev/null
mv speaker_analysis.json results/ 2>/dev/null

# 6. Mover documentos de teste
mv doc_teste.txt examples/ 2>/dev/null
mv test_doc.txt examples/ 2>/dev/null

# 7. Criar .gitignore se não existir
echo -e "\n📄 Atualizando .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Qualia específico
cache/
output/
results/
archive/
*.log

# Temporários
*.tmp
*.bak
*~

# Notebooks
.ipynb_checkpoints/

# Coverage
.coverage
htmlcov/
.pytest_cache/
EOF

# 8. Criar README para pastas
echo -e "\n📝 Criando READMEs..."

cat > archive/README.md << 'EOF'
# Archive

Esta pasta contém scripts e outputs antigos que foram usados durante o desenvolvimento.

## Conteúdo
- `scripts_debug/` - Scripts de debug e correção usados durante desenvolvimento
- `test_outputs/` - Outputs de teste antigos

Estes arquivos são mantidos para referência histórica.
EOF

cat > examples/README.md << 'EOF'
# Examples

Exemplos de uso do Qualia Core.

## Arquivos
- `transcript*.txt` - Exemplos de transcrições
- `cleaned*.txt` - Exemplos de transcrições limpas
- `demo_transcript.txt` - Transcrição usada na demonstração

## Como usar
```bash
qualia analyze examples/transcript_example.txt -p word_frequency
```
EOF

# 9. Limpar cache se existir
echo -e "\n🗑️  Limpando cache..."
rm -rf cache/* 2>/dev/null

# 10. Listar estrutura final
echo -e "\n✅ Limpeza concluída! Estrutura final:"
echo "======================================"
tree -L 2 -I 'venv|__pycache__|*.egg-info' 2>/dev/null || ls -la

echo -e "\n📊 Resumo:"
echo "- Scripts de debug → archive/scripts_debug/"
echo "- Outputs de teste → archive/test_outputs/"
echo "- Exemplos → examples/"
echo "- Resultados → results/"

echo -e "\n💡 Próximos passos:"
echo "1. git add -A"
echo "2. git commit -m 'feat: implement visualize command and base classes'"
echo "3. git tag v0.1.0"
echo "4. git push origin main --tags"