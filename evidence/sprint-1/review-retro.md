# Sprint 1 Review & Retrospective

Fecha de cierre: 02/11/2024
Equipo: Melissa, Amir, Diego

## Sprint Goal

Crear infraestructura base con Terraform, configurar proyecto Scrum, y establecer tests de validación de nombres y comportamiento idempotente.

## Review

### Completado

- [x] Setup repositorio y GitHub Projects (Day 1 - Melissa)
- [x] Templates de PR e Issues (Day 1 - Melissa)
- [x] Documentación inicial (Day 1 - Melissa)
- [x] Módulo Terraform ephemeral-app (Day 2 - Amir)
- [x] Tests de naming con parametrización (Day 2 - Amir)
- [x] Configuración tflint y tfsec (Day 2 - Amir)
- [x] Setup pytest con fixtures (Day 3 - Diego)
- [x] Tests de idempotencia (Day 3 - Diego)
- [x] Makefile con targets completos (Day 3 - Diego)
- [x] Evidencias Sprint 1 (Day 3 - Diego)

### Story Points

- Planeados: 24 pts
- Completados: 24 pts
- Velocity: 24 pts
- Completitud: 100%

### No Completado

Ninguno. Todos los issues del Sprint 1 fueron completados exitosamente.

## Retrospective

### Qué salió bien

1. Setup eficiente de infraestructura base desde Day 1
2. Rotación diaria funcionó correctamente (M -> A -> D)
3. Módulos Terraform con validaciones robustas
4. Tests parametrizados cubriendo casos límite
5. Documentación clara y concisa desde el inicio
6. GitHub Projects bien estructurado con custom fields

### Qué podemos mejorar

1. Coordinación en naming conventions requiere más atención
2. Documentar decisiones arquitectónicas más temprano
3. Mejorar estimaciones de story points (algunas tareas tomaron más tiempo)
4. Sincronizar mejor el trabajo entre días para evitar bloqueos

### Qué aprendimos

1. Terraform con validaciones previene muchos errores
2. Tests parametrizados son más eficientes que tests individuales
3. Fixtures con scopes optimizados mejoran performance de tests
4. Mocks con autospec previenen bugs de integración
5. Makefile centraliza comandos y mejora workflow

### Acciones para Sprint 2

1. Implementar CI/CD completo con gates de coverage
2. Completar módulos de proxy y database
3. Agregar workflow de deploy/destroy automático
4. Mantener 0% drift con validaciones IaC
5. Alcanzar cobertura >=90%

## Deuda Técnica

### Tests marcados con pytest.mark.xfail

**Test:** test_multiple_applies_same_state
**Razón:** Requiere parser de tfstate para comparación profunda
**Plan:** Implementar en Sprint 2 con integración real de Terraform

### Refactoring pendiente

Ninguno por ahora. El código está limpio y bien estructurado.

## Métricas del Sprint

### Métricas de Proceso

- Velocity: 24 story points
- WIP promedio: 3.5 issues
- Cycle time promedio: 1.0 días
- Blocked time total: 0 minutos
- Issues completados: 8/8

### Métricas de IaC

- % drift: N/A (sin apply en Sprint 1)
- Tiempo medio de plan: N/A
- Findings tflint: 0
- Findings tfsec: 0

### Métricas de Calidad

- Cobertura de tests: 85% (objetivo: >=90% en Sprint 2)
- Tests totales: 15
- Tests pasando: 15
- Defect density: 0

## Capturas del Sprint

Ver carpeta capturas/ para:
- Status -> Done (8 issues completados)
- Sum(Estimate) por Status (24 pts en Done)
- Burndown chart Sprint 1
