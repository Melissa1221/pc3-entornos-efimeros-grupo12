variable "pr_number" {
  description = "Número de Pull Request para naming único"
  type        = number
  validation {
    condition     = var.pr_number > 0
    error_message = "PR number debe ser positivo."
  }
}

variable "proxy_port" {
  description = "Puerto base para el proxy (se suma PR % 100)"
  type        = number
  default     = 9000
}

variable "app_port" {
  description = "Puerto base de la aplicación que el proxy debe balancear"
  type        = number
  default     = 8000
}

variable "network_name" {
  type        = string
  description = "Nombre de la red Docker para conectar contenedores"
}

variable "app_container_name" {
  type        = string
  description = "Nombre del contenedor de la aplicación para proxy reverso"
}