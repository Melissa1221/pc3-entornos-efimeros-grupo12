output "app_url" {
  description = "URL local de la aplicación"
  value       = "http://localhost:${local.app_port}"
}

output "container_name" {
  description = "Nombre del container Docker"
  value       = local.app_name
}

output "port" {
  description = "Puerto externo asignado"
  value       = local.app_port
}