variable "pr_number" {
  type        = number
  description = "Pull Request number para naming único del stack"

  validation {
    condition     = var.pr_number > 0
    error_message = "PR number debe ser positivo"
  }
}