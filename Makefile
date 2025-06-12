# Makefile para Qualia Core
# IMPORTANTE: Salvar como "Makefile" (sem extensão)

.PHONY: help test test-quick test-unit test-integration test-api test-all clean install

# Python executável
PYTHON := python3

# Diretório de scripts
SCRIPTS_DIR := scripts

help: ## Mostra esta mensagem de ajuda
	@echo "Qualia Core - Comandos Disponíveis"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ""
	@echo "Uso: make [comando]"
	@echo "Ex:  make test"

# ==== INSTALAÇÃO ====

install: ## Instala dependências do projeto
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e .

install-dev: install ## Instala dependências + ferramentas de dev
	$(PYTHON) -m pip install pytest pytest-cov pytest-asyncio httpx

# ==== TESTES RÁPIDOS ====

test: ## Roda testes essenciais (rápido)
	@echo "🚀 Rodando testes essenciais..."
	@$(PYTHON) -m pytest tests/test_core.py -v -k "not slow"

test-quick: ## Validação rápida do sistema
	@echo "⚡ Validação rápida..."
	@$(PYTHON) -c "from qualia.core import QualiaCore; c=QualiaCore(); print(f'✅ Core OK - {len(c.discover_plugins())} plugins')"
	@$(PYTHON) -c "import qualia.api; print('✅ API OK')"

# ==== TESTES COMPLETOS ====

test-unit: ## Roda todos os testes unitários
	@echo "🧪 Rodando testes unitários..."
	@$(PYTHON) -m pytest tests/test_core.py tests/test_plugins.py -v

test-api: ## Testa a API REST
	@echo "🌐 Testando API..."
	@$(PYTHON) -m pytest tests/test_api.py -v

test-integration: ## Roda testes de integração
	@echo "🔗 Rodando testes de integração..."
	@$(PYTHON) -m pytest tests/test_integration.py -v

test-performance: ## Roda testes de performance
	@echo "⚡ Testando performance..."
	@$(PYTHON) -m pytest tests/test_performance.py -v

test-all: ## Roda TODOS os testes
	@echo "🧪 Rodando todos os testes..."
	@$(PYTHON) -m pytest tests/ -v

# ==== SUITE VISUAL ====

test-suite: ## Roda suite visual completa
	@echo "📊 Rodando suite visual..."
	@$(PYTHON) $(SCRIPTS_DIR)/test_suite.py

# ==== COBERTURA ====

coverage: ## Gera relatório de cobertura
	@echo "📊 Gerando cobertura..."
	@$(PYTHON) -m pytest tests/ --cov=qualia --cov-report=html --cov-report=term
	@echo "✅ Relatório em htmlcov/index.html"

# ==== EXECUÇÃO ====

run-api: ## Inicia a API REST
	$(PYTHON) run_api.py

run-dashboard: ## Inicia o Health Dashboard
	$(PYTHON) ops/monitoring/health_dashboard.py --port 8080

run-all: ## Inicia API e Dashboard
	@echo "🚀 Iniciando todos os serviços..."
	@$(MAKE) run-api & $(MAKE) run-dashboard

# ==== LIMPEZA ====

clean: ## Remove arquivos temporários
	@echo "🧹 Limpando..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "✅ Limpo!"

# ==== DOCKER ====

docker-build: ## Constrói imagem Docker
	docker build -t qualia-core:latest .

docker-run: ## Roda via Docker
	docker-compose up -d

# ==== ATALHOS ====

t: test ## Atalho para 'test'
ta: test-all ## Atalho para 'test-all'
c: coverage ## Atalho para 'coverage'


test: ## Roda testes pragmáticos
	@echo "🚀 Rodando testes pragmáticos..."
	@$(PYTHON) -m pytest tests/test_pragmatic.py -v

test-all: ## Roda todos os testes pragmáticos
	@echo "🧪 Rodando bateria completa..."
	@$(PYTHON) -m pytest tests/test_pragmatic.py -v