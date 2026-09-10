# Convenciones del proyecto

- Mantener el árbol organizado por responsabilidad: `apps/` para ejecución,
  `data/` para el modelo, `database/` para operaciones y `docs/` para diseño.
- El servicio usa PostgreSQL local por defecto y no conoce proveedores cloud.
- Las credenciales siempre viven en variables de entorno; nunca en XML, SQL de
  ejemplo ni documentación.
- Las respuestas de catálogo son XML por defecto y JSON solo cuando se solicita
  `format=json`.
- Toda modificación del contrato debe actualizar el WSDL, XSD, documentación y
  pruebas del servicio.
