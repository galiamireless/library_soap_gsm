# Auditoría del contrato

| Área | Decisión |
|---|---|
| Catálogo | XML con ISBN, título, autor, año, precio, stock, formato e imagen |
| Conceptos | Concepto, definición, ISBN, libro y géneros asociados |
| SOAP | Document/literal con namespace `urn:udem:library:classifier` |
| Seguridad | UsernameToken para estadísticas por modelo |
| Errores | HTTP coherente en rutas de catálogo y SOAP Fault en `/soap` |
| Compatibilidad | `/cloud-concepts` se conserva como alias de `/books/concepts` |

No se exponen contraseñas, hashes, conexiones SQL ni datos internos de
auditoría.
