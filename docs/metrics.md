# Sistema de Métricas IaC

Documentación del sistema de métricas para Infrastructure as Code y operaciones de entornos efímeros.

## Descripción General

El sistema de métricas recolecta, analiza y reporta datos sobre:
- Tiempos de operaciones Terraform (deploy/destroy)
- % de drift de infraestructura
- Tasas de éxito/fallo de operaciones
- Métricas de calidad y compliance

## Componentes del Sistema

### 1. Recolector de Métricas (`scripts/metrics-collector.sh`)

**Propósito**: Script principal para capturar métricas operacionales y verificar drift.

**Funcionalidades**:
- Operaciones medidas (deploy/destroy con timestamps)
- Verificación de drift con cálculo de porcentajes
- Generación de reportes automáticos
- Almacenamiento en formato JSON

**Uso**:
```bash
# Deploy con medición de tiempo
./scripts/metrics-collector.sh collect deploy 123

# Destroy con medición
./scripts/metrics-collector.sh collect destroy 123

# Verificación de drift
./scripts/metrics-collector.sh drift-check 123

# Generar reporte completo
./scripts/metrics-collector.sh report
```

### 2. Workflow de Métricas (`.github/workflows/metrics-collection.yml`)

**Jobs Implementados**:

#### `drift-monitoring`
- **Trigger**: Cada 6 horas + manual
- **Función**: Monitorea drift en stacks activos
- **Criterios**: Detecta cambios en configuración vs estado real

#### `performance-analysis`
- **Trigger**: Al completar workflow de deploy/destroy
- **Función**: Analiza tendencias de performance
- **Métricas**: Tiempos promedio, tasas de éxito

#### `metrics-reporting`
- **Trigger**: Manual
- **Función**: Genera reportes detallados
- **Output**: Artifacts con reportes en Markdown

#### `drift-alerting`
- **Trigger**: Después de monitoreo de drift
- **Función**: Alertas por drift > 5%
- **Escalación**: Identifica stacks problemáticos

#### `quality-gates`
- **Trigger**: Manual con análisis completo
- **Función**: Evalúa gates de calidad
- **Criterios**: Success rate ≥95%, drift compliance ≥90%

### 3. Outputs de Terraform Extendidos

**Nuevos Outputs para Métricas**:
- `resource_count`: Conteo de recursos por tipo
- `health_endpoints`: URLs para health checks
- `metrics_labels`: Labels para categorización
- `drift_check_info`: Metadata para verificación de drift

## Métricas Capturadas

### Operacionales
- **Duración de deploy**: Tiempo total de terraform apply
- **Duración de destroy**: Tiempo total de terraform destroy  
- **Tasa de éxito**: % de operaciones exitosas vs fallidas
- **Conteo de recursos**: Número de recursos por stack

### Drift y Compliance
- **% Drift**: Porcentaje de recursos con cambios vs configuración
- **Frecuencia de drift**: Qué tan seguido se detecta drift
- **Tiempo de verificación**: Duración de terraform plan para drift check
- **Compliance**: % de verificaciones con 0% drift

### Calidad
- **Success rate**: Meta ≥95% para todas las operaciones
- **Drift compliance**: Meta ≥90% de verificaciones con 0% drift
- **Resource leaks**: Detección de recursos huérfanos
- **Performance**: Tiempos promedio vs baseline

## Estructura de Datos

### Archivo de Métricas (`metrics/operations.json`)

```json
{
  "operations": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "operation": "deploy",
      "pr_number": 123,
      "duration_seconds": 45,
      "status": "success",
      "resource_count": 5
    }
  ],
  "drift_checks": [
    {
      "timestamp": "2024-01-15T11:00:00Z", 
      "pr_number": 123,
      "drift_percent": 0,
      "check_duration_seconds": 12,
      "status": "no_changes"
    }
  ]
}
```

## Cálculo de Métricas Clave

### % Drift
```bash
total_resources=$(terraform state list | wc -l)
changed_resources=$(terraform show plan | grep -E "^\s*[~+-]" | wc -l)
drift_percent=$(echo "scale=2; ($changed_resources * 100) / $total_resources" | bc)
```

### Success Rate
```bash
total_ops=$(jq '[.operations[]] | length' metrics.json)
successful_ops=$(jq '[.operations[] | select(.status == "success")] | length' metrics.json)
success_rate=$(echo "scale=2; ($successful_ops * 100) / $total_ops" | bc)
```

### Drift Compliance
```bash
total_checks=$(jq '.drift_checks | length' metrics.json)
zero_drift=$(jq '[.drift_checks[] | select(.drift_percent == 0)] | length' metrics.json)
compliance=$(echo "scale=2; ($zero_drift * 100) / $total_checks" | bc)
```

## Reportes Generados

### Reporte Ejecutivo
- Resumen de operaciones por período
- Tiempos promedio de deploy/destroy
- % de compliance con metas
- Identificación de tendencias

### Reporte de Drift
- Histórico de verificaciones
- Stacks con mayor drift
- Correlación drift vs cambios de código
- Recommendations para reducir drift

### Reporte de Performance
- Comparación de tiempos vs baseline
- Identificación de degradación
- Análisis de resource count vs tiempo
- Optimizaciones sugeridas

## Thresholds y Alertas

### Critical Thresholds
- **Drift > 10%**: Requiere investigación inmediata
- **Success rate < 90%**: Indica problemas sistemáticos
- **Deploy time > 120s**: Performance degradada

### Warning Thresholds
- **Drift > 5%**: Monitoreo aumentado
- **Success rate < 95%**: Revisión de procesos
- **Deploy time > 90s**: Investigar causas

## Integración con CI/CD

### Flujo Automático
1. **Deploy/Destroy** → Métricas operacionales capturadas
2. **Post-Deploy** → Verificación de drift automática
3. **Scheduled** → Monitoreo proactivo cada 6h
4. **Weekly** → Reporte ejecutivo automático

### Quality Gates
- **Pre-merge**: Verificar que PR no cause drift excesivo
- **Post-merge**: Confirmar que deploy mantiene compliance
- **Production**: Alertas en tiempo real por anomalías

## Uso para Optimización

### Identificar Bottlenecks
- Analizar correlación entre resource count y tiempo
- Identificar módulos que más tiempo consumen
- Optimizar configuraciones problemáticas

### Mejorar Reliability
- Analizar patrones de falla
- Identificar PRs que causan más drift
- Establecer mejores prácticas basadas en datos

### Capacity Planning
- Predecir tiempos basado en cambios
- Planificar recursos de CI/CD
- Establecer SLAs realistas

## Comandos de Uso Frecuente

```bash
# Verificar drift de todos los stacks activos
for pr in $(docker ps --filter "label=environment=ephemeral" --format "{{.Names}}" | sed -n 's/.*-pr-\([0-9]*\)-.*/\1/p' | sort -u); do
  ./scripts/metrics-collector.sh drift-check $pr
done

# Generar reporte semanal
./scripts/metrics-collector.sh report

# Análisis rápido de health
jq '.operations[-10:] | map(select(.status == "failed"))' metrics/operations.json

# Ver tendencia de tiempos
jq '.operations | map(select(.operation == "deploy")) | sort_by(.timestamp) | .[-5:] | map(.duration_seconds)' metrics/operations.json
```

## Troubleshooting

### Métricas No Se Capturan
1. Verificar permisos del script metrics-collector.sh
2. Confirmar que directorio metrics/ existe
3. Revisar formato JSON del archivo de métricas

### Drift Check Falla
1. Verificar que terraform.tfstate existe
2. Confirmar que variables están correctas
3. Revisar que no hay terraform lock

### Reportes Vacíos
1. Confirmar que hay datos en operations.json
2. Verificar dependencias (jq, bc)
3. Revisar logs del workflow de métricas

## Próximas Mejoras

- **Dashboard web**: Visualización en tiempo real
- **Alertas Slack/Teams**: Notificaciones inmediatas
- **Métricas de costos**: Estimación de recursos consumidos
- **ML predictions**: Predicción de tiempos basado en cambios