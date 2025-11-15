# Módulo Terraform: Ephemeral App

Módulo para crear aplicaciones efímeras por Pull Request usando Docker.

## Descripción

Este módulo crea un container Docker con naming único basado en el número de PR, asegurando que cada Pull Request tenga su propia instancia aislada de la aplicación.

## Uso

```hcl
module "app" {
  source    = "../../modules/ephemeral-app"
  pr_number = 123
  app_port  = 8000  # opcional, default: 8000
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| pr_number | Pull Request number para naming único | `number` | n/a | yes |
| app_port | Puerto base para la aplicación | `number` | `8000` | no |

## Outputs

| Name | Description |
|------|-------------|
| app_url | URL local de la aplicación |
| container_name | Nombre del container Docker |
| port | Puerto externo asignado |

## Naming Convention

- **Container**: `ephemeral-pr-{pr_number}-app`
- **Puerto**: `app_port + (pr_number % 100)`

## Validaciones

- `pr_number` debe ser mayor a 0
- Evita colisiones con PRs concurrentes usando modulo 100 para puertos

## Ejemplo

Para PR #123:
- Container: `ephemeral-pr-123-app`
- Puerto: 8023 (8000 + 23)
- URL: `http://localhost:8023`