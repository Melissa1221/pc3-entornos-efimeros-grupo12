# Módulo Ephemeral Proxy

Módulo de Terraform para crear un proxy Nginx efímero por Pull Request.

## Descripción

Este módulo despliega un contenedor Docker con Nginx que actúa como proxy reverso para la aplicación de un PR específico. El proxy balancear el tráfico hacia la aplicación y proporciona endpoints de salud.

## Uso

```hcl
module "ephemeral_proxy" {
  source = "./modules/ephemeral-proxy"
  
  pr_number  = var.pr_number
  proxy_port = 9000
  app_port   = 8000
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| pr_number | Número de Pull Request para naming único | `number` | n/a | yes |
| proxy_port | Puerto base para el proxy (se suma PR % 100) | `number` | `9000` | no |
| app_port | Puerto base de la aplicación que el proxy debe balancear | `number` | `8000` | no |

## Outputs

| Name | Description |
|------|-------------|
| proxy_name | Nombre del contenedor proxy |
| proxy_port | Puerto externo del proxy |
| proxy_url | URL completa del proxy |
| container_id | ID del contenedor Docker |

## Recursos Creados

- `docker_image.proxy`: Imagen de Nginx Alpine
- `docker_container.proxy`: Contenedor del proxy con configuración personalizada

## Convención de Nombres

- Contenedor: `ephemeral-pr-{PR_NUMBER}-proxy`
- Puerto: `{proxy_port} + (PR_NUMBER % 100)`

## Health Check

El proxy incluye un endpoint `/health` que retorna 200 OK para monitoreo.