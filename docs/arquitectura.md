# Arquitectura del Sistema

## Principios de Diseño

Reproducibilidad: Mismo PR number debe producir stack idéntico
Idempotencia: Aplicar Terraform dos veces = 0% drift
Composabilidad: Módulos con interfaces bien definidas

## Patrones de Diseño Aplicados

### Dependency Inversion Principle (DIP)

El sistema invertirá dependencias entre módulos de alto nivel y detalles de implementación.

Abstracciones planificadas:
- Interfaz para provisioner de infraestructura
- Operaciones: create(), destroy(), get_status()

Beneficios esperados:
- Inyectar mocks en tests sin modificar lógica
- Soportar múltiples backends de infraestructura
- Tests unitarios con autospec

Implementación: Pendiente Sprint 1

### Composite Pattern

Stack efímero como composición de recursos individuales.

Componentes:
- Recurso aplicación
- Recurso proxy
- Recurso base de datos

Operaciones uniformes:
- create() en orden: db → app → proxy
- destroy() en orden inverso: proxy → app → db
- get_status() agregando estados individuales

Implementación: Pendiente Sprint 1-2

### Builder Pattern

Construcción de stacks con configuración flexible.

Métodos planificados:
- with_pr_number(): Valida y genera prefijo de nombres
- with_app_config(): Configura aplicación
- with_proxy_config(): Configura proxy
- with_db_config(): Configura base de datos
- build(): Validación final y construcción

Validaciones:
- PR number debe ser entero positivo
- Puertos no deben tener colisiones
- Configuración completa antes de apply

Implementación: Pendiente Sprint 1

## Módulos de Terraform

### Estructura Planificada

```
infra/terraform/
├── modules/
│   ├── ephemeral-app/       # Pendiente
│   ├── ephemeral-proxy/     # Pendiente
│   └── ephemeral-db/        # Pendiente
└── stacks/
    └── pr-preview/          # Pendiente
```

### Módulo ephemeral-app

Variables:
- pr_number (obligatoria)
- app_port
- app_image

Recursos: Por definir
Outputs: URL, estado, metadata

### Módulo ephemeral-proxy

Variables:
- pr_number (obligatoria)
- proxy_port
- backend_url

Recursos: Por definir (Nginx)
Outputs: URL, estado, metadata

### Módulo ephemeral-db

Variables:
- pr_number (obligatoria)
- db_port
- db_password (sensitive)

Recursos: Por definir (PostgreSQL)
Outputs: URL, estado, metadata

### Stack pr-preview

Composición de los tres módulos
Variable obligatoria: pr_number
Cálculo de puertos basado en PR number
Output consolidado con todas las URLs

## Validación de IaC

Pipeline de validación (por implementar):

1. terraform fmt -check
2. terraform validate
3. terraform plan -out=tfplan
4. tflint
5. tfsec
6. terraform apply tfplan (solo si pasos anteriores pasan)

Configuración pendiente:
- .tflint.hcl
- .tfsec/

Métricas a registrar:
- Duración de cada paso
- Cantidad de recursos en plan
- Findings por severidad
- % drift

## Testing de la Arquitectura

### Tests Unitarios (Pendiente Sprint 1)

Verificar builder y composite sin Terraform real
Usar create_autospec para provisioner
Validar naming con casos límite

Casos de prueba planificados:
- PR válidos: 1, 99, 1000, 99999
- PR inválidos: 0, -1, None, "abc"

### Tests de Idempotencia (Pendiente Sprint 1)

Aplicar plan dos veces
Verificar call_args_list idénticos
Confirmar 0% drift

### Tests de Integración (Pendiente Sprint 2)

Ciclos create/destroy completos
Verificar 0 recursos huérfanos
Usar Terraform real con backend local

## Naming Convention

Patrón: ephemeral-pr-{number}-{resource}

Ejemplos para PR 42:
- ephemeral-pr-42-app
- ephemeral-pr-42-proxy
- ephemeral-pr-42-db

Cálculo de puertos (por implementar):
- App: 3000 + PR number
- Proxy: 8000 + PR number  
- DB: 5000 + PR number


Este documento se actualizará conforme avance la implementación.
