```markdown
# Disclaimer sobre los Warnings del Event Broker en Vault

## Contexto Técnico

```sh
[WARN] secrets.kv.kv_61bbc8b8: Error sending event: error="event broker has not been started"
```

Este warning aparece porque Vault está configurado en modo producción pero con una configuración minimalista. Actualmente, tenemos auditoría básica mediante logs de archivo y no requerimos integración con sistemas externos, por lo que el event broker no es necesario.

## Justificación

El event broker es un componente opcional de Vault que se utiliza principalmente para:
- Entornos de producción a gran escala.
- Integración con sistemas de monitorización externos.
- Auditoría avanzada de eventos.

## Por qué es seguro ignorarlo

El proyecto ya implementa auditoría a través de logs de archivo:

```sh
vault audit enable file \
    file_path="${AUDIT_LOG}" \
    mode="0640" \
    log_raw=true
```

Los secretos se almacenan y recuperan correctamente, como se puede ver en los logs:

```sh
Success! Data written to: secret/django/database
Success! Data written to: secret/django/oauth
Success! Data written to: secret/django/email
```

## Decisión de Diseño

Este proyecto se centra en la seguridad básica y la gestión de secretos. Incluir el event broker añadiría una complejidad innecesaria sin aportar beneficios significativos para los requisitos del proyecto.

Esta decisión está alineada con los requisitos del módulo de Cybersecurity del subject, que solo especifica "WAF/ModSecurity with Hardened Configuration and HashiCorp Vault for Secrets Management" sin mencionar requisitos específicos sobre event brokers.
```