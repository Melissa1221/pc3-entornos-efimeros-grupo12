# Stack outputs
output "stack_name" {
  description = "Nombre del stack completo"
  value       = local.stack_name
}

output "pr_number" {
  description = "Número de PR"
  value       = var.pr_number
}

# App outputs
output "app_url" {
  description = "URL de la aplicación"
  value       = module.app.app_url
}

output "app_container" {
  description = "Nombre del contenedor de aplicación"
  value       = module.app.container_name
}

# Proxy outputs
output "proxy_url" {
  description = "URL del proxy (punto de entrada principal)"
  value       = module.proxy.proxy_url
}

output "proxy_container" {
  description = "Nombre del contenedor proxy"
  value       = module.proxy.proxy_name
}

# Database outputs
output "db_host" {
  description = "Host de la base de datos"
  value       = module.db.db_host
}

output "db_port" {
  description = "Puerto de la base de datos"
  value       = module.db.db_port
}

output "db_database" {
  description = "Nombre de la base de datos"
  value       = module.db.db_database
}

output "db_container" {
  description = "Nombre del contenedor de base de datos"
  value       = module.db.db_name
}

# Stack summary
output "stack_urls" {
  description = "URLs principales del stack"
  value = {
    proxy = module.proxy.proxy_url
    app   = module.app.app_url
  }
}

output "stack_containers" {
  description = "Contenedores creados en el stack"
  value = [
    module.app.container_name,
    module.proxy.proxy_name,
    module.db.db_name
  ]
}

# Métricas y monitoreo
output "resource_count" {
  description = "Número total de recursos creados"
  value = {
    containers = 3  # app + proxy + db
    volumes    = 1  # db volume
    networks   = 1  # ephemeral network
    total      = 5
  }
}

output "health_endpoints" {
  description = "Endpoints para verificar salud del entorno"
  value = {
    proxy_health = "${module.proxy.proxy_url}/health"
    app_health   = "${module.app.app_url}/health"
    app_ready    = "${module.app.app_url}/ready"
  }
}

output "metrics_labels" {
  description = "Labels para sistema de métricas"
  value = {
    environment   = "ephemeral"
    pr_number     = var.pr_number
    stack_name    = local.stack_name
    creation_time = timestamp()
  }
}

output "drift_check_info" {
  description = "Información para verificación de drift"
  value = {
    terraform_version = "1.5.0"
    provider_versions = {
      docker = "~> 3.0"
    }
    state_file = "terraform.tfstate"
    last_apply = timestamp()
  }
}