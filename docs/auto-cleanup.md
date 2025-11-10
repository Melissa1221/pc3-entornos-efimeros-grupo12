# Sistema de Limpieza Automática

Documentación del sistema de limpieza automática para stacks efímeros antiguos y recursos huérfanos.

## Descripción

El sistema de limpieza automática identifica y elimina stacks efímeros que:
- Han superado la edad máxima permitida (default: 72 horas)
- Pertenecen a PRs cerrados o mergeados
- Son huérfanos (PR no encontrado)
- Tienen recursos Docker sin gestión activa

## Componentes

### 1. Auto Cleanup (`scripts/auto-cleanup.sh`)

**Funcionalidad principal**:
- Escanea contenedores efímeros por edad
- Verifica estado de PRs usando GitHub CLI
- Ejecuta destroy de Terraform + limpieza manual
- Soporte para modo dry-run
- Verificación post-limpieza

**Uso**:
```bash
# Limpieza estándar (72h)
./scripts/auto-cleanup.sh

# Limpieza personalizada
./scripts/auto-cleanup.sh 48

# Modo dry-run (solo mostrar)
./scripts/auto-cleanup.sh 72 --dry-run

# Generar reporte
./scripts/auto-cleanup.sh --report
```

### 2. Cleanup Monitor (`scripts/cleanup-monitor.py`)

**Funcionalidad**:
- Análisis de recursos efímeros existentes
- Identificación de candidatos para limpieza
- Generación de reportes detallados
- Resúmenes en formato JSON

**Uso**:
```bash
# Resumen de recursos
python3 scripts/cleanup-monitor.py --summary

# Análisis de limpieza
python3 scripts/cleanup-monitor.py --max-age 48

# Reporte completo
python3 scripts/cleanup-monitor.py --report

# Salida JSON
python3 scripts/cleanup-monitor.py --json
```

### 3. Workflow Programado (`.github/workflows/scheduled-cleanup.yml`)

**Configuración**:
- Ejecución diaria a las 2 AM UTC
- Ejecución manual con parámetros
- Integración con GitHub CLI para estado de PRs
- Generación de reportes como artifacts

**Parámetros del workflow**:
- `max_age_hours`: Edad máxima en horas (default: 72)
- `dry_run`: Modo de solo análisis (default: false)

## Criterios de Limpieza

### Edad de Recursos
Los recursos se consideran antiguos cuando:
- Han existido por más de `max_age_hours` (default: 72h)
- Fueron creados antes del timestamp límite calculado

### Estado de PR
- **CLOSED/MERGED**: Limpieza inmediata
- **NOT_FOUND**: Limpieza inmediata (PR eliminado)
- **OPEN**: Limpieza solo si es muy antiguo
- **UNKNOWN**: Limpieza por seguridad si es antiguo

### Recursos Objetivo
- **Contenedores**: Con label `environment=ephemeral`
- **Volúmenes**: Con nombre `ephemeral-pr-*`
- **Redes**: Con nombre `ephemeral-pr-*` (excluyendo bridge/host/none)

## Proceso de Limpieza

### 1. Identificación
```bash
# Buscar contenedores antiguos
docker ps -a --filter "label=environment=ephemeral"

# Extraer números de PR
ephemeral-pr-123-app -> PR #123
```

### 2. Verificación de Estado
```bash
# Verificar estado con GitHub CLI
gh pr view 123 --json state --jq '.state'
```

### 3. Ejecución de Limpieza
```bash
# Terraform destroy
terraform destroy -auto-approve -var="pr_number=123"

# Limpieza manual de respaldo
docker rm -f ephemeral-pr-123-*
docker volume rm ephemeral-pr-123-*
docker network rm ephemeral-pr-123-*
```

### 4. Verificación Post-Limpieza
```bash
# Verificar recursos restantes
docker ps -a --filter "label=pr_number=123"
docker volume ls --filter "name=ephemeral-pr-123"
```

## Configuración y Personalización

### Variables de Entorno
- `GITHUB_TOKEN`: Para acceso a GitHub API (automático en Actions)
- `TF_IN_AUTOMATION`: Para modo automático de Terraform

### Dependencias
- **Docker**: Para gestión de contenedores/volúmenes/redes
- **Terraform**: Para destroy de infrastructure
- **GitHub CLI** (opcional): Para verificación de estado de PRs
- **jq**: Para procesamiento JSON
- **bc**: Para cálculos en bash

### Configuración de Edad
```bash
# En workflow
max_age_hours: '48'  # 2 días

# En script directo
./scripts/auto-cleanup.sh 96  # 4 días
```

## Monitoreo y Reportes

### Análisis de Recursos
```bash
# Ver recursos actuales
python3 scripts/cleanup-monitor.py --summary

# Resultado:
# Contenedores: 6 (ejecutándose: 3)
# Volúmenes: 2
# Redes: 1
# PRs únicos: 2
```

### Reportes Detallados
Los reportes incluyen:
- Tabla de contenedores con edad y estado
- Lista de PRs afectados
- Recomendaciones de limpieza
- Timestamps y metadatos

### Artifacts en CI/CD
- `cleanup-report-*.md`: Reporte detallado de limpieza
- Retención: 30 días
- Descarga desde Actions tab

## Seguridad y Protecciones

### Modo Dry-Run
- Analiza sin ejecutar cambios
- Muestra qué se limpiaría
- Útil para validar configuración

### Verificación de PRs
- Consulta estado real en GitHub
- Evita limpiar PRs activos incorrectamente
- Fallback seguro para PRs desconocidos

### Limpieza Incremental
- Procesa un PR a la vez
- Verifica limpieza después de cada stack
- Continúa aunque falle uno específico

### Logs Detallados
- Razón de limpieza para cada stack
- Timestamps de todas las operaciones
- Códigos de salida de comandos

## Troubleshooting

### Limpieza Incompleta
```bash
# Verificar recursos restantes
./scripts/cleanup-monitor.py --summary

# Limpieza manual específica
./scripts/manage-stacks.sh destroy 123

# Limpieza forzada del sistema
docker system prune -f --volumes
```

### GitHub CLI No Disponible
El script funciona sin GitHub CLI:
- Asume estado UNKNOWN para PRs
- Limpia recursos antiguos por edad
- Logging indica cuando no puede verificar estado

### Fallos de Terraform
- Script continúa con limpieza manual
- Docker cleanup como respaldo
- Reporta éxito parcial en logs

### Recursos Bloqueados
```bash
# Forzar eliminación de contenedores
docker rm -f $(docker ps -aq --filter "label=environment=ephemeral")

# Limpiar volúmenes huérfanos
docker volume prune -f

# Limpiar redes no utilizadas
docker network prune -f
```

## Integración con Monitoreo

### Métricas Clave
- Número de stacks limpiados por ejecución
- Tiempo total de limpieza
- Recursos huérfanos detectados
- Fallos de limpieza

### Alertas Recomendadas
- Limpieza falla consistentemente
- Acumulación de recursos antiguos (>100)
- Tiempo de limpieza excesivo (>10 min)

### Dashboard Integration
Los resultados se pueden integrar con el dashboard de trends:
```bash
# Agregar métricas de limpieza al JSON
./scripts/cleanup-monitor.py --json >> metrics/cleanup.json
```

## Comandos de Referencia

```bash
# Análisis rápido
./scripts/cleanup-monitor.py --summary

# Limpieza completa
./scripts/auto-cleanup.sh

# Limpieza conservadora
./scripts/auto-cleanup.sh 168 --dry-run  # 1 semana, solo análisis

# Reporte de estado
./scripts/auto-cleanup.sh --report

# Limpieza de emergencia
docker rm -f $(docker ps -aq --filter "label=environment=ephemeral")
docker volume rm $(docker volume ls -q --filter "name=ephemeral-pr-")
```