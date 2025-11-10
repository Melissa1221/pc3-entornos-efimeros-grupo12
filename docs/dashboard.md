# Dashboard de Trends

Documentación del sistema de dashboard para visualización de tendencias de métricas IaC.

## Descripción

El dashboard de trends proporciona una interfaz simple para visualizar y analizar las métricas de Infrastructure as Code, incluyendo:

- Tendencias de operaciones (deploy/destroy)
- Análisis de drift de infraestructura
- Estadísticas de performance
- Compliance y tasas de éxito

## Componentes

### 1. Generador de Dashboard (`scripts/generate-dashboard.py`)

**Funcionalidad**:
- Analiza datos de métricas desde JSON
- Genera dashboard HTML estático
- Calcula estadísticas y tendencias
- Presenta datos en formato tabular simple

**Uso**:
```bash
# Generar dashboard para últimos 30 días
python3 scripts/generate-dashboard.py

# Personalizar período y archivos
python3 scripts/generate-dashboard.py \
    --metrics-file metrics/operations.json \
    --output dashboard/trends.html \
    --days 14
```

### 2. Monitor de Trends (`scripts/trends-monitor.sh`)

**Funcionalidad**:
- Script wrapper para generación automática
- Validación de archivos de métricas
- Resumen de métricas en terminal
- Creación de directorios automática

**Uso**:
```bash
# Análisis estándar (30 días)
./scripts/trends-monitor.sh

# Análisis personalizado
./scripts/trends-monitor.sh 14
```

## Métricas Analizadas

### Operaciones
- **Total de operaciones**: Contador de deploy/destroy
- **Tasa de éxito**: % de operaciones exitosas vs fallidas
- **Tiempos de ejecución**: Estadísticas de duración (min, max, promedio, mediana)
- **Distribución diaria**: Operaciones por día

### Drift Analysis
- **Verificaciones totales**: Contador de drift checks realizados
- **Compliance rate**: % de verificaciones con 0% drift
- **Tendencias de drift**: Evolución del drift a lo largo del tiempo

### Performance
- **Tiempos promedio**: Deploy y destroy por período
- **Variabilidad**: Desviación estándar de tiempos
- **Tendencias**: Mejora, estabilidad o degradación

## Estructura del Dashboard

### Sección Principal
- Métricas clave destacadas
- Período de análisis
- Timestamp de generación

### Tablas de Estadísticas
- **Deploy Stats**: Min, max, promedio, mediana, count
- **Destroy Stats**: Mismas métricas para operaciones destroy
- **Operaciones Diarias**: Últimos 14 días con deploys, destroys, fallos
- **Drift Diario**: Verificaciones y compliance por día

### Indicadores de Estado
- **Verde**: Métricas saludables (éxito ≥95%, compliance ≥90%)
- **Naranja**: Métricas en advertencia (necesitan atención)
- **Rojo**: Métricas críticas (requieren acción inmediata)

## Análisis de Datos

### TrendsAnalyzer Class

**Métodos principales**:

#### `get_operation_trends(days)`
- Analiza operaciones en período especificado
- Calcula estadísticas de tiempo y éxito
- Agrupa datos por día

#### `get_drift_trends(days)`
- Analiza verificaciones de drift
- Calcula compliance rate
- Identifica patrones de drift

#### `_calculate_stats(values)`
- Estadísticas descriptivas básicas
- Min, max, mean, median, std deviation
- Manejo de listas vacías

### DashboardGenerator Class

**Funcionalidades**:
- Genera HTML estático con CSS simple
- Tablas responsivas con bordes básicos
- Colores semánticos (verde/naranja/rojo)
- Sin JavaScript, solo HTML/CSS

## Integración con CI/CD

### Generación Automática
El dashboard puede integrarse en workflows de CI/CD:

```yaml
- name: Generate Trends Dashboard
  run: |
    ./scripts/trends-monitor.sh 30
    
- name: Upload Dashboard
  uses: actions/upload-artifact@v4
  with:
    name: trends-dashboard
    path: dashboard/trends.html
```

### Scheduler Automático
Para generación periódica:

```yaml
on:
  schedule:
    - cron: '0 6 * * *'  # Diario a las 6 AM

jobs:
  dashboard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate Dashboard
        run: ./scripts/trends-monitor.sh
```

## Configuración

### Archivos Requeridos
- `metrics/operations.json`: Datos de métricas
- `dashboard/`: Directorio de salida (se crea automáticamente)

### Dependencias
- Python 3.x con módulos estándar
- `jq` para resumen en terminal (opcional)
- `bc` para cálculos en bash (opcional)

### Variables de Entorno
Ninguna requerida. Todo se configura por argumentos.

## Personalización

### Modificar Períodos
```bash
# Análisis semanal
./scripts/trends-monitor.sh 7

# Análisis trimestral
./scripts/trends-monitor.sh 90
```

### Cambiar Ubicaciones
```bash
python3 scripts/generate-dashboard.py \
    --metrics-file /ruta/custom/metrics.json \
    --output /ruta/custom/dashboard.html
```

### Ajustar CSS
Editar directamente el template HTML en `generate-dashboard.py`:
- Modificar colores en la sección `<style>`
- Ajustar tipografía y espaciado
- Personalizar tablas y métricas

## Interpretación de Resultados

### Métricas Saludables
- **Tasa de éxito**: ≥95%
- **Compliance drift**: ≥90%
- **Tiempo promedio deploy**: <60s
- **Tiempo promedio destroy**: <30s

### Señales de Alerta
- **Tasa de éxito**: <90%
- **Compliance drift**: <80%
- **Tiempos aumentando**: >20% vs baseline
- **Fallos frecuentes**: >1 por día

### Acciones Recomendadas
- **Baja tasa de éxito**: Revisar logs de fallos, mejorar validaciones
- **Alto drift**: Verificar cambios manuales, mejorar procesos
- **Tiempos altos**: Optimizar módulos Terraform, revisar recursos

## Troubleshooting

### Dashboard Vacío
- Verificar que existe `metrics/operations.json`
- Confirmar que hay datos en el período seleccionado
- Revisar permisos de escritura en directorio dashboard

### Errores de Generación
- Verificar instalación Python 3
- Confirmar formato JSON válido en métricas
- Revisar logs de error del script

### Datos Inconsistentes
- Validar timestamps en formato ISO
- Verificar estructura de datos esperada
- Limpiar datos corruptos si es necesario

## Comando de Referencia Rápida

```bash
# Generar dashboard completo
./scripts/trends-monitor.sh

# Solo dashboard sin resumen
python3 scripts/generate-dashboard.py

# Dashboard personalizado
python3 scripts/generate-dashboard.py --days 14 --output custom.html

# Ver métricas básicas
jq '.operations | length' metrics/operations.json
jq '[.operations[] | select(.status == "success")] | length' metrics/operations.json
```