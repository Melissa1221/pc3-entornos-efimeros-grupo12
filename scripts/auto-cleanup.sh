#!/bin/bash

# Script de limpieza automática de stacks antiguos
# Uso: ./scripts/auto-cleanup.sh [max_age_hours] [--dry-run]

set -e

MAX_AGE_HOURS=${1:-72}
DRY_RUN=false

# Procesar argumentos
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Uso: $0 [max_age_hours] [--dry-run]"
            echo "  max_age_hours: Máxima edad en horas (default: 72)"
            echo "  --dry-run: Solo mostrar qué se limpiaría, sin ejecutar"
            exit 0
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../infra/terraform/stacks/pr-preview"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

log_dry_run() {
    echo -e "${YELLOW}DRY-RUN: $1${NC}"
}

# Función para verificar dependencias
check_dependencies() {
    local missing_deps=()
    
    for cmd in docker terraform jq; do
        if ! command -v $cmd &> /dev/null; then
            missing_deps+=($cmd)
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Dependencias faltantes: ${missing_deps[*]}"
        exit 1
    fi
}

# Función para obtener PRs activos desde GitHub
get_active_prs() {
    if command -v gh &> /dev/null; then
        gh pr list --state open --json number --jq '.[].number' 2>/dev/null || echo ""
    else
        echo ""
    fi
}

# Función para encontrar contenedores antiguos
find_old_containers() {
    local cutoff_time=$(date -d "$MAX_AGE_HOURS hours ago" +%s)
    local old_prs=""
    
    log_info "Buscando contenedores con más de $MAX_AGE_HOURS horas..."
    log_info "Fecha límite: $(date -d @$cutoff_time)"
    
    for container in $(docker ps -a --filter "label=environment=ephemeral" --format "{{.Names}}" 2>/dev/null || true); do
        if [[ $container =~ ephemeral-pr-([0-9]+)- ]]; then
            local pr_num="${BASH_REMATCH[1]}"
            
            local created_time=$(docker inspect $container --format '{{.Created}}' 2>/dev/null || echo "")
            if [ -n "$created_time" ]; then
                local created_timestamp=$(date -d "$created_time" +%s)
                
                if [ $created_timestamp -lt $cutoff_time ]; then
                    log_warning "Contenedor antiguo encontrado: $container (PR #$pr_num, creado: $created_time)"
                    if [[ ! " $old_prs " =~ " $pr_num " ]]; then
                        old_prs="$old_prs $pr_num"
                    fi
                fi
            fi
        fi
    done
    
    echo "$old_prs"
}

# Función para verificar estado de PR
check_pr_status() {
    local pr_number=$1
    
    if command -v gh &> /dev/null; then
        local status=$(gh pr view $pr_number --json state --jq '.state' 2>/dev/null || echo "NOT_FOUND")
        echo "$status"
    else
        echo "UNKNOWN"
    fi
}

# Función para limpiar stack específico
cleanup_stack() {
    local pr_number=$1
    local reason=$2
    
    log_info "Limpiando stack para PR #$pr_number (razón: $reason)"
    
    if [ "$DRY_RUN" = true ]; then
        log_dry_run "Se limpiaría stack para PR #$pr_number"
        return 0
    fi
    
    # Intentar destroy con Terraform primero
    if [ -d "$TERRAFORM_DIR" ]; then
        log_info "Ejecutando terraform destroy para PR #$pr_number..."
        
        cd "$TERRAFORM_DIR"
        if terraform destroy -auto-approve -var="pr_number=$pr_number" 2>/dev/null; then
            log_success "Terraform destroy exitoso para PR #$pr_number"
        else
            log_warning "Terraform destroy falló para PR #$pr_number, procediendo con limpieza manual"
        fi
        cd - > /dev/null
    fi
    
    # Limpieza manual de recursos Docker
    log_info "Limpieza manual de recursos Docker para PR #$pr_number..."
    
    # Limpiar contenedores
    local containers=$(docker ps -a --filter "label=pr_number=$pr_number" --format "{{.Names}}" 2>/dev/null || true)
    if [ -n "$containers" ]; then
        log_info "Eliminando contenedores: $containers"
        docker rm -f $containers 2>/dev/null || true
    fi
    
    # Limpiar volúmenes
    local volumes=$(docker volume ls --filter "name=ephemeral-pr-$pr_number" --format "{{.Name}}" 2>/dev/null || true)
    if [ -n "$volumes" ]; then
        log_info "Eliminando volúmenes: $volumes"
        docker volume rm $volumes 2>/dev/null || true
    fi
    
    # Limpiar redes
    local networks=$(docker network ls --filter "name=ephemeral-pr-$pr_number" --format "{{.Name}}" 2>/dev/null | grep -v -E '^(bridge|host|none)$' || true)
    if [ -n "$networks" ]; then
        log_info "Eliminando redes: $networks"
        docker network rm $networks 2>/dev/null || true
    fi
    
    log_success "Limpieza completada para PR #$pr_number"
}

# Función para verificar limpieza completa
verify_cleanup() {
    local pr_number=$1
    
    local remaining_containers=$(docker ps -a --filter "label=pr_number=$pr_number" --format "{{.Names}}" 2>/dev/null | wc -l)
    local remaining_volumes=$(docker volume ls --filter "name=ephemeral-pr-$pr_number" --format "{{.Name}}" 2>/dev/null | wc -l)
    
    if [ $remaining_containers -eq 0 ] && [ $remaining_volumes -eq 0 ]; then
        log_success "Verificación: PR #$pr_number completamente limpio"
        return 0
    else
        log_warning "Verificación: PR #$pr_number tiene recursos restantes (containers: $remaining_containers, volumes: $remaining_volumes)"
        return 1
    fi
}

# Función principal de limpieza
main_cleanup() {
    log_info "Iniciando limpieza automática de stacks antiguos..."
    log_info "Edad máxima permitida: $MAX_AGE_HOURS horas"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "Modo DRY-RUN activado - no se realizarán cambios"
    fi
    
    check_dependencies
    
    # Obtener PRs activos
    local active_prs=$(get_active_prs)
    if [ -n "$active_prs" ]; then
        log_info "PRs activos encontrados: $active_prs"
    else
        log_warning "No se pudieron obtener PRs activos desde GitHub (gh CLI no disponible o no autenticado)"
    fi
    
    # Encontrar contenedores antiguos
    local old_prs=$(find_old_containers)
    
    if [ -z "$old_prs" ]; then
        log_success "No se encontraron stacks antiguos para limpiar"
        return 0
    fi
    
    log_info "PRs con stacks antiguos encontrados:$old_prs"
    
    local cleaned_count=0
    local total_count=0
    
    for pr_num in $old_prs; do
        total_count=$((total_count + 1))
        
        # Verificar estado del PR
        local pr_status=$(check_pr_status $pr_num)
        log_info "PR #$pr_num estado: $pr_status"
        
        local should_cleanup=false
        local cleanup_reason=""
        
        case $pr_status in
            "CLOSED"|"MERGED")
                should_cleanup=true
                cleanup_reason="PR cerrado/mergeado"
                ;;
            "NOT_FOUND")
                should_cleanup=true
                cleanup_reason="PR no encontrado"
                ;;
            "OPEN")
                if [ -n "$active_prs" ] && [[ " $active_prs " =~ " $pr_num " ]]; then
                    log_info "PR #$pr_num está abierto y activo, pero es muy antiguo - limpiando por edad"
                    should_cleanup=true
                    cleanup_reason="stack muy antiguo (>$MAX_AGE_HOURS h)"
                else
                    log_info "PR #$pr_num está abierto pero no en lista activa - limpiando"
                    should_cleanup=true
                    cleanup_reason="PR abierto pero inactivo"
                fi
                ;;
            "UNKNOWN")
                log_warning "No se pudo determinar estado de PR #$pr_num - limpiando por seguridad"
                should_cleanup=true
                cleanup_reason="estado desconocido + antiguo"
                ;;
        esac
        
        if [ "$should_cleanup" = true ]; then
            cleanup_stack $pr_num "$cleanup_reason"
            
            if [ "$DRY_RUN" = false ]; then
                if verify_cleanup $pr_num; then
                    cleaned_count=$((cleaned_count + 1))
                fi
            else
                cleaned_count=$((cleaned_count + 1))
            fi
        else
            log_info "Saltando limpieza de PR #$pr_num"
        fi
    done
    
    # Resumen final
    echo ""
    log_info "Resumen de limpieza automática:"
    echo "  Stacks antiguos encontrados: $total_count"
    echo "  Stacks limpiados: $cleaned_count"
    
    if [ "$DRY_RUN" = true ]; then
        echo "  Modo: DRY-RUN (no se realizaron cambios reales)"
    else
        echo "  Modo: EJECUCIÓN REAL"
    fi
    
    # Ejecutar limpieza general del sistema Docker
    if [ "$DRY_RUN" = false ] && [ $cleaned_count -gt 0 ]; then
        log_info "Ejecutando limpieza general del sistema Docker..."
        docker system prune -f --volumes 2>/dev/null || true
        log_success "Limpieza del sistema completada"
    fi
}

# Función para generar reporte de limpieza
generate_cleanup_report() {
    local report_file="cleanup_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" <<EOF
# Reporte de Limpieza Automática

**Fecha:** $(date -Iseconds)
**Edad máxima:** $MAX_AGE_HOURS horas
**Modo:** $([ "$DRY_RUN" = true ] && echo "DRY-RUN" || echo "EJECUCIÓN")

## Stacks Analizados

$(docker ps -a --filter "label=environment=ephemeral" --format "table {{.Names}}\t{{.Status}}\t{{.CreatedAt}}" 2>/dev/null || echo "No hay contenedores efímeros")

## Recursos por PR

EOF
    
    for container in $(docker ps -a --filter "label=environment=ephemeral" --format "{{.Names}}" 2>/dev/null || true); do
        if [[ $container =~ ephemeral-pr-([0-9]+)- ]]; then
            local pr_num="${BASH_REMATCH[1]}"
            echo "### PR #$pr_num" >> "$report_file"
            echo "- Contenedores: $(docker ps -a --filter "label=pr_number=$pr_num" --format "{{.Names}}" | wc -l)" >> "$report_file"
            echo "- Volúmenes: $(docker volume ls --filter "name=ephemeral-pr-$pr_num" --format "{{.Name}}" | wc -l)" >> "$report_file"
            echo "" >> "$report_file"
        fi
    done
    
    echo "Reporte generado: $report_file"
}

# Verificar argumentos especiales
if [[ "$1" == "--report" ]]; then
    generate_cleanup_report
    exit 0
fi

# Ejecutar limpieza principal
main_cleanup