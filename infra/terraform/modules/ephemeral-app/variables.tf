variable "pr_number" {
  type        = number
  description = "Pull Request number para naming único"

  validation {
    condition     = var.pr_number > 0
    error_message = "PR number debe ser positivo"
  }
}

variable "app_port" {
  type        = number
  default     = 8000
  description = "Puerto base para la aplicación"
}

variable "network_name" {
  type        = string
  description = "Nombre de la red Docker para conectar contenedores"
}