terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

locals {
  db_name = "ephemeral-pr-${var.pr_number}-db"
  db_port = var.db_port + (var.pr_number % 100)
  
  # Configuración de base de datos segura
  db_password = "ephemeral_${var.pr_number}_${random_password.db_password.result}"
  db_database = "ephemeral_pr_${var.pr_number}"
}

resource "random_password" "db_password" {
  length  = 16
  special = true
}

resource "docker_image" "db" {
  name = "postgres:15-alpine"
}

resource "docker_volume" "db_data" {
  name = "${local.db_name}-data"
}

resource "docker_container" "db" {
  name  = local.db_name
  image = docker_image.db.image_id

  ports {
    internal = 5432
    external = local.db_port
  }

  env = [
    "POSTGRES_DB=${local.db_database}",
    "POSTGRES_USER=ephemeral_user",
    "POSTGRES_PASSWORD=${local.db_password}",
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

  labels {
    label = "component"
    value = "database"
  }

  volumes {
    volume_name    = docker_volume.db_data.name
    container_path = "/var/lib/postgresql/data"
  }

  # Health check para verificar que la DB está lista
  healthcheck {
    test     = ["CMD-SHELL", "pg_isready -U ephemeral_user -d ${local.db_database}"]
    interval = "30s"
    timeout  = "5s"
    retries  = 3
  }

  depends_on = [docker_image.db, docker_volume.db_data]
}