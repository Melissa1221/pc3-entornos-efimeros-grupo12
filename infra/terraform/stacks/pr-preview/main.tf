terraform {
  required_version = ">= 1.5.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "docker" {}

locals {
  stack_name = "ephemeral-pr-${var.pr_number}"
}

module "app" {
  source    = "../../modules/ephemeral-app"
  pr_number = var.pr_number
}

module "proxy" {
  source     = "../../modules/ephemeral-proxy"
  pr_number  = var.pr_number
  app_port   = module.app.port
  depends_on = [module.app]
}

module "db" {
  source    = "../../modules/ephemeral-db"
  pr_number = var.pr_number
}