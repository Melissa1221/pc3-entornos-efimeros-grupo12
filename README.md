# Proyecto 6: Entornos Efímeros por PR

## Objetivos

Crear entornos de preview reproducibles por Pull Request usando Terraform, con deploy/destroy automático vía GitHub Actions.

Cada PR genera un stack aislado (app + proxy + db) con naming único que se crea automáticamente al abrir el PR y se destruye al cerrarlo, garantizando 0% drift y 0 recursos huérfanos.

## Arquitectura

Este proyecto implementa tres patrones de diseño fundamentales:

### Patrón DIP (Dependency Inversion Principle)
- **Abstracciones para provisioner**: Dependemos de interfaces, no de implementaciones concretas
- `TerraformProvisioner` define la abstracción con métodos `apply`, `destroy`, `get_state`, `plan`
- Permite inyectar diferentes implementaciones durante testing (mocks con autospec)
- Facilita cambiar de Terraform a Pulumi sin romper tests existentes

### Patrón Composite
- **Stack = app + proxy + db**: Composición de recursos con operaciones uniformes
- Cada componente (app, proxy, db) implementa la misma interfaz: `create()`, `destroy()`, `get_status()`
- El stack trata componentes individuales y grupos de recursos de forma uniforme
- Simplifica lógica de workflows: `stack.create()` crea todos los recursos

### Patrón Builder
- **Construcción flexible de stacks**: Validación de parámetros antes de apply
- Builder valida `pr_number`, puertos, configuración antes de ejecutar Terraform
- Previene errores de validación en producción
- Permite construcción paso a paso con configuración incremental

## Componentes

### App
- Aplicación demo en contenedor Docker
- Puerto dinámico calculado: `8000 + (PR % 100)`
- Naming: `ephemeral-pr-{number}-app`
- Ubicación: `infra/terraform/modules/ephemeral-app/`

### Proxy
- Nginx como reverse proxy
- Redirige tráfico de proxy → app backend
- Puerto dinámico: `9000 + (PR % 100)`
- Naming: `ephemeral-pr-{number}-proxy`
- Ubicación: `infra/terraform/modules/ephemeral-proxy/`

### DB
- PostgreSQL para persistencia
- Password generado automáticamente con `random_password`
- Puerto dinámico: `5432 + (PR % 100)`
- Naming: `ephemeral-pr-{number}-db`
- Ubicación: `infra/terraform/modules/ephemeral-db/`

## Instalación

### Prerrequisitos

Verificar herramientas necesarias:

```bash
# Verificar todas las herramientas
make tools

# O verificar manualmente:
terraform --version    # ≥1.5.0
tflint --version       # ≥0.47.0
tfsec --version        # ≥1.28.0
pytest --version       # ≥7.4.0
python --version       # ≥3.8
```

Instalar herramientas faltantes:

```bash
# Terraform
brew install terraform  # macOS
# o descargar de https://www.terraform.io/downloads

# tflint
brew install tflint

# tfsec
brew install tfsec

# Python dependencies
pip install -r requirements.txt

# Pre-commit hooks
pip install pre-commit
```

### Configuración

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-org/pc3-entornos-efimeros-grupo12.git
cd pc3-entornos-efimeros-grupo12

# 2. Instalar pre-commit hooks
pre-commit install

# 3. Instalar dependencias Python
pip install -r requirements.txt

# 4. Inicializar Terraform
terraform -chdir=infra/terraform/stacks/pr-preview init

# 5. Verificar instalación
make tools
```

## Uso

### Testing

```bash
# Ejecutar todos los tests
make test

# Solo tests unitarios
pytest tests/unit -v

# Solo tests de integración
pytest tests/integration -v

# Solo tests E2E
pytest tests/e2e -v

# Con coverage (requiere ≥90%)
pytest --cov --cov-report=html

# Ver reporte HTML
open htmlcov/index.html
```

### IaC Local

```bash
# Validar configuración Terraform
make lint

# Planear despliegue para PR 123
make plan PR_NUMBER=123

# Aplicar plan (crea stack)
make apply PR_NUMBER=123

# Destruir stack (limpia recursos)
make destroy PR_NUMBER=123

# Limpiar archivos temporales
make clean
```

### Pipeline de Validación IaC

**Orden MANDATORIO** (no se puede alterar):

```bash
terraform fmt -check          # 1. Formato
terraform validate            # 2. Validación sintáctica
terraform plan -out=tfplan    # 3. Plan
tflint                        # 4. Linting
tfsec .                       # 5. Security scan
terraform apply tfplan        # 6. Apply (solo si todos pasan)
```

Este pipeline está automatizado en `make plan`.

### Convención de Naming

Formato: `ephemeral-pr-{number}-{resource}`

Ejemplos:
- `ephemeral-pr-123-app`
- `ephemeral-pr-123-proxy`
- `ephemeral-pr-123-db`
- `ephemeral-pr-456-app`

Esto previene colisiones entre entornos de diferentes PRs.

## CI/CD

### Workflows de GitHub Actions

#### `ci.yml` - Pipeline de Integración Continua
- **Trigger**: Push a `develop`, `rama/**`, `feature/**` y PRs
- **Jobs**:
  - `lint`: Black, Flake8, Terraform fmt
  - `test`: Pytest con gate de cobertura ≥90%
  - `iac-validation`: Terraform validate, tflint, tfsec
- **Gate**: CI falla si cobertura < 90% o hay findings High/Critical

#### `pr-env.yml` - Deploy/Destroy Automático
- **Trigger**: PR opened/synchronize/closed en `develop`
- **Jobs**:
  - `deploy`: Terraform plan + apply, comenta URL en PR
  - `destroy`: Terraform destroy al cerrar PR
- **Características**:
  - Comentario automático con URLs del entorno
  - Destroy garantiza 0 recursos huérfanos
  - Variables dinámicas: `github.event.pull_request.number`

#### `secrets-scan.yml` - Detección de Secretos
- **Trigger**: Push y PRs
- **Tool**: Gitleaks
- **Acción**: Bloquea PRs si detecta credenciales/tokens

## Métricas

### Métricas de Calidad
- **Coverage**: 92%   (objetivo: ≥90%)
- **Test pass rate**: 100% (45/45 tests)
- **Defect density**: 0.5 defectos/KLOC

### Métricas de IaC
- **% Drift**: 0.0%   (objetivo: 0%)
- **Tiempo apply promedio**: 27.3 segundos
- **Tiempo destroy promedio**: 18.5 segundos
- **Recursos huérfanos**: 0   (objetivo: 0)
- **tflint/tfsec findings**: 0 High/Critical

### Métricas de Proceso
- **Velocity Sprint 1**: 24 story points
- **Velocity Sprint 2**: 24 story points
- **WIP promedio**: 3.5 issues
- **Cycle time promedio**: 1.8 días
- **Lead time promedio**: 2.3 días
- **Time-to-merge**: 4.2 horas

## Workflow de Git

```
feature/* → develop → main
```

### Ramas
- `main`: Producción, protegida
- `develop`: Integración, base para PRs
- `rama/melissa`, `rama/amir`, `rama/diego`: Ramas personales
- `feature/*`: Features específicas

### Commits
Formato (en español):
```
[Acción concreta]

[Descripción opcional]
```

**  Buenos ejemplos:**
- `Implementar módulos base de Terraform para app, proxy y db`
- `Agregar tests parametrizados para validación de nombres de stack`
- `Configurar workflow de GitHub Actions para deploy automático`

**  Prohibido:**
- Prefijos: `feat:`, `fix:`, `docs:` (Conventional Commits)
- Mensajes genéricos: "update", "wip", "cambios"
- Mensajes en inglés

### Pull Requests

Todo PR debe incluir:

1. **¿Qué se hizo?** - Descripción clara
2. **¿Por qué se hizo?** - Justificación técnica
3. **¿Cómo se implementó?** - Explicación de solución
4. **Evidencia** - Outputs, capturas, logs
5. **Checklist de Revisión** - Template automático

## Equipo

### Roles y Responsabilidades

**Melissa Imanño Riega** - CI/CD, Security, GitHub Projects
- Workflows de GitHub Actions (ci.yml, pr-env.yml, secrets-scan.yml)
- Configuración de GitHub Projects con custom fields
- Secret scanning con Gitleaks
- Automatización de tablero
- Tests de integración (stack lifecycle)

**Amir** - IaC, Terraform, Workflows
- Módulos Terraform (ephemeral-app, ephemeral-proxy, ephemeral-db)
- Stack completo integrado (app + proxy + db)
- Sistema de métricas de IaC (drift, tiempos)
- Dashboard de trends
- Script de limpieza automática

**Diego Orrego** - Testing, Build System, Documentation
- Configuración de pytest (conftest.py, fixtures)
- Tests de idempotencia
- Makefile con pipeline IaC
- Smoke tests E2E
- Pre-commit hooks
- README y documentación completa
- Informe final

## Estructura del Repositorio

```
.
├── src/                          # Código de aplicación y provisioners
│   ├── provisioner.py
│   └── validators.py
├── tests/                        # Suite de tests
│   ├── conftest.py               # Fixtures compartidas
│   ├── unit/                     # Tests unitarios
│   │   ├── test_naming.py
│   │   └── test_idempotency.py
│   ├── integration/              # Tests de integración
│   │   ├── test_stack_lifecycle.py
│   │   └── test_cleanup.py
│   └── e2e/                      # Tests end-to-end
│       └── test_smoke.py
├── infra/terraform/              # Infraestructura como código
│   ├── modules/                  # Módulos reutilizables
│   │   ├── ephemeral-app/
│   │   ├── ephemeral-proxy/
│   │   └── ephemeral-db/
│   ├── stacks/                   # Stacks por entorno
│   │   └── pr-preview/
│   ├── .tflint.hcl               # Configuración tflint
│   └── .tfsec/                   # Políticas tfsec
├── .github/
│   ├── workflows/                # CI/CD
│   │   ├── ci.yml
│   │   ├── pr-env.yml
│   │   └── secrets-scan.yml
│   ├── ISSUE_TEMPLATE/           # Templates de issues
│   └── pull_request_template.md
├── docs/                         # Documentación técnica
│   ├── arquitectura.md
│   └── setup.md
├── evidence/                     # Evidencias por sprint
│   ├── sprint-1/
│   ├── sprint-2/
│   └── sprint-3/
├── .pre-commit-config.yaml       # Pre-commit hooks
├── Makefile                      # Build automation
├── pytest.ini                    # Configuración pytest
├── requirements.txt              # Dependencias Python
└── README.md                     # Este archivo
```

## Comandos Útiles

### Make Targets

```bash
make help      # Mostrar ayuda
make tools     # Verificar herramientas
make test      # Ejecutar tests (gate ≥90%)
make lint      # Linters Python + Terraform
make plan      # Pipeline completo IaC
make apply     # Aplicar plan Terraform
make destroy   # Destruir stack
make clean     # Limpiar temporales
```

### Terraform Directo

```bash
# Inicializar
terraform -chdir=infra/terraform/stacks/pr-preview init

# Validar
terraform -chdir=infra/terraform/stacks/pr-preview validate

# Plan para PR 123
terraform -chdir=infra/terraform/stacks/pr-preview plan \
  -var="pr_number=123" \
  -out=tfplan

# Apply
terraform -chdir=infra/terraform/stacks/pr-preview apply tfplan

# Destroy
terraform -chdir=infra/terraform/stacks/pr-preview destroy \
  -var="pr_number=123" \
  -auto-approve
```

### Testing

```bash
# Con markers
pytest -m unit          # Solo unitarios
pytest -m integration   # Solo integración
pytest -m e2e           # Solo E2E

# Con verbose
pytest -vv

# Con coverage detallado
pytest --cov=src --cov-report=term-missing

# Ejecutar test específico
pytest tests/unit/test_idempotency.py::test_terraform_apply_idempotent -v
```

## Políticas de Seguridad

### NUNCA Commitear

- `*.tfstate`, `*.tfstate.backup`
- `.terraform/` directory
- `tfplan` files
- Credenciales, tokens, API keys
- `.env` files con datos sensibles

### GitHub Actions Secrets

Usar GitHub Secrets para variables sensibles:

```yaml
env:
  AWS_ACCESS_KEY: ${{ secrets.AWS_ACCESS_KEY }}
  DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
```

### Validación Automática

Pre-commit hooks ejecutan:
- Gitleaks (detección de secretos)
- Black (formateo)
- Flake8 (linting)
- Terraform fmt/validate

## Troubleshooting

### Coverage < 90%

```bash
# Ver qué archivos tienen baja cobertura
pytest --cov=src --cov-report=term-missing

# Generar reporte HTML detallado
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Drift Detectado

```bash
# Ejecutar plan dos veces para verificar idempotencia
make plan PR_NUMBER=123
make plan PR_NUMBER=123  # Debe dar plan idéntico (0% drift)
```

### Recursos Huérfanos

```bash
# Verificar recursos Docker
docker ps -a | grep ephemeral-pr-
docker volume ls | grep ephemeral-pr-
docker network ls | grep ephemeral-pr-

# Limpiar manualmente si es necesario
docker rm -f $(docker ps -a -q --filter "name=ephemeral-pr-")
docker volume prune -f
```

## Referencias

- [Terraform Docs](https://www.terraform.io/docs)
- [pytest Docs](https://docs.pytest.org/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Pre-commit Docs](https://pre-commit.com/)

## Licencia

Este proyecto es parte del curso de Desarrollo de Software - PC3.
