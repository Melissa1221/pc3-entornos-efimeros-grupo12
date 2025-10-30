# Avance Day 1 - Melissa

**Fecha:** 30/10/2024
**Sprint:** 1
**Responsible:** Melissa

## Tareas Completadas

### 1. Configuración del Repositorio

Repositorio creado: `Melissa1221/pc3-entornos-efimeros-grupo12`

Estructura de carpetas implementada:
- src/
- tests/ (unit, integration, e2e)
- infra/terraform/ (modules, stacks)
- .github/workflows/
- docs/
- evidence/ (sprint-1, sprint-2, sprint-3)

Archivo .gitignore configurado con:
- .terraform/
- *.tfstate
- *.tfstate.backup
- tfplan
- .env
- __pycache__/
- .pytest_cache/
- htmlcov/
- .coverage

Ramas creadas:
- main
- develop
- feature/melissa


### 2. GitHub Projects Setup

Tablero Kanban configurado con columnas:
New Issues → Icebox → Product Backlog → Sprint Backlog → In Progress → Review-QA → Done

![Tablero Kanban](capturas/creacion-kanban.png)

Custom fields configurados:
- Estimate (número): para story points
- blocked_time (número): tiempo bloqueado en minutos
- trend (selección): mejora/empeora/estable

Labels creados:
- priority:high, priority:medium, priority:low
- sprint-1, sprint-2, sprint-3
- user-story, task, bug

![Labels del Proyecto](capturas/custom-labels.png)

Product Backlog creado:
19 issues distribuidos en 3 sprints
Total: 61 story points

![Issues Creados](capturas/issues-creados.png)

### 3. Templates de GitHub

Templates creados:
- .github/pull_request_template.md
- .github/ISSUE_TEMPLATE/user_story.md
- .github/ISSUE_TEMPLATE/bug_report.md
- .github/ISSUE_TEMPLATE/task.md
- .github/ISSUE_TEMPLATE/config.yml

### 4. Documentación Inicial

Documentos creados:
- docs/setup.md (configuración del entorno)
- README.md (objetivos del proyecto)
- docs/arquitectura.md (decisiones de patrones DIP/Composite/Builder)

## Métricas

**Story Points:** 9 pts asignados para Day 1
**Tiempo invertido:** 6h
**Blocked time:** 0 minutos

## Issues del Sprint 1 Listos para Desarrollo

- #3: Configurar estructura inicial del repositorio (3 pts) - COMPLETADO
- #4: Configurar GitHub Projects y templates (3 pts) - COMPLETADO
- #5: Módulo Terraform para aplicación efímera (5 pts) - Pendiente
- #6: Tests parametrizados para validación de nombres (3 pts) - Pendiente
- #7: Setup pytest con fixtures y conftest (2 pts) - Pendiente
- #8: Tests de idempotencia de Terraform (3 pts) - Pendiente
- #9: Crear Makefile con targets para IaC y testing (3 pts) - Pendiente
- #10: Recopilar evidencias del Sprint 1 (2 pts) - Pendiente


## Observaciones

Sin bloqueos identificados.
Toda la infraestructura base está lista para que el equipo comience desarrollo.
