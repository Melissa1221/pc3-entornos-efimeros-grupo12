# Proyecto 6: Entornos Efímeros por PR

## Objetivo

Implementar un sistema de entornos efímeros que despliega stacks completos de infraestructura por cada pull request. Cada stack incluye aplicación, proxy y base de datos con nombres únicos basados en el número de PR.

Los entornos se crean automáticamente al abrir un PR y se destruyen al cerrarlo.

## Alcance Técnico

Infraestructura como código con Terraform
Automatización con GitHub Actions  
Testing disciplinado con pytest
Patrones: Composite, DIP, Builder

Convención de nombres: ephemeral-pr-{number}-{resource}
Objetivo: 0% drift, 90% cobertura

## Sprints

Sprint 1 (D1-D3): Stack base, tests de naming e idempotencia
Sprint 2 (D4-D6): Workflows automáticos, smoke tests
Sprint 3 (D7-D10): Métricas, dashboard, documentación final

## Estructura del Repositorio

```
.
├── src/                     # Código de aplicación
├── tests/                   # Tests (unit, integration, e2e)
│   └── conftest.py
├── infra/terraform/         # Módulos y stacks IaC
│   ├── modules/
│   └── stacks/
├── .github/
│   ├── workflows/           # CI/CD pipelines
│   └── ISSUE_TEMPLATE/
├── docs/                    # Documentación técnica
└── evidence/                # Capturas por sprint
    ├── sprint-1/
    ├── sprint-2/
    └── sprint-3/
```

## Workflow de Git

feature/* → develop → main
Commits: Conventional Commits
PRs: Requieren link a issue (Fixes #N) y ≥1 aprobación

## Comandos Principales

Pendiente crear Makefile con targets:
- tools: Verificar instalación de herramientas
- test: Ejecutar pytest con cobertura
- lint: Validaciones de código
- plan/apply/destroy: Workflow de IaC
- clean: Limpiar temporales

## Criterios de Aceptación

Create/destroy determinista sin recursos huérfanos
0% drift entre planes consecutivos
Cobertura ≥90%

## Métricas a Capturar

Tiempo de provisionado
Tasa de fugas de recursos
Cycle time por issue
Burndown por sprint
% drift por apply

