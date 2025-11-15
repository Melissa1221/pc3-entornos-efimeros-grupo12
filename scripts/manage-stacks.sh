#!/bin/bash

# Script para gestión manual de stacks efímeros
# Uso: ./scripts/manage-stacks.sh [deploy|destroy|list|cleanup] [PR_NUMBER]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../infra/terraform/stacks/pr-preview"

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

check_dependencies() {
    log_info "Verificando dependencias..."
    
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform no está instalado"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        exit 1
    fi
    
    log_success "Dependencias verificadas"
}

validate_pr_number() {
    local pr_number=$1
    
    if [[ ! $pr_number =~ ^[0-9]+$ ]]; then
        log_error "Número de PR inválido: $pr_number"
        exit 1
    fi
    
    if [ $pr_number -le 0 ]; then
        log_error "Número de PR debe ser positivo: $pr_number"
        exit 1
    fi
}

terraform_init() {
    log_info "Inicializando Terraform..."
    cd "$TERRAFORM_DIR"
    terraform init
    cd - > /dev/null
}

deploy_stack() {
    local pr_number=$1
    validate_pr_number "$pr_number"
    
    log_info "Desplegando stack para PR #$pr_number..."
    
    cd "$TERRAFORM_DIR"
    
    terraform fmt -check -recursive
    terraform validate
    
    log_info "Generando plan..."
    terraform plan -var="pr_number=$pr_number" -out=tfplan
    
    log_info "Aplicando cambios..."
    terraform apply -auto-approve tfplan
    
    log_success "Stack desplegado exitosamente!"
    echo ""
    log_info "URLs del stack:"
    echo "Proxy: $(terraform output -raw proxy_url)"
    echo "App:   $(terraform output -raw app_url)"
    
    cd - > /dev/null
}

destroy_stack() {
    local pr_number=$1
    validate_pr_number "$pr_number"
    
    log_warning "Destruyendo stack para PR #$pr_number..."
    
    cd "$TERRAFORM_DIR"
    
    terraform destroy -auto-approve -var="pr_number=$pr_number"
    
    log_info "Verificando limpieza..."
    
    containers=$(docker ps -a --filter "label=pr_number=$pr_number" --format "{{.Names}}" || true)
    if [ -n "$containers" ]; then
        log_warning "Contenedores restantes encontrados: $containers"
        log_info "Limpiando contenedores..."
        docker rm -f $containers || true
    fi
    
    volumes=$(docker volume ls --filter "name=ephemeral-pr-$pr_number" --format "{{.Name}}" || true)
    if [ -n "$volumes" ]; then
        log_warning "Volúmenes restantes encontrados: $volumes"
        log_info "Limpiando volúmenes..."
        docker volume rm $volumes || true
    fi
    
    log_success "Stack destruido exitosamente!"
    
    cd - > /dev/null
}

list_stacks() {
    log_info "Listando stacks efímeros activos..."
    
    echo ""
    echo "Contenedores efímeros:"
    docker ps --filter "label=environment=ephemeral" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.CreatedAt}}" || true
    
    echo ""
    echo "Volúmenes efímeros:"
    docker volume ls --filter "name=ephemeral-pr-" --format "table {{.Name}}\t{{.Driver}}\t{{.CreatedAt}}" || true
    
    echo ""
    echo "PRs activos detectados:"
    for container in $(docker ps --filter "label=environment=ephemeral" --format "{{.Names}}" 2>/dev/null || true); do
        if [[ $container =~ ephemeral-pr-([0-9]+)- ]]; then
            pr_num="${BASH_REMATCH[1]}"
            echo "  - PR #$pr_num"
        fi
    done
}

cleanup_old_stacks() {
    local max_age_hours=${1:-72}
    
    log_info "Limpiando stacks con más de $max_age_hours horas..."
    
    cutoff_time=$(date -d "$max_age_hours hours ago" +%s)
    log_info "Fecha límite: $(date -d @$cutoff_time)"
    
    old_prs=""
    
    for container in $(docker ps -a --filter "label=environment=ephemeral" --format "{{.Names}}" 2>/dev/null || true); do
        if [[ $container =~ ephemeral-pr-([0-9]+)- ]]; then
            pr_num="${BASH_REMATCH[1]}"
            
            created_time=$(docker inspect $container --format '{{.Created}}' 2>/dev/null || echo "")
            if [ -n "$created_time" ]; then
                created_timestamp=$(date -d "$created_time" +%s)
                
                if [ $created_timestamp -lt $cutoff_time ]; then
                    if [[ ! " $old_prs " =~ " $pr_num " ]]; then
                        old_prs="$old_prs $pr_num"
                    fi
                fi
            fi
        fi
    done
    
    if [ -n "$old_prs" ]; then
        log_warning "PRs antiguos encontrados: $old_prs"
        
        for pr_num in $old_prs; do
            log_info "Limpiando PR #$pr_num..."
            destroy_stack "$pr_num"
        done
        
        log_success "Limpieza completada!"
    else
        log_success "No se encontraron stacks antiguos"
    fi
}

show_help() {
    echo "Gestión de Stacks Efímeros"
    echo ""
    echo "Uso: $0 [COMANDO] [ARGUMENTOS]"
    echo ""
    echo "Comandos disponibles:"
    echo "  deploy PR_NUMBER     Despliega stack para el PR especificado"
    echo "  destroy PR_NUMBER    Destruye stack para el PR especificado"
    echo "  list                 Lista todos los stacks activos"
    echo "  cleanup [HOURS]      Limpia stacks con más de HOURS horas (default: 72)"
    echo "  help                 Muestra esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 deploy 123        # Despliega stack para PR #123"
    echo "  $0 destroy 123       # Destruye stack para PR #123"
    echo "  $0 list              # Lista stacks activos"
    echo "  $0 cleanup 48        # Limpia stacks con más de 48 horas"
}

main() {
    local command=${1:-help}
    
    case $command in
        deploy)
            check_dependencies
            terraform_init
            deploy_stack "$2"
            ;;
        destroy)
            check_dependencies
            terraform_init
            destroy_stack "$2"
            ;;
        list)
            check_dependencies
            list_stacks
            ;;
        cleanup)
            check_dependencies
            terraform_init
            cleanup_old_stacks "$2"
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