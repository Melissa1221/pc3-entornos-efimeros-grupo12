module "app" {
  source    = "../../modules/ephemeral-app"
  pr_number = var.pr_number
}

locals {
  stack_name = "ephemeral-pr-${var.pr_number}"
}