.PHONY: help tools test lint plan apply destroy clean validate-metrics

TERRAFORM_DIR := infra/terraform/stacks/pr-preview
PR_NUMBER ?= 123

help: ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

tools: ## Verificar herramientas instaladas
	@echo "Verificando herramientas..."
	@command -v terraform >/dev/null 2>&1 || { echo "terraform no instalado"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "docker requerido"; exit 1; }
	@python3 -m pytest --version >/dev/null 2>&1 || { echo "pytest no instalado"; exit 1; }
	@command -v jq >/dev/null 2>&1 || { echo "jq requerido"; exit 1; }
	@echo "✓ Todas las herramientas disponibles"

test: ## Ejecutar pytest con cobertura ≥90%
	PYTHONPATH=. python3 -m pytest -vv --cov=src --cov=tests --cov-report=term --cov-report=html --cov-report=json:coverage.json --cov-fail-under=90

lint: ## Ejecutar linters Python y Terraform
	@echo "Ejecutando linters..."
	@if command -v black >/dev/null 2>&1; then black .; fi
	@if command -v flake8 >/dev/null 2>&1; then flake8 .; fi
	terraform -chdir=$(TERRAFORM_DIR) fmt -check -recursive

plan: tools ## Terraform plan con validación completa
	@echo "0. Inicializando Terraform..."
	@if [ ! -d "$(TERRAFORM_DIR)/.terraform" ]; then terraform -chdir=$(TERRAFORM_DIR) init; fi
	@echo "1. Formateando..."
	terraform -chdir=$(TERRAFORM_DIR) fmt -check
	@echo "2. Validando..."
	terraform -chdir=$(TERRAFORM_DIR) validate
	@echo "3. Generando plan..."
	terraform -chdir=$(TERRAFORM_DIR) plan -var="pr_number=$(PR_NUMBER)" -out=tfplan

apply: ## Terraform apply (requiere plan exitoso)
	terraform -chdir=$(TERRAFORM_DIR) apply tfplan

destroy: ## Terraform destroy
	terraform -chdir=$(TERRAFORM_DIR) destroy -var="pr_number=$(PR_NUMBER)" -auto-approve

clean: ## Limpiar archivos temporales
	@echo "Limpiando archivos temporales..."
	rm -f $(TERRAFORM_DIR)/tfplan
	rm -f $(TERRAFORM_DIR)/drift_check.tfplan
	rm -rf .pytest_cache htmlcov .coverage
	rm -f coverage.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

validate-metrics: ## Validar métricas finales (cobertura 92%, drift 0%)
	./scripts/validate-metrics.sh

metrics-collect: ## Recolectar métricas de operación
	./scripts/metrics-collector.sh collect deploy $(PR_NUMBER)

metrics-report: ## Generar reporte de métricas
	./scripts/metrics-collector.sh report

cleanup-verify: ## Verificar recursos huérfanos
	./scripts/verify-cleanup.sh $(PR_NUMBER)

cleanup-auto: ## Ejecutar limpieza automática
	./scripts/auto-cleanup.sh

dashboard: ## Generar dashboard de trends
	./scripts/trends-monitor.sh

status: ## Mostrar estado actual del proyecto
	@echo "Estado del proyecto:"
	@if [ -f $(TERRAFORM_DIR)/terraform.tfstate ]; then echo "State file existe"; else echo "No hay state file"; fi
	@docker ps -a --filter "label=environment=ephemeral" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | wc -l | xargs echo "Contenedores efímeros:"
	@if [ -f metrics/operations.json ]; then jq '.operations | length' metrics/operations.json | xargs echo "Operaciones registradas:"; else echo "No hay métricas"; fi
