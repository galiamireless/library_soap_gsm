# Plan de pruebas

- XML predeterminado para `/books`, `/books/minimal` y `/books/concepts`.
- JSON explícito mediante `?format=json`.
- ISBN existente y no existente.
- SOAP con namespace válido, XML inválido y campos sin namespace.
- Autenticación de estadísticas y Fault de clasificación duplicada.
- Inicio de aplicación sin conexión activa a PostgreSQL.
- Respuesta controlada al exceder `MAX_XML_BYTES`.

Las pruebas unitarias usan un repositorio falso; las pruebas de integración se
ejecutan después de cargar `data/library_schema.sql` y `database/library_seed.sql`.
