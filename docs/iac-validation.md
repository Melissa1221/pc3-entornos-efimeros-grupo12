# Validación de Infrastructure as Code (IaC)

## Pipeline de Validación Obligatorio

**ORDEN MANDATORY** - Ejecutar en esta secuencia antes de apply:

```bash
# 1. Formatear código
terraform fmt -check

# 2. Validar sintaxis y configuración
terraform validate

# 3. Generar plan de ejecución
terraform plan -out=tfplan

# 4. Linting con tflint
tflint

# 5. Escaneo de seguridad con tfsec
tfsec .

# 6. Apply solo si todos los pasos anteriores pasan
terraform apply tfplan
```

## Configuración tflint

Archivo: `infra/terraform/.tflint.hcl`

**Reglas habilitadas:**
- `terraform_naming_convention`: Convenciones de nombres
- `terraform_documented_outputs`: Outputs documentados
- `terraform_documented_variables`: Variables documentadas  
- `terraform_typed_variables`: Variables con tipos explícitos
- `terraform_unused_declarations`: Detectar declaraciones sin uso

## Configuración tfsec

Archivo: `infra/terraform/.tfsec.yml`

**Políticas de seguridad:**
- Severity mínima: MEDIUM
- Excluye checks específicos para desarrollo local
- Genera reporte JSON para CI/CD
- Escanea módulos y stacks

## Comandos de Desarrollo

```bash
# Ejecutar validación completa
cd infra/terraform/stacks/pr-preview
terraform fmt -check && terraform validate && tflint && tfsec .

# Solo linting
tflint --init  # Primera vez
tflint

# Solo seguridad
tfsec . --config-file=../.tfsec.yml

# Formatear automáticamente
terraform fmt -recursive
```

## Integración con CI/CD

Estos comandos se ejecutan automáticamente en:
- **Pre-commit hooks**: fmt, validate
- **CI Pipeline**: tflint, tfsec 
- **PR Workflow**: validación completa antes de apply

## Métricas de Calidad

- **tflint findings**: 0 (objetivo)
- **tfsec High/Critical**: 0 (gate obligatorio)
- **% drift**: 0% (entre consecutive plans)