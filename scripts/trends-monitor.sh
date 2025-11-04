#!/bin/bash

# Script para monitorear trends de métricas IaC
# Uso: ./scripts/trends-monitor.sh [days]

set -e

DAYS=${1:-30}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
METRICS_FILE="$SCRIPT_DIR/../metrics/operations.json"
DASHBOARD_DIR="$SCRIPT_DIR/../dashboard"
DASHBOARD_FILE="$DASHBOARD_DIR/trends.html"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}INFO: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

log_info "Analizando trends para los últimos $DAYS días..."

# Verificar que existe archivo de métricas
if [ ! -f "$METRICS_FILE" ]; then
    log_warning "No se encontró archivo de métricas: $METRICS_FILE"
    log_info "Creando archivo de métricas vacío..."
    mkdir -p "$(dirname "$METRICS_FILE")"
    echo '{"operations": [], "drift_checks": []}' > "$METRICS_FILE"
fi

# Crear directorio de dashboard
mkdir -p "$DASHBOARD_DIR"

# Generar dashboard
log_info "Generando dashboard HTML..."
python3 "$SCRIPT_DIR/generate-dashboard.py" \
    --metrics-file "$METRICS_FILE" \
    --output "$DASHBOARD_FILE" \
    --days "$DAYS"

if [ $? -eq 0 ]; then
    log_info "Dashboard generado exitosamente: $DASHBOARD_FILE"
    
    # Mostrar resumen básico
    if command -v jq &> /dev/null && [ -f "$METRICS_FILE" ]; then
        echo ""
        log_info "Resumen de métricas:"
        
        total_ops=$(jq '.operations | length' "$METRICS_FILE")
        successful_ops=$(jq '[.operations[] | select(.status == "success")] | length' "$METRICS_FILE")
        total_checks=$(jq '.drift_checks | length' "$METRICS_FILE")
        zero_drift=$(jq '[.drift_checks[] | select(.drift_percent == 0)] | length' "$METRICS_FILE")
        
        echo "  Operaciones totales: $total_ops"
        
        if [ $total_ops -gt 0 ]; then
            success_rate=$(echo "scale=1; ($successful_ops * 100) / $total_ops" | bc -l 2>/dev/null || echo "0")
            echo "  Tasa de éxito: $success_rate%"
        fi
        
        echo "  Verificaciones drift: $total_checks"
        
        if [ $total_checks -gt 0 ]; then
            compliance=$(echo "scale=1; ($zero_drift * 100) / $total_checks" | bc -l 2>/dev/null || echo "0")
            echo "  Compliance drift: $compliance%"
        fi
        
        echo ""
        echo "Para ver el dashboard completo:"
        echo "  file://$(realpath "$DASHBOARD_FILE")"
    fi
else
    log_error "Error generando dashboard"
    exit 1
fi