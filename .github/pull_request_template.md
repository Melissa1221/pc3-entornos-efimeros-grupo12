## ¿Qué se hizo?
[Descripción clara de los cambios realizados]

## ¿Por qué se hizo?
[Justificación técnica del cambio]

## ¿Cómo se implementó?
[Breve explicación de la solución técnica]

## Evidencia
```bash
# Pegar aquí salidas de comandos relevantes
```

## Checklist de PR
- [ ] Convención de commits y link a issue (Fixes #N)
- [ ] Lint y tests verdes, cobertura ≥90%
- [ ] Sin secretos en diffs, .env gestionado correctamente
- [ ] IaC: fmt/validate/tflint/tfsec/plan sin findings High
- [ ] % drift documentado (objetivo: 0%)
- [ ] Patrones DIP aplicados con tests autospec
- [ ] Tarjeta movida a Review-QA, Estimate actualizado

## Políticas de Seguridad
- [ ] Puertos documentados y no hay conflictos
- [ ] No hay secretos hardcodeados (verificado con gitleaks)
- [ ] Naming convention: ephemeral-pr-{number}-{resource}
- [ ] Archivos .tfstate en .gitignore
- [ ] Licencias compatibles verificadas
