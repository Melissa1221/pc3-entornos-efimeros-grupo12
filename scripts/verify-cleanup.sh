#!/bin/bash

# Script para verificar limpieza completa después de destroy
# Uso: ./scripts/verify-cleanup.sh PR_NUMBER [terraform_dir]

set -e

PR_NUMBER=$1
TERRAFORM_DIR=${2:-"infra/terraform/stacks/pr-preview"}

# Colores para output
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

if [ -z "$PR_NUMBER" ]; then
    log_error "Número de PR requerido"
    echo "Uso: $0 PR_NUMBER [terraform_dir]"
    exit 1
fi

if [[ ! $PR_NUMBER =~ ^[0-9]+$ ]] || [ $PR_NUMBER -le 0 ]; then
    log_error "Número de PR inválido: $PR_NUMBER"
    exit 1
fi

log_info "Verificando limpieza para PR #$PR_NUMBER..."

# Variables para tracking
ORPHANED_RESOURCES=0
TOTAL_CHECKS=0

# Verificar state de Terraform
log_info "Verificando state de Terraform..."
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

if [ -f "$TERRAFORM_DIR/terraform.tfstate" ]; then
    TF_RESOURCES=$(terraform -chdir="$TERRAFORM_DIR" state list 2>/dev/null | wc -l)
    if [ $TF_RESOURCES -eq 0 ]; then
        log_success "State de Terraform vacío"
    else
        log_warning "State de Terraform contiene $TF_RESOURCES recursos"
        ORPHANED_RESOURCES=$((ORPHANED_RESOURCES + TF_RESOURCES))
    fi
else
    log_success "No hay state file de Terraform"
fi

# Verificar contenedores Docker
log_info "Verificando contenedores Docker..."
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

CONTAINERS=$(docker ps -a --filter "label=pr_number=$PR_NUMBER" --format "{{.Names}}" 2>/dev/null || true)
if [ -n "$CONTAINERS" ]; then
    CONTAINER_COUNT=$(echo "$CONTAINERS" | wc -l)
    log_warning "Encontrados $CONTAINER_COUNT contenedores huérfanos:"
    echo "$CONTAINERS"
    ORPHANED_RESOURCES=$((ORPHANED_RESOURCES + CONTAINER_COUNT))
else
    log_success "No hay contenedores huérfanos"
fi

# Verificar volúmenes Docker
log_info "Verificando volúmenes Docker..."
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

VOLUMES=$(docker volume ls --filter "name=ephemeral-pr-$PR_NUMBER" --format "{{.Name}}" 2>/dev/null || true)
if [ -n "$VOLUMES" ]; then
    VOLUME_COUNT=$(echo "$VOLUMES" | wc -l)
    log_warning "Encontrados $VOLUME_COUNT volúmenes huérfanos:"
    echo "$VOLUMES"
    ORPHANED_RESOURCES=$((ORPHANED_RESOURCES + VOLUME_COUNT))
else
    log_success "No hay volúmenes huérfanos"
fi

# Verificar redes Docker
log_info "Verificando redes Docker..."
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

NETWORKS=$(docker network ls --filter "name=ephemeral-pr-$PR_NUMBER" --format "{{.Name}}" 2>/dev/null | grep -v -E '^(bridge|host|none)$' || true)
if [ -n "$NETWORKS" ]; then
    NETWORK_COUNT=$(echo "$NETWORKS" | wc -l)
    log_warning "Encontradas $NETWORK_COUNT redes huérfanas:"
    echo "$NETWORKS"
    ORPHANED_RESOURCES=$((ORPHANED_RESOURCES + NETWORK_COUNT))
else
    log_success "No hay redes huérfanas"
fi

# Resumen final
echo ""
log_info "Resumen de verificación:"
echo "Verificaciones realizadas: $TOTAL_CHECKS"
echo "Recursos huérfanos encontrados: $ORPHANED_RESOURCES"

if [ $ORPHANED_RESOURCES -eq 0 ]; then
    log_success "CLEANUP COMPLETO: 0 recursos huérfanos"
    exit 0
else
    log_error "CLEANUP INCOMPLETO: $ORPHANED_RESOURCES recursos huérfanos"
    
    echo ""
    echo "Para limpiar manualmente:"
    echo "  ./scripts/manage-stacks.sh destroy $PR_NUMBER"
    echo "  docker system prune -f"
    
    exit 1
fi