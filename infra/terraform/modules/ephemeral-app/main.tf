terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

locals {
  app_name = "ephemeral-pr-${var.pr_number}-app"
  app_port = var.app_port + (var.pr_number % 100)
}

resource "docker_image" "app" {
  name = "nginx:alpine"
}

resource "docker_container" "app" {
  name  = local.app_name
  image = docker_image.app.image_id

  ports {
    internal = 80
    external = local.app_port
  }

  networks_advanced {
    name = var.network_name
  }

  env = [
    "PR_NUMBER=${var.pr_number}"
  ]

  labels {
    label = "pr_number"
    value = tostring(var.pr_number)
  }

  labels {
    label = "environment"
    value = "ephemeral"
  }
}