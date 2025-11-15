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
  stack_name   = "ephemeral-pr-${var.pr_number}"
  network_name = "ephemeral-pr-${var.pr_number}-network"
}

resource "docker_network" "stack_network" {
  name = local.network_name
  labels {
    label = "pr_number"
    value = tostring(var.pr_number)
  }
  labels {
    label = "environment"
    value = "ephemeral"
  }
}

module "app" {
  source       = "../../modules/ephemeral-app"
  pr_number    = var.pr_number
  network_name = docker_network.stack_network.name
}

module "proxy" {
  source             = "../../modules/ephemeral-proxy"
  pr_number          = var.pr_number
  app_port           = module.app.port
  app_container_name = module.app.container_name
  network_name       = docker_network.stack_network.name
  depends_on         = [module.app]
}

module "db" {
  source       = "../../modules/ephemeral-db"
  pr_number    = var.pr_number
  network_name = docker_network.stack_network.name
}