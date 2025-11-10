output "db_name" {
  description = "Nombre del contenedor de base de datos"
  value       = docker_container.db.name
}

output "db_port" {
  description = "Puerto externo de la base de datos"
  value       = docker_container.db.ports[0].external
}

output "db_host" {
  description = "Host de conexión a la base de datos"
  value       = "localhost"
}

output "db_database" {
  description = "Nombre de la base de datos"
  value       = local.db_database
}

output "db_user" {
  description = "Usuario de la base de datos"
  value       = "ephemeral_user"
}

output "db_password" {
  description = "Password de la base de datos"
  value       = local.db_password
  sensitive   = true
}

output "connection_string" {
  description = "String de conexión completo"
  value       = "postgresql://ephemeral_user:${local.db_password}@localhost:${docker_container.db.ports[0].external}/${local.db_database}"
  sensitive   = true
}

output "container_id" {
  description = "ID del contenedor Docker"
  value       = docker_container.db.id
}

output "volume_name" {
  description = "Nombre del volumen de datos"
  value       = docker_volume.db_data.name
}