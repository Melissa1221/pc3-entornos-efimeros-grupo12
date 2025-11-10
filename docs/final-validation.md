# Validación Final del Proyecto

Documentación para la validación final del proyecto pc3-entornos-efimeros-grupo12.

## Objetivos de Validación

### Métricas Obligatorias
- **Cobertura de tests**: ≥92%
- **Drift de Terraform**: 0%
- **Recursos huérfanos**: 0
- **Workflows funcionales**: Todos activos

## Proceso de Validación

### 1. Verificación de Cobertura
```bash
# Ejecutar tests con cobertura detallada
make test

# Objetivo: 92% o superior
# Archivo de reporte: htmlcov/index.html
```

### 2. Verificación de Drift
```bash
# Verificar drift de Terraform
terraform -chdir=infra/terraform/stacks/pr-preview plan -var="pr_number=999" -detailed-exitcode

# Exit code 0 = sin drift
# Exit code 2 = drift detectado
```

### 3. Verificación de Limpieza
```bash
# Verificar recursos huérfanos
make cleanup-verify PR_NUMBER=999

# Resultado esperado: 0 contenedores, 0 volúmenes
```

### 4. Validación Automática
```bash
# Ejecutar validación completa
make validate-metrics

# Script que verifica todas las métricas automáticamente
```

## Estructura del Proyecto Validada

### Directorios Requeridos
- `tests/unit/` - Tests unitarios
- `tests/integration/` - Tests de integración
- `infra/terraform/modules/` - Módulos Terraform
- `scripts/` - Scripts de automatización
- `docs/` - Documentación
- `.github/workflows/` - Workflows CI/CD

### Archivos Críticos
- `Makefile` - Automatización de tareas
- `scripts/validate-metrics.sh` - Validador de métricas
- `scripts/metrics-collector.sh` - Recolector de métricas
- `scripts/auto-cleanup.sh` - Limpieza automática
- `scripts/generate-dashboard.py` - Dashboard de trends

### Workflows CI/CD
- `pr-deploy.yml` - Deploy/destroy automático
- `metrics-collection.yml` - Recolección de métricas
- `cleanup-old-stacks.yml` - Limpieza de stacks antiguos
- `scheduled-cleanup.yml` - Limpieza programada

## Comandos de Validación

### Tests y Cobertura
```bash
# Tests básicos
make test

# Tests con reporte HTML
pytest -vv --cov --cov-report=html --cov-fail-under=92

# Ver reporte en navegador
open htmlcov/index.html
```

### Terraform y Drift
```bash
# Plan completo con validaciones
make plan

# Verificar drift específico
make metrics-drift PR_NUMBER=123

# Destroy y verificar limpieza
make destroy
make cleanup-verify
```

### Métricas y Monitoreo
```bash
# Generar dashboard de trends
make dashboard

# Reporte de métricas
make metrics-report

# Estado del proyecto
make status
```

## Criterios de Aprobación

### Tests (Obligatorio)
- Cobertura ≥92%
- Todos los tests pasan
- Sin errores de linting

### Infrastructure (Obligatorio)
- Terraform plan sin errores
- 0% drift detectado
- Modules validan correctamente

### Limpieza (Obligatorio)
- Destroy elimina todos los recursos
- 0 contenedores huérfanos
- 0 volúmenes huérfanos
- State file limpio

### Automatización (Obligatorio)
- Workflows CI/CD funcionales
- Scripts ejecutan sin errores
- Dashboard genera correctamente

## Troubleshooting

### Cobertura Insuficiente
```bash
# Ver archivos con baja cobertura
pytest --cov --cov-report=term-missing

# Agregar tests faltantes
# Ejecutar de nuevo hasta ≥92%
```

### Drift Detectado
```bash
# Ver cambios detectados
terraform show tfplan

# Resolver cambios manualmente
# Re-ejecutar plan hasta 0% drift
```

### Recursos Huérfanos
```bash
# Limpieza manual
make cleanup-auto

# Verificar docker directamente
docker ps -a --filter "label=environment=ephemeral"
docker volume ls --filter "name=ephemeral-pr-"

# Limpieza forzada si es necesario
docker system prune -f --volumes
```

### Workflows Fallando
- Verificar permisos de GitHub Actions
- Revisar secrets configurados
- Validar sintaxis YAML
- Comprobar dependencias en runners

## Entregables Finales

### Código
- Repositorio con todos los commits limpios
- Sin indicadores de IA (emojis, etc.)
- Mensajes de commit en español

### Documentación
- README completo
- Documentación de workflows
- Guías de troubleshooting
- Reportes de métricas

### Evidencia
- Screenshots de cobertura ≥92%
- Captura de 0% drift
- Dashboard de trends generado
- Logs de limpieza exitosa

## Comandos Finales

```bash
# Validación completa antes de entrega
make validate-metrics

# Limpieza final
make clean

# Verificación de estado final
make status

# Generar dashboard final
make dashboard
```

## Checklist de Entrega

- [ ] Cobertura de tests ≥92%
- [ ] Drift de Terraform = 0%
- [ ] Recursos huérfanos = 0
- [ ] Todos los workflows pasan
- [ ] Scripts ejecutan correctamente
- [ ] Dashboard genera sin errores
- [ ] Documentación completa
- [ ] Commits sin indicadores IA
- [ ] Mensajes en español
- [ ] Estructura de archivos correcta