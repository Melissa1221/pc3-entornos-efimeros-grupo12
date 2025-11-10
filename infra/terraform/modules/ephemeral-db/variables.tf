variable "pr_number" {
  description = "Número de Pull Request para naming único"
  type        = number
  validation {
    condition     = var.pr_number > 0
    error_message = "PR number debe ser positivo."
  }
}

variable "db_port" {
  description = "Puerto base para la base de datos (se suma PR % 100)"
  type        = number
  default     = 5432
}