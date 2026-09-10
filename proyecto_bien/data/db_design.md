# Diseño de datos

El esquema `library` separa el catálogo de las tablas de auditoría del servicio.
Las tablas `books`, `authors`, `genres`, `formats`, `book_images` y
`book_concepts` describen el catálogo. Las tablas `clasificadores`,
`clasificaciones_cloud` y `clientes_servidos` pertenecen exclusivamente al
servicio SOAP.

Las asociaciones usan claves compuestas donde la relación lo requiere. Una
clasificación referencia la pareja `(concept_id, isbn)` para impedir que se
clasifique un concepto que no pertenece al libro enviado. Los índices se
concentran en búsquedas por título, relaciones de catálogo, clasificador y
modelo Cloud.

El script de semilla es idempotente: puede ejecutarse más de una vez sin
duplicar registros de catálogo.
