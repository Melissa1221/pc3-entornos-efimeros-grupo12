#!/bin/bash

# Script para recolectar métricas de IaC y operaciones de stacks
# Uso: ./scripts/metrics-collector.sh [collect|report|drift-check] [PR_NUMBER]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../infra/terraform/stacks/pr-preview"
METRICS_DIR="$SCRIPT_DIR/../metrics"
METRICS_FILE="$METRICS_DIR/operations.json"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}INFO: $1${NC}"
}

log_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

# Crear directorio de métricas si no existe
ensure_metrics_dir() {
    mkdir -p "$METRICS_DIR"
    
    if [ ! -f "$METRICS_FILE" ]; then
        echo '{"operations": [], "drift_checks": []}' > "$METRICS_FILE"
    fi
}

# Registrar operación en métricas
record_operation() {
    local operation=$1
    local pr_number=$2
    local duration=$3
    local status=$4
    local resource_count=${5:-0}
    
    local timestamp=$(date -Iseconds)
    local entry=$(cat <<EOF
{
  "timestamp": "$timestamp",
  "operation": "$operation",
  "pr_number": $pr_number,
  "duration_seconds": $duration,
  "status": "$status",
  "resource_count": $resource_count
}
EOF
)
    
    # Agregar entrada al archivo JSON
    jq --argjson entry "$entry" '.operations += [$entry]' "$METRICS_FILE" > "$METRICS_FILE.tmp"
    mv "$METRICS_FILE.tmp" "$METRICS_FILE"
    
    log_info "Operación registrada: $operation PR#$pr_number ($duration s)"
}

# Medir % drift de Terraform
check_drift() {
    local pr_number=$1
    
    if [ -z "$pr_number" ]; then
        log_error "Número de PR requerido para drift check"
        exit 1
    fi
    
    log_info "Verificando drift para PR #$pr_number..."
    
    cd "$TERRAFORM_DIR"
    
    if [ ! -f "terraform.tfstate" ]; then
        log_warning "No hay state file, no se puede verificar drift"
        return 0
    fi
    
    local start_time=$(date +%s)
    
    # Generar plan para verificar drift
    if terraform plan -var="pr_number=$pr_number" -detailed-exitcode -out=drift_check.tfplan &>/dev/null; then
        local exit_code=$?
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        if [ $exit_code -eq 0 ]; then
            # No hay cambios = 0% drift
            record_drift_check "$pr_number" 0 "$duration" "no_changes"
            log_success "0% drift detectado"
            return 0
        elif [ $exit_code -eq 2 ]; then
            # Hay cambios = calcular % drift
            local total_resources=$(terraform state list | wc -l)
            local changed_resources=$(terraform show -no-color drift_check.tfplan | grep -E "^\s*[~+-]" | wc -l)
            
            local drift_percent=0
            if [ $total_resources -gt 0 ]; then
                drift_percent=$(echo "scale=2; ($changed_resources * 100) / $total_resources" | bc)
            fi
            
            record_drift_check "$pr_number" "$drift_percent" "$duration" "drift_detected"
            log_warning "${drift_percent}% drift detectado ($changed_resources/$total_resources recursos)"
            return $changed_resources
        fi
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        record_drift_check "$pr_number" -1 "$duration" "error"
        log_error "Error verificando drift"
        return 1
    fi
    
    cd - > /dev/null
}

# Registrar verificación de drift
record_drift_check() {
    local pr_number=$1
    local drift_percent=$2
    local duration=$3
    local status=$4
    
    local timestamp=$(date -Iseconds)
    local entry=$(cat <<EOF
{
  "timestamp": "$timestamp",
  "pr_number": $pr_number,
  "drift_percent": $drift_percent,
  "check_duration_seconds": $duration,
  "status": "$status"
}
EOF
)
    
    # Agregar entrada al archivo JSON
    jq --argjson entry "$entry" '.drift_checks += [$entry]' "$METRICS_FILE" > "$METRICS_FILE.tmp"
    mv "$METRICS_FILE.tmp" "$METRICS_FILE"
}

# Operación medida de deploy
timed_deploy() {
    local pr_number=$1
    
    log_info "Iniciando deploy medido para PR #$pr_number..."
    
    local start_time=$(date +%s)
    local status="success"
    local resource_count=0
    
    cd "$TERRAFORM_DIR"
    
    if terraform apply -auto-approve -var="pr_number=$pr_number"; then
        resource_count=$(terraform state list | wc -l)
        log_success "Deploy completado"
    else
        status="failed"
        log_error "Deploy falló"
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    record_operation "deploy" "$pr_number" "$duration" "$status" "$resource_count"
    
    cd - > /dev/null
    return $([[ "$status" == "success" ]] && echo 0 || echo 1)
}

# Operación medida de destroy
timed_destroy() {
    local pr_number=$1
    
    log_info "Iniciando destroy medido para PR #$pr_number..."
    
    local start_time=$(date +%s)
    local status="success"
    local resource_count=0
    
    cd "$TERRAFORM_DIR"
    
    # Contar recursos antes de destruir
    if [ -f "terraform.tfstate" ]; then
        resource_count=$(terraform state list | wc -l)
    fi
    
    if terraform destroy -auto-approve -var="pr_number=$pr_number"; then
        log_success "Destroy completado"
    else
        status="failed"
        log_error "Destroy falló"
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    record_operation "destroy" "$pr_number" "$duration" "$status" "$resource_count"
    
    cd - > /dev/null
    return $([[ "$status" == "success" ]] && echo 0 || echo 1)
}

# Generar reporte de métricas
generate_report() {
    log_info "Generando reporte de métricas..."
    
    if [ ! -f "$METRICS_FILE" ]; then
        log_error "No hay datos de métricas disponibles"
        exit 1
    fi
    
    local report_file="$METRICS_DIR/report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" <<EOF
# Reporte de Métricas IaC

**Generado:** $(date -Iseconds)

## Resumen Ejecutivo

### Operaciones Registradas
EOF
    
    # Estadísticas de operaciones
    echo "**Total operaciones:** $(jq '.operations | length' "$METRICS_FILE")" >> "$report_file"
    echo "**Deploy exitosos:** $(jq '[.operations[] | select(.operation == "deploy" and .status == "success")] | length' "$METRICS_FILE")" >> "$report_file"
    echo "**Destroy exitosos:** $(jq '[.operations[] | select(.operation == "destroy" and .status == "success")] | length' "$METRICS_FILE")" >> "$report_file"
    
    # Tiempos promedio
    local avg_deploy=$(jq '[.operations[] | select(.operation == "deploy" and .status == "success") | .duration_seconds] | add / length' "$METRICS_FILE" 2>/dev/null || echo "0")
    local avg_destroy=$(jq '[.operations[] | select(.operation == "destroy" and .status == "success") | .duration_seconds] | add / length' "$METRICS_FILE" 2>/dev/null || echo "0")
    
    cat >> "$report_file" <<EOF

### Tiempos Promedio
- **Deploy:** ${avg_deploy}s
- **Destroy:** ${avg_destroy}s

### Drift Analysis
EOF
    
    # Análisis de drift
    echo "**Verificaciones de drift:** $(jq '.drift_checks | length' "$METRICS_FILE")" >> "$report_file"
    local zero_drift=$(jq '[.drift_checks[] | select(.drift_percent == 0)] | length' "$METRICS_FILE")
    local total_checks=$(jq '.drift_checks | length' "$METRICS_FILE")
    
    if [ "$total_checks" -gt 0 ]; then
        local zero_drift_percent=$(echo "scale=2; ($zero_drift * 100) / $total_checks" | bc)
        echo "**0% drift:** $zero_drift_percent% de verificaciones" >> "$report_file"
    fi
    
    cat >> "$report_file" <<EOF

## Detalle de Operaciones

### Últimas 10 Operaciones
| Timestamp | Operación | PR | Duración (s) | Estado | Recursos |
|-----------|-----------|----|--------------| -------|----------|
EOF
    
    jq -r '.operations | sort_by(.timestamp) | reverse | .[0:10] | .[] | [.timestamp, .operation, .pr_number, .duration_seconds, .status, .resource_count] | @tsv' "$METRICS_FILE" | while IFS=$'\t' read -r timestamp operation pr duration status resources; do
        echo "| $timestamp | $operation | #$pr | $duration | $status | $resources |" >> "$report_file"
    done
    
    cat >> "$report_file" <<EOF

### Verificaciones de Drift Recientes
| Timestamp | PR | Drift % | Duración (s) | Estado |
|-----------|----|---------|--------------| -------|
EOF
    
    jq -r '.drift_checks | sort_by(.timestamp) | reverse | .[0:10] | .[] | [.timestamp, .pr_number, .drift_percent, .check_duration_seconds, .status] | @tsv' "$METRICS_FILE" | while IFS=$'\t' read -r timestamp pr drift duration status; do
        echo "| $timestamp | #$pr | $drift | $duration | $status |" >> "$report_file"
    done
    
    log_success "Reporte generado: $report_file"
    echo "$report_file"
}

show_help() {
    echo "Recolector de Métricas IaC"
    echo ""
    echo "Uso: $0 [COMANDO] [ARGUMENTOS]"
    echo ""
    echo "Comandos disponibles:"
    echo "  collect deploy PR_NUMBER    Ejecuta deploy medido"
    echo "  collect destroy PR_NUMBER   Ejecuta destroy medido"
    echo "  drift-check PR_NUMBER       Verifica % drift de stack"
    echo "  report                      Genera reporte de métricas"
    echo "  help                        Muestra esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 collect deploy 123       # Deploy medido para PR #123"
    echo "  $0 drift-check 123          # Verificar drift para PR #123"
    echo "  $0 report                   # Generar reporte completo"
}

main() {
    local command=${1:-help}
    
    ensure_metrics_dir
    
    case $command in
        collect)
            local operation=$2
            local pr_number=$3
            
            case $operation in
                deploy)
                    timed_deploy "$pr_number"
                    ;;
                destroy)
                    timed_destroy "$pr_number"
                    ;;
                *)
                    log_error "Operación desconocida: $operation"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        drift-check)
            check_drift "$2"
            ;;
        report)
            generate_report
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Comando desconocido: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"