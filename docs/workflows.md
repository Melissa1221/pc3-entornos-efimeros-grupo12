# Workflows de GitHub Actions

Documentación de los workflows automatizados para gestión de entornos efímeros.

## Workflows Disponibles

### 1. PR Environment Deploy/Destroy (`pr-deploy.yml`)

**Propósito**: Gestión automática del ciclo de vida de entornos efímeros por PR.

**Triggers**:
- `pull_request`: opened, synchronize, reopened, closed
- `workflow_dispatch`: Ejecución manual

**Jobs**:

#### `deploy`
- **Cuándo se ejecuta**: PR abierto/actualizado
- **Validaciones**: fmt, validate, tflint, tfsec
- **Acciones**:
  - Despliega stack completo (app + proxy + db)
  - Comenta plan en el PR
  - Comenta URLs de acceso
  - Health check de servicios

#### `destroy`
- **Cuándo se ejecuta**: PR cerrado
- **Acciones**:
  - Destruye todos los recursos del stack
  - Verifica limpieza completa (0 recursos huérfanos)
  - Comenta confirmación de destrucción

#### `metrics`
- **Cuándo se ejecuta**: Después de deploy exitoso
- **Acciones**:
  - Registra métricas de despliegue
  - Timestamps de operaciones

### 2. Cleanup Old Stacks (`cleanup-old-stacks.yml`)

**Propósito**: Limpieza automática de stacks antiguos/huérfanos.

**Triggers**:
- `schedule`: Diario a las 2 AM UTC
- `workflow_dispatch`: Ejecución manual

**Proceso**:
1. Busca contenedores ephemeral con más de 72 horas
2. Extrae números de PR de los contenedores
3. Verifica estado de PRs (cerrado/merged/no existe)
4. Destruye stacks de PRs cerrados
5. Limpieza manual como fallback

### 3. CI Pipeline (`ci.yml`)

**Propósito**: Validación continua de código y IaC.

**Jobs**:
- `lint-python`: Black, flake8, pylint
- `lint-terraform`: Format check
- `test`: pytest con coverage ≥90%
- `iac-validation`: terraform validate, tflint, tfsec

## Script Manual (`scripts/manage-stacks.sh`)

**Uso**:
```bash
# Desplegar stack
./scripts/manage-stacks.sh deploy 123

# Destruir stack
./scripts/manage-stacks.sh destroy 123

# Listar stacks activos
./scripts/manage-stacks.sh list

# Limpiar stacks antiguos (>48h)
./scripts/manage-stacks.sh cleanup 48
```

**Características**:
- Validaciones completas de Terraform
- Verificación de dependencias
- Limpieza automática de recursos huérfanos
- Output colorizado
- Manejo de errores

## Flujo de Trabajo Típico

### 1. Apertura de PR
```
PR opened → pr-deploy.yml:deploy
├── Terraform validation
├── Plan generation
├── Plan comment en PR
├── Apply infrastructure
├── Health checks
└── Success comment con URLs
```

### 2. Actualizaciones de PR
```
PR updated → pr-deploy.yml:deploy
├── Re-deploy con cambios
├── Nuevo plan comment
└── URLs actualizadas
```

### 3. Cierre de PR
```
PR closed → pr-deploy.yml:destroy
├── Terraform destroy
├── Verification cleanup
└── Destruction comment
```

### 4. Limpieza Programada
```
Daily 2 AM → cleanup-old-stacks.yml
├── Find containers >72h
├── Check PR status
├── Destroy closed PR stacks
└── Manual cleanup fallback
```

## Configuración Requerida

### Secrets de GitHub
- `GITHUB_TOKEN`: Automático, para comentarios en PRs

### Permisos del Workflow
- `contents: read`: Leer código del repositorio
- `pull-requests: write`: Comentar en PRs
- `issues: write`: Crear/actualizar comentarios

### Dependencias Externas
- Docker (para contenedores)
- Terraform 1.5.0
- tflint (latest)
- tfsec v1.0.0

## Monitoreo y Debugging

### Logs de Deployment
Los workflows generan logs detallados para cada operación:
- Terraform plan output
- Apply/destroy logs
- Health check results
- Cleanup verification

### Métricas Capturadas
- Tiempo de despliegue
- URLs generadas
- Número de recursos creados
- Estado de health checks

### Troubleshooting Común

#### Stack no se destruye completamente
1. Revisar logs de terraform destroy
2. Ejecutar cleanup manual: `./scripts/manage-stacks.sh destroy PR_NUMBER`
3. Verificar docker containers y volumes manualmente

#### Health checks fallan
1. Verificar que containers estén running
2. Revisar logs de containers: `docker logs ephemeral-pr-X-app`
3. Verificar puertos no estén en uso

#### Terraform state lock
1. Revisar si otro workflow está ejecutándose
2. Esperar o cancelar workflow bloqueante
3. State locks se auto-resuelven en 15 minutos

## Mejores Prácticas

### Para Desarrolladores
- Esperar a que termine el deployment antes de hacer push adicionales
- Revisar comentarios de plan antes de merge
- Reportar URLs que no respondan

### Para Administradores
- Monitorear uso de recursos Docker
- Revisar logs de cleanup diarios
- Ajustar max_age_hours según necesidad

### Para CI/CD
- No hacer cambios manuales a recursos gestionados por Terraform
- Usar workflow_dispatch para operaciones de emergencia
- Mantener secrets actualizados