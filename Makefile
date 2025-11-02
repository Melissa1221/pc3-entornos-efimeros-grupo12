.PHONY: help tools test lint plan apply destroy clean

TERRAFORM_DIR := infra/terraform/stacks/pr-preview
PR_NUMBER ?= 1

help: ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

tools: ## Verificar herramientas instaladas
	@echo "Verificando herramientas..."
	@command -v terraform >/dev/null 2>&1 || { echo "terraform no instalado"; exit 1; }
	@command -v tflint >/dev/null 2>&1 || { echo "tflint no instalado"; exit 1; }
	@command -v tfsec >/dev/null 2>&1 || { echo "tfsec no instalado"; exit 1; }
	@command -v pytest >/dev/null 2>&1 || { echo "pytest no instalado"; exit 1; }
	@echo "✓ Todas las herramientas disponibles"

test: ## Ejecutar pytest con cobertura ≥90%
	pytest --cov-fail-under=90

lint: ## Ejecutar linters Python y Terraform
	@echo "Linting Python..."
	black --check src tests
	flake8 src tests
	@echo "Linting Terraform..."
	terraform -chdir=$(TERRAFORM_DIR) fmt -check -recursive

plan: tools ## Terraform plan con validación completa
	@echo "1. Formateando..."
	terraform -chdir=$(TERRAFORM_DIR) fmt -check
	@echo "2. Validando..."
	terraform -chdir=$(TERRAFORM_DIR) validate
	@echo "3. Ejecutando tflint..."
	cd $(TERRAFORM_DIR) && tflint
	@echo "4. Ejecutando tfsec..."
	tfsec $(TERRAFORM_DIR)
	@echo "5. Generando plan..."
	terraform -chdir=$(TERRAFORM_DIR) plan -var="pr_number=$(PR_NUMBER)" -out=tfplan

apply: ## Terraform apply (requiere plan exitoso)
	terraform -chdir=$(TERRAFORM_DIR) apply tfplan

destroy: ## Terraform destroy
	terraform -chdir=$(TERRAFORM_DIR) destroy -var="pr_number=$(PR_NUMBER)" -auto-approve

clean: ## Limpiar archivos temporales
	rm -rf $(TERRAFORM_DIR)/.terraform
	rm -f $(TERRAFORM_DIR)/tfplan
	rm -f $(TERRAFORM_DIR)/*.tfstate*
	rm -rf .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
