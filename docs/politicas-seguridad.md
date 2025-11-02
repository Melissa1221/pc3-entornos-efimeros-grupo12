# Políticas de Seguridad

## Gestión de Secretos

### Nunca Commitear

Los siguientes archivos y datos nunca deben ser commiteados al repositorio:

- API keys
- Tokens de autenticación
- Passwords o credenciales
- Archivos .env con datos sensibles
- Certificados privados
- Claves SSH privadas

### Usar GitHub Secrets

Para workflows de CI/CD utilizar GitHub Secrets:

```yaml
env:
  API_KEY: ${{ secrets.API_KEY }}
  DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
```

### Archivo .env

El archivo .env debe estar en .gitignore y nunca debe ser commiteado. Crear archivo .env.example con valores placeholder:

```bash
# .env.example
API_KEY=your_api_key_here
DB_PASSWORD=your_password_here
```

## Terraform State

### Archivos Prohibidos

Nunca commitear los siguientes archivos de Terraform:

- *.tfstate
- *.tfstate.backup
- .terraform/
- tfplan

### Configuración

Verificar que .gitignore incluye:

```
.terraform/
*.tfstate
*.tfstate.backup
tfplan
```

### Backend

Este proyecto utiliza backend local para state. En producción considerar backend remoto con:

- S3 + DynamoDB para state locking
- Terraform Cloud
- GitLab Managed Terraform State

## Convención de Nombres

### Formato Obligatorio

Todos los recursos deben seguir la convención:

```
ephemeral-pr-{number}-{resource}
```

### Ejemplos Correctos

- ephemeral-pr-123-app
- ephemeral-pr-123-proxy
- ephemeral-pr-123-db

### Ejemplos Incorrectos

- app-pr-123 (orden incorrecto)
- ephemeral-123-app (falta "pr")
- preview-pr-123-app (palabra incorrecta)

## Asignación de Puertos

### Tabla de Puertos Base

| Servicio | Puerto Base | Cálculo | Ejemplo PR 42 |
|----------|-------------|---------|---------------|
| App      | 8000        | 8000 + (PR % 100) | 8042 |
| Proxy    | 9000        | 9000 + (PR % 100) | 9042 |
| DB       | 5432        | 5432 + (PR % 100) | 5474 |

### Justificación

El módulo evita colisiones entre PRs concurrentes calculando offset basado en PR number. El módulo 100 limita el rango a 100 puertos.

### Verificación de Conflictos

Antes de deploy verificar que puertos no están en uso:

```bash
# Verificar puerto en uso
lsof -i :8042

# Verificar rango de puertos
netstat -tuln | grep -E '80[0-9]{2}|90[0-9]{2}|54[0-9]{2}'
```

## Validación de IaC

### Pipeline Obligatorio

Todo código Terraform debe pasar el siguiente pipeline:

1. terraform fmt -check
2. terraform validate
3. terraform plan
4. tflint
5. tfsec

Solo si todos pasan se permite terraform apply.

### Configuración tflint

Archivo .tflint.hcl debe incluir:

```hcl
plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

rule "terraform_naming_convention" {
  enabled = true
}
```

### Configuración tfsec

Archivo .tfsec.yml debe incluir políticas de:

- No hardcodear credenciales
- Variables sensibles marcadas como sensitive
- Recursos con nombres apropiados

### Findings Bloqueantes

Los siguientes findings bloquean el deploy:

- High severity en tfsec
- Critical severity en tfsec
- Errors en tflint
- Errors en terraform validate

## Detección de Secretos

### Gitleaks

El workflow secrets-scan.yml ejecuta gitleaks en cada push y PR. Si detecta secretos el CI falla.

### Pre-commit Hook

Instalar pre-commit hook localmente:

```bash
pre-commit install
```

El hook ejecuta gitleaks antes de cada commit local.

### Qué Detecta

Gitleaks detecta patrones de:

- AWS keys
- GitHub tokens
- API keys genéricas
- Passwords en código
- Certificados privados

## Dependencias y Licencias

### Verificación de Licencias

Antes de agregar dependencias verificar licencias compatibles:

- MIT: Compatible
- Apache 2.0: Compatible
- BSD: Compatible
- GPL: Requiere revisión legal

### Dependencias Prohibidas

No usar dependencias con:

- Licencias propietarias sin autorización
- Vulnerabilidades conocidas (CVE)
- Falta de mantenimiento (>2 años sin updates)

### Auditoría

Ejecutar regularmente:

```bash
# Python
pip-audit

# npm (si aplica)
npm audit
```

## Control de Acceso

### Permisos de GitHub

- main: Protegida, requiere PR + review
- develop: Protegida, requiere PR
- feature/*: Sin proteccion, desarrollo libre

### Secretos de GitHub

Solo administradores pueden:

- Crear secretos
- Modificar secretos
- Eliminar secretos

### Tokens Personales

Tokens personales (PAT) deben:

- Tener scope mínimo necesario
- Expirar en 90 días o menos
- Nunca ser compartidos
- Ser revocados inmediatamente si se comprometen

## Respuesta a Incidentes

### Si se Commitea un Secreto

1. Revocar inmediatamente el secreto comprometido
2. Generar nuevo secreto
3. Actualizar GitHub Secrets
4. Usar git-filter-repo para eliminar del historial
5. Force push (solo si es necesario y coordinado)
6. Notificar al equipo

### Contacto

Para reportar problemas de seguridad contactar al equipo via issues privados o email directo.

## Cumplimiento

Todos los miembros del equipo deben:

- Leer y entender estas políticas
- Seguir las políticas en todo momento
- Reportar violaciones observadas
- Mantener actualizados sus conocimientos de seguridad
