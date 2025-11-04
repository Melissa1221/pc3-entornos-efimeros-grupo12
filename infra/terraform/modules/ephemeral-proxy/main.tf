terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

locals {
  proxy_name = "ephemeral-pr-${var.pr_number}-proxy"
  proxy_port = var.proxy_port + (var.pr_number % 100)
  
  nginx_config = <<-EOT
    upstream app {
        server host.docker.internal:${var.app_port + (var.pr_number % 100)};
    }
    
    server {
        listen 80;
        server_name _;
        
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location /health {
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
  EOT
}

resource "docker_image" "proxy" {
  name = "nginx:alpine"
}

resource "docker_container" "proxy" {
  name  = local.proxy_name
  image = docker_image.proxy.image_id

  ports {
    internal = 80
    external = local.proxy_port
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

  labels {
    label = "component"
    value = "proxy"
  }

  upload {
    content = local.nginx_config
    file    = "/etc/nginx/conf.d/default.conf"
  }

  depends_on = [docker_image.proxy]
}