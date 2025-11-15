# Módulo Ephemeral Database

Módulo de Terraform para crear una base de datos PostgreSQL efímera por Pull Request.

## Descripción

Este módulo despliega un contenedor Docker con PostgreSQL específico para un PR. Cada instancia tiene credenciales únicas, base de datos aislada y volumen persistente para la duración del PR.

## Uso

```hcl
module "ephemeral_db" {
  source = "./modules/ephemeral-db"
  
  pr_number = var.pr_number
  db_port   = 5432
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| pr_number | Número de Pull Request para naming único | `number` | n/a | yes |
| db_port | Puerto base para la base de datos (se suma PR % 100) | `number` | `5432` | no |

## Outputs

| Name | Description | Sensitive |
|------|-------------|-----------|
| db_name | Nombre del contenedor de base de datos | no |
| db_port | Puerto externo de la base de datos | no |
| db_host | Host de conexión a la base de datos | no |
| db_database | Nombre de la base de datos | no |
| db_user | Usuario de la base de datos | no |
| db_password | Password de la base de datos | yes |
| connection_string | String de conexión completo | yes |
| container_id | ID del contenedor Docker | no |
| volume_name | Nombre del volumen de datos | no |

## Recursos Creados

- `random_password.db_password`: Password único por PR
- `docker_image.db`: Imagen de PostgreSQL 15 Alpine
- `docker_volume.db_data`: Volumen persistente para datos
- `docker_container.db`: Contenedor de base de datos

## Convención de Nombres

- Contenedor: `ephemeral-pr-{PR_NUMBER}-db`
- Base de datos: `ephemeral_pr_{PR_NUMBER}`
- Volumen: `ephemeral-pr-{PR_NUMBER}-db-data`
- Puerto: `{db_port} + (PR_NUMBER % 100)`

## Seguridad

- Password generado aleatoriamente por PR
- Usuario específico (`ephemeral_user`)
- Base de datos aislada por PR
- Outputs sensibles marcados apropiadamente

## Health Check

Incluye health check con `pg_isready` para verificar disponibilidad de la base de datos.