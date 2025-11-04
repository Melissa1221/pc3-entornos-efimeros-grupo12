output "proxy_name" {
  description = "Nombre del contenedor proxy"
  value       = docker_container.proxy.name
}

output "proxy_port" {
  description = "Puerto externo del proxy"
  value       = docker_container.proxy.ports[0].external
}

output "proxy_url" {
  description = "URL completa del proxy"
  value       = "http://localhost:${docker_container.proxy.ports[0].external}"
}

output "container_id" {
  description = "ID del contenedor Docker"
  value       = docker_container.proxy.id
}